import os
from PyQt6.QtWidgets import (QWidget, QDialog, QVBoxLayout, QLabel, QPushButton, 
                             QFrame, QGridLayout, QGraphicsBlurEffect)
from PyQt6.QtCore import Qt, QRectF, QSize, QThread, pyqtSignal
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
    def __init__(self, image_path, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Full Size Preview")
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.WindowCloseButtonHint)

        self.setStyleSheet(f"background-color: {cf.APP_BACKGROUND};")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setStyleSheet("border: none;")

        pixmap = QPixmap(image_path)
        if not pixmap.isNull():
            max_size = QSize(800, 600)
            if pixmap.width() > max_size.width() or pixmap.height() > max_size.height():
                scaled_pixmap = pixmap.scaled(max_size, Qt.AspectRatioMode.KeepAspectRatio,
                                              Qt.TransformationMode.SmoothTransformation)
                self.image_label.setPixmap(scaled_pixmap)
            else: self.image_label.setPixmap(pixmap)
        else:
            self.image_label.setText("Could not load image.")
            self.image_label.setStyleSheet(f"color: {cf.DARK_TEXT}; font-size: 16px;")

        layout.addWidget(self.image_label)

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        close_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {cf.L_BUTTON_BACKGROUND}; color: white; border-radius: 5px;
                padding: 10px 20px; font-weight: bold; border: none;
            }}
            QPushButton:hover {{opacity: 0.8;}}
        """)
        layout.addWidget(close_btn, 0, Qt.AlignmentFlag.AlignCenter)

class ScoreGauge(QWidget):
    def __init__(self, score, width=200, height=120, parent=None):
        super().__init__(parent)
        self.score = score
        # [CONFIG] Tham số hóa kích thước để tái sử dụng
        self.setFixedSize(width, height) 

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w = self.width()
        h = self.height() * 2 # Vẽ nửa vòng tròn nên nhân đôi chiều cao ảo

        # Padding
        padding = 10 if w > 180 else 5
        rect = QRectF(padding, padding, w - 2*padding, h - 2*padding)

        start_angle = 180 * 16
        span_angle = -180 * 16
        stroke_width = 15 if w > 180 else 12
        
        # 1. Vẽ đường nền (Track)
        pen_track = QPen(QColor(cf.SHADOW_COLOR), stroke_width, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
        painter.setPen(pen_track)
        painter.drawArc(rect, start_angle, span_angle)

        # 2. Xác định màu sắc
        if self.score < 3.0: color = QColor(cf.UNSAFE); status_text = "POTENTIALLY UNSAFE"
        elif 3.0 <= self.score <= 4.0: color = QColor(cf.CAUTION); status_text = "USE WITH CAUTION"
        else: color = QColor(cf.TRUSTED); status_text = "CAN BE TRUSTED"

        # 3. Vẽ giá trị (Value Arc)
        percentage = min(self.score / 5.0, 1.0)
        value_span = -percentage * 180 * 16
        pen_value = QPen(color, stroke_width, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
        painter.setPen(pen_value)
        painter.drawArc(rect, start_angle, int(value_span))

        # 4. Vẽ Text
        painter.setPen(QColor(cf.DARK_TEXT))
        
        # Font size dynamic
        font_size_score = 24 if w > 180 else 18
        font_score = QFont("Arial", font_size_score, QFont.Weight.Bold)
        painter.setFont(font_score)
        
        text_y = 45 if w > 180 else 35
        painter.drawText(QRectF(0, text_y, w, 40), Qt.AlignmentFlag.AlignCenter, f"{self.score}/5.0")

        font_size_status = 8
        font_status = QFont("Arial", font_size_status, QFont.Weight.Bold)
        painter.setFont(font_status)
        painter.setPen(color)
        
        status_y = 85 if w > 180 else 65
        painter.drawText(QRectF(0, status_y, w, 20), Qt.AlignmentFlag.AlignCenter, status_text)
        painter.end()

    def update_ui(self):
        """Hàm này được gọi từ trang cha để vẽ lại gauge theo màu mới"""
        self.update() # Trigger paintEvent

class PreviewImageCard(QFrame):
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
            popup = ImagePopup(self.image_path, self.window())
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