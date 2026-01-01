# frontend/main_window.py
from PyQt6.QtWidgets import QMainWindow, QStackedWidget, QWidget, QVBoxLayout, QLabel, QHBoxLayout
from PyQt6.QtCore import Qt
from . import configuration as cf

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # 1. Setup cơ bản của cửa sổ
        self.setWindowTitle("TrueWeb")
        self.setCentralWidget(QWidget())
        
        # 2. Layout chính
        self.main_layout = QVBoxLayout(self.centralWidget())
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        # 3. Header (Thanh tiêu đề nhỏ ở trên cùng - Giữ lại từ code cũ)
        self._create_header()

        # 4. StackedWidget (Nơi chứa các trang Home, Login, Result...)
        self.pages_stack = QStackedWidget()
        self.main_layout.addWidget(self.pages_stack)
        
        # Style
        self.update_ui()

    def _create_header(self):
        self.header = QWidget()
        self.header.setObjectName("header")
        header_layout = QHBoxLayout(self.header)
        header_layout.setContentsMargins(12, 8, 12, 8)

        self.app_label = QLabel("TrueWeb")
        self.app_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.app_label.setStyleSheet(f"color: {cf.HEADER_TITLE}; font-size: 50px; font-weight: 1000;")

        header_layout.addStretch(1)
        header_layout.addWidget(self.app_label)
        header_layout.addStretch(1)

        self.main_layout.addWidget(self.header)

    def set_page(self, widget):
        """Hàm tiện ích để chuyển trang"""
        self.pages_stack.setCurrentWidget(widget)

    def add_page(self, widget):
        """Hàm tiện ích để thêm trang vào stack"""
        self.pages_stack.addWidget(widget)
    
    def remove_page(self, widget):
         self.pages_stack.removeWidget(widget)

    def update_ui(self):
        self.setStyleSheet(f"background-color: {cf.APP_BACKGROUND};")
        self.header.setStyleSheet(f"background-color: {cf.HEADER_BACKGROUND};")