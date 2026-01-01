import sys
import signal
from PyQt6.QtWidgets import QApplication
from backend import firebaseDB
from backend.take_screenshot import setup_screenshots_folder

from app import AppManager

if __name__ == "__main__":
    # Setup hidden screenshots folder
    setup_screenshots_folder()
    
    firebaseDB.init()
    app = AppManager(sys.argv)
    
    # Enable Ctrl+C to close app immediately
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    
    sys.exit(app.exec())
