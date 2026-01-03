"""
Scoring system for website information
Calculates a score based on the amount and quality of information retrieved

NEW SYSTEM:
- Each module returns sub_score (0.0-1.0)
- Multiply by weight from config
- Sum all weighted scores
- Divide by total weight to get average (0-1.0)
- Multiply by 5.0 to get final score (0.0-5.0)

OPTIMIZED WITH MULTI-THREADING:
- All modules run in parallel using ThreadPoolExecutor
- Reduces total scan time to the slowest module's time (instead of sum of all)

RETRY MECHANISM:
- Failed modules automatically retry with exponential backoff
- Retry count configurable in Settings (default 3)
"""
import concurrent.futures
import os
import time
import requests
import urllib3
from urllib.parse import urlparse
from .config                            import SCORE_WEIGHTS

# Disable SSL warnings when verify=False is used (for sites with self-signed certificates)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
from .utils.url_utils                   import extract_parent_url
from .                                  import review
from .DAandSR                           import get_website_info
from .                                  import calculate_score
from .take_screenshot                   import take_screenshot

def quick_connectivity_check(url: str, timeout: int = 3) -> tuple[bool, str]:
    """
    Quick check if website is reachable (2-3 seconds max).
    Returns: (is_reachable: bool, error_message: str)
    """
    try:
        # Normalize URL
        check_url = url if url.startswith(('http://', 'https://')) else f'https://{url}'
        
        # Headers to mimic a real browser (some sites block Python user-agents)
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Connection': 'keep-alive',
        }
        
        # Try HEAD request first (faster, no body download)
        # verify=False allows self-signed/invalid SSL certificates (like university sites)
        response = requests.head(check_url, timeout=timeout, allow_redirects=True, 
                                headers=headers, verify=False)
        
        # If HEAD not supported (405, 501, or any error), try GET with minimal data
        if response.status_code in [405, 501, 403]:
            response = requests.get(check_url, timeout=timeout, stream=True, 
                                   allow_redirects=True, headers=headers, verify=False)
        
        # Check if response is valid
        # Accept any 2xx, 3xx, 4xx status (even 404 means server is reachable)
        if response.status_code < 500:  # Accept any non-server-error status
            return True, ""
        else:
            return False, f"Server error: HTTP {response.status_code}"
            
    except requests.exceptions.SSLError as e:
        # SSL error - try again with verify=False (already set above, but fallback)
        return False, f"SSL certificate error: {str(e)}"
    except requests.exceptions.Timeout:
        return False, "Connection timeout - website is not responding"
    except requests.exceptions.ConnectionError as e:
        return False, f"Connection failed - website appears to be down"
    except Exception as e:
        return False, f"Network error: {str(e)}"


def check_website_reachable(url: str, timeout: int = 3) -> tuple[bool, str]:
    """
    Backwards-compatible wrapper used by UI controller.
    Returns (is_reachable, error_message) same as quick_connectivity_check.
    """
    return quick_connectivity_check(url, timeout=timeout)

def execute_with_retry(func, max_retries=3, module_name="Unknown"):
    """
    Execute a function with retry logic and exponential backoff.
    
    Args:
        func: Function to execute
        max_retries: Number of retry attempts (from settings)
        module_name: Name of module for logging
    
    Returns:
        Function result or raises last exception
    """
    for attempt in range(max_retries + 1):  # +1 for initial attempt
        try:
            return func()
        except Exception as e:
            if attempt < max_retries:
                wait_time = (2 ** attempt) * 0.5  # 0.5s, 1s, 2s, 4s...
                print(f"[RETRY] {module_name} failed (attempt {attempt + 1}/{max_retries + 1}), retrying in {wait_time}s: {e}")
                time.sleep(wait_time)
            else:
                print(f"[ERROR] {module_name} failed after {max_retries + 1} attempts: {e}")
                raise

