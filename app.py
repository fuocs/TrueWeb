# app.py
import os
from PyQt6.QtWidgets import QApplication, QMessageBox
from PyQt6.QtGui import QIcon, QShortcut, QKeySequence
from PyQt6.QtCore import QThread, pyqtSignal, Qt, QTimer
import os, sys

# --- IMPORT CÁC MODULE GIAO DIỆN (VIEW) ---
from frontend.main_window import MainWindow        # Khung cửa sổ chính (Container)
from frontend.home_page import HomePage            # Trang chủ (View)
from frontend.login_page import LoginPage
from frontend.write_review_page import WriteReviewPage
from frontend.settings_page import SettingsPage
from frontend.info_page import InfoPage
from frontend.result_page import SearchResultsPage # Trang kết quả (Dynamic)
from frontend.respond_window import RespondWindow   # Popup window for extension
from frontend.UI_helpers import get_asset_path     # Asset path for PyInstaller compatibility

# --- IMPORT MODULE HỆ THỐNG & BACKEND ---
from frontend.system_tray_utils import SystemTrayManager
from frontend import configuration as cf
from backend import user  # Module quản lý user
from backend import localserver  # Local server for extension integration

# ============================================================
# CLASS CHẠY SERVER DƯỚI DẠNG LUỒNG (THREAD)
# ============================================================
class ServerWorker(QThread):
    """Thread worker to run Flask server in background"""
    new_url_signal = pyqtSignal(str)
    
    def run(self):
        # Hàm cầu nối: Flask gọi hàm này -> Hàm này phát tín hiệu PyQt
        def bridge_callback(url):
            self.new_url_signal.emit(url)

        # Đăng ký cầu nối với server
        localserver.set_callback(bridge_callback)
        
        # Khởi chạy server (Hàm này sẽ chặn luồng này, nhưng ko chặn App chính)
        try:
            print("[ServerWorker] Starting local server on http://127.0.0.1:38999")
            localserver.run()
        except Exception as e:
            print(f"[ServerWorker] Server error: {e}")

