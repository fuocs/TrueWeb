from . import configuration as cf
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, 
                             QPushButton, QGridLayout, QSizePolicy, QDialog, QScrollArea)
from PyQt6.QtGui import QFont, QCursor
from PyQt6.QtCore import Qt, pyqtSignal

from .UI_helpers import format_post_time
from backend import user, review

# --- [CLASS MỚI] Popup hiển thị chi tiết Review ---
class ReviewDetailsPopup(QDialog):
    def __init__(self, username, url, score, comment, post_time, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Full Review Details")
        self.setMinimumSize(500, 400) # Kích thước to hơn Card
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.WindowCloseButtonHint)
        
        # Main Layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(25, 25, 25, 25)
        layout.setSpacing(15)

        # 1. Header (User + Score)
        header_layout = QHBoxLayout()
        
        lbl_user = QLabel(username)
        font_user = QFont(); font_user.setBold(True); font_user.setPointSize(14)
        lbl_user.setFont(font_user)
        lbl_user.setStyleSheet(f"color: {cf.DARK_TEXT}; border: none;")
        
        lbl_score = QLabel(f"{score}/10")
        font_score = QFont(); font_score.setBold(True); font_score.setPointSize(14)
        lbl_score.setFont(font_score)
        lbl_score.setAlignment(Qt.AlignmentFlag.AlignRight)
        lbl_score.setStyleSheet(f"color: {cf.DARK_TEXT}; border: none;")
        
        header_layout.addWidget(lbl_user)
        header_layout.addWidget(lbl_score)
        layout.addLayout(header_layout)

        # 2. URL Link
        lbl_url = QLabel(url)
        lbl_url.setStyleSheet(f"color: {cf.LINK_TEXT}; text-decoration: underline; font-size: 12px; border: none;")
        layout.addWidget(lbl_url)

        # 3. Separator Line
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setStyleSheet(f"background-color: {cf.SHADOW_COLOR}; max-height: 1px; border: none;")
        layout.addWidget(line)

        # 4. Scrollable Comment Content
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("background: transparent; border: none;")
        
        content_widget = QWidget()
        content_widget.setStyleSheet("background: transparent; border: none;")
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(0, 10, 0, 10)
        
        lbl_comment = QLabel(comment)
        lbl_comment.setWordWrap(True)
        font_comment = QFont(); font_comment.setPointSize(11) # Font to hơn một chút
        lbl_comment.setFont(font_comment)
        lbl_comment.setStyleSheet(f"color: {cf.DARK_TEXT}; border: none;")
        # Cho phép bôi đen copy text
        lbl_comment.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        
        content_layout.addWidget(lbl_comment)
        content_layout.addStretch()
        
        scroll.setWidget(content_widget)
        layout.addWidget(scroll)

        # 5. Footer (Time + Close Button)
        footer_layout = QHBoxLayout()
        
        lbl_time = QLabel(format_post_time(post_time))
        lbl_time.setStyleSheet(f"color: {cf.LIGHT_TEXT}; font-style: italic; font-size: 11px; border: none;")
        
        btn_close = QPushButton("Close")
        btn_close.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_close.clicked.connect(self.accept)
        btn_close.setStyleSheet(f"""
            QPushButton {{
                background-color: {cf.BUTTON_BACKGROUND};
                color: {cf.WHITE};
                border-radius: 6px;
                padding: 8px 25px;
                font-weight: bold;
                border: none;
            }}
            QPushButton:hover {{ opacity: 0.9; }}
        """)
        
        footer_layout.addWidget(lbl_time)
        footer_layout.addStretch()
        footer_layout.addWidget(btn_close)
        
        layout.addLayout(footer_layout)

        # Background chung cho Popup (Dùng màu nền thẻ hoặc nền app)
        self.setStyleSheet(f"background-color: {cf.APP_BACKGROUND};")


