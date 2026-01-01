from . import configuration as cf
from .UI_helpers import *
from .UI_helpers import _add_separator

from PyQt6.QtGui import QMouseEvent, QIcon
from PyQt6.QtWidgets import (QWidget, QHBoxLayout, QLabel, QVBoxLayout,
                             QLineEdit, QSizePolicy, QPushButton, QFrame, QCheckBox)
from PyQt6.QtCore import Qt, pyqtSignal, QSize, QTimer


# ---SEARCH BAR---
class ClickableLabel(QLabel):
    clicked = pyqtSignal()

    def mousePressEvent(self, event: QMouseEvent):
        self.clicked.emit()
        super().mousePressEvent(event)

class SearchBar(QWidget):
    search_requested = pyqtSignal(str, int, bool)  # (url, timeout, screenshot_enabled)

    def __init__(self, parent=None):
        super().__init__(parent)
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 0, 10, 20)
        main_layout.setSpacing(8)

        # Search box container
        self.search_box = QWidget()
        search_box_layout = QHBoxLayout(self.search_box)
        search_box_layout.setContentsMargins(15, 8, 15, 8)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Enter URL of the website that you want to check...")
        self.search_input.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.search_input.setMinimumHeight(28)

        self.icon_label = ClickableLabel()
        self.icon_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.icon_label.setFixedWidth(26)
        self.icon_label.clicked.connect(self._on_magnifier_clicked)

        search_box_layout.addWidget(self.search_input)
        search_box_layout.addWidget(self.icon_label)

        main_layout.addWidget(self.search_box)
        
        # Screenshot checkbox
        checkbox_layout = QHBoxLayout()
        checkbox_layout.setContentsMargins(15, 5, 15, 0)
        
        self.screenshot_checkbox = QCheckBox("📷 Take website screenshots? (🟩: Yes, 🟥: No)")
        self.screenshot_checkbox.setChecked(True)  # Default enabled
        self.screenshot_checkbox.setCursor(Qt.CursorShape.PointingHandCursor)
        
        checkbox_layout.addWidget(self.screenshot_checkbox)
        checkbox_layout.addStretch()
        
        main_layout.addLayout(checkbox_layout)
        
        self.search_input.returnPressed.connect(self._on_magnifier_clicked)

        self.update_ui()

    def update_ui(self):
        apply_shadow(self.search_box)

        self.search_input.setStyleSheet(f"""
            QLineEdit {{
                color: {cf.DARK_TEXT}; 
                border: none; 
                background: transparent;
            }}
            QLineEdit::placeholder {{
                color: {cf.LIGHT_TEXT};
            }}
        """)

        self.icon_label.setStyleSheet("border: none; background: transparent;")
        self.search_box.setStyleSheet(f"background: {cf.BAR_BACKGROUND}; border-radius: 18px; border: none;")

        search_pixmap = get_icon_pixmap("search")
        if not search_pixmap.isNull():
            scaled_pixmap = search_pixmap.scaled(20, 20, Qt.AspectRatioMode.KeepAspectRatio,
                                                 Qt.TransformationMode.SmoothTransformation)
            self.icon_label.setPixmap(scaled_pixmap)
        else:
            self.icon_label.setText("🔍")
        
        # Style checkbox with custom indicator (green tick / red cross)
        self.screenshot_checkbox.setStyleSheet(f"""
            QCheckBox {{
                color: {cf.DARK_TEXT};
                font-size: 13px;
                spacing: 8px;
            }}
            QCheckBox::indicator {{
                width: 18px;
                height: 18px;
                border-radius: 3px;
                border: 2px solid {cf.SHADOW_COLOR};
                background-color: {cf.BAR_BACKGROUND};
            }}
            QCheckBox::indicator:checked {{
                background-color: #22c55e;
                border-color: #16a34a;
                image: url(data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTIiIGhlaWdodD0iMTIiIHZpZXdCb3g9IjAgMCAxMiAxMiIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cGF0aCBkPSJNMTAgM0w0LjUgOC41TDIgNiIgc3Ryb2tlPSJ3aGl0ZSIgc3Ryb2tlLXdpZHRoPSIyIiBzdHJva2UtbGluZWNhcD0icm91bmQiIHN0cm9rZS1saW5lam9pbj0icm91bmQiLz48L3N2Zz4=);
            }}
            QCheckBox::indicator:unchecked {{
                background-color: #ef4444;
                border-color: #dc2626;
                image: url(data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTIiIGhlaWdodD0iMTIiIHZpZXdCb3g9IjAgMCAxMiAxMiIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cGF0aCBkPSJNMyAzTDkgOSIgc3Ryb2tlPSJ3aGl0ZSIgc3Ryb2tlLXdpZHRoPSIyIiBzdHJva2UtbGluZWNhcD0icm91bmQiLz48cGF0aCBkPSJNOSAzTDMgOSIgc3Ryb2tlPSJ3aGl0ZSIgc3Ryb2tlLXdpZHRoPSIyIiBzdHJva2UtbGluZWNhcD0icm91bmQiLz48L3N2Zz4=);
            }}
            QCheckBox::indicator:hover {{
                border-color: {cf.BUTTON_BACKGROUND};
            }}
        """)

    def _on_magnifier_clicked(self):
        from PyQt6.QtWidgets import QMessageBox
        from . import configuration as cf
        import re
        
        query = self.search_input.text().strip()
        # Remove ALL spaces and tabs (including middle ones)
        query = query.replace(' ', '').replace('\t', '').replace('(.)', '.')
        
        if not query:
            msg = QMessageBox(self)
            msg.setIcon(QMessageBox.Icon.Warning)
            msg.setWindowTitle("Invalid Input")
            msg.setText("Please enter a URL!")
            msg.setStyleSheet("QLabel{color: #000000;} QPushButton{color: #000000;}")
            msg.exec()
            return
        
        # Validate URL format
        url_pattern = r'^(?:https?:\/\/)?(?:[\w-]+\.)+[a-z]{2,}(?:\/.*)?$'
        if not re.match(url_pattern, query, re.IGNORECASE):
            msg = QMessageBox(self)
            msg.setIcon(QMessageBox.Icon.Warning)
            msg.setWindowTitle("Invalid URL")
            msg.setText("Please enter a valid URL!\n\nExamples:\n• google.com\n• https://google.com\n• http://example.org")
            msg.setStyleSheet("QLabel{color: #000000;} QPushButton{color: #000000;}")
            msg.exec()
            return
        
        # Get timeout from configuration (set in Settings page)
        timeout = cf.get_timeout()
        
        # Get screenshot preference from checkbox
        screenshot_enabled = self.screenshot_checkbox.isChecked()
        
        # All valid - proceed
        self.search_input.clear()
        self.search_input.clearFocus()
        QTimer.singleShot(100, lambda: self.search_requested.emit(query, timeout, screenshot_enabled))


