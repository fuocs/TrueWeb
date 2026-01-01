"""
WHOIS information service
"""
import whois
from datetime import datetime


def get_whois_info(domain: str) -> dict:
    """
    Get WHOIS information for a domain
    Returns registration and expiration dates
    """
    tld = domain.split('.')[-1]
    
    # Special handling for .vn domains - VNNIC blocks automated queries
    if tld == 'vn':
        return {
            "registration_date": "Not available",
            "expiration_date": "Not available"
        }
    
    # Handle other TLDs with python-whois library
    try:
        w = whois.whois(domain)
        
        def _first_date(d):
            if d is None:
                return None
            if isinstance(d, (list, tuple)):
                return d[0] if d else None
            return d

        creation = _first_date(w.creation_date)
        expiration = _first_date(w.expiration_date)

        result = {}
        
        if isinstance(creation, datetime):
            result["registration_date"] = creation.strftime("%Y-%m-%d")
        else:
            result["registration_date"] = "Not available"
            
        if isinstance(expiration, datetime):
            result["expiration_date"] = expiration.strftime("%Y-%m-%d")
        else:
            result["expiration_date"] = "Not available"
        
        return result
        
    except Exception as e:
        return {
            "registration_date": f"Error: {e}",
            "expiration_date": f"Error: {e}"
        }