class ReviewCard(QFrame):
    def __init__(self, username, url, score, comment, post_time, review_id=None, parent=None):
        super().__init__(parent)
        
        # Lưu dữ liệu thô để truyền vào Popup
        self.raw_username = username
        self.raw_url = url
        self.raw_score = score
        self.raw_comment = comment
        self.raw_post_time = post_time
        self.raw_review_id = review_id

        # Define character limit for truncation
        self.char_limit = 60

        scale_factor = 0.95
        self.scaled_width = int(cf.REVIEW_CARD_WIDTH * scale_factor)
        self.scaled_height = int(cf.REVIEW_CARD_HEIGHT * scale_factor)

        self.setFixedSize(self.scaled_width, self.scaled_height)
        
        self._init_ui(username, url, score, comment, post_time)

        self.update_ui()

    def _init_ui(self, username, url, score, comment, post_time):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(8, 8, 8, 8)
        main_layout.setSpacing(2)

        # Row 1: Username
        self.username_label = QLabel(username)
        font = QFont()
        font.setBold(True)
        font.setPointSize(11)
        self.username_label.setFont(font)
        self.username_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        main_layout.addWidget(self.username_label)

        # Row 2: URL & Score
        url_score_layout = QHBoxLayout()
        self.url_label = QLabel(url)
        self.url_label.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.url_label.setFixedWidth(int(self.scaled_width * 0.6))
        self.url_label.linkActivated.connect(lambda link: print(f"Clicked URL: {link}"))
        url_score_layout.addWidget(self.url_label)

        self.score_label = QLabel(f"<b>{score}/10</b>")
        self.score_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        url_score_layout.addWidget(self.score_label)
        main_layout.addLayout(url_score_layout)

        # Row 3: Comment (Truncated)
        self.comment_label = QLabel()
        font_comment = QFont()
        font_comment.setPointSize(9)
        self.comment_label.setFont(font_comment)
        self.comment_label.setWordWrap(True)
        self.comment_label.setAlignment(Qt.AlignmentFlag.AlignJustify)
        main_layout.addWidget(self.comment_label)

        # "See more/See less" button for comment
        self.show_more_comment_button = QPushButton("See more", self)
        self.show_more_comment_button.setFont(font_comment)
        self.show_more_comment_button.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.show_more_comment_button.clicked.connect(self._open_full_review) # [NEW]

        if len(self.raw_comment) >= self.char_limit: 
            main_layout.addWidget(self.show_more_comment_button, 0, alignment=Qt.AlignmentFlag.AlignLeft)
        else: 
            self.show_more_comment_button.setVisible(False)

        self._set_comment_display()

        # Row 4: Time
        self.post_time_label = QLabel(format_post_time(post_time))
        font_time = QFont()
        font_time.setItalic(True)
        font_time.setPointSize(9)
        self.post_time_label.setFont(font_time)
        self.post_time_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        main_layout.addWidget(self.post_time_label)

        main_layout.addStretch()
        
        # Delete button (bottom left, only visible for own reviews)
        self.delete_button = QPushButton("🗑️ Delete")
        self.delete_button.setFixedHeight(28)
        self.delete_button.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.delete_button.clicked.connect(self._on_delete_clicked)
        self.delete_button.setVisible(False)  # Hidden by default
        main_layout.addWidget(self.delete_button, 0, Qt.AlignmentFlag.AlignLeft)
        
        self.update_ui()

    def update_ui(self):
        """Cập nhật màu sắc thẻ review theo theme"""
        # Nền thẻ: BAR_BACKGROUND (Trắng/Xám tối), Viền: SHADOW_COLOR
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {cf.BAR_BACKGROUND};
                border-radius: 8px;
                border: 1px solid {cf.SHADOW_COLOR};
            }}
            QLabel {{ border: none; }}
        """)
        
        self.username_label.setStyleSheet(f"color: {cf.DARK_TEXT}; border: none;")
        self.url_label.setStyleSheet(f"color: {cf.LINK_TEXT}; text-decoration: underline; border: none;")
        self.score_label.setStyleSheet(f"color: {cf.DARK_TEXT}; border: none;")
        self.comment_label.setStyleSheet(f"color: {cf.DARK_TEXT}; border: none;")
        self.post_time_label.setStyleSheet(f"color: {cf.LIGHT_TEXT}; border: none;")
        
        self.show_more_comment_button.setStyleSheet(f"""
            QPushButton {{
                color: {cf.LINK_TEXT}; 
                border: none; 
                background: transparent; 
                text-decoration: underline;
                text-align: left;
            }}
            QPushButton:hover {{color: {cf.DARK_TEXT};}}
        """)
        
        self.delete_button.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                border: 2px solid #ff0000;
                border-radius: 5px;
                color: #ff0000;
                font-size: 12px;
                font-weight: bold;
                padding: 4px 12px;
            }}
            QPushButton:hover {{
                background-color: #ff0000;
                color: white;
            }}
        """)

    def _set_comment_display(self):
        # Luôn hiển thị text rút gọn nếu dài
        if len(self.raw_comment) > self.char_limit:
            self.comment_label.setText(self.raw_comment[:self.char_limit] + "...")
            self.show_more_comment_button.setVisible(True)
        else:
            self.comment_label.setText(self.raw_comment)
            self.show_more_comment_button.setVisible(False)

    def _open_full_review(self):
        # [MỚI] Mở Popup thay vì giãn thẻ
        popup = ReviewDetailsPopup(
            self.raw_username, 
            self.raw_url, 
            self.raw_score, 
            self.raw_comment, 
            self.raw_post_time, 
            self.window()
        )
        popup.exec()
    
    def _on_delete_clicked(self):
        """Handle delete button click"""
        from PyQt6.QtWidgets import QMessageBox
        
        msg = QMessageBox(self.window())
        msg.setWindowTitle("Delete Review")
        msg.setText("Are you sure you want to delete this review?")
        msg.setIcon(QMessageBox.Icon.Question)
        msg.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        msg.setDefaultButton(QMessageBox.StandardButton.No)
        
        # Black styling for dialog
        msg.setStyleSheet(f"""
            QMessageBox {{
                background-color: {cf.APP_BACKGROUND};
            }}
            QLabel {{
                color: {cf.DARK_TEXT};
                font-size: 13px;
            }}
            QPushButton {{
                background-color: {cf.DARK_TEXT};
                color: white;
                border: 2px solid {cf.DARK_TEXT};
                border-radius: 5px;
                padding: 6px 20px;
                font-weight: bold;
                min-width: 70px;
            }}
            QPushButton:hover {{
                background-color: {cf.BLACK};
                border-color: {cf.BLACK};
            }}
        """)
        
        if msg.exec() == QMessageBox.StandardButton.Yes:
            # Show loading state
            self.delete_button.setEnabled(False)
            self.delete_button.setText("⏳ Deleting...")
            self.delete_button.setStyleSheet(f"""
                QPushButton {{
                    background-color: transparent;
                    border: 2px solid #999999;
                    border-radius: 5px;
                    color: #999999;
                    font-size: 12px;
                    font-weight: bold;
                    padding: 4px 12px;
                }}
            """)
            
            # Process events to show loading state
            from PyQt6.QtWidgets import QApplication
            QApplication.processEvents()
            
            # Emit signal to parent to handle deletion
            parent = self.parent()
            while parent and not isinstance(parent, ReviewsSection):
                parent = parent.parent()
            if parent:
                parent.delete_review(self.raw_review_id)
    
    def set_delete_button_visible(self, visible):
        """Show/hide delete button based on ownership"""
        self.delete_button.setVisible(visible)


