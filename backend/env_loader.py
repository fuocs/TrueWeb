"""
Environment variable loader with PyInstaller support
Searches for .env in multiple locations:
1. Same directory as .exe (for easy editing without rebuild)
2. Bundled backend/.env (included in .exe)
"""
import os
import sys
from pathlib import Path


def get_env_path() -> Path:
    """
    Get .env file path with priority:
    1. External .env next to .exe (for user customization)
    2. Bundled backend/.env (packed inside .exe)
    
    Returns: Path to .env file
    """
    # Get base directory
    if getattr(sys, 'frozen', False):
        # Running as compiled .exe
        # sys.executable = path to .exe file
        exe_dir = Path(sys.executable).parent
        
        # Priority 1: Check for .env next to .exe (external, user-editable)
        external_env = exe_dir / '.env'
        if external_env.exists():
            print(f"[ENV] Using external .env: {external_env}")
            return external_env
        
        # Priority 2: Use bundled .env in _MEIPASS temp directory
        # sys._MEIPASS is the temp folder where PyInstaller extracts files
        bundled_env = Path(sys._MEIPASS) / 'backend' / '.env'
        if bundled_env.exists():
            print(f"[ENV] Using bundled .env: {bundled_env}")
            return bundled_env
        else:
            print(f"[ENV WARNING] No .env found! Checked:")
            print(f"  - External: {external_env}")
            print(f"  - Bundled: {bundled_env}")
            # Return external path anyway (dotenv will handle missing file)
            return external_env
    else:
        # Running from source code (development mode)
        # Use backend/.env relative to this file
        dev_env = Path(__file__).parent / '.env'
        print(f"[ENV] Development mode, using: {dev_env}")
        return dev_env


def load_env():
    """
    Load environment variables from .env file
    Call this at the start of any module that needs env vars
    """
    try:
        from dotenv import load_dotenv
        env_path = get_env_path()
        load_dotenv(dotenv_path=env_path, override=True)
        return True
    except ImportError:
        print("[ENV WARNING] python-dotenv not installed")
        return False
    except Exception as e:
        print(f"[ENV ERROR] Failed to load .env: {e}")
        return False