# ---MENU BAR---
class MenuButton(QPushButton):
    def __init__(self, icon_type, text="", parent=None):
        super().__init__(text, parent)
        self.setFixedHeight(40)
        self.icon_type = icon_type

        self.setIconSize(QSize(20, 20))
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.update_ui()

    def update_ui(self):
        self.setIcon(QIcon(get_icon_pixmap(self.icon_type)))

        self.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                border: none;
                border-radius: 20px;
                padding: 0 15px;
                color: {cf.DARK_TEXT};
                text-align: left;
            }}
            QPushButton:hover {{
                background-color: {cf.LIGHT_TEXT}30;
            }}
        """)

class MenuBar(QFrame):
    go_to_login_requested = pyqtSignal()
    go_to_settings_requested = pyqtSignal()
    see_info_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 5, 20, 5)
        layout.setSpacing(7)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.log_button = MenuButton("login", "Login")
        self.log_button.clicked.connect(self.go_to_login_requested.emit)
        layout.addWidget(self.log_button)

        _add_separator(layout)

        self.settings_button = MenuButton("settings", "Settings")
        self.settings_button.clicked.connect(self.go_to_settings_requested.emit)
        layout.addWidget(self.settings_button)

        _add_separator(layout)

        self.info_button = MenuButton("info", "See Information")
        self.info_button.clicked.connect(self.see_info_requested.emit)
        layout.addWidget(self.info_button)

        self.update_ui()

    def update_ui(self):
        apply_shadow(self)
        self.setStyleSheet(f"""QFrame {{background-color: {cf.BAR_BACKGROUND}; border-radius: 25px;}}""")

        if hasattr(self, 'log_button'): self.log_button.update_ui()
        if hasattr(self, 'settings_button'): self.settings_button.update_ui()
        if hasattr(self, 'info_button'): self.info_button.update_ui()

    def update_login_state(self, is_logged_in):
        if is_logged_in:
            self.log_button.setText("Log-out")
            self.log_button.icon_type = "logout"
        else:
            self.log_button.setText("Log-in")
            self.log_button.icon_type = "login"

        self.log_button.update_ui()

class HomePage(QWidget): 
    # Các tín hiệu gửi ra ngoài
    search_requested = pyqtSignal(str, int, bool)  # (url, timeout, screenshot_enabled)
    login_nav_requested = pyqtSignal()
    settings_nav_requested = pyqtSignal()
    info_nav_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Layout chính của trang chủ
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setContentsMargins(20, 5, 20, 5)
        layout.setSpacing(20)

        # 1. Search Bar
        self.search_bar_widget = SearchBar()
        self.search_bar_widget.setFixedWidth(600)
        # Nối tín hiệu nội bộ ra tín hiệu của Class
        self.search_bar_widget.search_requested.connect(self.search_requested.emit)
        layout.addWidget(self.search_bar_widget, alignment=Qt.AlignmentFlag.AlignCenter)

        # 2. Menu Bar
        self.home_menu_bar = MenuBar()
        self.home_menu_bar.setFixedWidth(450)
        
        # Nối tín hiệu từ Menu ra tín hiệu của Class
        self.home_menu_bar.go_to_login_requested.connect(self.login_nav_requested.emit)
        self.home_menu_bar.go_to_settings_requested.connect(self.settings_nav_requested.emit)
        self.home_menu_bar.see_info_requested.connect(self.info_nav_requested.emit)
        
        layout.addWidget(self.home_menu_bar, alignment=Qt.AlignmentFlag.AlignCenter)

    def update_login_state(self, is_logged_in):
        """Hàm update UI trạng thái login"""
        self.home_menu_bar.update_login_state(is_logged_in)

    def update_ui(self):
        """Hàm update theme"""
        self.search_bar_widget.update_ui()
        self.home_menu_bar.update_ui()