def get_results(url: str, timeout: int = 30, retry_count: int = 3, screenshot_enabled: bool = True):
    """
    Get raw results from all modules using MULTI-THREADING for maximum speed.
    Each module returns: {"score": 0.0-1.0, "details": [...]}
    
    All modules run in parallel, reducing total time from sum of all modules
    to just the time of the slowest module.
    
    Args:
        url: URL to check
        timeout: Timeout in seconds per module
        retry_count: Number of retry attempts for failed modules (from settings)
        screenshot_enabled: Whether to take screenshots (from user checkbox)
    """
    
    # ⚡ QUICK CONNECTIVITY CHECK (2-3 seconds max)
    # Detect unreachable websites immediately before running expensive modules
    print(f"[DEBUG] Quick connectivity check for {url}...")
    is_reachable, error_msg = quick_connectivity_check(url, timeout=3)
    
    if not is_reachable:
        print(f"[ERROR] Website unreachable: {error_msg}")
        # Return error state immediately - no need to run any modules
        return {
            'error': True,
            'error_message': error_msg,
            'url': url
        }
    
    print(f"[DEBUG] ✓ Website is reachable, proceeding with analysis...")
    parent_url = extract_parent_url(url)
    
    # Generate screenshot filename from URL (prepare early)
    screenshot_url = url if url.startswith(('http://', 'https://')) else f'https://{url}'
    hostname = urlparse(screenshot_url).netloc or urlparse(url).netloc or "unknown"
    screenshot_filename = f"screenshot_{hostname.replace('.', '_')}.png"
    screenshot_path = os.path.join("screenshots", screenshot_filename)
    
    # Start ALL heavy tasks in parallel immediately - screenshot only if enabled
    print(f"[DEBUG] Starting parallel tasks: screenshot (if enabled), web info, reviews...")
    screenshot_future = None
    screenshot_executor = None
    
    if screenshot_enabled:
        screenshot_executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
        screenshot_future = screenshot_executor.submit(take_screenshot, screenshot_url, screenshot_path, timeout * 3)  # Give more time
    else:
        print(f"[DEBUG] Screenshot disabled by user - skipping capture")
    
    # 2. Pre-fetch data in parallel (don't wait)
    data_executor = concurrent.futures.ThreadPoolExecutor(max_workers=2)
    web_info_future = data_executor.submit(get_website_info, url)
    review_future = data_executor.submit(review.get_reviews, parent_url)
    
    # Get results from pre-fetch (should be quick)
    try:
        web_info = web_info_future.result(timeout=timeout)
    except Exception as e:
        print(f"[ERROR] Failed to fetch website info: {e}")
        web_info = None
    
    try:
        review_future.result(timeout=timeout)  # Just trigger, result stored in review.CURRENT_REVIEW
    except Exception as e:
        print(f"[ERROR] Failed to fetch reviews: {e}")
    
    data_executor.shutdown(wait=False)
    
    # Fetch HTML content ONCE for both AI and HTML heuristic modules (optimization)
    print(f"[DEBUG] Fetching HTML content (shared for AI + HTML analysis)...")
    from .utils import url_utils
    raw_html, extracted_text = url_utils.fetch_raw_html(url=url)
    print(f"[DEBUG] Raw HTML length = {len(raw_html)}, Extracted text length = {len(extracted_text)}")
    
    # If extracted text is empty but we have HTML, extract basic text from HTML for AI
    if (not extracted_text or len(extracted_text.strip()) == 0) and raw_html:
        print("[DEBUG] Extracted text is empty, using raw HTML for AI analysis...")
        from bs4 import BeautifulSoup
        try:
            soup = BeautifulSoup(raw_html, 'html.parser')
            # Remove script and style elements
            for script in soup(['script', 'style', 'meta', 'link']):
                script.decompose()
            # Get text content
            text = soup.get_text(separator=' ', strip=True)
            if text:
                extracted_text = text
                print(f"[DEBUG] Extracted {len(extracted_text)} characters from raw HTML")
            else:
                # No visible text in static HTML (likely JS-rendered). Use raw HTML as fallback.
                extracted_text = raw_html[:40000]
                print(f"[DEBUG] No visible text found — falling back to raw HTML ({len(extracted_text)} chars) for AI")
        except Exception as e:
            print(f"[DEBUG] Failed to extract text from HTML: {e}")
            # If all else fails, use raw HTML itself (AI can handle HTML)
            extracted_text = raw_html[:40000]  # Limit to 40k chars
            print(f"[DEBUG] Using raw HTML for AI (truncated to {len(extracted_text)} chars)")
    
    print(f"[DEBUG] Starting parallel module checks with {retry_count} retries...")
    
    # Define all scoring tasks to run in parallel (screenshot already running separately)
    # Wrap each task with retry logic
    tasks = {
        'Certificate details': lambda: execute_with_retry(
            lambda: calculate_score.certificate_score(url=url), 
            max_retries=retry_count, 
            module_name='Certificate details'
        ),
        'Protocol security': lambda: execute_with_retry(
            lambda: calculate_score.protocol_score(url=url), 
            max_retries=retry_count, 
            module_name='Protocol security'
        ),
        'HTML content and behavior': lambda: execute_with_retry(
            lambda: calculate_score.html_score(url=url, html_content=raw_html), 
            max_retries=retry_count, 
            module_name='HTML content and behavior'
        ),
        'Reputation Databases': lambda: execute_with_retry(
            lambda: calculate_score.reputationDB_score(url=url), 
            max_retries=retry_count, 
            module_name='Reputation Databases'
        ),
        'Domain pattern': lambda: execute_with_retry(
            lambda: calculate_score.domain_pattern_score(url=url), 
            max_retries=retry_count, 
            module_name='Domain pattern'
        ),
        'AI analysis': lambda: execute_with_retry(
            lambda: calculate_score.AI_score(url=url, extracted_text=extracted_text), 
            max_retries=retry_count, 
            module_name='AI analysis'
        ),
        'Server reliability': lambda: execute_with_retry(
            lambda: calculate_score.server_reliability_score(website_info=web_info), 
            max_retries=retry_count, 
            module_name='Server reliability'
        ),
        'Domain age': lambda: execute_with_retry(
            lambda: calculate_score.domain_age_score(website_info=web_info), 
            max_retries=retry_count, 
            module_name='Domain age'
        ),
        'User review': lambda: execute_with_retry(
            lambda: calculate_score.review_score(list_of_review=review.CURRENT_REVIEW), 
            max_retries=retry_count, 
            module_name='User review'
        )
    }

    results = {}
    
    # Use ThreadPoolExecutor to run all 9 scoring modules in parallel
    # Screenshot already running in separate executor, web_info & reviews completed
    with concurrent.futures.ThreadPoolExecutor(max_workers=9) as executor:
        # Submit all tasks
        future_to_name = {executor.submit(func): name for name, func in tasks.items()}
        
        # Collect results as they complete
        for future in concurrent.futures.as_completed(future_to_name):
            name = future_to_name[future]
            try:
                result = future.result(timeout=timeout * (retry_count + 1))  # Adjust timeout for retries
                results[name] = result
                score = result.get('score', 0)
                score_display = f"{score:.2f}" if score is not None else "no data"
                print(f"[DEBUG] ✓ {name}: score={score_display}, details_count={len(result.get('details', []))}")
            except Exception as exc:
                print(f"[ERROR] ✗ {name} failed after all retries: {exc}")
                # Fallback to safe default for scoring modules
                results[name] = {
                    "score": 0.0,
                    "details": [f"<b>Error:</b> Analysis failed after {retry_count + 1} attempts - {str(exc)}"]
                }
    
    print(f"[DEBUG] All modules completed!")
    
    # Wait for screenshot to finish (only if it was started)
    if screenshot_future is not None:
        try:
            screenshot_result = screenshot_future.result(timeout=timeout * 3 + 10)  # Much longer timeout
            if screenshot_result:
                success_count = sum(1 for _, _, success in screenshot_result if success)
                print(f"[DEBUG] ✓ Screenshot completed: {success_count}/{len(screenshot_result)} devices captured")
                results['__screenshot_paths__'] = screenshot_result
            else:
                print(f"[DEBUG] ⚠ Screenshot returned no results")
        except concurrent.futures.TimeoutError:
            print(f"[DEBUG] ⚠ Screenshot timeout after {timeout * 3 + 10}s - continuing without screenshots")
        except Exception as e:
            print(f"[DEBUG] ✗ Screenshot error: {e}")
        finally:
            if screenshot_executor:
                screenshot_executor.shutdown(wait=False)
    else:
        print(f"[DEBUG] Screenshot skipped - user disabled screenshots")
    
    return results

