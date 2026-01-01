"""
HTTP redirect chain detection service
"""
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import urllib3


def get_redirect_chain(url: str):
    """
    Follow HTTP redirects and return the redirection chain
    """
    s = requests.Session()
    s.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate',
        'Connection': 'close'
    })

    # Retry strategy
    retry = Retry(
        total=2,
        backoff_factor=0.5,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=frozenset(['GET', 'HEAD'])
    )
    adapter = HTTPAdapter(max_retries=retry)
    s.mount('http://', adapter)
    s.mount('https://', adapter)

    # Disable SSL warnings
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    attempts = [
        ('GET with verify', lambda: s.get(url, allow_redirects=True, timeout=(3, 10), verify=True)),
        ('GET without verify', lambda: s.get(url, allow_redirects=True, timeout=(3, 10), verify=False)),
        ('HEAD without verify', lambda: s.head(url, allow_redirects=True, timeout=(3, 10), verify=False))
    ]

    for attempt_name, attempt_func in attempts:
        try:
            resp = attempt_func()
            chain = [r.url for r in getattr(resp, 'history', [])]
            chain.append(resp.url)
            if len(chain) == 1:
                return "No redirection", None
            else:
                return " -> ".join(chain), chain[-1]
        except (requests.exceptions.SSLError, 
                requests.exceptions.ConnectionError, 
                requests.exceptions.Timeout) as e:
            continue
        except Exception as e:
            continue

    return "Unable to check (server may block automated requests)", None