import sys
import ctypes
import os
from PyQt6.QtWidgets import QSystemTrayIcon, QMenu, QApplication
from PyQt6.QtGui import QIcon, QAction
from PyQt6.QtCore import QObject, QEvent

class SystemTrayManager(QObject):
    """
    Module quản lý việc chạy ngầm dưới khay hệ thống.
    """
    def __init__(self, main_window, app, icon_path=None, app_id="my.app.id"):
        super().__init__()
        self.window = main_window
        self.app = app
        self.icon_path = icon_path
                
        self.minimize_to_tray_mode = True  # Mặc định là BẬT
       
        # 2. Fix lỗi icon taskbar trên Windows
        if sys.platform == 'win32':
            try:
                ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(app_id)
            except:
                pass

        # 3. Khởi tạo Tray Icon
        self.tray_icon = QSystemTrayIcon(self.window)
        
        # Xử lý icon: Nếu có path thì dùng, không thì dùng icon của window
        if self.icon_path and os.path.exists(self.icon_path):
            self.icon = QIcon(self.icon_path)
        else:
            self.icon = self.window.windowIcon()
        
        if self.icon.isNull():
            print(f"[WARNING] System tray icon is null! Path: {self.icon_path}")
        
        self.tray_icon.setIcon(self.icon)
        
        # 4. Tạo Menu
        self._create_menu()
        
        # 5. Hiển thị
        self.tray_icon.show()
        
        # 6. Bắt sự kiện click vào icon
        self.tray_icon.activated.connect(self._on_tray_activated)
        
        # 7. Cài đặt Event Filter để chặn sự kiện đóng cửa sổ (Magic nằm ở đây)
        self.window.installEventFilter(self)


    def set_minimize_to_tray(self, enabled: bool):
        """Hàm nhận lệnh từ Settings"""
        self.minimize_to_tray_mode = enabled

    def _create_menu(self):
        menu = QMenu()
        
        # Action to show window
        show_action = QAction("Open application", self.window)
        show_action.triggered.connect(self.show_window)
        menu.addAction(show_action)
        
        # Separator
        menu.addSeparator()
        
        # Action to quit
        quit_action = QAction("Exit application", self.window)
        quit_action.triggered.connect(self.quit_app)
        menu.addAction(quit_action)
        
        self.tray_icon.setContextMenu(menu)

    def _on_tray_activated(self, reason):
        # Click chuột trái hoặc đúp chuột thì hiện app
        try:
            if reason == QSystemTrayIcon.ActivationReason.Trigger or \
               reason == QSystemTrayIcon.ActivationReason.DoubleClick:
                if self.window.isVisible():
                    self.window.hide()
                else:
                    self.show_window()
        except Exception as e:
            print(f"[WARNING] Tray activation error: {e}")

    def show_window(self):
        self.window.show()
        self.window.activateWindow() # Đưa lên trên cùng

    def quit_app(self):
        self.tray_icon.hide()
        self.app.quit()

    def eventFilter(self, source, event):
        """
        Tự động bắt sự kiện khi người dùng bấm nút X trên cửa sổ.
        """
        if source == self.window and event.type() == QEvent.Type.Close:
            
            # TRƯỜNG HỢP 1: Chế độ chạy ngầm đang BẬT
            if self.minimize_to_tray_mode:
                event.ignore()  # 1. Chặn lệnh đóng
                self.window.hide()  # 2. Chỉ ẩn cửa sổ đi
                
                # 3. Hiện thông báo (Optional)
                self.tray_icon.showMessage(
                    "TrueWeb",
                    "Ứng dụng đang chạy ngầm dưới khay hệ thống.",
                    QSystemTrayIcon.MessageIcon.Information,
                    2000
                )
                return True # Đánh dấu là đã xử lý xong

            # TRƯỜNG HỢP 2: Chế độ chạy ngầm đang TẮT (Người dùng muốn thoát hẳn)
            else:
                # 1. Chấp nhận lệnh đóng cửa sổ
                event.accept()
                
                # 2. Ẩn icon dưới khay để tránh "icon ma" (biến mất khi di chuột qua)
                self.tray_icon.hide()
                
                # 3. ÉP BUỘC THOÁT ỨNG DỤNG (Chắc chắn 100% sẽ tắt)
                self.app.quit()
                
                return True   

        return super().eventFilter(source, event)