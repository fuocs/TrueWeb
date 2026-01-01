"""
Main module for extracting website information
"""
import requests
import urllib3
from typing import Optional
from .utils.url_utils import normalize_url, extract_domain
from .services.whois_service import get_whois_info
from .services.ip import get_a_records
from .services.location import get_ip_geoinfo
from .services.redirection import get_redirect_chain

# Disable SSL warnings when verify=False
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def fetch_website_content(url: str, timeout: int = 5) -> Optional[str]:
    """
    Fetches the HTML content of a website, pretending to be a browser
    to avoid simple anti-crawler cloaking.
    """
    # Ensure URL has a scheme
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    try:
        response = requests.get(url, headers=headers, timeout=timeout, verify=False)
        response.raise_for_status()
        return response.text
    except requests.exceptions.RequestException as e:
        print(f"  [Content Fetch Error: {e}]")
        return None


def get_website_info(url: str) -> dict:
    """
    Get comprehensive website information:
    - Domain registration and expiration dates
    - IP address
    - Hosting information (country, ISP, city)
    - Redirect chain behavior

    Returns: dict containing all data
    """
    normalized_url = normalize_url(url)
    domain = extract_domain(normalized_url)

    result = {}

    # WHOIS info
    whois_info = get_whois_info(domain)
    result["Registration Date"] = whois_info.get("registration_date")
    result["Expiration Date"] = whois_info.get("expiration_date")

    # IP records
    a_records = get_a_records(domain)
    if isinstance(a_records, list) and len(a_records) > 0:
        result["IP Address"] = a_records[0] if len(a_records) == 1 else a_records
        
        # Hosting location from first IP
        geo = get_ip_geoinfo(a_records[0])
        if "error" not in geo:
            location_parts = [geo.get("city"), geo.get("region"), geo.get("country")]
            location = ", ".join([p for p in location_parts if p])
            result["Hosting Location"] = location if location else "Unknown"
            result["ISP"] = geo.get("isp")
        else:
            result["Hosting Location"] = "Unknown"
            result["ISP"] = "Unknown"
    else:
        result["IP Address"] = "Not found"
        result["Hosting Location"] = "Unknown"
        result["ISP"] = "Unknown"

    # Redirection
    result["Redirection"], result['Last url'] = get_redirect_chain(normalized_url)

    return result


# if __name__ == "__main__":
#     import json
    
#     # Get website information
#     # url = input("Enter website URL: ").strip()
#     url = 'https://linkneverdie.net/'
#     if not url:
#         url = "apple.com"
#         print(f"Using default: {url}")
    
#     print(f"\nFetching information for: {url}")
#     print("-" * 60)
    
#     data = get_website_info(url)
    
#     # Display raw information
#     print("\nWEBSITE INFORMATION:")
#     print("=" * 60)
#     # print(json.dumps(data, indent=2, ensure_ascii=False))
    
#     # Calculate and display score
#     score_result = calculate_score.domain_age_score(data)
#     print(json.dumps(score_result, indent=2))
