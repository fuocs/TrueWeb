from datetime import datetime
import os
import sys
from pathlib import Path
from . import configuration as cf
from PyQt6.QtGui import QPixmap, QColor, QPainter
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QGraphicsDropShadowEffect, QFrame

BASE_DIR = Path(__file__).resolve().parent
MEDIA_DIR = BASE_DIR / "media"

def get_asset_path(filename):
    """
    Trả về đường dẫn tuyệt đối của file trong folder media.
    Hỗ trợ cả khi chạy code thường và khi đóng gói thành file .exe (PyInstaller)
    """
    if hasattr(sys, '_MEIPASS'):
        # PyInstaller extracts to _MEIPASS/frontend/media/
        base_path = Path(sys._MEIPASS) / "frontend" / "media"
    else:
        # Development mode: use local media folder
        base_path = MEDIA_DIR

    file_path = base_path / filename
    
    # Debug logging (remove after confirming it works)
    if not file_path.exists():
        print(f"[WARNING] Asset not found: {file_path}")
        print(f"[DEBUG] _MEIPASS: {getattr(sys, '_MEIPASS', 'Not set')}")
        print(f"[DEBUG] Searching in: {base_path}")
    
    return str(file_path)

def get_icon_pixmap(name):
    # 1. Load from png file
    file_path = get_asset_path(f"{name}.png")
    
    if os.path.exists(file_path):
        original_pixmap = QPixmap(file_path)
        if not original_pixmap.isNull():
            # create clear pixmap
            colored_pixmap = QPixmap(original_pixmap.size())
            colored_pixmap.fill(Qt.GlobalColor.transparent)

            painter = QPainter(colored_pixmap)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)

            # draw original image
            painter.drawPixmap(0, 0, original_pixmap)

            # change original color
            painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceIn)
            painter.fillRect(colored_pixmap.rect(), QColor(cf.DARK_TEXT))

            painter.end()
            return colored_pixmap
    else:
        print(f"[ERROR] Icon file not found: {file_path}")

    # 2. Fallbacks
    pixmap = QPixmap(30, 30)
    pixmap.fill(QColor("gray"))

    if name == "home": pixmap.fill(QColor("#007bff"))
    elif name == "login": pixmap.fill(QColor("#28a745"))
    elif name == "write": pixmap.fill(QColor("#ffc107"))
    elif name == "settings": pixmap.fill(QColor("#6c757d"))
    elif name == "info": pixmap.fill(QColor("#17a2b8"))
    elif name == "search": pixmap.fill(QColor(cf.LIGHT_TEXT))

    return pixmap

def format_post_time(post_datetime):
    post_datetime = datetime.fromtimestamp(post_datetime / 1000)
    now = datetime.now()
    diff = now - post_datetime

    if diff.total_seconds() < 60: return f"{int(diff.total_seconds())} seconds ago"
    elif diff.total_seconds() < 3600: return f"{int(diff.total_seconds() / 60)} minutes ago"
    elif diff.total_seconds() < 86400: return f"{int(diff.total_seconds() / 3600)} hours ago"
    elif diff.total_seconds() < 7 * 86400: return f"{int(diff.total_seconds() / 86400)} days ago"
    else: return post_datetime.strftime("%d/%m/%Y")


def apply_shadow(target_widget):
    shadow = QGraphicsDropShadowEffect()
    shadow.setBlurRadius(5)
    shadow.setOffset(2, 5)
    shadow.setColor(QColor(cf.SHADOW_COLOR))
    target_widget.setGraphicsEffect(shadow)


def _add_separator(layout):
    line = QFrame()
    line.setFrameShape(QFrame.Shape.VLine)
    line.setFrameShadow(QFrame.Shadow.Sunken)
    line.setStyleSheet(f"background-color: {cf.LIGHT_TEXT}; max-height: 20px;")
    line.setFixedHeight(20)
    layout.addWidget(line)