class ReviewsSection(QWidget):
    reviews_changed = pyqtSignal()

    def __init__(self, grid_columns=3, load_increment=None, parent=None):
        super().__init__(parent)
        self.reviews_data = review.CURRENT_REVIEW
        self.displayed_reviews_count = 3

        self.grid_columns = grid_columns
        self.reviews_per_load = grid_columns
        self.reviews_load_increment = load_increment if load_increment is not None else grid_columns

        self.is_collapsing_mode = False

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(15)


        self.cards_layout = QGridLayout()
        self.cards_layout.setSpacing(15)
        self.cards_layout.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        main_layout.addLayout(self.cards_layout)

        # Style nút bấm
        btn_style = f"""
            QPushButton {{
                background-color: {cf.BUTTON_BACKGROUND};
                border-radius: 5px;
                padding: 8px 15px;
                color: white; 
                font-weight: bold;
                font-size: 12px;
            }}
            QPushButton:hover {{opacity: 0.9;}}
        """


        self.show_more_reviews_button = QPushButton("Show more")
        self.show_more_reviews_button.setStyleSheet(btn_style)
        self.show_more_reviews_button.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.show_more_reviews_button.clicked.connect(self.load_more_reviews)
        main_layout.addWidget(self.show_more_reviews_button, 0, alignment=Qt.AlignmentFlag.AlignCenter)

        self.show_less_reviews_button = QPushButton("Show less")
        self.show_less_reviews_button.setStyleSheet(btn_style)
        self.show_less_reviews_button.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.show_less_reviews_button.clicked.connect(self.load_less_reviews)
        self.show_less_reviews_button.setVisible(False)
        main_layout.addWidget(self.show_less_reviews_button, 0, alignment=Qt.AlignmentFlag.AlignCenter)

        self._update_buttons_state()
        self.update_ui() # Set style lần đầu

    def update_ui(self):
        """Cập nhật UI cho section và lan truyền xuống các thẻ con"""
        btn_style = f"""
            QPushButton {{
                background-color: {cf.BUTTON_BACKGROUND};
                border-radius: 5px;
                padding: 8px 15px;
                color: {cf.WHITE}; 
                font-weight: bold;
                font-size: 12px;
            }}
            QPushButton:hover {{opacity: 0.9; color: {cf.BLACK}}}
        """

        self.show_more_reviews_button.setStyleSheet(btn_style)
        self.show_less_reviews_button.setStyleSheet(btn_style)

        for i in range(self.cards_layout.count()):
            item = self.cards_layout.itemAt(i)
            if item and item.widget():
                widget = item.widget()
                if isinstance(widget, ReviewCard):
                    widget.update_ui()

    def add_review(self, url, score, comment, post_time):
        # Check if user has already reviewed
        if review.has_user_reviewed(user.CURRENT_USER.uid, url):
            from PyQt6.QtWidgets import QMessageBox
            msg = QMessageBox(self.window())
            msg.setWindowTitle("Review Limit")
            msg.setText("You have already reviewed this website. Each user can only submit one review per website.")
            msg.setIcon(QMessageBox.Icon.Warning)
            msg.setStyleSheet(f"""
                QMessageBox {{
                    background-color: {cf.APP_BACKGROUND};
                }}
                QLabel {{
                    color: {cf.DARK_TEXT};
                    font-size: 13px;
                }}
                QPushButton {{
                    background-color: {cf.DARK_TEXT};
                    color: white;
                    border: 2px solid {cf.DARK_TEXT};
                    border-radius: 5px;
                    padding: 6px 20px;
                    font-weight: bold;
                    min-width: 70px;
                }}
                QPushButton:hover {{
                    background-color: {cf.BLACK};
                    border-color: {cf.BLACK};
                }}
            """)
            msg.exec()
            return False
        
        review_data = {
            "username": user.CURRENT_USER.username, "url": url, "score": score, "comment": comment, "post_time": post_time
        }
        
        # Save to Firebase first to get review_id
        success = review.save_review(user.CURRENT_USER.uid, url, review_data=review_data)
        if not success:
            from PyQt6.QtWidgets import QMessageBox
            msg = QMessageBox(self.window())
            msg.setWindowTitle("Error")
            msg.setText("Failed to save review. Please try again.")
            msg.setIcon(QMessageBox.Icon.Critical)
            msg.setStyleSheet(f"""
                QMessageBox {{
                    background-color: {cf.APP_BACKGROUND};
                }}
                QLabel {{
                    color: {cf.DARK_TEXT};
                    font-size: 13px;
                }}
                QPushButton {{
                    background-color: {cf.DARK_TEXT};
                    color: white;
                    border: 2px solid {cf.DARK_TEXT};
                    border-radius: 5px;
                    padding: 6px 20px;
                    font-weight: bold;
                    min-width: 70px;
                }}
                QPushButton:hover {{
                    background-color: {cf.BLACK};
                    border-color: {cf.BLACK};
                }}
            """)
            msg.exec()
            return False
        
        # After successful save, review_data will have reviewId from save_review
        # Reload reviews to get updated data with IDs
        review.get_reviews(url)
        self.reviews_data = review.CURRENT_REVIEW
        self.is_collapsing_mode = False

        if self.displayed_reviews_count < self.reviews_per_load:
            self.displayed_reviews_count = len(self.reviews_data)

        self.display_reviews()
        self._update_buttons_state()
        # Notify listeners that reviews have changed
        try:
            self.reviews_changed.emit()
        except Exception:
            pass
        return True

    def display_reviews(self):
        # Clear all existing widgets from layout
        for i in reversed(range(self.cards_layout.count())):
            item = self.cards_layout.itemAt(i)
            if item and item.widget():
                widget = item.widget()
                widget.setParent(None)
                widget.deleteLater()

        if self.displayed_reviews_count >= len(self.reviews_data): self.displayed_reviews_count = len(self.reviews_data)

        reviews_to_display = self.reviews_data[:self.displayed_reviews_count]
        for i, review_info in enumerate(reviews_to_display):
            review_id = review_info.get("reviewId", None)
            card = ReviewCard(
                review_info["username"],
                review_info["url"],
                review_info["score"],
                review_info["comment"],
                review_info["timestamp"],
                review_id
            )
            # Gọi update_ui cho card mới
            card.update_ui()
            
            # Show delete button only for current user's reviews
            if user.CURRENT_USER and review_info.get("uid") == user.CURRENT_USER.uid:
                card.set_delete_button_visible(True)

            row = i // self.grid_columns
            col = i % self.grid_columns
            self.cards_layout.addWidget(card, row, col)

        self._update_buttons_state()

    def load_more_reviews(self):
        # Sử dụng biến increment đã được cấu hình
        new_reviews_to_add = self.reviews_load_increment
        remaining_reviews = len(self.reviews_data) - self.displayed_reviews_count

        if remaining_reviews > 0:
            self.displayed_reviews_count += min(new_reviews_to_add, remaining_reviews)
            self.display_reviews()

        if self.displayed_reviews_count >= len(self.reviews_data): self.is_collapsing_mode = True

        self._update_buttons_state()

    def load_less_reviews(self):
        self.displayed_reviews_count -= self.reviews_load_increment

        if self.displayed_reviews_count <= self.reviews_per_load:
            self.displayed_reviews_count = self.reviews_per_load
            self.is_collapsing_mode = False

        self.display_reviews()
        self._update_buttons_state()

    def _update_buttons_state(self):
        total_reviews = len(self.reviews_data)

        if total_reviews <= self.reviews_per_load:
            self.show_more_reviews_button.setVisible(False)
            self.show_less_reviews_button.setVisible(False)
            return

        if self.is_collapsing_mode:
            self.show_more_reviews_button.setVisible(False)
            self.show_less_reviews_button.setVisible(True)
        else:
            self.show_more_reviews_button.setVisible(True)
            self.show_less_reviews_button.setVisible(False)

    def check_user_has_reviewed(self, username):
        for review in self.reviews_data:
            if review["username"] == username: return True
        return False

    def delete_review(self, review_id):
        """Delete a review by review_id"""
        if not review_id:
            return False
        
        # Find the review to get URL and UID
        review_to_delete = None
        for r in self.reviews_data:
            if r.get("reviewId") == review_id:
                review_to_delete = r
                break
        
        if not review_to_delete:
            return False
        
        # Delete from Firebase
        success = review.delete_review(
            user.CURRENT_USER.uid, 
            review_to_delete["url"], 
            review_id
        )
        
        if success:
            # Remove from local data
            self.reviews_data = [r for r in self.reviews_data if r.get("reviewId") != review_id]
            if self.displayed_reviews_count > len(self.reviews_data):
                self.displayed_reviews_count = len(self.reviews_data)
            
            if self.displayed_reviews_count <= self.reviews_per_load:
                self.is_collapsing_mode = False
            
            self.display_reviews()
            self._update_buttons_state()
            # Notify listeners that reviews have changed
            try:
                self.reviews_changed.emit()
            except Exception:
                pass
            
            from PyQt6.QtWidgets import QMessageBox
            msg = QMessageBox(self.window())
            msg.setWindowTitle("Success")
            msg.setText("Review deleted successfully.")
            msg.setIcon(QMessageBox.Icon.Information)
            msg.setStyleSheet(f"""
                QMessageBox {{
                    background-color: {cf.APP_BACKGROUND};
                }}
                QLabel {{
                    color: {cf.DARK_TEXT};
                    font-size: 13px;
                }}
                QPushButton {{
                    background-color: {cf.DARK_TEXT};
                    color: white;
                    border: 2px solid {cf.DARK_TEXT};
                    border-radius: 5px;
                    padding: 6px 20px;
                    font-weight: bold;
                    min-width: 70px;
                }}
                QPushButton:hover {{
                    background-color: {cf.BLACK};
                    border-color: {cf.BLACK};
                }}
            """)
            msg.exec()
            return True
        else:
            from PyQt6.QtWidgets import QMessageBox
            msg = QMessageBox(self.window())
            msg.setWindowTitle("Error")
            msg.setText("Failed to delete review.")
            msg.setIcon(QMessageBox.Icon.Critical)
            msg.setStyleSheet(f"""
                QMessageBox {{
                    background-color: {cf.APP_BACKGROUND};
                }}
                QLabel {{
                    color: {cf.DARK_TEXT};
                    font-size: 13px;
                }}
                QPushButton {{
                    background-color: {cf.DARK_TEXT};
                    color: white;
                    border: 2px solid {cf.DARK_TEXT};
                    border-radius: 5px;
                    padding: 6px 20px;
                    font-weight: bold;
                    min-width: 70px;
                }}
                QPushButton:hover {{
                    background-color: {cf.BLACK};
                    border-color: {cf.BLACK};
                }}
            """)
            msg.exec()
            return False
    
    def remove_review_by_user(self, username):
        self.reviews_data = [r for r in self.reviews_data if r["username"] != username]
        if self.displayed_reviews_count > len(self.reviews_data): self.displayed_reviews_count = len(self.reviews_data)

        if self.displayed_reviews_count <= self.reviews_per_load: self.is_collapsing_mode = False

        self.display_reviews()
        self._update_buttons_state()