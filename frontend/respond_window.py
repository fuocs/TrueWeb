# frontend/respond_window.py
import sys
import os
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QWidget,
                             QStackedWidget, QProgressBar, QFrame, QScrollArea, QMessageBox)
from PyQt6.QtCore import Qt, pyqtSignal, QEvent

from frontend import configuration as cf
from frontend.user_review import ReviewsSection
from frontend.loading_page import LoadingPage

# [IMPORT MỚI]
from .result_components import AnalysisWorker, ScoreGauge, PreviewImageCard, shorten_url

# --- PAGE 1: GENERAL RESULT ---
class ResultSummaryPage(QWidget):
    see_reviews_clicked = pyqtSignal()
    close_clicked = pyqtSignal()

    def __init__(self, url, score, criteria_scores_dict, descriptions_dict, parent=None):
        super().__init__(parent)
        self.descriptions = descriptions_dict 

        main_v_layout = QVBoxLayout(self)
        main_v_layout.setContentsMargins(15, 10, 15, 15)
        main_v_layout.setSpacing(0)

        # URL
        self.shorten_url = shorten_url(url)
        lbl_url = QLabel(self.shorten_url)
        lbl_url.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_url.setStyleSheet(f"font-size: 18px; font-weight: bold; color: {cf.LINK_TEXT}; text-decoration: underline;")
        main_v_layout.addWidget(lbl_url)

        # Content
        content_h_layout = QHBoxLayout()
        content_h_layout.setSpacing(5)
        content_h_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # 1. Preview Image (Dùng Component mới - Size NHỎ)
        self.preview_card = PreviewImageCard(width=240, height=135)
        
        # Bọc vào layout dọc để canh giữa
        col_preview = QVBoxLayout()
        col_preview.addWidget(self.preview_card, 0, Qt.AlignmentFlag.AlignCenter)
        content_h_layout.addLayout(col_preview)

        # 2. Gauge (Dùng Component mới - Size NHỎ)
        col_gauge = QVBoxLayout()
        col_gauge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.gauge = ScoreGauge(score, width=160, height=100)
        col_gauge.addWidget(self.gauge, 0, Qt.AlignmentFlag.AlignCenter)
        
        self.btn_details = QPushButton("Show details >>")
        self.btn_details.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_details.setCheckable(True)
        self.btn_details.setStyleSheet(f"""
            QPushButton {{ color: {cf.LINK_TEXT}; background: transparent; border: none; text-decoration: underline; font-size: 11px; margin-top: 5px; }}
            QPushButton:hover {{color: {cf.DARK_TEXT};}}
        """)
        self.btn_details.clicked.connect(self.toggle_details)
        col_gauge.addWidget(self.btn_details, 0, Qt.AlignmentFlag.AlignCenter)
        content_h_layout.addLayout(col_gauge)

        # 3. Criteria List (Logic giữ nguyên do config size bar khác)
        self.criteria_frame = QFrame()
        self.criteria_frame.setVisible(False)
        self.criteria_frame.setFixedWidth(250)
        self.criteria_frame.setStyleSheet(f"background-color: white; border-radius: 8px; border: 1px solid #eee;")
        c_layout = QVBoxLayout(self.criteria_frame)
        c_layout.setSpacing(2); c_layout.setContentsMargins(5, 5, 5, 5)

        ordered_keys = ['Certificate details', 'Server reliablity', 'Domain age', 'Domain pattern', 'HTML content and behavior', 'Protocol security', 'AI analysis', 'Reputation DB', 'User review']
        self.criteria_bars = []
        for name in ordered_keys:
            score_val = criteria_scores_dict.get(name, 0.0)
            row = QHBoxLayout()
            btn_name = QPushButton(name)
            btn_name.setCursor(Qt.CursorShape.PointingHandCursor)
            btn_name.setStyleSheet(f"QPushButton {{text-align: left; border: none; background: transparent; color: {cf.DARK_TEXT}; font-size: 10px;}} QPushButton:hover {{ text-decoration: underline; color: {cf.LINK_TEXT}; }}")
            btn_name.clicked.connect(lambda checked, n=name: self.show_criteria_info(n))

            p_bar = QProgressBar()
            p_bar.setRange(0, 100); p_bar.setValue(int(score_val * 10)); p_bar.setTextVisible(True); p_bar.setFormat(f"{score_val:.1f}")
            p_bar.setFixedSize(40, 8); p_bar.setStyleSheet(f"QProgressBar {{border: 1px solid #ddd; border-radius: 4px; text-align: center; color: black; background-color: #f9f9f9; font-size: 8px;}} QProgressBar::chunk {{ background-color: {cf.HEADER_BACKGROUND}; border-radius: 4px; }}")
            
            p_bar.installEventFilter(self)
            p_bar.setProperty("criteria_name", name)
            self.criteria_bars.append(p_bar)
            row.addWidget(btn_name); row.addStretch(); row.addWidget(p_bar)
            c_layout.addLayout(row)

        content_h_layout.addWidget(self.criteria_frame)
        main_v_layout.addLayout(content_h_layout)
        main_v_layout.addSpacing(25)

        # Footer
        btn_layout = QHBoxLayout(); btn_layout.setSpacing(20); btn_layout.addStretch()
        
        btn_reviews = QPushButton("Reviews"); btn_reviews.setStyleSheet(self._get_btn_style(True))
        btn_reviews.clicked.connect(self.see_reviews_clicked.emit)
        
        btn_ok = QPushButton("OK"); btn_ok.setStyleSheet(self._get_btn_style(False))
        btn_ok.clicked.connect(self.close_clicked.emit)
        
        btn_layout.addWidget(btn_reviews); btn_layout.addWidget(btn_ok); btn_layout.addStretch()
        main_v_layout.addLayout(btn_layout)

    def _get_btn_style(self, is_primary):
        bg = cf.BUTTON_BACKGROUND if is_primary else "#6c757d"
        return f"QPushButton {{background-color: {bg}; color: white; border-radius: 5px; padding: 12px 20px; font-size: 12px; font-weight: bold; border: none;}} QPushButton:hover {{ opacity: 0.8; }}"

    def eventFilter(self, source, event):
        if (event.type() == QEvent.Type.MouseButtonPress and source in self.criteria_bars and event.button() == Qt.MouseButton.LeftButton):
            name = source.property("criteria_name")
            if name: self.show_criteria_info(name)
            return True
        return super().eventFilter(source, event)

    def toggle_details(self, checked):
        main_win = self.window() 
        if main_win:
            if checked: 
                self.criteria_frame.setVisible(True)
                self.btn_details.setText("<< Hide details")
                main_win.setFixedSize(880, 280)
            else: 
                self.criteria_frame.setVisible(False)
                self.btn_details.setText("Show details >>")
                main_win.setFixedSize(620, 280)

    def show_criteria_info(self, criteria_name):
        desc = "\n".join(self.descriptions.get(criteria_name, ["Detail."]))
        msg = QMessageBox(self)
        msg.setWindowTitle(f"Criteria: {criteria_name}")
        msg.setText(f"<b>{criteria_name}</b>")
        msg.setInformativeText(desc)
        msg.setIcon(QMessageBox.Icon.Information)
        msg.setStyleSheet(f"QLabel{{color: {cf.DARK_TEXT};}} QPushButton{{color: {cf.DARK_TEXT};}} background-color: white;")
        msg.exec()

