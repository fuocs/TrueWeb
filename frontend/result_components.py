# frontend/result_components.py
# Unified components used by both result_page and respond_window

import os
from PyQt6.QtWidgets import (QWidget, QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
                             QFrame, QGridLayout, QGraphicsBlurEffect, QScrollArea, QStackedWidget)
from PyQt6.QtCore import Qt, QRectF, QSize, QThread, pyqtSignal, QEvent, QPoint, QTimer, QPropertyAnimation, QEasingCurve, QParallelAnimationGroup
from PyQt6.QtGui import QPainter, QPen, QColor, QFont, QPixmap, QCursor

from frontend import configuration as cf
from frontend.UI_helpers import get_asset_path
from backend import scoring_system

class AnalysisWorker(QThread):
    """
    Unified AnalysisWorker for both result_page and respond_window.
    Supports full analysis with screenshots, progress updates, and error handling.
    """
    # Signal để gửi dữ liệu về giao diện chính khi xử lý xong
    finished_signal = pyqtSignal(float, dict, dict, object, object)  # score, criteria, descriptions, screenshot_paths, error_modules
    progress_signal = pyqtSignal(str)  # Signal to update loading status

    def __init__(self, url, timeout=10, retry_count=3, screenshot_enabled=True):
        super().__init__()
        self.url = url
        self.timeout = timeout
        self.retry_count = retry_count
        self.screenshot_enabled = screenshot_enabled

    def run(self):
        try:
            # Step 1: Check if website is reachable
            self.progress_signal.emit("Checking if website is reachable...")
            from backend.scoring_system import quick_connectivity_check
            is_reachable, error_msg = quick_connectivity_check(self.url, timeout=5)
            
            if not is_reachable:
                # Website unreachable
                error_modules = {'__website_unreachable__': True}
                descriptions = {'Connection Error': [error_msg]}
                self.finished_signal.emit(0.0, {}, descriptions, None, error_modules)
                return
            
            self.progress_signal.emit("Analyzing website...")
            
            # Step 2: Full analysis with screenshots
            score, criteria, descriptions, screenshot_paths, error_modules = scoring_system.check_url(
                url=self.url, 
                timeout=self.timeout,
                retry_count=self.retry_count,
                screenshot_enabled=self.screenshot_enabled
            )
            
            # Emit complete results
            self.finished_signal.emit(score, criteria, descriptions, screenshot_paths, error_modules)
            
        except Exception as e:
            print(f"Error in analysis thread: {e}")
            import traceback
            traceback.print_exc()
            # Gửi về dữ liệu mặc định
            self.finished_signal.emit(0.0, {}, {}, None, {})


