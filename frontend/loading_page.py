from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QRectF
from PyQt6.QtGui import QPainter, QPen, QColor, QConicalGradient
from . import configuration as cf


# --- CUSTOM SPINNER WIDGET ---
class RotatingSpinner(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(60, 60)
        self.angle = 0

        # Timer for animation (rotation)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._rotate)
        self.timer.start(30)  # Rotate every 30ms

    def _rotate(self):
        self.angle = (self.angle + 10) % 360
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Center point
        rect = QRectF(5, 5, self.width() - 10, self.height() - 10)

        # Set up pen
        pen = QPen()
        pen.setWidth(5)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)

        # Use App Theme Color for the spinner
        # Gradient effect for spinning tail
        gradient = QConicalGradient(rect.center(), -self.angle)
        gradient.setColorAt(0, QColor(cf.BUTTON_BACKGROUND))
        gradient.setColorAt(1, Qt.GlobalColor.transparent)

        pen.setBrush(gradient)
        painter.setPen(pen)

        # Draw the full circle arc but strictly controlled by gradient to look like a tail
        painter.drawArc(rect, 0, 360 * 16)
        painter.end()


class LoadingPage(QWidget):
    loading_finished = pyqtSignal()  # Signal when done

    def __init__(self, parent=None):
        super().__init__(parent)

        # Main layout
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Container widget
        self.container = QWidget()
        self.container.setFixedSize(400, 250)
        self.container.setObjectName("Container")

        self.inner_layout = QVBoxLayout(self.container)
        self.inner_layout.setSpacing(20)
        self.inner_layout.setContentsMargins(20, 20, 20, 20)
        self.inner_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Title
        self.lbl_title = QLabel("ANALYZING...")
        self.lbl_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_title.setStyleSheet(
            f"color: {cf.DARK_TEXT}; font-size: 20px; font-weight: bold; background: transparent;")
        self.inner_layout.addWidget(self.lbl_title)

        # --- UPDATE: Replace ProgressBar with Spinner ---
        self.spinner = RotatingSpinner()
        self.inner_layout.addWidget(self.spinner, 0, Qt.AlignmentFlag.AlignCenter)

        # Status text
        self.lbl_status = QLabel("Processing data...")
        self.lbl_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_status.setStyleSheet("font-size: 14px; background: transparent;")
        self.inner_layout.addWidget(self.lbl_status)

        self.main_layout.addWidget(self.container)

        # Timer for duration (5 seconds)
        self.finish_timer = QTimer()
        self.finish_timer.setSingleShot(True)  # Run only once
        self.finish_timer.timeout.connect(self._on_timeout)

        self.update_ui()

    def update_ui(self):
        # 1. Background color
        self.setStyleSheet(f"background-color: {cf.APP_BACKGROUND};")

        # 2. Text styles
        text_style = f"color: {cf.DARK_TEXT}; background: transparent;"
        self.lbl_title.setStyleSheet(f"{text_style} font-size: 20px; font-weight: bold;")
        self.lbl_status.setStyleSheet(f"{text_style} font-size: 14px;")

        self.container.setStyleSheet("background: transparent; border: none;")

        self.spinner.update()

    def start_loading(self):
        self.lbl_status.setText("Starting analysis...")
        self.finish_timer.start(0)

    def update_status(self, status_text: str):
        """Update loading status text"""
        self.lbl_status.setText(status_text)

    def _on_timeout(self):
        self.loading_finished.emit()