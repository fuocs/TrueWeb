"""
URL utilities for normalizing and extracting domain information
"""
import tldextract
import requests
from urllib.parse import urlparse
from bs4 import BeautifulSoup
import urllib3

# Disable SSL warnings when verify=False
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def normalize_url(input_url: str) -> str:
    """Add http:// prefix if URL doesn't have protocol"""
    if not input_url.startswith(("http://", "https://")):
        return "http://" + input_url
    return input_url


def extract_domain(input_url: str) -> str:
    """Extract registered domain from URL"""
    e = tldextract.extract(input_url)
    if e.registered_domain:
        return e.registered_domain
    parsed = urlparse(input_url)
    return parsed.netloc

def extract_parent_url(url: str) -> str:
    """
    Trích xuất hostname (URL mẹ) từ một đường link đầy đủ.
    Hàm này xử lý cả trường hợp có hoặc không có http/https.

    Ví dụ: 
        Input: 'https://www.youtube.com/watch?v=dQw4w9WgXcQ'
        Output: 'www.youtube.com'
        
        Input: 'google.com/maps'
        Output: 'google.com'
    """
    if not url:
        return ""
        
    # Chuẩn hóa về chữ thường và xóa khoảng trắng thừa
    url = url.strip().lower()
    
    # Thêm http:// nếu người dùng quên nhập, để urlparse hoạt động đúng logic nhận diện netloc
    if not url.startswith("http://") and not url.startswith("https://"):
        url = "https://" + url
        
    try:
        parsed_uri = urlparse(url)
        return parsed_uri.netloc
    except Exception:
        return url
    
def fetch_raw_html(url) -> tuple:
    """
    Fetch raw HTML content from a website.
    Returns (html_content, extracted_text) tuple.
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Cache-Control': 'max-age=0'
    }
    
    try:
        # Normalize URL - preserve scheme if present, default to https
        original_scheme = None
        if url.startswith('http://'):
            original_scheme = 'http'
        elif url.startswith('https://'):
            original_scheme = 'https'
        else:
            # No scheme specified, try https first
            url = 'https://' + url
        
        print(f"[DEBUG] Fetching content from {url}")
        
        # Create session to handle cookies/redirects better
        session = requests.Session()
        session.headers.update(headers)
        
        # Make request with improved settings
        # Disable SSL verification to allow self-signed/invalid certificates (like university sites)
        response = session.get(
            url, 
            timeout=20,
            allow_redirects=True,
            verify=False  # Allow self-signed certificates
        )
        
        print(f"[DEBUG] Response status: {response.status_code}")
        print(f"[DEBUG] Response headers: {dict(response.headers)}")
        print(f"[DEBUG] Response size: {len(response.content)} bytes")
        
        response.raise_for_status()
        
        # Check if response is HTML
        content_type = response.headers.get('Content-Type', '').lower()
        if 'text/html' not in content_type and 'application/xhtml' not in content_type:
            print(f"[DEBUG] Non-HTML content type: {content_type}")
            return ("", "")
        
        # Check if content is empty
        if not response.content or len(response.content) < 100:
            print(f"[DEBUG] Response content too small or empty")
            return ("", "")
        
        # Parse HTML with multiple parsers for better compatibility
        try:
            soup = BeautifulSoup(response.content, 'html.parser')
        except Exception:
            # Fallback to lxml parser if html.parser fails
            try:
                soup = BeautifulSoup(response.content, 'lxml')
            except Exception:
                print(f"[DEBUG] Failed to parse HTML with both parsers")
                return ("", "")
        
        # Debug: check raw HTML size
        raw_html = str(soup)
        print(f"[DEBUG] Parsed HTML size: {len(raw_html)} characters")
        
        # Check for common anti-bot patterns
        body = soup.find('body')
        if not body:
            print(f"[DEBUG] No <body> tag found in HTML")
            # Try to extract from html tag directly
            html_tag = soup.find('html')
            if html_tag:
                body = html_tag
        
        # Remove unwanted elements (but keep some for better extraction)
        for element in soup(["script", "style", "noscript", "meta", "link"]):
            element.extract()
        
        # Try multiple extraction methods
        # Method 1: Standard get_text()
        text = soup.get_text(separator=' ', strip=True)
        
        # Method 2: If text is empty, try extracting from specific tags
        if not text or len(text) < 50:
            print(f"[DEBUG] Standard extraction failed, trying alternative methods")
            important_tags = soup.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'div', 'span', 'article', 'section', 'main'])
            text = ' '.join([tag.get_text(strip=True) for tag in important_tags if tag.get_text(strip=True)])
        
        # Clean up whitespace
        if text:
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            clean_text = ' '.join(chunk for chunk in chunks if chunk)
        else:
            clean_text = ""
        
        print(f"[DEBUG] Extracted {len(clean_text)} characters text from {url}")
        
        # If still no content, dump first 500 chars of HTML for debugging
        if not clean_text or len(clean_text) < 50:
            print(f"[DEBUG] Failed to extract meaningful text. HTML preview:")
            print(f"[DEBUG] {raw_html[:500]}")
        
        # Return tuple: (html_content, extracted_text)
        truncated_text = clean_text[:40000] if clean_text else ""
        return (response.text, truncated_text)
        
    except requests.exceptions.Timeout:
        print(f"[DEBUG] Timeout fetching content from {url}")
        return ("", "")
    except requests.exceptions.SSLError as e:
        print(f"[DEBUG] SSL error fetching content from {url}: {e}")
        return ("", "")
    except requests.exceptions.RequestException as e:
        print(f"[DEBUG] Request error fetching content from {url}: {e}")
        return ("", "")
    except Exception as e:
        print(f"[DEBUG] Error parsing content from {url}: {e}")
        import traceback
        traceback.print_exc()
        return ("", "")


def fetch_website_content(url) -> str:
    """
    Fetch visible text content from a website (backward compatibility).
    Returns extracted text only.
    """
    _, extracted_text = fetch_raw_html(url)
    return extracted_text
