import os
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QPushButton, QLineEdit,
                             QMessageBox, QStackedWidget, QHBoxLayout, QFrame, QSizePolicy)
from PyQt6.QtCore import Qt, pyqtSignal, QThread
from PyQt6.QtGui import QAction, QIcon, QPainter

from backend import user
from .UI_helpers import *

# --- HELPER FUNCTIONS ---
def isValidLoginInfo(email, password):
    return user.login(email=email, password=password)

class PasswordLineEdit(QLineEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setEchoMode(QLineEdit.EchoMode.Password)
        self.setPlaceholderText("Password")

        self.toggle_action = QAction(self)
        
        self.toggle_action.triggered.connect(self._toggle_visibility)
        self.addAction(self.toggle_action, QLineEdit.ActionPosition.TrailingPosition)

        self.update_ui()

    def _toggle_visibility(self):
        if self.echoMode() == QLineEdit.EchoMode.Password:
            self.setEchoMode(QLineEdit.EchoMode.Normal)
            self.toggle_action.setIcon(self.icon_show)
        else:
            self.setEchoMode(QLineEdit.EchoMode.Password)
            self.toggle_action.setIcon(self.icon_hide)
    
    def update_ui(self):

        self.icon_show = QIcon(get_icon_pixmap("eye-on"))
        self.icon_hide = QIcon(get_icon_pixmap("eye-off"))

        if self.echoMode() == QLineEdit.EchoMode.Normal:
            self.toggle_action.setIcon(self.icon_show)
        else:
            self.toggle_action.setIcon(self.icon_hide)
        
        self.setStyleSheet(f"""
            QLineEdit {{
                color: {cf.DARK_TEXT}; 
                background-color: {cf.WHITE};
                font-size: 15px; 
                border: 1px solid {cf.SHADOW_COLOR}; 
                border-radius: 6px; 
                padding: 8px; 
            }}
            QLineEdit:focus {{
                border: 1px solid {cf.LINK_TEXT};
                background-color: {cf.WHITE};
            }}
        """)

class GoogleLoginWorker(QThread):
    login_finished = pyqtSignal(dict)

    def run(self):
        result = user.login_with_google_flow()
        self.login_finished.emit(result)


class LoginPage(QWidget):
    back_to_home_requested = pyqtSignal()
    login_success_signal = pyqtSignal()
    logout_signal = pyqtSignal()

    def __init__(self, title, parent=None):
        super().__init__(parent)
        self.title = title

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.container = QFrame()
        self.container.setFixedWidth(400)
        self.container.setObjectName("main_card")

        self.container_layout = QVBoxLayout(self.container)
        self.container_layout.setContentsMargins(40, 40, 40, 40)
        self.container_layout.setSpacing(15)

        self.header_label = QLabel("Log-in Page")
        self.header_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.container_layout.addWidget(self.header_label)

        self.stack = QStackedWidget()

        self.page_login = QWidget()
        self._setup_login_ui()
        self.stack.addWidget(self.page_login)

        self.page_register = QWidget()
        self._setup_register_ui()
        self.stack.addWidget(self.page_register)

        self.page_forgot_password = QWidget()
        self._setup_forgot_password_ui()
        self.stack.addWidget(self.page_forgot_password)

        self.container_layout.addWidget(self.stack)

        self.btn_google = QPushButton("Sign in with Google")
        self.btn_google.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_google.setIcon(QIcon(get_icon_pixmap('icon-google')))
        self.btn_google.clicked.connect(self.handle_google_login)
        
        self.container_layout.addWidget(self.btn_google)
        

        self.back_button = QPushButton("Back to Home Page")
        self.back_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.back_button.clicked.connect(self.back_to_home_requested.emit)
        self.container_layout.addWidget(self.back_button, alignment=Qt.AlignmentFlag.AlignCenter)

        layout.addWidget(self.container)

        self.update_ui()

    def show_message(self, title, text, icon=QMessageBox.Icon.Information):
        msg = QMessageBox(self)
        msg.setWindowTitle(title)
        msg.setText(text)
        msg.setIcon(icon)
        msg.setStyleSheet(f"""
            QMessageBox {{
                background-color: {cf.APP_BACKGROUND};
            }}
            QLabel {{
                color: {cf.DARK_TEXT};
            }}
            QPushButton {{
                color: {cf.WHITE};
                background-color: {cf.BUTTON_BACKGROUND};
                border: none;
                padding: 5px 15px;
                border-radius: 3px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                opacity: 0.8;
            }}
            "padding-right: 30px;"
        """)
        msg.exec()

    # --- UI SETUP ---
    def _setup_login_ui(self):
        layout = QVBoxLayout(self.page_login)
        layout.setContentsMargins(0,0,0,0)
        
        #logic 
        self.login_email = QLineEdit()
        self.login_email.setPlaceholderText("Email")
        self.login_pass = PasswordLineEdit()

        self.btn_login = QPushButton("LOGIN")
        self.btn_login.clicked.connect(self._handle_login)

        sub_layout = QHBoxLayout()
        self.btn_to_reg = QPushButton("Create Account")
        self.btn_to_reg.clicked.connect(lambda: self._switch_mode(1, "Create Account"))
        self.btn_forgot = QPushButton("Forgot Password?")
        self.btn_forgot.clicked.connect(self._start_forgot_password_flow)

        sub_layout.addWidget(self.btn_to_reg)
        sub_layout.addStretch()
        sub_layout.addWidget(self.btn_forgot)

        layout.addWidget(self.login_email)
        layout.addWidget(self.login_pass)
        layout.addWidget(self.btn_login)
        layout.addLayout(sub_layout)

    def _setup_register_ui(self):
        layout = QVBoxLayout(self.page_register)
        layout.setContentsMargins(0,0,0,0)

        self.reg_email = QLineEdit();
        self.reg_email.setPlaceholderText("Email")
        self.reg_user = QLineEdit();
        self.reg_user.setPlaceholderText("Username")
        self.reg_pass1 = PasswordLineEdit();
        self.reg_pass1.setPlaceholderText("Password")
        self.reg_pass2 = PasswordLineEdit();
        self.reg_pass2.setPlaceholderText("Confirm Password")

        self.btn_register = QPushButton("Register")
        self.btn_register.clicked.connect(self._handle_register)
        self.btn_reg_cancel = QPushButton("Cancel")
        self.btn_reg_cancel.clicked.connect(lambda: self._switch_mode(0, "Log-in Page"))

        layout.addWidget(self.reg_email);
        layout.addWidget(self.reg_user)
        layout.addWidget(self.reg_pass1);
        layout.addWidget(self.reg_pass2)
        layout.addWidget(self.btn_register);
        layout.addWidget(self.btn_reg_cancel)

    def _setup_forgot_password_ui(self):
        layout = QVBoxLayout(self.page_forgot_password)
        layout.setSpacing(15)
        layout.setContentsMargins(0,10,0,10)

        # Hướng dẫn
        self.lbl_instruction = QLabel("Enter your email address to receive a password reset link.")
        self.lbl_instruction.setWordWrap(True)
        self.lbl_instruction.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.lbl_instruction.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Minimum)
        self.lbl_instruction.setStyleSheet("border: none; padding: 0px;")


        # Ô nhập Email
        self.forgot_email = QLineEdit()
        self.forgot_email.setPlaceholderText("Enter your email")

        # Nút Gửi
        self.btn_send_reset = QPushButton("Send Reset Link")
        self.btn_send_reset.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_send_reset.clicked.connect(self._handle_send_reset_email)

        # Nút Quay lại
        self.btn_ver_cancel = QPushButton("Back to Login")
        self.btn_ver_cancel.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_ver_cancel.clicked.connect(lambda: self._switch_mode(0, "Log-in Page"))

        self.btn_to_reg_forgot = QPushButton("Create Account")
        self.btn_to_reg_forgot.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_to_reg_forgot.clicked.connect(lambda: self._switch_mode(1, "Create Account"))

        layout.addWidget(self.lbl_instruction)
        layout.addWidget(self.forgot_email)
        layout.addWidget(self.btn_send_reset)
        layout.addWidget(self.btn_ver_cancel)
        layout.addWidget(self.btn_to_reg_forgot)
        layout.addStretch()

    # --- LOGIC ---
    def handle_entry_request(self, is_logged_in):
        if is_logged_in:
            msg = QMessageBox(self)
            msg.setWindowTitle("Log-out")
            msg.setText("Are you sure you want to logout?")
            msg.setIcon(QMessageBox.Icon.Question)
            msg.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            msg.setStyleSheet(f"QLabel{{color: {cf.DARK_TEXT};}} QPushButton{{color: {cf.DARK_TEXT};}}")
            response = msg.exec()

            if response == QMessageBox.StandardButton.Yes:
                self.logout_signal.emit()
                self.back_to_home_requested.emit()
            else:
                self.back_to_home_requested.emit()
        else:
            self._switch_mode(0, "Log-in Page")
            self._clear_inputs()

    def _handle_login(self):
        e = self.login_email.text().strip()
        p = self.login_pass.text().strip()

        if not(e and p): 
            self.show_message("Login Failed", "Not enough infomation", QMessageBox.Icon.Question)
            return
        
        result = isValidLoginInfo(e, p)
        
        if result['status'] == True:
            user_info = user.get_user_profile(result['userId'])
            if(user_info != None):
                self._clear_inputs()
                user.CURRENT_USER.login(uid=user_info['userId'], 
                                        username=user_info["username"],
                                        email=user_info['email'])
                self.show_message("Success", f"Welcome back, {user_info['username']}!")
                self.login_success_signal.emit()
                self.back_to_home_requested.emit()
        else:
            self.show_message("Login Failed", result['message'], QMessageBox.Icon.Warning)
            return

    def _handle_register(self):
        e = self.reg_email.text().strip()
        p1 = self.reg_pass1.text().strip()
        p2 = self.reg_pass2.text().strip()
        u = self.reg_user.text().strip()

        if not (e and u and p1 and p2):
            self.show_message("Error", "Not enough infomation", QMessageBox.Icon.Warning)
            return
        
        if p1 != p2:
            self.show_message("Registeration failed", "Passwords do not match!", QMessageBox.Icon.Warning)
            self.reg_pass1.clear()
            self.reg_pass2.clear()
            return
        
        if len(p1) < 6:
            self.show_message("Registeration failed", "Password must be at least 6 characters long", QMessageBox.Icon.Warning)
            self.reg_pass1.clear()
            self.reg_pass2.clear()
            return
        result = user.register(email=self.reg_email.text(), 
                            password=self.reg_pass1.text(), 
                            name=self.reg_user.text())
        if(result['status'] == True):
            self.show_message("Success", "Account created!")
            user.CURRENT_USER.login(uid=result['uid'],
                                    username=self.reg_user.text(),
                                    email=self.reg_email.text()) 
            self._switch_mode(0, "Log-in Page")
            self._clear_inputs()
        else:
            self.show_message("Registeration failed", f"{result['message']}", QMessageBox.Icon.Warning)
            return
    
    def _handle_send_reset_email(self):
        email = self.forgot_email.text().strip()
        
        if not email:
            self.show_message("Error", "Please enter your email address.", QMessageBox.Icon.Warning)
            return
        
        status, message = user.reset_password(email)

        if status:
            self.show_message("Email Sent", 
                              f"A password reset link has been sent to {email}.\nPlease check your inbox.", 
                              QMessageBox.Icon.Information)
            
            self._switch_mode(0, "Log-in Page")
            self._clear_inputs()
        else:
            self.show_message("Failed", f"Could not send email: {message}", QMessageBox.Icon.Critical)
        
    def _start_forgot_password_flow(self):
        self._switch_mode(2, "Reset Password")

    def _switch_mode(self, idx, title):
        self.stack.setCurrentIndex(idx)
        self.header_label.setText(title)

    def _clear_inputs(self):
        for w in self.findChildren(QLineEdit): w.clear()

    def update_ui(self):
        # 1. Nền tổng thể
        self.setStyleSheet(f"background-color: {cf.APP_BACKGROUND};")

        # 2. Container (Khung trắng ở giữa)
        
        self.container.setStyleSheet(f"""
            QFrame {{
                background-color: {cf.WHITE}; 
                border-radius: 10px; 
                border: 1px solid {cf.SHADOW_COLOR};
            }}
        """)

        self.stack.setStyleSheet("background: transparent; border: none;")
        self.page_login.setStyleSheet("background: transparent; border: none;")
        self.page_register.setStyleSheet("background: transparent; border: none;")
        self.page_forgot_password.setStyleSheet("background: transparent; border: none;")

        # 3. Header Label
        self.header_label.setStyleSheet(f"font-size: 27px; font-weight: bold; color: {cf.NORMAL_TITLE}; border: none; background: transparent;")

        # 4. Các Label hướng dẫn (nếu có)
        if hasattr(self, 'lbl_instruction'):
            self.lbl_instruction.setStyleSheet(f"color: {cf.DARK_TEXT}; font-size: 14px; margin-bottom: 10px; border: none; padding: 0px; background: transparent;")

        # 5. Input Fields (Email, Pass)
        input_style = f"""
            QLineEdit {{
                color: {cf.DARK_TEXT}; 
                background-color: {cf.WHITE};
                font-size: 16px; 
                border: 1px solid {cf.SHADOW_COLOR}; 
                border-radius: 5px; 
                padding: 5px;
            }}
            QLineEdit:focus {{
                border: 1px solid {cf.LINK_TEXT};
                background-color: {cf.WHITE};
            }}
        """
        for inp in self.findChildren(QLineEdit):
            current_style = input_style
            if isinstance(inp, PasswordLineEdit): 
                inp.update_ui()
            else: inp.setStyleSheet(current_style)

        # 6. Các nút chính (Primary Buttons)
        # Bao gồm: Login, Register, Send Reset, Back Home
        # Lưu ý: Tôi gộp cả btn_ver_cancel (Back to Login) vào đây để nó đẹp như nút Send Reset
        primary_btns = [
            self.btn_login, self.btn_register, 
            self.btn_send_reset, self.btn_ver_cancel, 
            self.back_button,self.btn_reg_cancel
        ]
        
        btn_style_primary = f"""
            QPushButton {{
                background-color: {cf.BUTTON_BACKGROUND};
                color: {cf.WHITE}; 
                border-radius: 5px; 
                padding: 10px; 
                font-weight: bold;
                border: none;
            }}
            QPushButton:hover {{ opacity: 0.9; color: {cf.BLACK}}}
        """
        
        for btn in primary_btns:
            # Kiểm tra tồn tại trước khi set (phòng trường hợp chưa init xong)
            if btn: btn.setStyleSheet(btn_style_primary)

        cancel_btns = [
            self.btn_reg_cancel,   # Cancel ở trang Register
            self.btn_ver_cancel    # Back to Login ở trang Forgot
        ]
        btn_style_cancel = f"""
            QPushButton {{
                background-color: {cf.CANCEL_BG}; /* Màu xám trung tính */
                color: #ffffff; 
                border-radius: 6px; padding: 10px; font-weight: bold; border: none; font-size: 14px;
            }}
            QPushButton:hover {{ background-color: {cf.CANCEL_HOVER}; }} /* Xám đậm hơn khi hover */
        """
        for btn in cancel_btns:
            if btn: btn.setStyleSheet(btn_style_cancel)


        # 7. Các nút dạng Link (Text only)
        link_btns = [self.btn_to_reg, self.btn_forgot, self.btn_to_reg_forgot]
        link_style = f"""
            QPushButton {{
                background-color: transparent;
                color: {cf.LINK_TEXT};
                border: none; text-decoration: underline;
            }}
            QPushButton:hover {{ color: {cf.DARK_TEXT}; }}
        """
        for btn in link_btns:
            if btn: btn.setStyleSheet(link_style)
            
        # 8. Nút Google với colorful border gradient (Google colors: Blue, Red, Yellow, Green)
        self.btn_google.setIcon(QIcon(get_icon_pixmap('icon-google')))

        # Colorful Google button với gradient border (Qt-compatible)
        self.btn_google.setStyleSheet(f"""
            QPushButton {{
                background-color: {cf.GOOGLE_BG};
                color: {cf.GOOGLE_TEXT};
                border: 3px solid qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #4285f4, stop:0.33 #ea4335, stop:0.66 #fbbc05, stop:1 #34a853);
                border-radius: 8px;
                padding: 12px 20px;
                font-weight: bold;
                font-size: 15px;
            }}
            QPushButton:hover {{
                background-color: #f8f9fa;
                border: 3px solid qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #34a853, stop:0.33 #4285f4, stop:0.66 #ea4335, stop:1 #fbbc05);
            }}
            QPushButton:pressed {{
                background-color: #e8e9ea;
                border: 3px solid qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #fbbc05, stop:0.33 #34a853, stop:0.66 #4285f4, stop:1 #ea4335);
            }}
            QPushButton:disabled {{
                opacity: 0.6;
                color: #999;
            }}
        """)
    
    def handle_google_login(self):
        # Disable nút để tránh bấm nhiều lần
        self.btn_google.setEnabled(False)
        self.btn_google.setText("Waiting for browser...")
        
        # Khởi chạy luồng login
        self.google_thread = GoogleLoginWorker()
        self.google_thread.login_finished.connect(self.on_google_login_finished)
        self.google_thread.start()

    def on_google_login_finished(self, result):
        # Kích hoạt lại nút
        self.btn_google.setEnabled(True)
        self.btn_google.setText("Sign in with Google")

        if result["success"]:
            user.CURRENT_USER = result['user']
            print(user.CURRENT_USER)
            
            # Show welcome popup with animation
            self._show_welcome_popup()
            
            self.login_success_signal.emit()
        else:
            self.show_message("Login Failed", f"Google Login Error: {result['error']}", QMessageBox.Icon.Warning)
    
    def _show_welcome_popup(self):
        """Show animated welcome popup for successful login"""
        from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel
        from PyQt6.QtCore import QTimer, QPropertyAnimation
        from PyQt6.QtGui import QFont
        
        dialog = QDialog(self)
        dialog.setWindowTitle("Welcome!")
        dialog.setFixedSize(500, 280)
        dialog.setModal(True)
        
        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(40, 35, 40, 35)
        layout.setSpacing(20)
        
        # Welcome emoji with animation
        emoji_label = QLabel("🎉")
        emoji_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        emoji_label.setStyleSheet("font-size: 60px; border: none;")
        layout.addWidget(emoji_label)
        
        # Welcome text
        welcome_label = QLabel(f"Welcome back, {user.CURRENT_USER.username}!")
        welcome_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        welcome_font = QFont()
        welcome_font.setBold(True)
        welcome_font.setPointSize(16)
        welcome_label.setFont(welcome_font)
        welcome_label.setStyleSheet(f"color: {cf.BUTTON_BACKGROUND}; border: none;")
        layout.addWidget(welcome_label)
        
        # Success message
        success_label = QLabel("✨ You have successfully logged in! ✨")
        success_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        success_label.setStyleSheet(f"color: {cf.DARK_TEXT}; font-size: 13px; border: none;")
        layout.addWidget(success_label)
        
        # OK button to close dialog
        btn_ok = QPushButton("OK")
        btn_ok.setFixedHeight(35)
        btn_ok.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_ok.clicked.connect(dialog.accept)
        btn_ok.setStyleSheet(f"""
            QPushButton {{
                background-color: {cf.BUTTON_BACKGROUND};
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 25px;
                font-weight: bold;
                font-size: 13px;
            }}
            QPushButton:hover {{
                background-color: {cf.LINK_TEXT};
            }}
        """)
        layout.addWidget(btn_ok, 0, Qt.AlignmentFlag.AlignCenter)
        
        dialog.setStyleSheet(f"""
            QDialog {{
                background-color: {cf.APP_BACKGROUND};
                border-radius: 15px;
            }}
        """)
        
        # Fade in animation
        dialog.setWindowOpacity(0)
        animation = QPropertyAnimation(dialog, b"windowOpacity")
        animation.setDuration(500)
        animation.setStartValue(0.0)
        animation.setEndValue(1.0)
        animation.start()
        
        dialog.exec()