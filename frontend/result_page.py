import os
import json
import time
from datetime import datetime
from . import configuration as cf
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QProgressBar, QDialog, QGraphicsBlurEffect, QGridLayout, QMessageBox,
    QStackedWidget, QScrollArea, QApplication # Import thêm StackedWidget
)
from PyQt6.QtCore import Qt, pyqtSignal, QRectF, QEvent, QSize, QThread, QTimer, QPropertyAnimation, QEasingCurve, QPoint, pyqtProperty, QParallelAnimationGroup, QUrl
from PyQt6.QtGui import QFont, QPainter, QPen, QPixmap, QColor, QDesktopServices, QMouseEvent
from PyQt6.QtWidgets import QGraphicsOpacityEffect

from backend import scoring_system
from backend.config import SCORE_WEIGHTS
from .user_review import ReviewsSection
from .loading_page import LoadingPage

# Custom clickable label for URL handling
class ClickableLabel(QLabel):
    def __init__(self, url, display_text, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.url = url
        self.display_text = display_text
        
        # Normalize URL: add https:// if missing protocol
        if not self.url.startswith(('http://', 'https://')):
            self.url = 'https://' + self.url
        
        # Set clickable cursor
        self.setCursor(Qt.CursorShape.PointingHandCursor)
    
    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            # Left click: Open URL in browser
            QDesktopServices.openUrl(QUrl(self.url))
        elif event.button() == Qt.MouseButton.RightButton:
            # Right click: Copy URL to clipboard
            clipboard = QApplication.clipboard()
            clipboard.setText(self.url)
            
            # Show confirmation dialog
            msg = QMessageBox(self)
            msg.setWindowTitle("Copied")
            msg.setText(f"URL copied to clipboard:\n{self.url}")
            msg.setIcon(QMessageBox.Icon.Information)
            msg.setStandardButtons(QMessageBox.StandardButton.Ok)
            msg.setStyleSheet(f"""
                QMessageBox {{
                    background-color: {cf.APP_BACKGROUND};
                }}
                QMessageBox QLabel {{
                    color: {cf.DARK_TEXT};
                }}
                QPushButton {{
                    background-color: {cf.BUTTON_BACKGROUND};
                    color: #000000;
                    border: none;
                    padding: 8px 16px;
                    border-radius: 4px;
                    font-weight: bold;
                }}
                QPushButton:hover {{
                    background-color: {cf.LINK_TEXT};
                }}
            """)
            msg.exec()
        
        super().mousePressEvent(event)

# Simple explanations for all users (non-IT, children, elders)
CRITERIA_EXPLANATIONS = {
    'Certificate details': {
        'title': 'Certificate Details (Safety Lock Check)',
        'simple': 'Like checking if a store has a real business license on the wall.',
        'details': [
            '<b>Safe:</b> Has official papers proving identity',
            '<b>Why Dangerous?</b> Scammers hide who they are! Without proof of identity, they can steal your money and disappear. Real companies always show their license.',
            '<b>Phishing Trick:</b> Fake websites pretend to be your bank but have no real license - they just want to steal your password!'
        ]
    },
    'Server reliablity': {
        'title': 'Server Reliability (Website Speed & Stability)',
        'simple': 'Like checking if a store is always open and working properly.',
        'details': [
            '<b>Good:</b> Opens fast and works smoothly',
            '<b>Why Suspicious?</b> Scammers use cheap/bad computers that break often! They don\'t care about quality because they\'re only trying to trick you quickly.',
            '<b>Warning Sign:</b> Very slow websites might be infected with viruses or secretly stealing your information in the background!'
        ]
    },
    'Domain age': {
        'title': 'Domain Age (How old is this website?)',
        'simple': 'Like trusting your favorite old restaurant more than a brand new one that opened yesterday.',
        'details': [
            '<b>Safe:</b> Been here 5+ years (old and trusted)',
            '<b>Why Dangerous?</b> Scammers make NEW websites every day! When people discover the scam, they throw away the website and make a new one with a different name.',
            '<b>Red Flag:</b> Website just created yesterday? Could be a trap to steal money from people who don\'t check!'
        ]
    },
    'Domain pattern': {
        'title': 'Domain Pattern (Does the name look fake?)',
        'simple': 'Like seeing a fake "Walmart" spelled "Wa1mart" or "Wal-Mart-cheap.com".',
        'details': [
            '<b>Real:</b> Name spelled correctly',
            '<b>Why Phishing?</b> Scammers copy famous names to trick you! They use "Paypa1.com" (with number 1) instead of "Paypal.com" hoping you won\'t notice.',
            '<b>Common Trick:</b> Adding extra words like "secure-login-amazon.com" - looks safe but it\'s NOT the real Amazon!'
        ]
    },
    'HTML content and behavior': {
        'title': 'HTML Content and Behavior (Does the page look real?)',
        'simple': 'Like checking if a store looks clean and organized, or messy and shady.',
        'details': [
            '<b>Professional:</b> Looks nice and organized',
            '<b>Why Malware?</b> Fake "Download" buttons install viruses on your computer! Too many ads means they\'re trying to trick you into clicking dangerous links.',
            '<b>Danger Signs:</b> Windows popping up saying "Your computer has virus!" - that\'s the REAL virus trying to scare you!'
        ]
    },
    'Protocol security': {
        'title': 'Protocol Security (Is your info private?)',
        'simple': 'Like talking in a locked room (private) vs. shouting in a busy street (everyone hears).',
        'details': [
            '<b>Safe:</b> Info is secret (lock symbol)',
            '<b>Why Steal Info?</b> Without encryption, hackers sitting in cafes can SEE your password when you type it! They can steal your bank account, email, everything!',
            '<b>Big Danger:</b> Typing passwords on sites without lock symbol = giving your keys to strangers on the street!'
        ]
    },
    'AI analysis': {
        'title': 'AI Analysis (Smart computer check)',
        'simple': 'Our smart computer reads the website and warns about lies and scams.',
        'details': [
            '<b>Scam Words We Look For:</b>',
            '• "You won $1000!" = Lie to get your info',
            '• "Hurry! Only 5 minutes!" = Fake rush so you don\'t think carefully',
            '• "Enter your bank card" = Stealing your money directly!',
            '• Bad spelling = Real companies hire professional writers. Scammers don\'t care about quality.'
        ]
    },
    'Reputation Databases': {
        'title': 'Reputation Databases (What do others say?)',
        'simple': 'Like reading restaurant reviews before eating there - do people say good or bad things?',
        'details': [
            '<b>Clean:</b> Nobody reported as dangerous',
            '<b>Why Blacklisted?</b> Security companies found this site stealing passwords, installing viruses, or taking money without sending products!',
            '<b>Warning:</b> If many people got scammed here, you will too! They won\'t suddenly become honest.'
        ]
    },
    'User review': {
        'title': 'User Review (What real people say)',
        'simple': 'Like reading what other customers say - did they have good or bad experience?',
        'details': [
            '<b>Many Happy People:</b> Good experiences',
            '<b>Why Trust Reviews?</b> Real people share their bad experiences to WARN others! If someone says "They stole my money!" - believe them and stay away!',
            '<b>Learn from Others:</b> Don\'t be the next victim - read what happened to people who trusted this site before!'
        ]
    }
}

# --- ANIMATED PROGRESS BAR ---
class AnimatedProgressBar(QProgressBar):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._animated_value = 0
        self.animation = QPropertyAnimation(self, b"animated_value")
        self.animation.setDuration(1500)  # 1.5 seconds
        self.animation.setEasingCurve(QEasingCurve.Type.OutCubic)
    
    def get_animated_value(self):
        return self._animated_value
    
    def set_animated_value(self, value):
        self._animated_value = value
        self.setValue(int(value))
    
    animated_value = pyqtProperty(float, get_animated_value, set_animated_value)
    
    def animateTo(self, target_value):
        self.animation.setStartValue(0)
        self.animation.setEndValue(target_value)
        self.animation.start()

# --- WORKER THREAD ---
class AnalysisWorker(QThread):
    # Signal để gửi dữ liệu về giao diện chính khi xử lý xong (thêm screenshot_paths và error_modules)
    finished_signal = pyqtSignal(float, dict, dict, object, object)  # objects for lists/dicts
    progress_signal = pyqtSignal(str)  # Signal to update loading status

    def __init__(self, url, timeout, retry_count, screenshot_enabled=True):
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
            
            score, criteria, descriptions, screenshot_paths, error_modules = scoring_system.check_url(
                url=self.url, 
                timeout=self.timeout,
                retry_count=self.retry_count,
                screenshot_enabled=self.screenshot_enabled
            )
            # Emit với screenshot_paths và error_modules
            self.finished_signal.emit(score, criteria, descriptions, screenshot_paths, error_modules)
        except Exception as e:
            print(f"Error in analysis thread: {e}")
            import traceback
            traceback.print_exc()
            # Gửi về dữ liệu mặc định hoặc xử lý lỗi tùy ý
            self.finished_signal.emit(0.0, {}, {}, None, {})

# --- POPUP & GRAPH CLASS (Giữ nguyên) ---
class ImagePopup(QDialog):
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
        self.btn_prev.clicked.connect(self._prev_image)
        self.btn_prev.setStyleSheet(f"""
            QPushButton {{
                background-color: rgba(0, 0, 0, 150);
                color: white;
                border: 2px solid white;
                border-radius: 25px;
                font-size: 20px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {cf.BUTTON_BACKGROUND};
                border-color: {cf.BUTTON_BACKGROUND};
            }}
        """)
        self.btn_prev.hide()  # Show on hover
        
        nav_layout.addWidget(self.btn_prev)
        nav_layout.addStretch()
        
        # Right arrow button
        self.btn_next = QPushButton("▶")
        self.btn_next.setFixedSize(50, 50)
        self.btn_next.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_next.clicked.connect(self._next_image)
        self.btn_next.setStyleSheet(f"""
            QPushButton {{
                background-color: rgba(0, 0, 0, 150);
                color: white;
                border: 2px solid white;
                border-radius: 25px;
                font-size: 20px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {cf.BUTTON_BACKGROUND};
                border-color: {cf.BUTTON_BACKGROUND};
            }}
        """)
        self.btn_next.hide()  # Show on hover
        
        nav_layout.addWidget(self.btn_next)
        
        # Stacked widget for image transition
        self.image_stack = QStackedWidget()
        self.image_stack.setStyleSheet(f"background: {cf.IMAGE_BG};")
        
        # Animation for smooth transitions
        self.slide_animation = None
        self.is_animating = False
        
        # Mouse tracking for navigation buttons
        self.image_container.setMouseTracking(True)
        self.image_container.installEventFilter(self)
        
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
    
    def eventFilter(self, obj, event):
        """Show/hide navigation buttons on mouse hover"""
        if obj == self.image_container:
            if event.type() == QEvent.Type.Enter:
                if len(self.screenshots) > 1:
                    self.btn_prev.show()
                    self.btn_next.show()
            elif event.type() == QEvent.Type.Leave:
                self.btn_prev.hide()
                self.btn_next.hide()
        return super().eventFilter(obj, event)
    
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

# --- GRAPH ---
class ScoreGauge(QWidget):
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
        # Giảm font size và hiển thị dạng "4.59/5.0"
        font_score = QFont("Arial", 20, QFont.Weight.Bold)
        painter.setFont(font_score); painter.drawText(QRectF(0, 45, width, 40), Qt.AlignmentFlag.AlignCenter, f"{self.current_score:.2f}/5.0")
        font_status = QFont("Arial", 8, QFont.Weight.Bold)
        painter.setFont(font_status); painter.setPen(color)
        painter.drawText(QRectF(0, 85, width, 20), Qt.AlignmentFlag.AlignCenter, status_text)
        painter.end()

# --- RESULT PAGE (ĐÃ SỬA ĐỔI) ---
class SearchResultsPage(QWidget):
    back_to_home_requested = pyqtSignal()
    write_review_requested = pyqtSignal()
    analysis_finished = pyqtSignal()

    def __init__(self, query, timeout=30, screenshot_enabled=True, parent=None, is_extension_mode=False):
        super().__init__(parent)
        self.query_url = query
        self.timeout = timeout
        self.screenshot_enabled = screenshot_enabled  # User preference from checkbox
        self.is_extension_mode = is_extension_mode  # True if opened from extension
        self.screenshot_data = None  # Will store list of (device_name, path, success)
        self.has_finished_loading = False
        # Biến chứa dữ liệu (sẽ được gán khi thread chạy xong)
        self.score = 0
        self.criteria = {}
        self.descriptions = {}
        self.error_modules = {}  # Track which modules had errors
        self.criteria_bars = []
        self.criteria_widgets = {}

        # Layout chính chứa StackedWidget
        self.layout_main = QVBoxLayout(self)
        self.layout_main.setContentsMargins(0, 0, 0, 0)

        # Sử dụng StackedWidget để chuyển đổi giữa Loading và Result
        self.stack = QStackedWidget()
        self.layout_main.addWidget(self.stack)

        # 1. Tạo màn hình Loading
        self.loading_page = LoadingPage()
        self.stack.addWidget(self.loading_page)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll_area.setStyleSheet("background: transparent;")

        # 2. Tạo màn hình Result (Container rỗng trước)
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(40, 20, 40, 10)
        self.content_layout.setSpacing(20)
        self.content_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)


        self.scroll_area.setWidget(self.content_widget)
        self.stack.addWidget(self.scroll_area)

        # Style chung
        self.setStyleSheet(f"background-color: {cf.APP_BACKGROUND};")

        # Bắt đầu chạy Thread phân tích
        self.start_analysis()

    def start_analysis(self):
        """Khởi tạo và chạy worker thread"""
        from . import configuration as cf
        retry_count = cf.get_retry_count()
        self.worker = AnalysisWorker(self.query_url, self.timeout, retry_count, self.screenshot_enabled)
        self.worker.finished_signal.connect(self.on_analysis_finished)
        self.worker.progress_signal.connect(self.on_progress_update)
        self.worker.start()
    
    def on_progress_update(self, status_text: str):
        """Update loading status when worker reports progress"""
        self.loading_page.update_status(status_text)

    def on_analysis_finished(self, score, criteria, descriptions, screenshot_paths, error_modules):
        """Được gọi khi Worker Thread hoàn thành"""
        self.score = score
        self.criteria = criteria
        self.descriptions = descriptions
        self.error_modules = error_modules or {}  # Store error status
        
        # Check if website is unreachable (quick connectivity check failed)
        if error_modules.get('__website_unreachable__'):
            error_msg = descriptions.get('Connection Error', ['Website is unreachable'])[0]
            # Website cannot be reached - show error dialog
            msg = QMessageBox()
            msg.setWindowTitle("Website Unreachable")
            msg.setText("This site can't be reached")
            msg.setInformativeText(f"Unable to connect to {self.query_url}\n\n{error_msg}")
            msg.setIcon(QMessageBox.Icon.Critical)
            msg.setStandardButtons(QMessageBox.StandardButton.Ok)
            msg.setStyleSheet(f"""
                QMessageBox {{
                    background-color: {cf.APP_BACKGROUND};
                }}
                QMessageBox QLabel {{
                    color: {cf.DARK_TEXT};
                }}
                QPushButton {{
                    background-color: {cf.BUTTON_BACKGROUND};
                    color: #000000;
                    border: none;
                    padding: 8px 16px;
                    border-radius: 4px;
                    font-weight: bold;
                }}
                QPushButton:hover {{
                    background-color: {cf.LINK_TEXT};
                }}
            """)
            msg.exec()
            
            # Emit back signal to close window/return to home
            self.back_to_home_requested.emit()
            return
        
        # Set screenshot data (list of tuples)
        if screenshot_paths:
            self.screenshot_data = screenshot_paths
        
        # Xây dựng giao diện kết quả sau khi đã có dữ liệu
        self.setup_result_ui()
        
        # Chuyển stack sang màn hình kết quả
        self.stack.setCurrentWidget(self.scroll_area)
        
        # Start animations after a short delay
        QTimer.singleShot(100, self._start_animations)
        
        # Start screenshot auto-update timer (check for new screenshots every 2 seconds)
        self.screenshot_check_count = 0
        self.screenshot_timer = QTimer()
        self.screenshot_timer.timeout.connect(self._check_and_update_screenshots)
        self.screenshot_timer.start(2000)  # Check every 2 seconds
        
        self.analysis_finished.emit()
    
    def _check_and_update_screenshots(self):
        """Check for newly downloaded screenshots and update preview if needed"""
        self.screenshot_check_count += 1
        
        # Stop checking after 30 seconds (15 checks * 2s)
        if self.screenshot_check_count > 15:
            self.screenshot_timer.stop()
            return
        
        if not self.screenshot_data:
            return
        
        # Check if any screenshots became available
        updated = False
        for i, (device_name, path, success) in enumerate(self.screenshot_data):
            if not success and os.path.exists(path):
                # Screenshot now exists! Update the tuple
                self.screenshot_data[i] = (device_name, path, True)
                updated = True
        
        # If screenshots were updated and preview is showing "Unavailable", update it
        if updated and hasattr(self, 'lbl_preview_image'):
            current_text = self.lbl_preview_image.text()
            if "Screenshot" in current_text and "Unavailable" in current_text:
                # Try to load first available screenshot
                for device_name, path, success in self.screenshot_data:
                    if success and os.path.exists(path):
                        pixmap = QPixmap(path)
                        if not pixmap.isNull():
                            scaled_pixmap = pixmap.scaled(
                                self.preview_container.size(),
                                Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                                Qt.TransformationMode.SmoothTransformation
                            )
                            self.lbl_preview_image.setPixmap(scaled_pixmap)
                            self.lbl_preview_image.setStyleSheet("border: none; border-radius: 10px;")
                            
                            blur_effect = QGraphicsBlurEffect()
                            blur_effect.setBlurRadius(30)
                            self.lbl_preview_image.setGraphicsEffect(blur_effect)
                            
                            # Show the button
                            if hasattr(self, 'btn_show_image'):
                                self.btn_show_image.show()
                            
                            print(f"[Screenshot] Auto-updated preview with {device_name}")
                            break
    
    def _start_animations(self):
        """Start all animations (gauge and progress bars)"""
        # Animate gauge
        if hasattr(self, 'gauge'):
            self.gauge.start_animation()
        
        # Animate progress bars with staggered delay
        for i, p_bar in enumerate(self.criteria_bars):
            target = p_bar.property("target_value")
            if target is not None:
                QTimer.singleShot(i * 100, lambda bar=p_bar, val=target: bar.animateTo(val))

    def setup_result_ui(self):
        """Hàm này chứa toàn bộ logic vẽ giao diện kết quả (Code cũ trong __init__)"""

        # SECTION 1: SCORING SYSTEM RESULT
        # Truncate URL if too long (max 97 chars + ...)
        display_url = self.query_url if len(self.query_url) <= 100 else self.query_url[:97] + "..."
        
        lbl_url = ClickableLabel(self.query_url, display_url)
        lbl_url.setText(f'<a href="#" style="color: {cf.LINK_TEXT}; text-decoration: underline;">{display_url}</a>')
        lbl_url.setTextFormat(Qt.TextFormat.RichText)
        lbl_url.setStyleSheet(f"font-size: 22px; font-weight: bold;")
        lbl_url.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_url.setWordWrap(True)
        self.content_layout.addWidget(lbl_url)
        
        # Check for redirection and show warning
        redirection_info = self.descriptions.get('Domain age', [])
        final_url = None
        for detail in redirection_info:
            if 'Last url' in detail or 'Redirection' in detail:
                # Extract final URL from details
                if 'Last url:' in detail:
                    final_url = detail.split('Last url:')[-1].strip()
                    break
        
        if final_url and final_url != self.query_url and final_url != display_url:
            # Truncate final URL too if needed
            display_final = final_url if len(final_url) <= 100 else final_url[:97] + "..."
            
            lbl_redirect = ClickableLabel(final_url, display_final)
            lbl_redirect.setText(f'⚠️ Redirection detected! The final link is: <a href="#" style="color: {cf.REDIRECT_WARNING}; text-decoration: underline;">{display_final}</a>')
            lbl_redirect.setTextFormat(Qt.TextFormat.RichText)
            lbl_redirect.setStyleSheet(f"font-size: 13px; color: {cf.REDIRECT_WARNING}; font-weight: bold; margin-top: 5px;")
            lbl_redirect.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl_redirect.setWordWrap(True)
            self.content_layout.addWidget(lbl_redirect)

        sys_container = QHBoxLayout()
        sys_container.setSpacing(60)
        sys_container.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Preview Image
        self.preview_container = QFrame()
        self.preview_container.setFixedSize(280, 158)
        self.preview_container.setStyleSheet(f"background-color: {cf.PREVIEW_BG}; border: 1px solid {cf.BORDER_COLOR}; border-radius: 10px;")

        stack_layout = QGridLayout(self.preview_container)
        stack_layout.setContentsMargins(0, 0, 0, 0)

        self.lbl_preview_image = QLabel()
        self.lbl_preview_image.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_preview_image.setStyleSheet("border: none; border-radius: 10px;")
        self.lbl_preview_image.setScaledContents(True)

        self.btn_show_image = QPushButton("Show Image")
        self.btn_show_image.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_show_image.setStyleSheet(f"""
            QPushButton {{
                background-color: {cf.BUTTON_BACKGROUND};
                color: {cf.WHITE};
                font-weight: bold;
                border-radius: 15px;
                padding: 8px 16px;
                font-size: 12px;
                border: none;
            }}
            QPushButton:hover {{ color: {cf.BLACK}; }}
        """)
        self.btn_show_image.clicked.connect(self.show_full_image)

        # Display first successful screenshot as preview
        preview_loaded = False
        if self.screenshot_data:
            for device_name, path, success in self.screenshot_data:
                if success and os.path.exists(path):
                    pixmap = QPixmap(path)
                    if not pixmap.isNull():
                        scaled_pixmap = pixmap.scaled(
                            self.preview_container.size(),
                            Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                            Qt.TransformationMode.SmoothTransformation
                        )
                        self.lbl_preview_image.setPixmap(scaled_pixmap)

                        blur_effect = QGraphicsBlurEffect()
                        blur_effect.setBlurRadius(30)
                        self.lbl_preview_image.setGraphicsEffect(blur_effect)
                        preview_loaded = True
                        break
        
        if not preview_loaded:
            self.lbl_preview_image.setText("Screenshot\nUnavailable")
            self.lbl_preview_image.setStyleSheet(f"color: {cf.DARK_TEXT}; font-size: 14px; font-weight: bold; border: none;")
            self.btn_show_image.hide()

        stack_layout.addWidget(self.lbl_preview_image, 0, 0)
        stack_layout.addWidget(self.btn_show_image, 0, 0, Qt.AlignmentFlag.AlignCenter)

        self.preview_container.setCursor(Qt.CursorShape.PointingHandCursor)
        self.preview_container.installEventFilter(self)

        sys_container.addWidget(self.preview_container)

        # Gauge + Button Details
        right_col_layout = QVBoxLayout()
        right_col_layout.setSpacing(5)
        right_col_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.gauge = ScoreGauge(self.score)
        right_col_layout.addWidget(self.gauge, 0, Qt.AlignmentFlag.AlignCenter)

        # Score thresholds legend (3 milestones with labels)
        thresholds_layout = QHBoxLayout()
        thresholds_layout.setSpacing(8)
        thresholds_layout.setContentsMargins(0, 5, 0, 0)
        
        # Threshold 1: < 3.0 - POTENTIALLY UNSAFE (Red)
        threshold1_container = QVBoxLayout()
        threshold1_container.setSpacing(2)
        threshold1_container.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        threshold1 = QLabel("< 3.0")
        threshold1.setAlignment(Qt.AlignmentFlag.AlignCenter)
        threshold1.setFixedWidth(100)
        threshold1.setStyleSheet(f"""
            background-color: #ff4444;
            color: white;
            font-size: 11px;
            font-weight: bold;
            padding: 4px 6px;
            border-radius: 4px;
        """)
        
        threshold1_label = QLabel("POTENTIALLY\nUNSAFE")
        threshold1_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        threshold1_label.setFixedWidth(100)
        threshold1_label.setStyleSheet(f"""
            color: #ff4444;
            font-size: 9px;
            font-weight: bold;
            line-height: 1.1;
        """)
        
        threshold1_container.addWidget(threshold1)
        threshold1_container.addWidget(threshold1_label)
        
        # Threshold 2: 3.0-4.0 - USE WITH CAUTION (Yellow)
        threshold2_container = QVBoxLayout()
        threshold2_container.setSpacing(2)
        threshold2_container.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        threshold2 = QLabel("3.0 - 4.0")
        threshold2.setAlignment(Qt.AlignmentFlag.AlignCenter)
        threshold2.setFixedWidth(100)
        threshold2.setStyleSheet(f"""
            background-color: #ffaa00;
            color: white;
            font-size: 11px;
            font-weight: bold;
            padding: 4px 6px;
            border-radius: 4px;
        """)
        
        threshold2_label = QLabel("USE WITH\nCAUTION")
        threshold2_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        threshold2_label.setFixedWidth(100)
        threshold2_label.setStyleSheet(f"""
            color: #ffaa00;
            font-size: 9px;
            font-weight: bold;
            line-height: 1.1;
        """)
        
        threshold2_container.addWidget(threshold2)
        threshold2_container.addWidget(threshold2_label)
        
        # Threshold 3: > 4.0 - CAN BE TRUSTED (Green)
        threshold3_container = QVBoxLayout()
        threshold3_container.setSpacing(2)
        threshold3_container.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        threshold3 = QLabel("> 4.0")
        threshold3.setAlignment(Qt.AlignmentFlag.AlignCenter)
        threshold3.setFixedWidth(100)
        threshold3.setStyleSheet(f"""
            background-color: #00c851;
            color: white;
            font-size: 11px;
            font-weight: bold;
            padding: 4px 6px;
            border-radius: 4px;
        """)
        
        threshold3_label = QLabel("CAN BE\nTRUSTED")
        threshold3_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        threshold3_label.setFixedWidth(100)
        threshold3_label.setStyleSheet(f"""
            color: #00c851;
            font-size: 9px;
            font-weight: bold;
            line-height: 1.1;
        """)
        
        threshold3_container.addWidget(threshold3)
        threshold3_container.addWidget(threshold3_label)
        
        thresholds_layout.addLayout(threshold1_container)
        thresholds_layout.addLayout(threshold2_container)
        thresholds_layout.addLayout(threshold3_container)
        
        right_col_layout.addLayout(thresholds_layout)

        self.btn_details = QPushButton("Show details >>")
        self.btn_details.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_details.setCheckable(True)
        self.btn_details.setStyleSheet(f"""
            QPushButton {{
                color: {cf.LINK_TEXT}; background: transparent; border: none; 
                text-decoration: underline; font-size: 12px;
            }}
            QPushButton:hover {{color: {cf.LINK_TEXT};}}
        """)
        self.btn_details.clicked.connect(self.toggle_details)
        right_col_layout.addWidget(self.btn_details, 0, Qt.AlignmentFlag.AlignCenter)

        sys_container.addLayout(right_col_layout)
        self.content_layout.addLayout(sys_container)

        # Criteria List
        self.criteria_frame = QFrame()
        self.criteria_frame.setVisible(False)
        self.criteria_frame.setFixedWidth(550)
        self.criteria_frame.setStyleSheet(f"background-color: {cf.BAR_BACKGROUND}; border: none;")

        c_layout = QVBoxLayout(self.criteria_frame)
        c_layout.setSpacing(8)
        c_layout.setContentsMargins(25, 15, 25, 15)

        lbl_criteria_title = QLabel("Detailed Criteria Analysis")
        lbl_criteria_title.setStyleSheet(f"font-weight: bold; color: {cf.DARK_TEXT}; font-size: 16px; margin-bottom: 5px;")
        lbl_criteria_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        c_layout.addWidget(lbl_criteria_title)
        
        # Add helpful subtitle
        lbl_subtitle = QLabel('💡 Click on any item to learn more (<b>The top ones are the most important</b>)')
        lbl_subtitle.setTextFormat(Qt.TextFormat.RichText)
        lbl_subtitle.setStyleSheet(f"color: {cf.LINK_TEXT}; font-size: 13px; font-style: italic; margin-bottom: 10px;")
        lbl_subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        c_layout.addWidget(lbl_subtitle)

        criteria_names = [
            'Certificate details', 'Server reliablity', 'Domain age',
            'Domain pattern', 'HTML content and behavior', 'Protocol security',
            'AI analysis', 'Reputation Databases', 'User review'
        ]

        self.criteria_bars = []
        
        # Calculate total weight for percentage
        total_weight = sum(SCORE_WEIGHTS.values())
        
        # Sort criteria by percentage (weight) descending
        criteria_with_percentage = [(name, (SCORE_WEIGHTS.get(name, 0.0) / total_weight) * 100) for name in criteria_names]
        criteria_with_percentage.sort(key=lambda x: x[1], reverse=True)
        sorted_criteria_names = [item[0] for item in criteria_with_percentage]

        for name in sorted_criteria_names:
            # Kiểm tra xem name có trong dict criteria không để tránh lỗi
            score_val = self.criteria.get(name, 0.0)
            weight = SCORE_WEIGHTS.get(name, 0.0)
            percentage = (weight / total_weight) * 100
            
            # Check if this module had an error or no data
            error_status = self.error_modules.get(name, False)
            has_error = error_status is True
            has_no_data = error_status == 'no-data'

            row = QHBoxLayout()
            row.setSpacing(8)
            
            # Clickable rich-text label with name and percentage (bolded including parentheses)
            # If error, show in red; if no data, show in yellow/orange
            if has_error:
                btn_name = QLabel(f"❌ {name} <b>({percentage:.0f}%)</b> <i style='color:{cf.ERROR_TEXT};'>(Error)</i>")
                label_color = cf.ERROR_TEXT  # Red for errors
                hover_bg = "rgba(255, 68, 68, 0.1)"
            elif has_no_data:
                btn_name = QLabel(f"⚠️ {name} <b>({percentage:.0f}%)</b> <i style='color:{cf.WARNING_TEXT};'>(No data)</i>")
                label_color = cf.WARNING_TEXT  # Orange/yellow for no data
                hover_bg = "rgba(255, 152, 0, 0.1)"
            else:
                btn_name = QLabel(f"{name} <b>({percentage:.0f}%)</b>")
                label_color = cf.DARK_TEXT
                hover_bg = "rgba(0, 123, 255, 0.1)"
            
            btn_name.setTextFormat(Qt.TextFormat.RichText)
            btn_name.setCursor(Qt.CursorShape.PointingHandCursor)
            btn_name.setStyleSheet(f"""
                QLabel {{
                    color: {label_color}; font-size: 14px; padding: 2px; border: none;
                }}
                QLabel:hover {{ 
                    color: {cf.LINK_TEXT if not (has_error or has_no_data) else label_color}; 
                    background-color: {hover_bg};
                    border-radius: 4px;
                }}
            """)
            tooltip_text = "Click to learn about " + name
            if has_error:
                tooltip_text += " (Module failed - excluded from score)"
            elif has_no_data:
                tooltip_text += " (No data available - excluded from score)"
            btn_name.setToolTip(tooltip_text)
            btn_name.mousePressEvent = lambda event, n=name: self.show_criteria_info(n)

            p_bar = AnimatedProgressBar()
            p_bar.setRange(0, 100)
            p_bar.setValue(0)  # Start at 0 for animation
            p_bar.setTextVisible(True)
            
            # Set format and color based on status
            if has_error:
                p_bar.setFormat("Error")
                bar_bg = cf.ERROR_BG  # Light red background
                bar_chunk = cf.ERROR_TEXT  # Red chunk
            elif has_no_data:
                p_bar.setFormat("No data")
                bar_bg = cf.WARNING_BG  # Light yellow background
                bar_chunk = cf.WARNING_TEXT  # Orange chunk
            else:
                p_bar.setFormat(f"{score_val:.1f}/10")
                bar_bg = cf.PREVIEW_BG
                bar_chunk = cf.HEADER_BACKGROUND
            
            p_bar.setFixedHeight(10)
            p_bar.setFixedWidth(250)
            p_bar.setCursor(Qt.CursorShape.PointingHandCursor)
            p_bar.setStyleSheet(f"""
                QProgressBar {{
                    border: 1px solid {cf.BORDER_COLOR}; border-radius: 5px;
                    text-align: center; color: black; background-color: {bar_bg}; font-size: 11px;
                }}
                QProgressBar::chunk {{ background-color: {bar_chunk}; border-radius: 5px; }}
            """)

            p_bar.installEventFilter(self)
            p_bar.setProperty("criteria_name", name)
            p_bar.setProperty("target_value", int(score_val * 10))
            self.criteria_bars.append(p_bar)
            # Save widgets for dynamic updates
            self.criteria_widgets[name] = (btn_name, p_bar)

            row.addWidget(btn_name)
            row.addStretch()
            row.addWidget(p_bar)
            c_layout.addLayout(row)

        self.content_layout.addWidget(self.criteria_frame, 0, alignment=Qt.AlignmentFlag.AlignCenter)

        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        line.setStyleSheet(f"background-color: {cf.SHADOW_COLOR}; max-height: 1px;")
        line.setFixedWidth(600)
        self.content_layout.addWidget(line, 0, alignment=Qt.AlignmentFlag.AlignCenter)

        # SECTION 2: USER REVIEWS
        review_header_layout = QHBoxLayout()
        lbl_review_title = QLabel("Reviews")
        lbl_review_title.setStyleSheet(f"font-size: 24px; font-weight: bold; color: {cf.NORMAL_TITLE};")
        review_header_layout.addWidget(lbl_review_title)

        review_header_layout.addStretch()

        btn_write = QPushButton("+ Write Review")
        btn_write.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_write.setFixedSize(130, 32)
        btn_write.setStyleSheet(f"""
            QPushButton {{
                background-color: {cf.BUTTON_BACKGROUND}; color: {cf.WHITE}; border-radius: 16px;
                padding: 5px 10px; font-weight: bold; font-size: 12px;
            }}
            QPushButton:hover {{color: {cf.BLACK};}}
        """)
        btn_write.clicked.connect(self.write_review_requested.emit)
        review_header_layout.addWidget(btn_write)

        self.content_layout.addLayout(review_header_layout)

        self.reviews_section = ReviewsSection(grid_columns=3, load_increment=6)
        # Listen for review changes to update score & UI
        try:
            self.reviews_section.reviews_changed.connect(self.on_reviews_changed)
        except Exception:
            pass
        self.content_layout.addWidget(self.reviews_section)
        
        # Load reviews from Firebase for this URL before displaying
        from backend import review
        review.get_reviews(self.query_url)
        self.reviews_section.display_reviews()
        # Footer
        btn_back_text = "Close" if self.is_extension_mode else "Back to Home Page"
        btn_back = QPushButton(btn_back_text)
        btn_back.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_back.setStyleSheet(f"""
            QPushButton {{
                background-color: {cf.BUTTON_BACKGROUND};
                color: {cf.WHITE};
                border-radius: 8px;
                padding: 10px 25px;
                font-size: 14px; font-weight: bold;
            }}
            QPushButton:hover {{color: {cf.BLACK}}}
        """)
        btn_back.clicked.connect(self.back_to_home_requested.emit)
        self.content_layout.addWidget(btn_back, 0, alignment=Qt.AlignmentFlag.AlignCenter)

    def toggle_details(self, checked):
        if checked:
            self.criteria_frame.setVisible(True)
            self.btn_details.setText("<< Hide details")
        else:
            self.criteria_frame.setVisible(False)
            self.btn_details.setText("Show details >>")

    def on_reviews_changed(self):
        """Recalculate the 'User review' component and update overall score/UI with animations."""
        try:
            from backend import calculate_score
            from . import scoring_system
            from .config import SCORE_WEIGHTS
        except Exception:
            # Fallback imports
            from backend import calculate_score
            import backend.scoring_system as scoring_system
            from backend.config import SCORE_WEIGHTS

        # Recompute review_score using current reviews data
        report = calculate_score.review_score(self.reviews_section.reviews_data)

        # Update descriptions and criteria value
        self.descriptions['User review'] = report.get('details', ["<b>Status:</b> No data available"])
        score_val = report.get('score', 0.0)

        # Detect no-data marker (report may use NO-DATA text)
        details_text = ' '.join(self.descriptions['User review']).lower()
        if len(self.reviews_section.reviews_data) == 0 or 'no-data' in details_text or 'no data' in details_text:
            # mark as no-data so it's excluded from scoring
            self.error_modules['User review'] = 'no-data'
            self.criteria['User review'] = 0.0
        else:
            self.error_modules['User review'] = False
            # report['score'] is 0.0-1.0 -> convert to 0-10
            try:
                self.criteria['User review'] = round(score_val * 10, 1)
            except Exception:
                self.criteria['User review'] = 0.0

        # Build a lightweight results dict to recalc final verdict
        results = {}
        for crit in SCORE_WEIGHTS.keys():
            comp_score = self.criteria.get(crit, 0.0)
            # If excluded, set sub-score to None to indicate no-data
            if self.error_modules.get(crit) == 'no-data':
                sub = None
            else:
                sub = comp_score / 10.0 if comp_score is not None else 0.0
            results[crit] = {
                'score': sub,
                'details': self.descriptions.get(crit, ["<b>Status:</b> No data available"])
            }

        # Recalculate final verdict using existing scoring logic
        try:
            final_score, comp_scores, details, error_modules = scoring_system.calculate_final_verdict(results)
        except Exception:
            # If calculation fails, leave UI unchanged
            return

        # Update stored state
        self.score = final_score
        # comp_scores are 0-10 numbers
        self.criteria = comp_scores
        self.descriptions = details
        self.error_modules = error_modules

        # Update gauge with animation
        try:
            if hasattr(self, 'gauge'):
                self.gauge.target_score = self.score if self.score is not None else 0.0
                self.gauge.start_animation()
        except Exception:
            pass

        # Update each criterion's label and progress bar with animation
        for i, (name, widgets) in enumerate(self.criteria_widgets.items()):
            try:
                btn_name, p_bar = widgets
                weight = SCORE_WEIGHTS.get(name, 0.0)
                total_weight = sum(SCORE_WEIGHTS.values())
                percentage = (weight / total_weight) * 100 if total_weight > 0 else 0

                err_status = self.error_modules.get(name, False)
                has_error = err_status is True
                has_no_data = err_status == 'no-data'

                # Update label text + style
                if has_error:
                    new_text = f"❌ {name} <b>({percentage:.0f}%)</b> <i style='color:{cf.ERROR_TEXT};'>(Error)</i>"
                    label_color = cf.ERROR_TEXT
                elif has_no_data:
                    new_text = f"⚠️ {name} <b>({percentage:.0f}%)</b> <i style='color:{cf.WARNING_TEXT};'>(No data)</i>"
                    label_color = cf.WARNING_TEXT
                else:
                    comp_val = self.criteria.get(name, 0.0)
                    new_text = f"{name} <b>({percentage:.0f}%)</b>"
                    label_color = cf.DARK_TEXT

                btn_name.setText(new_text)
                btn_name.setStyleSheet(f"""
                    color: {label_color}; 
                    font-size: 14px; 
                    padding: 2px; 
                    border: none;
                    text-align: left;
                """)
                tooltip_text = "Click to learn about " + name
                if has_error:
                    tooltip_text += " (Module failed - excluded from score)"
                elif has_no_data:
                    tooltip_text += " (No data available - excluded from score)"
                btn_name.setToolTip(tooltip_text)

                # Update progress bar display
                # Determine new numeric target (0-100)
                new_score_0_10 = self.criteria.get(name, 0.0) or 0.0
                new_value = int(new_score_0_10 * 10)

                if has_error:
                    p_bar.setFormat("Error")
                    bar_bg = cf.ERROR_BG
                    bar_chunk = cf.ERROR_TEXT
                elif has_no_data:
                    p_bar.setFormat("No data")
                    bar_bg = cf.WARNING_BG
                    bar_chunk = cf.WARNING_TEXT
                else:
                    p_bar.setFormat(f"{new_score_0_10:.1f}/10")
                    bar_bg = cf.PREVIEW_BG
                    bar_chunk = cf.HEADER_BACKGROUND

                p_bar.setStyleSheet(f"""
                    QProgressBar {{
                        border: 1px solid {cf.BORDER_COLOR}; 
                        border-radius: 5px; 
                        text-align: center; 
                        color: black; 
                        background-color: {bar_bg}; 
                        font-size: 11px;
                    }}
                    QProgressBar::chunk {{
                        background-color: {bar_chunk}; 
                        border-radius: 5px;
                    }}
                """)
                p_bar.setProperty("target_value", new_value)
                
                # Animate with staggered delay (100ms per item)
                try:
                    QTimer.singleShot(i * 100, lambda bar=p_bar, val=new_value: bar.animateTo(val))
                except Exception:
                    p_bar.setValue(new_value)
            except Exception as e:
                print(f"Error updating criterion {name}: {e}")
                continue

    def show_criteria_info(self, criteria_name):
        """Show detailed information for a criterion in a friendly popup dialog"""
        # Get user-friendly explanation
        explanation = CRITERIA_EXPLANATIONS.get(criteria_name, {})
        icon = explanation.get('icon', '📋')
        title = explanation.get('title', criteria_name)
        simple = explanation.get('simple', 'Analysis of this security criteria.')
        general_details = explanation.get('details', [])
        
        # Get actual scan results
        scan_results = self.descriptions.get(criteria_name, [])
        score_val = self.criteria.get(criteria_name, 0.0)
        weight = SCORE_WEIGHTS.get(criteria_name, 0.0)
        total_weight = sum(SCORE_WEIGHTS.values())
        percentage = (weight / total_weight) * 100
        
        # Create custom dialog
        dialog = QDialog(self)
        dialog.setWindowTitle(f"{icon} {title}")
        dialog.setMinimumWidth(750)
        dialog.setStyleSheet(f"QDialog {{ background-color: {cf.APP_BACKGROUND}; color: {cf.DARK_TEXT}; }}")
        
        main_layout = QVBoxLayout(dialog)
        main_layout.setContentsMargins(25, 25, 25, 25)
        main_layout.setSpacing(15)
        
        # Header section
        # Icon
        icon_label = QLabel(icon)
        icon_label.setStyleSheet("font-size: 48px; background: transparent;")
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(icon_label)
        
        # Title
        title_label = QLabel(title)
        title_label.setStyleSheet(f"font-size: 20px; font-weight: bold; color: {cf.LINK_TEXT}; background: transparent;")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(title_label)
        
        # Simple explanation
        simple_label = QLabel(simple)
        simple_label.setWordWrap(True)
        simple_label.setStyleSheet(f"font-size: 13px; color: {cf.LIGHT_TEXT}; font-style: italic; background: transparent;")
        simple_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        main_layout.addWidget(simple_label)
        
        # Separator
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setStyleSheet(f"background-color: {cf.SHADOW_COLOR};")
        main_layout.addWidget(line)
        
        # Score and weight
        score_label = QLabel(f"<b>Score:</b> {score_val:.1f}/10 | <b>Weight:</b> {percentage:.0f}% of total analysis")
        score_label.setStyleSheet(f"font-size: 13px; color: {cf.DARK_TEXT}; background: transparent;")
        main_layout.addWidget(score_label)
        
        # Two-column layout for content
        content_layout = QHBoxLayout()
        content_layout.setSpacing(20)
        
        # LEFT COLUMN: What we check
        left_scroll = QScrollArea()
        left_scroll.setWidgetResizable(True)
        left_scroll.setStyleSheet(f"""
            QScrollArea {{
                border: 1px solid {cf.SHADOW_COLOR}; 
                border-radius: 5px; 
                background-color: {cf.BAR_BACKGROUND};
            }}
            QScrollBar:vertical {{
                background-color: {cf.BAR_BACKGROUND};
                width: 12px;
                border: none;
            }}
            QScrollBar::handle:vertical {{
                background-color: {cf.SHADOW_COLOR};
                border-radius: 6px;
                min-height: 20px;
            }}
            QScrollBar::handle:vertical:hover {{
                background-color: {cf.LINK_TEXT};
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0px;
            }}
        """)
        left_scroll.setMaximumHeight(400)
        left_scroll.setMinimumWidth(130)
        
        left_content = QWidget()
        left_content.setStyleSheet(f"background-color: {cf.BAR_BACKGROUND};")
        left_layout = QVBoxLayout(left_content)
        left_layout.setContentsMargins(15, 15, 15, 15)
        left_layout.setSpacing(8)
        
        check_title = QLabel("Easy Explanation:")
        check_title.setStyleSheet(f"font-size: 14px; font-weight: bold; color: {cf.DARK_TEXT}; background: transparent;")
        left_layout.addWidget(check_title)
        
        for detail in general_details:
            detail_label = QLabel(f"• {detail}")
            detail_label.setWordWrap(True)
            detail_label.setTextFormat(Qt.TextFormat.RichText)
            detail_label.setStyleSheet(f"font-size: 12px; color: {cf.DARK_TEXT}; margin-left: 5px; background: transparent;")
            left_layout.addWidget(detail_label)
        
        left_layout.addStretch()
        left_scroll.setWidget(left_content)
        content_layout.addWidget(left_scroll)
        
        # RIGHT COLUMN: This Website Results
        right_scroll = QScrollArea()
        right_scroll.setWidgetResizable(True)
        right_scroll.setStyleSheet(f"""
            QScrollArea {{
                border: 1px solid {cf.SHADOW_COLOR}; 
                border-radius: 5px; 
                background-color: {cf.BAR_BACKGROUND};
            }}
            QScrollBar:vertical {{
                background-color: {cf.BAR_BACKGROUND};
                width: 12px;
                border: none;
            }}
            QScrollBar::handle:vertical {{
                background-color: {cf.SHADOW_COLOR};
                border-radius: 6px;
                min-height: 20px;
            }}
            QScrollBar::handle:vertical:hover {{
                background-color: {cf.LINK_TEXT};
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0px;
            }}
        """)
        right_scroll.setMaximumHeight(900)
        right_scroll.setMinimumWidth(330)
        
        right_content = QWidget()
        right_content.setStyleSheet(f"background-color: {cf.BAR_BACKGROUND};")
        right_layout = QVBoxLayout(right_content)
        right_layout.setContentsMargins(15, 15, 15, 15)
        right_layout.setSpacing(8)
        
        results_title = QLabel("🔍 This Website Results:")
        results_title.setStyleSheet(f"font-size: 14px; font-weight: bold; color: {cf.DARK_TEXT}; background: transparent;")
        right_layout.addWidget(results_title)
        
        if scan_results:
            for result in scan_results[:10]:  # Show up to 10 results
                result_label = QLabel(f"• {result}")
                result_label.setWordWrap(True)
                result_label.setTextFormat(Qt.TextFormat.RichText)
                result_label.setStyleSheet(f"font-size: 12px; color: {cf.DARK_TEXT}; margin-left: 5px; background: transparent;")
                right_layout.addWidget(result_label)
        else:
            no_data = QLabel("No specific results available for this website.")
            no_data.setWordWrap(True)
            no_data.setStyleSheet(f"font-size: 12px; color: {cf.LIGHT_TEXT}; font-style: italic; margin-left: 5px; background: transparent;")
            right_layout.addWidget(no_data)
        
        right_layout.addStretch()
        right_scroll.setWidget(right_content)
        content_layout.addWidget(right_scroll)
        
        main_layout.addLayout(content_layout)
        
        # OK button
        btn_ok = QPushButton("Got it!")
        btn_ok.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_ok.setFixedHeight(35)
        btn_ok.setStyleSheet(f"""
            QPushButton {{
                background-color: {cf.BUTTON_BACKGROUND};
                color: {cf.WHITE};
                border: none;
                border-radius: 6px;
                padding: 8px 25px;
                font-weight: bold;
                font-size: 13px;
            }}
            QPushButton:hover {{
                background-color: {cf.LINK_TEXT};
                color: {cf.BLACK};
            }}
        """)
        btn_ok.clicked.connect(dialog.accept)
        main_layout.addWidget(btn_ok, 0, Qt.AlignmentFlag.AlignCenter)
        
        dialog.exec()

    def eventFilter(self, source, event):
        if (event.type() == QEvent.Type.MouseButtonPress and
                source is self.preview_container and
                event.button() == Qt.MouseButton.LeftButton):

            if self.screenshot_data: self.show_full_image()
            return True

        if (event.type() == QEvent.Type.MouseButtonPress and
                source in self.criteria_bars and
                event.button() == Qt.MouseButton.LeftButton):

            name = source.property("criteria_name")
            if name: self.show_criteria_info(name)
            return True

        return super().eventFilter(source, event)

    def show_full_image(self):
        if self.screenshot_data:
            popup = ImagePopup(self.screenshot_data, self.window())
            popup.exec()

    def update_ui(self):
        self.setStyleSheet(f"background-color: {cf.APP_BACKGROUND};")

    def add_user_review(self, score, comment):
        if not comment:
            comment = "No comment provided."
        self.reviews_section.add_review(self.query_url, score, comment, datetime.now())
        self.reviews_section.display_reviews()

    def delete_user_review(self, username): self.reviews_section.remove_review_by_user(username)