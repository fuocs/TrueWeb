from . import configuration as cf
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, 
    QLabel, QPushButton, QFrame, QCheckBox, QSpinBox
)
from PyQt6.QtCore import Qt, pyqtSignal, QPropertyAnimation, QEasingCurve, pyqtProperty
from PyQt6.QtGui import QColor, QPainter, QPen, QIntValidator



# --- CUSTOM SWITCH BUTTON ---
class SwitchButton(QCheckBox):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(50, 30)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._bg_color = "#777"  # Màu khi tắt
        self._circle_position = 3  # Vị trí vòng tròn
        self._active_color = "#007bff"  # Màu khi bật (Blue)

        self.setText("")  # Tắt text mặc định

        self.animation = QPropertyAnimation(self, b"circle_position", self)
        self.animation.setEasingCurve(QEasingCurve.Type.InOutCubic)
        self.animation.setDuration(200)

        self.stateChanged.connect(self.start_transition)

    def hitButton(self, pos):
        return self.contentsRect().contains(pos)

    @pyqtProperty(float)
    def circle_position(self): return self._circle_position

    @circle_position.setter
    def circle_position(self, pos):
        self._circle_position = pos
        self.update()

    def start_transition(self, state):
        self.animation.stop()
        if state: self.animation.setEndValue(self.width() - 26)
        else: self.animation.setEndValue(3)
        self.animation.start()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        if self.isChecked():
            p.setBrush(QColor(self._active_color))
            p.setPen(Qt.PenStyle.NoPen)
        else:
            p.setBrush(QColor(self._bg_color))
            p.setPen(Qt.PenStyle.NoPen)

        p.drawRoundedRect(0, 0, self.width(), self.height(), self.height() / 2, self.height() / 2)

        p.setBrush(QColor("#ffffff"))
        p.setPen(QPen(QColor("#d5d5d5")))

        p.drawEllipse(int(self._circle_position), 3, 24, 24)
        p.end()

