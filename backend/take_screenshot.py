"""
Screenshot module using Selenium WebDriver
Lightweight alternative to Playwright for taking website screenshots
"""
try:
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.support.ui import WebDriverWait
    from webdriver_manager.chrome import ChromeDriverManager
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False
    print("[WARNING] Selenium or webdriver_manager not installed. Screenshot feature disabled.")

import os
import time
import concurrent.futures
import hashlib
# Device configurations for screenshots (7 most popular devices)
DEVICE_CONFIGS = [
    {
        "name": "Desktop [Windows PC]",
        "width": 1920,
        "height": 1080,
        "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    },
    {
        "name": "Desktop [MacBook Pro]",
        "width": 1440,
        "height": 900,
        "user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    },
    {
        "name": "iPad [iPad Pro 12.9]",
        "width": 1024,
        "height": 1366,
        "user_agent": "Mozilla/5.0 (iPad; CPU OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1"
    },
    {
        "name": "iOS Mobile [iPhone 14-16]",
        "width": 390,
        "height": 844,
        "user_agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1"
    },
    {
        "name": "Android Mobile [Samsung Galaxy S24]",
        "width": 360,
        "height": 800,
        "user_agent": "Mozilla/5.0 (Linux; Android 14; SM-S921B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36"
    }
]

def setup_screenshots_folder():
    """Create screenshots folder and hide it (Windows)"""
    import ctypes
    screenshots_dir = "screenshots"
    
    # Create folder if not exists
    if not os.path.exists(screenshots_dir):
        os.makedirs(screenshots_dir)
        print(f"[Setup] Created screenshots folder")
    
    # Hide folder on Windows
    try:
        FILE_ATTRIBUTE_HIDDEN = 0x02
        ctypes.windll.kernel32.SetFileAttributesW(screenshots_dir, FILE_ATTRIBUTE_HIDDEN)
        print(f"[Setup] Hidden screenshots folder")
    except Exception as e:
        print(f"[Setup] Could not hide folder: {e}")

def cleanup_screenshots_folder():
    """Delete entire screenshots folder on app exit"""
    import shutil
    screenshots_dir = "screenshots"
    if os.path.exists(screenshots_dir):
        try:
            shutil.rmtree(screenshots_dir)
            print(f"[Cleanup] Deleted screenshots folder")
        except Exception as e:
            print(f"[Cleanup] Error deleting screenshots folder: {e}")

def take_screenshot(url: str, output_path: str = "screenshots/temp.png", timeout: int = 30):
    """
    Takes screenshots of a given URL from multiple device perspectives.
    Uses Selenium WebDriver in headless mode.

    Args:
        url: The URL of the website to screenshot.
        output_path: The base file path (will be suffixed with device name).
        timeout: Maximum time to wait for page load (seconds).
    
    Returns:
        list: List of tuples (device_name, screenshot_path, success)
    """
    print(f"[Screenshot] 🚀 take_screenshot() CALLED for {url}")
    
    if not SELENIUM_AVAILABLE:
        print("[ERROR] Selenium not available. Cannot take screenshot.")
        return []
    
    # Pre-install chromedriver ONCE before creating threads (avoid blocking in threads)
    print(f"[Screenshot] Installing/verifying chromedriver...")
    try:
        chromedriver_path = ChromeDriverManager().install()
        print(f"[Screenshot] ✓ Chromedriver ready at: {chromedriver_path}")
    except Exception as e:
        print(f"[Screenshot] ✗ Failed to install chromedriver: {e}")
        return []
    
    # Create unique folder for this URL to prevent conflicts
    url_hash = hashlib.md5(url.encode()).hexdigest()[:8]
    unique_dir = f"screenshots/url_{url_hash}"
    os.makedirs(unique_dir, exist_ok=True)
    
    # Update output path to use unique directory
    base_name = os.path.basename(output_path)
    output_path = os.path.join(unique_dir, base_name)
    
    # Extract base name without extension
    base_name = os.path.splitext(output_path)[0]
    ext = os.path.splitext(output_path)[1] or ".png"
    
    def capture_device(device, max_retries=2):
        """Capture screenshot for a single device with retry mechanism"""
        # Sanitize device name for filename
        safe_name = device['name'].replace('[', '').replace(']', '').replace(' ', '_').lower()
        device_output = f"{base_name}_{safe_name}{ext}"
        
        # Log IMMEDIATELY when thread starts (before any blocking operations)
        print(f"[Screenshot] [{device['name']}] Thread started, preparing Chrome...")
        
        for attempt in range(max_retries):
            driver = None
            try:
                # Setup Chrome options for this device
                chrome_options = Options()
                chrome_options.add_argument("--headless=new")
                chrome_options.add_argument("--no-sandbox")
                chrome_options.add_argument("--disable-dev-shm-usage")
                chrome_options.add_argument("--disable-gpu")
                chrome_options.add_argument(f"--window-size={device['width']},{device['height']}")
                chrome_options.add_argument("--disable-blink-features=AutomationControlled")
                chrome_options.add_argument(f"user-agent={device['user_agent']}")
                chrome_options.add_argument("--log-level=3")  # Suppress logs
                chrome_options.add_argument("--disable-extensions")
                chrome_options.add_argument("--disable-images")  # Speed up loading
                chrome_options.page_load_strategy = 'eager'  # Don't wait for everything
                
                # Use pre-installed chromedriver path (no blocking call here)
                service = Service(chromedriver_path)
                driver = webdriver.Chrome(service=service, options=chrome_options)
                driver.set_page_load_timeout(timeout * 2)  # Double timeout for complex sites
                driver.set_script_timeout(timeout * 2)
                
                # Navigate to URL
                if attempt == 0:
                    print(f"[Screenshot] [{device['name']}] Navigating to {url}...")
                else:
                    print(f"[Screenshot] [{device['name']}] Retry {attempt}/{max_retries-1}...")
                
                driver.get(url)
                
                # Wait for page to stabilize (shorter wait)
                time.sleep(1.5)
                
                # Take screenshot
                driver.save_screenshot(device_output)
                print(f"[Screenshot] [{device['name']}] ✓ Saved to {device_output}")
                return (device['name'], device_output, True)
                
            except Exception as e:
                error_msg = str(e).split('\n')[0]  # First line only
                if attempt < max_retries - 1:
                    print(f"[Screenshot] [{device['name']}] ⚠ {error_msg} - Retrying...")
                else:
                    print(f"[Screenshot] [{device['name']}] ✗ Failed after {max_retries} attempts: {error_msg}")
                
            finally:
                if driver:
                    try:
                        driver.quit()
                    except:
                        pass
        
        # All retries failed
        return (device['name'], device_output, False)
    
    # Use ThreadPoolExecutor to capture all devices in parallel
    print(f"[Screenshot] Creating thread pool for {len(DEVICE_CONFIGS)} devices...")
    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=7) as executor:
        print(f"[Screenshot] Submitting {len(DEVICE_CONFIGS)} screenshot tasks...")
        futures = [executor.submit(capture_device, device, 2) for device in DEVICE_CONFIGS]
        print(f"[Screenshot] All tasks submitted, waiting for completion...")
        for future in concurrent.futures.as_completed(futures, timeout=timeout*3):
            try:
                result = future.result()
                results.append(result)
            except concurrent.futures.TimeoutError:
                print(f"[Screenshot] A device timed out completely")
            except Exception as e:
                print(f"[Screenshot] Thread error: {e}")
    
    return results