from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QLineEdit,
    QTextEdit, QHBoxLayout, QFrame, QMessageBox, QSpacerItem, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QDoubleValidator
from frontend import configuration as cf


class WriteReviewPage(QWidget):
    review_submitted = pyqtSignal(float, str)
    cancelled = pyqtSignal()

    def __init__(self, title, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"background-color: {cf.APP_BACKGROUND};")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(20)

        # 1. Header
        self.header = QLabel("Write a Review")
        self.header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.header)

        # Container for Form
        self.form_frame = QFrame()
        form_layout = QVBoxLayout(self.form_frame)
        form_layout.setContentsMargins(30, 30, 30, 30)
        form_layout.setSpacing(15)

        # 2. Input Score
        self.lbl_score = QLabel("Your Score (0.0 - 10.0) *")
        form_layout.addWidget(self.lbl_score)

        self.input_score = QLineEdit()
        self.input_score.setPlaceholderText("e.g. 8.5")
        self.input_score.setValidator(QDoubleValidator(0.0, 10.0, 1))
        self.input_score.textChanged.connect(self._check_input_validity)
        form_layout.addWidget(self.input_score)

        # 3. Input Comment
        self.lbl_comment = QLabel("Your Comment (Optional)")
        form_layout.addWidget(self.lbl_comment)

        self.input_comment = QTextEdit()
        self.input_comment.setPlaceholderText("Share your experience with this website...")
        self.input_comment.setFixedHeight(120)
        form_layout.addWidget(self.input_comment)

        layout.addWidget(self.form_frame)
        layout.addStretch()

        # 4. Buttons (Cancel & Confirm)
        btn_layout = QHBoxLayout()

        self.btn_cancel = QPushButton("Cancel")
        self.btn_cancel.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_cancel.clicked.connect(self._on_cancel)

        self.btn_confirm = QPushButton("Confirm")
        self.btn_confirm.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_confirm.setEnabled(False)
        self.btn_confirm.clicked.connect(self._on_confirm)

        btn_layout.addWidget(self.btn_cancel)
        btn_layout.addWidget(self.btn_confirm)
        layout.addLayout(btn_layout)
        self.update_ui()

    def _check_input_validity(self):
        text = self.input_score.text().strip()
        if text:
            self.btn_confirm.setEnabled(True)
            self.btn_confirm.setStyleSheet(f"""
                QPushButton {{
                    background-color: {cf.BUTTON_BACKGROUND}; color: white; border-radius: 8px; 
                    padding: 12px 30px; font-weight: bold; font-size: 14px;
                }}
                QPushButton:hover {{opacity: 0.9;}}
            """)
        else:
            self.btn_confirm.setEnabled(False)
            self.btn_confirm.setStyleSheet(f"""
                QPushButton {{
                    background-color: {cf.SWITCH_INACTIVE}; color: {cf.LIGHT_TEXT}; border-radius: 8px; 
                    padding: 12px 30px; font-weight: bold; font-size: 14px;
                }}
            """)

    def _on_confirm(self):
        msg = QMessageBox(self)
        msg.setWindowTitle("Confirmation")
        msg.setText("Are you sure you want to submit this review?")
        msg.setIcon(QMessageBox.Icon.Question)
        msg.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        msg.setDefaultButton(QMessageBox.StandardButton.No)
        msg.setStyleSheet(f"QLabel{{color: {cf.DARK_TEXT};}} QPushButton{{color: {cf.DARK_TEXT};}}")

        ret = msg.exec()

        if ret == QMessageBox.StandardButton.Yes:
            # 2. Validate data
            score_text = self.input_score.text().strip()
            try:
                score = float(score_text)
                if 0.0 <= score <= 10.0:
                    # Hợp lệ -> Gửi signal và reset
                    comment = self.input_comment.toPlainText().strip()
                    self.review_submitted.emit(score, comment)
                    self._reset_form()
                else: self._show_error("Invalid Score", "Score must be between 0.0 and 10.0")
            except ValueError: self._show_error("Invalid Input", "Please enter a valid number for score.")

    def _show_error(self, title, text):
        msg = QMessageBox(self)
        msg.setWindowTitle(title)
        msg.setText(text)
        msg.setIcon(QMessageBox.Icon.Warning)
        msg.setStyleSheet(f"QLabel{{color: {cf.DARK_TEXT};}} QPushButton{{color: {cf.DARK_TEXT};}}")
        msg.exec()
        
    def _on_cancel(self):
        self._reset_form()
        self.cancelled.emit()

    def _reset_form(self):
        self.input_score.clear()
        self.input_comment.clear()
        self._check_input_validity()

    def update_ui(self):
        self.setStyleSheet(f"background-color: {cf.APP_BACKGROUND};")
        
        # Header
        self.header.setStyleSheet(f"font-size: 28px; font-weight: bold; color: {cf.NORMAL_TITLE};")

        # Form Frame
        self.form_frame.setStyleSheet(f"""
            background-color: {cf.BAR_BACKGROUND}; 
            border-radius: 10px; 
            border: 1px solid {cf.SHADOW_COLOR};
        """)

        # Labels
        label_style = f"font-weight: bold; color: {cf.DARK_TEXT}; border: none;"
        self.lbl_score.setStyleSheet(label_style)
        self.lbl_comment.setStyleSheet(label_style)

        # Inputs
        input_style = f"""
            padding: 10px; 
            border: 2px solid {cf.LINK_TEXT}; 
            border-radius: 5px; 
            color: {cf.DARK_TEXT};
            background-color: {cf.WHITE}; 
        """
        input_style_focus = f"""
            QLineEdit, QTextEdit {{
                padding: 10px; 
                border: 2px solid {cf.LINK_TEXT}; 
                border-radius: 5px; 
                color: {cf.DARK_TEXT};
                background-color: {cf.WHITE};
            }}
            QLineEdit:focus, QTextEdit:focus {{
                border: 3px solid {cf.LINK_TEXT};
            }}
        """
        self.input_score.setStyleSheet(input_style_focus)
        self.input_comment.setStyleSheet(input_style_focus)

        # Cancel Button
        self.btn_cancel.setStyleSheet(f"""
            QPushButton {{
                background-color: {cf.CANCEL_BG}; color: white; border-radius: 8px; 
                padding: 12px 30px; font-weight: bold; font-size: 14px;
            }}
            QPushButton:hover {{background-color: {cf.CANCEL_HOVER};}}
        """)

        # Update confirm button state
        self._check_input_validity()