# --- SETTINGS PAGE ---
class SettingsPage(QWidget):
    back_to_home_requested = pyqtSignal()
    theme_toggled = pyqtSignal(bool)  # Signal gửi đi: True (Dark), False (Light)
    minimize_to_tray_toggled = pyqtSignal(bool)

    def __init__(self, title, parent=None):
        super().__init__(parent)
        # === UPDATE: Bỏ setFixedSize ở đây để MainWindow tự quản lý ===
        # self.setFixedSize(700, 500)

        # Main layout
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        layout.setContentsMargins(40, 20, 40, 20)

        # Title
        self.header_label = QLabel("Settings")
        self.header_label.setStyleSheet(f"font-size: 28px; font-weight: bold; color: {cf.NORMAL_TITLE}; background: transparent")
        layout.addWidget(self.header_label)

        # --- APPEARANCE (Light/Dark Mode) ---
        self.group_appearance = self._create_setting_item(
            "Dark Mode",
            "Switch between Light and Dark themes",
            self._on_theme_changed
        )
        self.theme_switch = self.group_appearance.findChild(SwitchButton)
        self.theme_switch.setChecked(False)  # Mặc định là Light Mode
        layout.addWidget(self.group_appearance)

        # --- SYSTEM (Background Run) ---
        self.group_system = self._create_setting_item(
            "Run in Background",
            "Keep the app running in system tray when closed",
            self._on_background_run_changed
        )
        self.background_switch = self.group_system.findChild(SwitchButton)
        # self.background_switch.setChecked(False)  # Mặc định bật 
        self.background_switch.setChecked(True)  # Mặc định bật 
        layout.addWidget(self.group_system)

        # --- TIMEOUT SETTINGS ---
        from PyQt6.QtWidgets import QSpinBox
        self.group_timeout = self._create_timeout_setting(
            "Analysis Timeout",
            "Maximum time (in seconds) to wait for website analysis"
        )
        layout.addWidget(self.group_timeout)

        # --- RETRY SETTINGS ---
        self.group_retry = self._create_retry_setting(
            "Module Retries",
            "Number of retry attempts for failed security checks (0-5)"
        )
        layout.addWidget(self.group_retry)

        layout.addStretch()

        back_button = QPushButton("Back to Home Page")
        back_button.setCursor(Qt.CursorShape.PointingHandCursor)
        back_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {cf.BUTTON_BACKGROUND};
                color: {cf.WHITE};
                border-radius: 8px;
                padding: 10px 25px;
                font-size: 14px; font-weight: bold;
            }}
            QPushButton:hover {{color: {cf.BLACK}}}
        """)
        back_button.clicked.connect(self.back_to_home_requested.emit)
        layout.addWidget(back_button, alignment=Qt.AlignmentFlag.AlignCenter)

        self.setStyleSheet(f"background-color: {cf.APP_BACKGROUND};")

    def update_ui(self):
        self.setStyleSheet(f"background-color: {cf.APP_BACKGROUND};")
        self.header_label.setStyleSheet(f"font-size: 27px; font-weight: bold; color: {cf.HEADER_BACKGROUND}; margin-bottom: 20px; border: none; background: transparent;")
        
        # Update all setting containers
        for container in [self.group_appearance, self.group_system, self.group_timeout, self.group_retry]:
            container.setStyleSheet(f"background-color: {cf.BAR_BACKGROUND}; border-radius: 10px; border: 1px solid {cf.SHADOW_COLOR};")
            
            # Update all labels inside each container
            for label in container.findChildren(QLabel):
                if label.property("settings_title"):
                    label.setStyleSheet(f"font-size: 16px; font-weight: bold; color: {cf.DARK_TEXT}; border: none;")
                elif label.property("settings_desc"):
                    label.setStyleSheet(f"font-size: 12px; color: {cf.DARK_TEXT}; border: none;")
        
        # Update spinboxes
        spinbox_style = f"""
            QSpinBox {{
                font-size: 15px;
                font-weight: bold;
                color: {cf.DARK_TEXT};
                background-color: {cf.WHITE};
                border: 2px solid {cf.LINK_TEXT};
                border-radius: 8px;
                padding: 8px 12px;
            }}
            QSpinBox:hover {{
                border: 2px solid {cf.LINK_TEXT};
                background-color: {cf.PREVIEW_BG};
            }}
            QSpinBox:focus {{
                border: 3px solid {cf.LINK_TEXT};
                background-color: {cf.PREVIEW_BG};
            }}
            QSpinBox::up-button, QSpinBox::down-button {{
                width: 20px;
                border: none;
                background-color: {cf.LINK_TEXT};
            }}
            QSpinBox::up-button:hover, QSpinBox::down-button:hover {{
                background-color: {cf.BUTTON_BACKGROUND};
            }}
            QSpinBox::up-arrow {{
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-bottom: 5px solid white;
                width: 0;
                height: 0;
            }}
            QSpinBox::down-arrow {{
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid white;
                width: 0;
                height: 0;
            }}
        """
        self.timeout_spinbox.setStyleSheet(spinbox_style)
        self.retry_spinbox.setStyleSheet(spinbox_style)

    def _create_setting_item(self, title, description, slot_function):
        container = QFrame()
        container.setStyleSheet(f"background-color: {cf.BAR_BACKGROUND}; border-radius: 10px; border: 1px solid {cf.SHADOW_COLOR};")
        container.setFixedHeight(80)

        h_layout = QHBoxLayout(container)
        h_layout.setContentsMargins(20, 5, 20, 5)

        # Text Section
        text_layout = QVBoxLayout()
        title_lbl = QLabel(title)
        title_lbl.setStyleSheet(f"font-size: 16px; font-weight: bold; color: {cf.DARK_TEXT}; border: none;")
        title_lbl.setProperty("settings_title", True)  # Mark for later updates

        desc_lbl = QLabel(description)
        desc_lbl.setStyleSheet(f"font-size: 12px; color: {cf.DARK_TEXT}; border: none;")
        desc_lbl.setProperty("settings_desc", True)  # Mark for later updates

        text_layout.addWidget(title_lbl)
        text_layout.addWidget(desc_lbl)

        # Switch Section
        switch = SwitchButton()
        switch.stateChanged.connect(slot_function)

        h_layout.addLayout(text_layout)
        h_layout.addStretch()
        h_layout.addWidget(switch)

        return container

    def _on_theme_changed(self, state):
        is_dark_mode = (state == 2)
        self.theme_toggled.emit(is_dark_mode)
        # Update UI immediately after theme change
        self.update_ui()

    def _on_background_run_changed(self, state):
        # state: 0 (Unchecked), 2 (Checked)
        is_running_bg = (state == 2)
        self.minimize_to_tray_toggled.emit(is_running_bg)

    def _create_timeout_setting(self, title, description):
        """Create timeout setting with spinbox"""
        container = QFrame()
        container.setStyleSheet(f"background-color: {cf.BAR_BACKGROUND}; border-radius: 10px; border: 1px solid {cf.SHADOW_COLOR};")
        container.setFixedHeight(80)

        h_layout = QHBoxLayout(container)
        h_layout.setContentsMargins(20, 5, 20, 5)

        # Text Section
        text_layout = QVBoxLayout()
        title_lbl = QLabel(title)
        title_lbl.setStyleSheet(f"font-size: 16px; font-weight: bold; color: {cf.DARK_TEXT}; border: none;")
        title_lbl.setProperty("settings_title", True)

        desc_lbl = QLabel(description)
        desc_lbl.setStyleSheet(f"font-size: 12px; color: {cf.DARK_TEXT}; border: none;")
        desc_lbl.setProperty("settings_desc", True)

        text_layout.addWidget(title_lbl)
        text_layout.addWidget(desc_lbl)

        # SpinBox Section
        self.timeout_spinbox = QSpinBox()
        self.timeout_spinbox.setRange(10, 120)
        self.timeout_spinbox.setValue(cf.get_timeout())
        self.timeout_spinbox.setSuffix(" sec")
        self.timeout_spinbox.setFixedSize(120, 40)
        self.timeout_spinbox.setAlignment(Qt.AlignmentFlag.AlignCenter)
        # Allow typing numbers directly; validate input to int range
        timeout_validator = QIntValidator(self.timeout_spinbox.minimum(), self.timeout_spinbox.maximum(), self)
        self.timeout_spinbox.lineEdit().setValidator(timeout_validator)
        # Save on Enter or when focus leaves the line edit
        self.timeout_spinbox.lineEdit().editingFinished.connect(self._on_timeout_edit_finished)
        self.timeout_spinbox.setStyleSheet(f"""
            QSpinBox {{
                font-size: 15px;
                font-weight: bold;
                color: {cf.DARK_TEXT};
                background-color: {cf.WHITE};
                border: 2px solid {cf.LINK_TEXT};
                border-radius: 8px;
                padding: 8px 12px;
            }}
            QSpinBox:hover {{
                border: 2px solid {cf.LINK_TEXT};
                background-color: {cf.PREVIEW_BG};
            }}
            QSpinBox:focus {{
                border: 3px solid {cf.LINK_TEXT};
                background-color: {cf.PREVIEW_BG};
            }}
            QSpinBox::up-button, QSpinBox::down-button {{
                width: 20px;
                border: none;
                background-color: {cf.LINK_TEXT};
            }}
            QSpinBox::up-button:hover, QSpinBox::down-button:hover {{
                background-color: {cf.BUTTON_BACKGROUND};
            }}
            QSpinBox::up-arrow {{
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-bottom: 5px solid white;
                width: 0;
                height: 0;
            }}
            QSpinBox::down-arrow {{
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid white;
                width: 0;
                height: 0;
            }}
        """)
        self.timeout_spinbox.valueChanged.connect(self._on_timeout_changed)

        h_layout.addLayout(text_layout)
        h_layout.addStretch()
        h_layout.addWidget(self.timeout_spinbox)

        return container

    def _on_timeout_changed(self, value):
        """Update timeout in configuration when changed"""
        cf.set_timeout(value)

    def _on_timeout_edit_finished(self):
        """Handle when user types a number and presses Enter or leaves the field."""
        try:
            text = self.timeout_spinbox.lineEdit().text()
            # Extract integer (spinbox validator ensures digits)
            value = int(text) if text and text.isdigit() else self.timeout_spinbox.value()
        except Exception:
            value = self.timeout_spinbox.value()

        # Clamp to allowed range
        min_v = self.timeout_spinbox.minimum()
        max_v = self.timeout_spinbox.maximum()
        if value < min_v: value = min_v
        if value > max_v: value = max_v

        # Apply and save
        self.timeout_spinbox.setValue(value)
        cf.set_timeout(value)

    def _create_retry_setting(self, title, description):
        """Create retry count setting with spinbox"""
        container = QFrame()
        container.setStyleSheet(f"background-color: {cf.BAR_BACKGROUND}; border-radius: 10px; border: 1px solid {cf.SHADOW_COLOR};")
        container.setFixedHeight(80)

        h_layout = QHBoxLayout(container)
        h_layout.setContentsMargins(20, 5, 20, 5)

        # Text Section
        text_layout = QVBoxLayout()
        title_lbl = QLabel(title)
        title_lbl.setStyleSheet(f"font-size: 16px; font-weight: bold; color: {cf.DARK_TEXT}; border: none;")
        title_lbl.setProperty("settings_title", True)

        desc_lbl = QLabel(description)
        desc_lbl.setStyleSheet(f"font-size: 12px; color: {cf.DARK_TEXT}; border: none;")
        desc_lbl.setProperty("settings_desc", True)

        text_layout.addWidget(title_lbl)
        text_layout.addWidget(desc_lbl)

        # SpinBox Section
        self.retry_spinbox = QSpinBox()
        self.retry_spinbox.setRange(0, 5)
        self.retry_spinbox.setValue(cf.get_retry_count())
        self.retry_spinbox.setSuffix(" retries")
        self.retry_spinbox.setFixedSize(140, 40)
        self.retry_spinbox.setAlignment(Qt.AlignmentFlag.AlignCenter)
        # Allow typing numbers directly; validate input to int range
        retry_validator = QIntValidator(self.retry_spinbox.minimum(), self.retry_spinbox.maximum(), self)
        self.retry_spinbox.lineEdit().setValidator(retry_validator)
        # Save on Enter or when focus leaves the line edit
        self.retry_spinbox.lineEdit().editingFinished.connect(self._on_retry_edit_finished)
        self.retry_spinbox.setStyleSheet(f"""
            QSpinBox {{
                font-size: 15px;
                font-weight: bold;
                color: {cf.DARK_TEXT};
                background-color: {cf.WHITE};
                border: 2px solid {cf.LINK_TEXT};
                border-radius: 8px;
                padding: 8px 12px;
            }}
            QSpinBox:hover {{
                border: 2px solid {cf.LINK_TEXT};
                background-color: {cf.PREVIEW_BG};
            }}
            QSpinBox:focus {{
                border: 3px solid {cf.LINK_TEXT};
                background-color: {cf.PREVIEW_BG};
            }}
            QSpinBox::up-button, QSpinBox::down-button {{
                width: 20px;
                border: none;
                background-color: {cf.LINK_TEXT};
            }}
            QSpinBox::up-button:hover, QSpinBox::down-button:hover {{
                background-color: {cf.BUTTON_BACKGROUND};
            }}
            QSpinBox::up-arrow {{
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-bottom: 5px solid white;
                width: 0;
                height: 0;
            }}
            QSpinBox::down-arrow {{
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid white;
                width: 0;
                height: 0;
            }}
        """)
        self.retry_spinbox.valueChanged.connect(self._on_retry_changed)

        h_layout.addLayout(text_layout)
        h_layout.addStretch()
        h_layout.addWidget(self.retry_spinbox)

        return container

    def _on_retry_changed(self, value):
        """Update retry count in configuration when changed"""
        cf.set_retry_count(value)

    def _on_retry_edit_finished(self):
        """Handle when user types a number and presses Enter or leaves the field."""
        try:
            text = self.retry_spinbox.lineEdit().text()
            value = int(text) if text and text.isdigit() else self.retry_spinbox.value()
        except Exception:
            value = self.retry_spinbox.value()

        min_v = self.retry_spinbox.minimum()
        max_v = self.retry_spinbox.maximum()
        if value < min_v: value = min_v
        if value > max_v: value = max_v

        self.retry_spinbox.setValue(value)
        cf.set_retry_count(value)