def calculate_final_verdict(results):
    """
    Calculate final verdict using new system:
    1. Each module has sub_score (0.0-1.0)
    2. Multiply by weight
    3. Sum and divide by total weight -> average (0.0-1.0)
    4. Multiply by 5.0 -> final score (0.0-5.0)
    
    NEW: Modules with errors are excluded from weight calculation
    and marked with has_error flag for UI highlighting.
    """
    weighted_sum = 0.0
    total_weight_used = 0.0
    component_scores = {}
    all_details = {}
    error_modules = {}  # Track which modules had errors

    for criterion, weight in SCORE_WEIGHTS.items():
        data = results[criterion]
        sub_score = data.get('score', 0.0)  # 0.0-1.0
        details = data.get('details', [])
        
        # Check if module had error (details contain "Error:" or "failed")
        # or no data (score is None or details contain "no data available")
        has_error = False
        has_no_data = False
        
        # Check score is None (explicit no-data marker)
        if sub_score is None:
            has_no_data = True
        elif details:
            detail_text = ' '.join(str(d) for d in details).lower()
            has_error = 'error:' in detail_text or 'failed' in detail_text
            has_no_data = 'no data available' in detail_text or 'no-data:' in detail_text
        
        # If module has error or no data, DO NOT include it in weight calculation
        if has_error or has_no_data:
            reason = "no data" if has_no_data else "error"
            print(f"[SCORING] Excluding {criterion} from weight calculation due to {reason}")
            component_scores[criterion] = 0.0  # Show as 0.0 in UI
            error_modules[criterion] = 'no-data' if has_no_data else True
        else:
            # Normal module - include in weighted sum
            weighted_sum += sub_score * weight
            total_weight_used += weight
            component_scores[criterion] = round(sub_score * 10, 1)
            error_modules[criterion] = False
        
        # Store details (even if empty list)
        if details and len(details) > 0:
            all_details[criterion] = details
        else:
            all_details[criterion] = ["<b>Status:</b> No data available"]

    # Calculate average (0.0-1.0) using only non-error modules
    if total_weight_used > 0:
        avg_score = weighted_sum / total_weight_used
    else:
        avg_score = 0.0

    # Convert to 0.0-5.0 scale
    final_score_5 = avg_score * 5.0

    return round(final_score_5, 2), component_scores, all_details, error_modules