# --- PAGE 2: REVIEWS (Giữ nguyên) ---
class ResultReviewsPage(QWidget):
    back_clicked = pyqtSignal()
    close_clicked = pyqtSignal()
    def __init__(self, url, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 10, 15, 10)
        layout.setSpacing(5)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        lbl_title = QLabel(f"Reviews for {url}")
        lbl_title.setStyleSheet(f"font-size: 14px; font-weight: bold; color: {cf.DARK_TEXT};")
        lbl_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(lbl_title)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("border: none; background: transparent;")

        scroll.setFixedSize(580, 165)

        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self.reviews_widget = ReviewsSection(grid_columns=2, load_increment=4)

        self.reviews_widget.display_reviews()

        scroll.setWidget(self.reviews_widget)
        layout.addWidget(scroll, 0, Qt.AlignmentFlag.AlignCenter)

        btn_layout = QHBoxLayout()

        small_btn_style = f"""
            QPushButton {{
                background-color: #6c757d; color: white; border-radius: 5px;
                padding: 6px 15px; font-size: 11px; font-weight: bold; border: none;
            }}
            QPushButton:hover {{opacity: 0.8;}}
        """

        btn_back = QPushButton("Back")
        btn_back.setStyleSheet(small_btn_style)
        btn_back.clicked.connect(self.back_clicked.emit)

        btn_ok = QPushButton("OK")
        btn_ok.setStyleSheet(small_btn_style.replace("#6c757d", cf.BUTTON_BACKGROUND))
        btn_ok.clicked.connect(self.close_clicked.emit)

        btn_layout.addWidget(btn_back)
        btn_layout.addWidget(btn_ok)
        layout.addLayout(btn_layout)

