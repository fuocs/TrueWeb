import firebase_admin
from firebase_admin import credentials, firestore, auth
import json
import os
from pathlib import Path

# ---------------------------------------------------------
# LOAD ENVIRONMENT VARIABLES
# ---------------------------------------------------------
try:
    from .env_loader import load_env
    load_env()
except ImportError:
    print("[WARNING] env_loader not available. Using system environment variables only.")

# ---------------------------------------------------------
# CẤU HÌNH (Load from environment variables)
# ---------------------------------------------------------
SERVICE_ACCOUNT_CONFIG = os.getenv('SERVICE_ACCOUNT_CONFIG')
GOOGLE_CLIENT_CONFIG = os.getenv('GOOGLE_CLIENT_CONFIG')
FIREBASE_WEB_API_KEY = os.getenv('FIREBASE_WEB_API_KEY')

def init():
    """Khởi tạo kết nối Firebase Admin"""
    try:
        if SERVICE_ACCOUNT_CONFIG:
            cred = credentials.Certificate(json.loads(SERVICE_ACCOUNT_CONFIG))
            firebase_admin.initialize_app(cred)
            return True
        else:
            print('Cant load SERVICE_ACCOUNT_CONFIG')
            return False
    except Exception as e:
        print(e)
        return False