class ImagePopup(QDialog):
    """
    Full-featured image popup with screenshot carousel, zoom, and navigation.
    Supports multiple device screenshots with smooth transitions.
    """
    def __init__(self, screenshot_data, parent=None):
        """
        screenshot_data: list of tuples (device_name, path, success)
        """
        super().__init__(parent)
        self.setWindowTitle("Website Screenshots")
        self.setWindowFlags(Qt.WindowType.Window)
        
        # Filter successful screenshots
        self.screenshots = [(name, path) for name, path, success in screenshot_data if success and os.path.exists(path)]
        self.current_index = 0
        
        # Zoom tracking
        self.zoom_scales = []
        self.original_pixmaps = []
        
        if not self.screenshots:
            # No valid screenshots
            self.setMinimumSize(400, 300)
            layout = QVBoxLayout(self)
            error_label = QLabel("No screenshots available")
            error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            error_label.setStyleSheet(f"color: {cf.DARK_TEXT}; font-size: 16px;")
            layout.addWidget(error_label)
            return
        
        # Set minimum size and initial size
        self.setMinimumSize(600, 400)
        self.resize(1000, 800)

        self.setStyleSheet(f"""
            QDialog {{
                background-color: {cf.APP_BACKGROUND};
            }}
        """)

        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Image container with navigation
        self.image_container = QWidget()
        self.image_container.setStyleSheet(f"background: {cf.IMAGE_BG};")
        container_layout = QVBoxLayout(self.image_container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(0)
        
        # Navigation layer (overlay on image)
        nav_widget = QWidget()
        nav_widget.setStyleSheet("background: transparent;")
        nav_layout = QHBoxLayout(nav_widget)
        nav_layout.setContentsMargins(10, 0, 10, 0)
        
        # Left arrow button
        self.btn_prev = QPushButton("◀")
        self.btn_prev.setFixedSize(50, 50)
        self.btn_prev.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_prev.setFocusPolicy(Qt.FocusPolicy.NoFocus)  # Prevent button from taking focus
        self.btn_prev.clicked.connect(self._prev_image)
        self.btn_prev.setStyleSheet(f"""
            QPushButton {{
                background-color: rgba(0, 0, 0, 150);
                color: white;
                border: 2px solid white;
                border-radius: 25px;
                font-size: 20px;
                font-weight: bold;
                outline: none;
            }}
            QPushButton:hover {{
                background-color: {cf.BUTTON_BACKGROUND};
                border-color: {cf.BUTTON_BACKGROUND};
            }}
            QPushButton:focus {{
                outline: none;
                border: 2px solid white;
            }}
        """)
        
        nav_layout.addWidget(self.btn_prev)
        nav_layout.addStretch()
        
        # Right arrow button
        self.btn_next = QPushButton("▶")
        self.btn_next.setFixedSize(50, 50)
        self.btn_next.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_next.setFocusPolicy(Qt.FocusPolicy.NoFocus)  # Prevent button from taking focus
        self.btn_next.clicked.connect(self._next_image)
        self.btn_next.setStyleSheet(f"""
            QPushButton {{
                background-color: rgba(0, 0, 0, 150);
                color: white;
                border: 2px solid white;
                border-radius: 25px;
                font-size: 20px;
                font-weight: bold;
                outline: none;
            }}
            QPushButton:hover {{
                background-color: {cf.BUTTON_BACKGROUND};
                border-color: {cf.BUTTON_BACKGROUND};
            }}
            QPushButton:focus {{
                outline: none;
                border: 2px solid white;
            }}
        """)
        
        nav_layout.addWidget(self.btn_next)
        
        # Stacked widget for image transition
        self.image_stack = QStackedWidget()
        self.image_stack.setStyleSheet(f"background: {cf.IMAGE_BG};")
        
        # Animation for smooth transitions
        self.slide_animation = None
        self.is_animating = False
        
        container_layout.addWidget(self.image_stack)
        container_layout.addWidget(nav_widget)
        
        main_layout.addWidget(self.image_container)
        
        # Device label at bottom
        self.device_label = QLabel()
        self.device_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.device_label.setStyleSheet(f"""
            QLabel {{
                background-color: {cf.HEADER_BACKGROUND};
                color: {cf.HEADER_TITLE};
                padding: 10px;
                font-size: 14px;
                font-weight: bold;
            }}
        """)
        main_layout.addWidget(self.device_label)
        
        # Load all images
        self._load_images()
        self._update_display()
        
        # Set focus to dialog for keyboard events
        self.setFocus()
    
    def _load_images(self):
        """Load all screenshots into stacked widget"""
        for idx, (device_name, path) in enumerate(self.screenshots):
            scroll_area = QScrollArea()
            scroll_area.setWidgetResizable(False)  # Changed to False for zoom control
            scroll_area.setStyleSheet("QScrollArea { border: none; background: transparent; }")
            scroll_area.setAlignment(Qt.AlignmentFlag.AlignCenter)
            
            img_label = QLabel()
            img_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            img_label.setStyleSheet("background: transparent;")
            
            pixmap = QPixmap(path)
            if not pixmap.isNull():
                # Store original pixmap
                self.original_pixmaps.append(pixmap)
                self.zoom_scales.append(1.0)  # Default zoom = 100%
                
                # Scale to fit initially
                max_size = QSize(self.width() - 40, self.height() - 100)
                scaled = pixmap.scaled(max_size, Qt.AspectRatioMode.KeepAspectRatio,
                                      Qt.TransformationMode.SmoothTransformation)
                img_label.setPixmap(scaled)
            else:
                self.original_pixmaps.append(None)
                self.zoom_scales.append(1.0)
            
            # Create wheel event handler with proper closure
            def make_wheel_handler(image_idx):
                return lambda event: self._zoom_image(event, image_idx)
            
            scroll_area.wheelEvent = make_wheel_handler(idx)
            
            scroll_area.setWidget(img_label)
            self.image_stack.addWidget(scroll_area)
    
    def _update_display(self):
        """Update current image and device label"""
        if self.screenshots:
            self.image_stack.setCurrentIndex(self.current_index)
            device_name, _ = self.screenshots[self.current_index]
            self.device_label.setText(f"Captured using: {device_name} ({self.current_index + 1}/{len(self.screenshots)})")
            
            # Update button visibility
            self.btn_prev.setVisible(len(self.screenshots) > 1)
            self.btn_next.setVisible(len(self.screenshots) > 1)
    
    def _prev_image(self):
        """Show previous image with smooth slide animation"""
        if len(self.screenshots) > 1 and not self.is_animating:
            self._slide_to_image((self.current_index - 1) % len(self.screenshots), direction="left")
    
    def _next_image(self):
        """Show next image with smooth slide animation"""
        if len(self.screenshots) > 1 and not self.is_animating:
            self._slide_to_image((self.current_index + 1) % len(self.screenshots), direction="right")
    
    def _slide_to_image(self, new_index, direction="right"):
        """Animate slide transition between images (iPhone-style swipe)"""
        if self.is_animating:
            return
        
        self.is_animating = True
        old_index = self.current_index
        old_widget = self.image_stack.widget(old_index)
        new_widget = self.image_stack.widget(new_index)
        
        # Get widget dimensions
        width = self.image_stack.width()
        
        # Position new widget off-screen based on direction
        if direction == "right":
            # Sliding right: new comes from right, old goes to left
            new_start_x = width
            old_end_x = -width
        else:
            # Sliding left: new comes from left, old goes to right
            new_start_x = -width
            old_end_x = width
        
        # Show both widgets temporarily
        self.image_stack.setCurrentIndex(new_index)
        new_widget.move(new_start_x, 0)
        new_widget.show()
        old_widget.show()
        old_widget.raise_()
        
        # Animate old widget sliding out
        old_anim = QPropertyAnimation(old_widget, b"pos")
        old_anim.setDuration(350)
        old_anim.setStartValue(QPoint(0, 0))
        old_anim.setEndValue(QPoint(old_end_x, 0))
        old_anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        
        # Animate new widget sliding in
        new_anim = QPropertyAnimation(new_widget, b"pos")
        new_anim.setDuration(350)
        new_anim.setStartValue(QPoint(new_start_x, 0))
        new_anim.setEndValue(QPoint(0, 0))
        new_anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        
        # Group animations
        self.slide_animation = QParallelAnimationGroup()
        self.slide_animation.addAnimation(old_anim)
        self.slide_animation.addAnimation(new_anim)
        
        # Update index immediately
        self.current_index = new_index
        self._update_display()
        
        # Cleanup after animation
        def cleanup():
            self.is_animating = False
            # Reset positions
            old_widget.move(0, 0)
            new_widget.move(0, 0)
            # Hide old widget
            old_widget.hide()
        
        self.slide_animation.finished.connect(cleanup)
        self.slide_animation.start()
    
    def _zoom_image(self, event, image_index):
        """Handle mouse wheel for zoom in/out on images"""
        if image_index >= len(self.original_pixmaps) or self.original_pixmaps[image_index] is None:
            return
        
        # Get wheel delta (positive = zoom in, negative = zoom out)
        delta = event.angleDelta().y()
        
        # Calculate zoom factor (10% per scroll tick)
        zoom_factor = 1.1 if delta > 0 else 0.9
        
        # Update zoom scale with limits (10% to 500%)
        old_scale = self.zoom_scales[image_index]
        new_scale = old_scale * zoom_factor
        new_scale = max(0.1, min(5.0, new_scale))  # Clamp between 10% and 500%
        
        self.zoom_scales[image_index] = new_scale
        
        # Get current scroll area and label
        scroll_area = self.image_stack.widget(image_index)
        img_label = scroll_area.widget()
        
        # Calculate new size
        original = self.original_pixmaps[image_index]
        new_width = int(original.width() * new_scale)
        new_height = int(original.height() * new_scale)
        
        # Scale and apply pixmap
        scaled = original.scaled(new_width, new_height,
                                Qt.AspectRatioMode.KeepAspectRatio,
                                Qt.TransformationMode.SmoothTransformation)
        img_label.setPixmap(scaled)
        img_label.adjustSize()
        
        # Keep scroll position centered on mouse
        scroll_x = scroll_area.horizontalScrollBar().value()
        scroll_y = scroll_area.verticalScrollBar().value()
        
        # Adjust scroll to zoom center
        if delta > 0:  # Zooming in
            scroll_area.horizontalScrollBar().setValue(int(scroll_x * zoom_factor))
            scroll_area.verticalScrollBar().setValue(int(scroll_y * zoom_factor))
    
    def keyPressEvent(self, event):
        """Handle keyboard navigation with animation"""
        if not self.is_animating:
            if event.key() == Qt.Key.Key_Left:
                self._prev_image()
            elif event.key() == Qt.Key.Key_Right:
                self._next_image()
            elif event.key() == Qt.Key.Key_Escape:
                self.accept()
            else:
                super().keyPressEvent(event)
        elif event.key() == Qt.Key.Key_Escape:
            self.accept()


class ScoreGauge(QWidget):
    """
    Animated score gauge with color-coded safety levels.
    Supports animation from 0 to target score.
    """
    def __init__(self, score, parent=None):
        super().__init__(parent)
        # Handle None score (unreachable website case)
        self.target_score = score if score is not None else 0.0
        self.current_score = 0.0  # Start from 0
        self.setFixedSize(200, 120)
        
        # Animation timer
        self.animation_timer = QTimer(self)
        self.animation_timer.timeout.connect(self._animate_score)
        self.animation_steps = 0
        self.max_steps = 60  # 60 frames over 1.5 seconds
    
    def start_animation(self):
        """Start score animation from 0 to target"""
        self.current_score = 0.0
        self.animation_steps = 0
        self.animation_timer.start(25)  # 25ms per frame = 40fps
    
    def _animate_score(self):
        """Animate score increment"""
        self.animation_steps += 1
        progress = self.animation_steps / self.max_steps
        
        # Ease out cubic
        eased_progress = 1 - pow(1 - progress, 3)
        self.current_score = self.target_score * eased_progress
        
        self.update()  # Trigger repaint
        
        if self.animation_steps >= self.max_steps:
            self.current_score = self.target_score
            self.animation_timer.stop()
            self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        width = self.width()
        height = self.height() * 2

        rect = QRectF(10, 10, width - 20, height - 20)

        start_angle = 180 * 16
        span_angle = -180 * 16

        pen_track = QPen(QColor(cf.L_LIGHT_TEXT), 15, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
        painter.setPen(pen_track); painter.drawArc(rect, start_angle, span_angle)
        
        # Use target_score for color/status so they don't change during animation
        if self.target_score < 3.0: color = QColor(cf.UNSAFE); status_text = "POTENTIALLY UNSAFE"
        elif 3.0 <= self.target_score <= 4.0: color = QColor(cf.CAUTION); status_text = "USE WITH CAUTION"
        else: color = QColor(cf.TRUSTED); status_text = "CAN BE TRUSTED"
        
        percentage = min(self.current_score / 5.0, 1.0); value_span = -percentage * 180 * 16
        pen_value = QPen(color, 15, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
        painter.setPen(pen_value); painter.drawArc(rect, start_angle, int(value_span))
        painter.setPen(QColor(cf.DARK_TEXT))
        
        # Display score as "4.59/5.0"
        font_score = QFont("Arial", 20, QFont.Weight.Bold)
        painter.setFont(font_score); painter.drawText(QRectF(0, 45, width, 40), Qt.AlignmentFlag.AlignCenter, f"{self.current_score:.2f}/5.0")
        font_status = QFont("Arial", 8, QFont.Weight.Bold)
        painter.setFont(font_status); painter.setPen(color)
        painter.drawText(QRectF(0, 85, width, 20), Qt.AlignmentFlag.AlignCenter, status_text)
        painter.end()


class PreviewImageCard(QFrame):
    """Simple preview image card with blur effect (used in respond_window)"""
    def __init__(self, image_path="fit-logo-chuan-V2 (2).png", width=280, height=158, parent=None):
        super().__init__(parent)
        self.image_path = get_asset_path(image_path)
        self.setFixedSize(width, height)
        
        # Layout chồng (Stack) để hiện nút Show Image lên trên ảnh
        self.main_layout = QGridLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)

        # 1. Ảnh nền
        self.lbl_image = QLabel()
        self.lbl_image.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_image.setStyleSheet("border: none; border-radius: 10px;")
        self.lbl_image.setScaledContents(True)

        # 2. Nút bấm Show Image
        self.btn_show = QPushButton("Show Image")
        self.btn_show.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_show.clicked.connect(self._on_show_clicked)

        # 3. Logic Load ảnh và Blur
        if os.path.exists(self.image_path):
            pixmap = QPixmap(self.image_path)
            if not pixmap.isNull():
                scaled = pixmap.scaled(self.size(), Qt.AspectRatioMode.KeepAspectRatioByExpanding, 
                                       Qt.TransformationMode.SmoothTransformation)
                self.lbl_image.setPixmap(scaled)
                
                # Hiệu ứng mờ
                blur = QGraphicsBlurEffect()
                blur.setBlurRadius(30)
                self.lbl_image.setGraphicsEffect(blur)
            else:
                self.lbl_image.setText("Image Error")
                self.btn_show.hide()
        else:
            self.lbl_image.setText("Preview Not Found")
            self.btn_show.hide()

        # Thêm vào main_layout
        self.main_layout.addWidget(self.lbl_image, 0, 0)
        self.main_layout.addWidget(self.btn_show, 0, 0, Qt.AlignmentFlag.AlignCenter)

        # Sự kiện click vào cả khung
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

        self.update_ui()
    
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._on_show_clicked()
        super().mousePressEvent(event)

    def _on_show_clicked(self):
        if os.path.exists(self.image_path):
            # Note: This uses simple single-image popup, not the full carousel
            popup = QDialog(self.window())
            popup.setWindowTitle("Preview")
            layout = QVBoxLayout(popup)
            img_label = QLabel()
            img_label.setPixmap(QPixmap(self.image_path).scaled(800, 600, Qt.AspectRatioMode.KeepAspectRatio))
            layout.addWidget(img_label)
            popup.exec()

    def update_ui(self):
        self.setStyleSheet("background-color: transparent; border: 1px solid #ccc; border-radius: 10px;")
        self.btn_show.setStyleSheet(f"""
            QPushButton {{
                background-color: {cf.BUTTON_BACKGROUND}; color: white; font-weight: bold;
                border-radius: 12px; padding: 6px 12px; font-size: 11px; border: none;
            }}
            QPushButton:hover {{ opacity: 0.9; }}
        """)


def shorten_url(url, max_length=55):
    """
    Cắt ngắn URL nếu dài quá max_length.
    Ví dụ: https://very-long-domain.../file.html
    """
    if len(url) <= max_length:
        return url
    
    # Trừ đi 3 ký tự cho dấu "..."
    part_len = (max_length - 3) // 2
    
    # Lấy đầu và đuôi, ghép lại
    return f"{url[:part_len]}...{url[-part_len:]}"