# --- MAIN POPUP WINDOW ---
class RespondWindow(QDialog):
    def __init__(self, url, parent=None):
        super().__init__(parent)
        self.url = url
        self.setWindowTitle("TrueWeb Safety Scan")
        # self.setWindowFlags(self.windowFlags() | Qt.WindowType.WindowStaysOnTopHint)
        self.setStyleSheet(f"background-color: {cf.APP_BACKGROUND};")
        self.setFixedSize(620, 280)
        self.main_layout = QVBoxLayout(self); self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.stack = QStackedWidget(); self.main_layout.addWidget(self.stack)

        self.loading_page = LoadingPage()
        self.stack.addWidget(self.loading_page)
        self.start_analysis()

    def start_analysis(self):
        self.loading_page.start_loading()
        self.worker = AnalysisWorker(self.url)
        self.worker.finished_signal.connect(self.on_analysis_finished)
        self.worker.start()

    def on_analysis_finished(self, score, criteria, descriptions):
        # Check if website is unreachable
        if 'Connection Error' in descriptions:
            error_msg = descriptions['Connection Error'][0] if descriptions['Connection Error'] else 'Website is unreachable'
            # Show error message and close
            from PyQt6.QtWidgets import QMessageBox
            msg = QMessageBox()
            msg.setWindowTitle("Website Unreachable")
            msg.setText("This site can't be reached")
            msg.setInformativeText(f"Unable to connect to {self.url}\n\n{error_msg}")
            msg.setIcon(QMessageBox.Icon.Critical)
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
            self.reject()  # Close the popup window
            return
        
        self.page_summary = ResultSummaryPage(self.url, score, criteria, descriptions)
        self.page_reviews = ResultReviewsPage(self.url)
        self.page_summary.see_reviews_clicked.connect(self.show_reviews)
        self.page_summary.close_clicked.connect(self.accept)
        self.page_reviews.back_clicked.connect(self.show_summary)
        self.page_reviews.close_clicked.connect(self.accept)
        self.stack.addWidget(self.page_summary); self.stack.addWidget(self.page_reviews)
        self.stack.setCurrentWidget(self.page_summary)

    def show_reviews(self): self.stack.setCurrentWidget(self.page_reviews); self.setFixedSize(620, 280)
    
    def show_summary(self):
        self.stack.setCurrentWidget(self.page_summary)
        self.setFixedSize(620, 280)
        
        self.page_summary.criteria_frame.setVisible(False)
        self.page_summary.btn_details.setText("Show details >>")
        self.page_summary.btn_details.setChecked(False)

