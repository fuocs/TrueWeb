from . import configuration as cf
from PyQt6.QtWidgets import (QWidget, QLabel, QPushButton, QScrollArea, QFrame, QVBoxLayout)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont


class InfoPage(QWidget):
    back_to_home_requested = pyqtSignal()

    def __init__(self, title, parent=None):
        super().__init__(parent)

        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 1. Header Title
        self.header_label = QLabel("About TrueWeb")
        self.header_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.header_label.setStyleSheet("padding: 20px 0;")
        main_layout.addWidget(self.header_label)

        # 2. Scroll Area
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.Shape.NoFrame)

        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(40, 20, 40, 40)
        self.content_layout.setSpacing(20)

        # --- SECTION 1: WHAT IS TRUEWEB? ---
        what_is_trueweb = (
            "TrueWeb is a free security tool that helps you check if a website is safe before you visit it. "
            "It analyzes websites for phishing, malware, and other dangerous content to protect you online.\n\n"
            "Our tool checks 10 different security factors including SSL certificates, domain age, server security, "
            "URL patterns, HTML content, protocols, AI analysis, website reputation, and user reviews. "
            "Each check gives a score from 0 to 5 stars, with higher scores meaning safer websites.\n\n"
            "TrueWeb is designed for everyone - whether you're tech-savvy or not. We explain everything in simple terms "
            "so you can understand exactly why a website might be dangerous."
        )
        self.card_what = self._create_info_card("What is TrueWeb?", what_is_trueweb)
        self.content_layout.addWidget(self.card_what)

        # --- SECTION 2: HOW TO USE? ---
        how_to_use = (
            "Using TrueWeb is easy! Just follow these 4 simple steps:\n\n"
            "1️⃣ Enter a Website: Type or paste the website URL into the search box on the home page. "
            "You can enter it with or without 'https://' (e.g., both 'google.com' and 'https://google.com' work).\n\n"
            "2️⃣ Click Search: Press Enter or click the magnifying glass icon to start the analysis. "
            "TrueWeb will begin checking the website's security.\n\n"
            "3️⃣ Wait for Results: The analysis usually takes 15-45 seconds depending on your timeout setting. "
            "You'll see a progress animation while we check the website.\n\n"
            "4️⃣ Review the Score: Once complete, you'll see a safety score from 0-5 stars and detailed explanations "
            "for each security check. Click on any criterion to learn why it matters and what we found.\n\n"
            "💡 Tip: You can adjust the analysis timeout in Settings if checks take too long or you want faster results!"
        )
        self.card_how = self._create_info_card("How to use TrueWeb?", how_to_use)
        self.content_layout.addWidget(self.card_how)

        # --- SECTION 3: CREDITS ---
        self.card_credits = self._create_credits_card()
        self.content_layout.addWidget(self.card_credits)

        self.content_layout.addStretch()

        self.scroll_area.setWidget(self.content_widget)
        main_layout.addWidget(self.scroll_area)

        # 3. Back button
        self.btn_container = QWidget()
        btn_layout = QVBoxLayout(self.btn_container)
        btn_layout.setContentsMargins(0, 20, 0, 20)

        self.back_button = QPushButton("Back to Home Page")
        self.back_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.back_button.clicked.connect(self.back_to_home_requested.emit)
        btn_layout.addWidget(self.back_button, alignment=Qt.AlignmentFlag.AlignCenter)

        main_layout.addWidget(self.btn_container)

        self.update_ui()

    def _create_info_card(self, title_text, content_text):
        card = QFrame()
        card.setObjectName("InfoCard")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(10)

        title = QLabel(title_text)
        title.setObjectName("CardTitle")
        font = QFont()
        font.setBold(True)
        font.setPointSize(16)
        title.setFont(font)

        content = QLabel(content_text)
        content.setObjectName("CardContent")
        content.setWordWrap(True)
        content.setStyleSheet("line-height: 1.4;")
        font_content = QFont()
        font_content.setPointSize(11)
        content.setFont(font_content)

        layout.addWidget(title)
        layout.addWidget(content)
        return card

    def _create_credits_card(self):
        card = QFrame()
        card.setObjectName("InfoCard")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        title = QLabel("Credits")
        title.setObjectName("CardTitle")
        font = QFont()
        font.setBold(True)
        font.setPointSize(16)
        title.setFont(font)
        layout.addWidget(title)

        info_text = (
            "<b>Course:</b> Computer Thinking<br>"
            "<b>Class:</b> 24C06<br>"
            "<b>Group:</b> 4NPC"
        )
        lbl_info = QLabel(info_text)
        lbl_info.setObjectName("CardContent")
        font_content = QFont()
        font_content.setPointSize(11)
        lbl_info.setFont(font_content)
        layout.addWidget(lbl_info)

        lbl_members_title = QLabel("<b>Group Members:</b>")
        lbl_members_title.setObjectName("CardContent")
        lbl_members_title.setFont(font_content)
        layout.addWidget(lbl_members_title)

        members_list = [
            "Võ Nguyễn Vân Anh - 24127016",
            "Nguyễn Võ Tấn Duy - 24127159",
            "Trần Gia Phúc - 24127221",
            "Trần Nguyễn Hữu Phước - 24127222"
        ]

        for member in members_list:
            lbl_mem = QLabel(f"• {member}")
            lbl_mem.setObjectName("CardContent")
            lbl_mem.setStyleSheet("margin-left: 10px;")
            lbl_mem.setFont(font_content)
            layout.addWidget(lbl_mem)

        return card

    def update_ui(self):
        # 1. Main background
        self.setStyleSheet(f"background-color: {cf.APP_BACKGROUND};")
        self.scroll_area.setStyleSheet("background: transparent; border: none;")
        self.content_widget.setStyleSheet("background: transparent;")

        # 2. Header Style
        self.header_label.setStyleSheet(
            f"font-size: 28px; font-weight: bold; color: {cf.HEADER_BACKGROUND}; padding: 20px 0;")

        # 3. Card Style
        card_style = f"""
            QFrame#InfoCard {{
                background-color: {cf.BAR_BACKGROUND};
                border-radius: 10px;
                border: 1px solid {cf.SHADOW_COLOR};
            }}
            QLabel#CardTitle {{color: {cf.HEADER_BACKGROUND};}}
            QLabel#CardContent {{color: {cf.DARK_TEXT};}}
        """
        self.card_what.setStyleSheet(card_style)
        self.card_how.setStyleSheet(card_style)
        self.card_credits.setStyleSheet(card_style)

        # 4. Button Style
        self.back_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {cf.BUTTON_BACKGROUND};
                color: {cf.WHITE};
                border-radius: 8px;
                padding: 10px 25px;
                font-size: 14px; font-weight: bold;
            }}
            QPushButton:hover {{color: {cf.BLACK}}}
        """)