def check_url(url: str, timeout: int = 30, retry_count: int = 3, screenshot_enabled: bool = True):
    """
    Main entry point for checking a URL.
    Returns: (final_score, component_scores, details, screenshot_paths, error_modules)
    - final_score: 0.0-5.0
    - component_scores: dict of criterion -> score (0-10)
    - details: dict of criterion -> list of detail strings
    - screenshot_paths: list of tuples (device_name, path, success) or None
    - error_modules: dict of criterion -> bool (True if module had error)
    - timeout: user-specified timeout in seconds
    - retry_count: number of retry attempts for failed modules (from settings)
    - screenshot_enabled: whether to take screenshots (from user checkbox)
    """
    raw_results = get_results(url=url, timeout=timeout, retry_count=retry_count, screenshot_enabled=screenshot_enabled)
    
    # Check if website is unreachable (early error from quick connectivity check)
    if raw_results.get('error'):
        error_msg = raw_results.get('error_message', 'Website is unreachable')
        return (
            None,  # score = None (no data, not 0.0 which means dangerous)
            {},   # component_scores
            {'Connection Error': [f'<b>Cannot connect to website:</b> {error_msg}', 
                                  '<b>Note:</b> Website may be temporarily down, blocked by firewall, or offline. This does not indicate malicious intent.']},  # details
            None,  # screenshot_paths
            {'__website_unreachable__': True}  # error_modules with special flag
        )
    
    # Extract screenshot paths before calculating verdict
    screenshot_paths = raw_results.pop('__screenshot_paths__', None)
    
    average_score, component_scores, details, error_modules = calculate_final_verdict(raw_results)
    return average_score, component_scores, details, screenshot_paths, error_modules