class AppManager(QApplication):
    def __init__(self, argv):
        super().__init__(argv)

        # ============================================================
        # 1. KHỞI TẠO CỬA SỔ CHÍNH & SYSTEM TRAY
        # ============================================================
        self.main_window = MainWindow()
        
        self.icon_path = get_asset_path('icon.png')  # PyInstaller compatible path
        self.main_window.setWindowIcon(QIcon(self.icon_path))
        
        # Quản lý System Tray (Chạy ngầm)
        self.tray_manager = SystemTrayManager(
            main_window=self.main_window,
            app=self, 
            icon_path=self.icon_path, 
            app_id="TrueWeb"
        )

        # Ngăn app tự tắt khi đóng cửa sổ cuối cùng (popup)
        self.setQuitOnLastWindowClosed(False)

        # Quản lý popup windows từ extension
        self.active_popups = []

        # ============================================================
        # 2. KHỞI TẠO CÁC TRANG (PAGES)
        # ============================================================
        # Các trang tĩnh (Static) chỉ cần tạo 1 lần
        self.home_page = HomePage()
        self.login_page = LoginPage("Login")
        self.write_review_page = WriteReviewPage("Write Review")
        self.settings_page = SettingsPage("Settings")
        self.info_page = InfoPage("About Us")
        
        # Trang động (Dynamic) sẽ tạo sau khi search
        self.search_results_page_instance = None

        # ============================================================
        # 5. KẾT NỐI TÍN HIỆU (WIRING SIGNALS)
        # ============================================================
        self._connect_signals()

        # ============================================================
        # 3. ĐƯA CÁC TRANG VÀO STACK CỦA MAIN WINDOW
        # ============================================================
        self.main_window.add_page(self.home_page)         
        self.main_window.add_page(self.login_page)        
        self.main_window.add_page(self.write_review_page) 
        self.main_window.add_page(self.settings_page)     
        self.main_window.add_page(self.info_page)         

        # Set trang mặc định là Home
        self.main_window.set_page(self.home_page)

        # ============================================================
        # 4. QUẢN LÝ TRẠNG THÁI (STATE MANAGEMENT)
        # ============================================================
        self.is_logged_in = False
        
        # Cập nhật UI Home ban đầu
        self.home_page.update_login_state(self.is_logged_in)

        # Hiển thị app
        self.main_window.show()

        # ============================================================
        # 6. KHỞI ĐỘNG LOCAL SERVER (EXTENSION INTEGRATION)
        # ============================================================
        self.server_thread = ServerWorker()
        self.server_thread.new_url_signal.connect(self.handle_incoming_link)
        # Khi app chính tắt, luồng server cũng sẽ bị hủy theo
        self.server_thread.start()
        
        # ============================================================
        # 7. GLOBAL KEYBOARD SHORTCUT (FOCUS ANALYZE WINDOW)
        # ============================================================
        # Ctrl+Shift+Space: Focus vào analyze window nếu đang mở
        self.focus_shortcut = QShortcut(QKeySequence("Ctrl+Shift+Space"), self.main_window)
        self.focus_shortcut.activated.connect(self.focus_analyze_window)
        
        # ============================================================
        # 8. CLEANUP ON APP EXIT
        # ============================================================
        self.aboutToQuit.connect(self.cleanup_on_exit)

        # ============================================================
        # 9. REAL-TIME CONNECTIVITY CHECK (periodic)
        # ============================================================
        # Check internet connectivity periodically; on loss show dialog and exit.
        self.connectivity_timer = QTimer(self)
        self.connectivity_timer.setInterval(5000)  # check every 5 seconds
        self.connectivity_timer.timeout.connect(self._check_connectivity)
        self.connectivity_timer.start()

    def _connect_signals(self):
        """Hàm tập trung kết nối tất cả Signal/Slot"""

        # --- A. TÍN HIỆU TỪ HOME PAGE ---
        self.home_page.search_requested.connect(self.show_search_results_page)
        self.home_page.login_nav_requested.connect(self.handle_login_nav_request)
        self.home_page.settings_nav_requested.connect(lambda: self.main_window.set_page(self.settings_page))
        self.home_page.info_nav_requested.connect(lambda: self.main_window.set_page(self.info_page))

        # --- B. TÍN HIỆU TỪ LOGIN PAGE ---
        self.login_page.back_to_home_requested.connect(self.return_home)
        self.login_page.login_success_signal.connect(self.on_user_logged_in)
        self.login_page.logout_signal.connect(self.on_user_logged_out)

        # --- C. TÍN HIỆU TỪ CÁC TRANG KHÁC ---
        self.settings_page.back_to_home_requested.connect(self.return_home)
        self.info_page.back_to_home_requested.connect(self.return_home)
        
        # --- D. TÍN HIỆU TỪ WRITE REVIEW PAGE ---
        self.write_review_page.cancelled.connect(self.return_to_results_or_home)
        self.write_review_page.review_submitted.connect(self.handle_new_review_submission)

        # --- E. TÍN HIỆU HỆ THỐNG (RESIZE WINDOW & SETTINGS) ---
        self.main_window.pages_stack.currentChanged.connect(self.handle_page_changed)
        self.settings_page.minimize_to_tray_toggled.connect(self.tray_manager.set_minimize_to_tray)
        self.settings_page.theme_toggled.connect(self.handle_theme_change)

    # ============================================================
    # 6. CÁC HÀM XỬ LÝ LOGIC (CONTROLLER LOGIC)
    # ============================================================

    # --- LOGIC TÌM KIẾM & KẾT QUẢ ---
    def show_search_results_page(self, query, timeout=30, screenshot_enabled=True):
        # 0. EARLY CHECK: Verify website is reachable before showing result page
        from PyQt6.QtWidgets import QMessageBox
        from backend.scoring_system import check_website_reachable
        
        # Show loading cursor while checking
        from PyQt6.QtGui import QCursor
        from PyQt6.QtCore import Qt
        self.main_window.setCursor(QCursor(Qt.CursorShape.WaitCursor))
        
        try:
            is_reachable, error_message = check_website_reachable(query, timeout=5)
            
            if not is_reachable:
                # Website is unreachable - show error and stay on home page
                self.main_window.setCursor(QCursor(Qt.CursorShape.ArrowCursor))
                
                msg = QMessageBox(self.main_window)
                msg.setIcon(QMessageBox.Icon.Critical)
                msg.setWindowTitle("Website Unreachable")
                msg.setText(f"Cannot connect to the website:\n\n{query}")
                msg.setInformativeText(f"Reason: {error_message}\n\nPlease check:\n• The URL is correct\n• The website is online\n• Your internet connection")
                msg.setStyleSheet("QLabel{color: #000000;} QPushButton{color: #000000;}")
                msg.exec()
                return  # Stop here, don't proceed to result page
        finally:
            self.main_window.setCursor(QCursor(Qt.CursorShape.ArrowCursor))
        
        # 1. Dọn dẹp trang kết quả cũ nếu có
        if self.search_results_page_instance:
            self.main_window.remove_page(self.search_results_page_instance)
            self.search_results_page_instance.deleteLater()
            self.search_results_page_instance = None

        # 2. Tạo trang kết quả mới với timeout và screenshot preference từ user
        self.search_results_page_instance = SearchResultsPage(query, timeout, screenshot_enabled)

        # 3. Kết nối tín hiệu riêng của trang kết quả
        self.search_results_page_instance.back_to_home_requested.connect(self.return_home)
        # Nút "Write Review" nằm trong trang kết quả -> Kết nối vào logic xử lý
        self.search_results_page_instance.write_review_requested.connect(self.handle_write_review_request)
        # Khi load xong -> Mở rộng cửa sổ
        self.search_results_page_instance.analysis_finished.connect(self.expand_window_for_results)

        # 4. Thêm vào stack và hiển thị
        self.main_window.add_page(self.search_results_page_instance)
        self.main_window.set_page(self.search_results_page_instance)

    def expand_window_for_results(self):
        """Mở rộng cửa sổ khi kết quả đã load xong"""
        if self.search_results_page_instance:
            self.search_results_page_instance.has_finished_loading = True

        self.main_window.setFixedSize(900, 700)
        self._center_window()

    # --- LOGIC ĐIỀU HƯỚNG CƠ BẢN ---
    def return_home(self):
        self.main_window.set_page(self.home_page)
        
    def return_to_results_or_home(self):
        """Quay lại trang kết quả nếu có, không thì về Home"""
        if self.search_results_page_instance:
            self.main_window.set_page(self.search_results_page_instance)
        else:
            self.return_home()

    # --- LOGIC ĐĂNG NHẬP / ĐĂNG XUẤT ---
    def handle_login_nav_request(self):
        """Xử lý khi bấm nút Login trên Menu"""
        if self.is_logged_in:
            # Nếu đã login -> Trang login sẽ hiện popup hỏi Logout
            self.login_page.handle_entry_request(True)
        else:
            # Nếu chưa -> Trang login hiện form nhập liệu
            self.login_page.handle_entry_request(False)
        
        self.main_window.set_page(self.login_page)

    def on_user_logged_in(self):
        self.is_logged_in = True
        # Cập nhật giao diện Home (đổi icon Login -> Logout)
        self.home_page.update_login_state(True)
        self.return_home()

    def on_user_logged_out(self):
        self.is_logged_in = False
        # Gọi backend logout nếu cần: user.CURRENT_USER.logout()
        self.home_page.update_login_state(False)
        self.return_home()

    # --- LOGIC VIẾT REVIEW ---
    def handle_write_review_request(self):
        """Logic kiểm tra quyền trước khi cho phép viết review"""
        
        # 1. Kiểm tra đăng nhập
        if not self.is_logged_in:
            self._show_message("Login Required", "You need to log in to write a review!", QMessageBox.Icon.Warning)
            return
        
        self.main_window.set_page(self.write_review_page)

    def handle_new_review_submission(self, score, comment):
        """Xử lý khi người dùng bấm Confirm Review"""
        if self.search_results_page_instance:
            # Thêm review vào trang kết quả
            # Lưu ý: result_page.py cần xử lý việc lấy tên user hoặc nhận tham số username
            self.search_results_page_instance.add_user_review(score, comment)
            
        self.return_to_results_or_home()

    # --- LOGIC RESIZE CỬA SỔ (QUAN TRỌNG) ---
    def handle_page_changed(self, index):
        """
        Tự động thay đổi kích thước cửa sổ dựa trên trang đang hiển thị.
        Logic này trước đây nằm ở home_page, giờ App quản lý.
        """
        widget = self.main_window.pages_stack.widget(index)
        
        if widget == self.home_page:
            self.main_window.setFixedSize(750, 280)
            
        elif widget == self.login_page:
            self.main_window.setFixedSize(500, 600)
            
        elif widget == self.write_review_page:
            self.main_window.setFixedSize(600, 600)
            
        elif widget == self.settings_page or widget == self.info_page:
            self.main_window.setFixedSize(700, 500)
            
        elif isinstance(widget, SearchResultsPage):
            if getattr(widget, 'has_finished_loading', False):
                 self.main_window.setFixedSize(900, 700)
            else:
                # Nếu chưa (mới vào), thì set size nhỏ (Loading state)
                self.main_window.setFixedSize(750, 350)
                self._center_window()

    # --- UTILS HELPER ---
    def _center_window(self):
        screen = self.main_window.screen()
        if screen:
            geom = screen.availableGeometry()
            current_geo = self.main_window.frameGeometry()
            current_geo.moveCenter(geom.center())
            self.main_window.move(current_geo.topLeft())

    def _show_message(self, title, text, icon):
        msg = QMessageBox(self.main_window)
        msg.setWindowTitle(title)
        msg.setText(text)
        msg.setIcon(icon)
        msg.setStyleSheet(f"QLabel{{color: #000000;}} QPushButton{{color: #000000;}}")
        msg.exec()

    def _check_connectivity(self):
        """Periodic check: if internet unreachable, show dialog and exit app on OK."""
        try:
            from backend.scoring_system import quick_connectivity_check
            # Use a simple well-known host for checking (no user URL)
            ok, err = quick_connectivity_check('https://www.google.com', timeout=3)
        except Exception as e:
            # If check routine fails unexpectedly, treat as not connected
            ok = False
            err = str(e)

        if not ok:
            # Stop timer to avoid repeated dialogs
            try:
                self.connectivity_timer.stop()
            except Exception:
                pass

            # Show critical dialog and then quit fully when user acknowledges
            msg = QMessageBox(self.main_window)
            msg.setIcon(QMessageBox.Icon.Critical)
            msg.setWindowTitle("Connection Lost")
            msg.setText("Internet connection appears to be lost.")
            info = f"Details: {err}" if err else ""
            msg.setInformativeText(info + "\n\nClick OK to close the application.")
            msg.setStandardButtons(QMessageBox.StandardButton.Ok)
            # Ensure dialog text/buttons are rendered in black for readability
            msg.setStyleSheet("QLabel{color: #000000;} QPushButton{color: #000000;}")
            try:
                msg.exec()
            except Exception:
                pass

            # Force a full exit
            try:
                self.quit()
            finally:
                # Ensure process exits
                os._exit(0)

    # --- EXTENSION INTEGRATION ---
    def handle_incoming_link(self, url):
        """
        Xử lý URL nhận từ browser extension.
        Tạo cửa sổ SearchResultsPage đầy đủ (như input thông thường).
        Hỗ trợ nhiều cửa sổ đồng thời (multi-threading).
        """
        print(f"[AppManager] Received URL from extension: {url}")
        
        # Import thêm QDialog để tạo container window
        from PyQt6.QtWidgets import QDialog, QVBoxLayout
        
        # 1. Tạo cửa sổ dialog container
        dialog = QDialog(parent=None)
        dialog.setWindowTitle(f"TrueWeb - Analyzing: {url[:50]}...")
        dialog.setWindowFlags(Qt.WindowType.Window)  # Cửa sổ độc lập
        
        # Set icon nếu có
        if os.path.exists(self.icon_path):
            from PyQt6.QtGui import QIcon
            dialog.setWindowIcon(QIcon(self.icon_path))
        
        # 2. Tạo SearchResultsPage đầy đủ với timeout từ settings
        timeout = cf.get_timeout()
        results_page = SearchResultsPage(url, timeout)
        
        # 3. Đặt SearchResultsPage vào dialog
        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(results_page)
        
        # 4. Kết nối signals
        # Khi bấm Back -> đóng cửa sổ này
        results_page.back_to_home_requested.connect(dialog.close)
        
        # Khi analysis xong -> resize cửa sổ
        results_page.analysis_finished.connect(lambda: self._expand_extension_window(dialog, results_page))
        
        # Khi bấm Write Review
        results_page.write_review_requested.connect(lambda: self._handle_extension_write_review(dialog, results_page))
        
        # Khi đóng cửa sổ -> cleanup
        dialog.finished.connect(lambda: self._cleanup_popup(dialog))
        
        # 5. Set kích thước ban đầu (loading state)
        dialog.setFixedSize(750, 350)
        
        # 6. Thêm vào danh sách quản lý
        self.active_popups.append(dialog)
        
        # 7. Center window
        screen = dialog.screen()
        if screen:
            geom = screen.availableGeometry()
            current_geo = dialog.frameGeometry()
            current_geo.moveCenter(geom.center())
            dialog.move(current_geo.topLeft())
        
        # 8. Hiện cửa sổ (non-blocking - mỗi URL có cửa sổ riêng)
        dialog.show()
        dialog.raise_()
        dialog.activateWindow()

    def _cleanup_popup(self, popup):
        """Xóa popup khỏi danh sách quản lý khi người dùng tắt nó"""
        if popup in self.active_popups:
            self.active_popups.remove(popup)
            popup.deleteLater()  # Giải phóng bộ nhớ hoàn toàn
    
    def _expand_extension_window(self, dialog, results_page):
        """Mở rộng cửa sổ extension khi analysis hoàn tất"""
        results_page.has_finished_loading = True
        dialog.setFixedSize(900, 700)
        
        # Store URL in dialog for cleanup when closed
        dialog.analyzed_url = results_page.query_url
        
        # Connect dialog close event to cleanup analyzed URLs
        dialog.finished.connect(lambda: self._cleanup_analyzed_url(dialog))
        
        # Center lại sau khi resize
        screen = dialog.screen()
        if screen:
            geom = screen.availableGeometry()
            current_geo = dialog.frameGeometry()
            current_geo.moveCenter(geom.center())
            dialog.move(current_geo.topLeft())
    
    def _handle_extension_write_review(self, dialog, results_page):
        """Xử lý Write Review từ extension window"""
        # Kiểm tra đăng nhập
        if not self.is_logged_in:
            self._show_message("Login Required", "You need to log in to write a review!", QMessageBox.Icon.Warning)
            return
        
        # Tạo WriteReviewPage trong extension window
        write_review_page = WriteReviewPage("Write Review")
        
        # Thay thế nội dung dialog bằng write review page
        # Clear layout cũ
        layout = dialog.layout()
        if layout:
            # Remove results_page
            layout.removeWidget(results_page)
            results_page.setVisible(False)
            
            # Add write review page
            layout.addWidget(write_review_page)
            dialog.setFixedSize(600, 600)
            
            # Set dialog background to match write review page
            dialog.setStyleSheet(f"QDialog {{ background-color: {cf.APP_BACKGROUND}; }}")
            
            # Kết nối signals
            write_review_page.cancelled.connect(lambda: self._restore_results_view(dialog, results_page, write_review_page))
            write_review_page.review_submitted.connect(lambda score, comment: self._handle_extension_review_submit(dialog, results_page, write_review_page, score, comment))
    
    def _restore_results_view(self, dialog, results_page, write_review_page):
        """Quay lại results page sau khi cancel review"""
        layout = dialog.layout()
        if layout:
            layout.removeWidget(write_review_page)
            write_review_page.deleteLater()
            
            results_page.setVisible(True)
            layout.addWidget(results_page)
            dialog.setFixedSize(900, 700)
            
            # Reset dialog background to default (remove green background)
            dialog.setStyleSheet("")
    
    def _handle_extension_review_submit(self, dialog, results_page, write_review_page, score, comment):
        """Xử lý submit review từ extension window"""
        # Add review vào results page
        results_page.add_user_review(score, comment)
        
        # Quay lại results view
        self._restore_results_view(dialog, results_page, write_review_page)

    def _cleanup_analyzed_url(self, dialog):
        """Remove URL from analyzed set when extension window closes"""
        if hasattr(dialog, 'analyzed_url'):
            url = dialog.analyzed_url
            # Remove from localserver's analyzed_urls set
            if url in localserver.analyzed_urls:
                localserver.analyzed_urls.remove(url)
                print(f"[AppManager] Removed {url} from analyzed URLs - can scan again")
    
    def focus_analyze_window(self):
        """Focus vào analyze window khi nhấn Ctrl+Shift+Space"""
        # Ưu tiên focus vào popup extension windows
        if self.active_popups:
            # Focus vào popup mới nhất
            latest_popup = self.active_popups[-1]
            if latest_popup.isMinimized():
                latest_popup.showNormal()  # Restore if minimized
            latest_popup.show()  # Ensure visible
            latest_popup.raise_()
            latest_popup.activateWindow()
            latest_popup.setFocus()
            print("[AppManager] Focused extension analyze window")
        # Nếu không có popup, focus vào main window nếu đang ở results page
        elif self.search_results_page_instance:
            current_page = self.main_window.pages_stack.currentWidget()
            if current_page == self.search_results_page_instance:
                if self.main_window.isMinimized():
                    self.main_window.showNormal()  # Restore if minimized
                self.main_window.show()  # Ensure visible
                self.main_window.raise_()
                self.main_window.activateWindow()
                self.main_window.setFocus()
                print("[AppManager] Focused main window (results page)")
        else:
            # Không có analyze window nào đang mở
            print("[AppManager] No analyze window to focus")
    
    def cleanup_on_exit(self):
        """Cleanup khi app đóng - xóa screenshots folder"""
        from backend.take_screenshot import cleanup_screenshots_folder
        print("[AppManager] App closing - cleaning up...")
        cleanup_screenshots_folder()
    
    def handle_theme_change(self, is_dark):
        """Xử lý khi bật/tắt Dark Mode"""
        # 1. Cập nhật biến màu sắc toàn cục
        cf.set_mode(is_dark) 

        # 2. Cập nhật giao diện Container chính
        self.main_window.update_ui()

        # 3. Cập nhật giao diện các trang con (để chúng lấy màu mới)
        self.home_page.update_ui()
        self.login_page.update_ui()
        self.write_review_page.update_ui()
        self.settings_page.update_ui()
        self.info_page.update_ui()

        # 4. Nếu đang có trang kết quả, cũng phải cập nhật nó
        if self.search_results_page_instance:
            self.search_results_page_instance.update_ui()