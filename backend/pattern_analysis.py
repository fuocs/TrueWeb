# TrueWeb - Module 4: Domain Pattern Analyzer
#
# Analyzes the domain name for common phishing patterns.
# (Incorporates research: homoglyphs, URL encoding, TLDs)

import socket
from typing import Dict, Any


# --- HEURISTICS ---
# Deceptive TLDs are often used for phishing
DECEPTIVE_TLDS = {'.xyz', '.info', '.top', '.icu', '.site', '.online', '.link'}


# --- Domain Pattern Penalties (these are subtractions from 1.0) ---
PATTERN_PENALTIES = {
    "IP_ADDRESS": 0.5,
    "DECEPTIVE_TLD": 0.3,
    "URL_ENCODED_CHARS": 0.4,
    "POTENTIAL_TYPOSQUATTING": 0.2,  # Contains numbers 0 or 1
}


def calculate_hyphen_penalty(hyphen_count: int) -> float:
    """
    Calculate penalty for hyphens in domain name.

    Optimized formula: penalty increases by 0.1 per hyphen (after 1st), max 0.4
    - 0-1: 0.0, 2: 0.1, 3: 0.2, 4: 0.3, 5+: 0.4

    Args:
        hyphen_count: Number of hyphens in domain

    Returns:
        float: Penalty value to subtract from base score
    """
    # Simple linear formula: max(0, min(0.4, (count - 1) * 0.1))
    return min(0.4, max(0.0, (hyphen_count - 1.0) * 0.1)) # examples: 0-1=0.0, 2=0.1, 3=0.2, 4=0.3, 5+=0.4


def calculate_subdomain_length_penalty(max_subdomain_length: int) -> float:
    """
    Calculate penalty for unusually long subdomain names.

    Formula:
    - 0-15 chars: 0.0 (normal)
    - 16-25 chars: Linear scale from 0.0 to 0.15 (slightly suspicious)
    - 26-40 chars: Linear scale from 0.15 to 0.3 (suspicious)
    - 40+ chars: 0.4 (very suspicious)

    Args:
        max_subdomain_length: Length of longest subdomain part

    Returns:
        float: Penalty value to subtract from base score
    """
    if max_subdomain_length <= 15:
        return 0.0
    elif max_subdomain_length <= 25:
        # Linear interpolation: 16-25 chars → 0.0-0.15
        return ((max_subdomain_length - 15) / 10) * 0.15
    elif max_subdomain_length <= 40:
        # Linear interpolation: 26-40 chars → 0.15-0.3
        return 0.15 + ((max_subdomain_length - 25) / 15) * 0.15
    else:
        # 40+ chars - very suspicious
        return 0.4


def check_domain_pattern(hostname: str) -> Dict[str, Any]:
    """
    Analyzes the domain name for common phishing patterns.

    Returns:
    Dict[str, Any]: A report dictionary.

    # Example Return Data (Good):
    # {
    #     "sub_score": 1.0,
    #     "details": "Domain pattern appears normal.",
    #     "warnings": []
    # }
    #
    # Example Return Data (Bad):
    # {
    #     "sub_score": 0.3,
    #     "details": "WARNING: Excessive hyphens in domain. | Uses a deceptive TLD: .xyz",
    #     "warnings": [
    #         "Excessive hyphens in domain.",
    #         "Uses a deceptive TLD: .xyz"
    #     ]
    # }
    """
    report = {
        "sub_score": 1.0,  # Start with a perfect score
        "details": "Domain pattern appears normal.",
        "warnings": []
    }

    # 1. Check for IP address as hostname
    # Ref: Section VII.A.1 - "obfuscation techniques... replace hostnames with IP addresses"
    try:
        socket.inet_aton(hostname)
        report["warnings"].append("Hostname is an IP address (Obfuscation technique).")
        report["sub_score"] -= 0.3
    except socket.error:
        pass

        # 2. Check for excessive hyphens
    # Ref: Section VII.A.1.a - Lexical properties (delimiters, structure)
    if hostname.count('-') > 2:
        report["warnings"].append("Excessive hyphens in domain (often used to hide brand names).")
        report["sub_score"] -= 0.2

    # 3. Check for deceptive TLDs
    # Ref: Section II (Anatomy of Phishing) - "register specific domains"
    tld = "." + hostname.split('.')[-1]
    if tld in DECEPTIVE_TLDS:
        report["warnings"].append(f"Uses a deceptive TLD often associated with phishing: {tld}")
        report["sub_score"] -= 0.3

    # 4. Check for long subdomains / URL length
    # Ref: Section VII.A.1 - "URL and domain lengths... are particularly relevant"
    # Phishers often use long URLs to hide the actual domain in mobile browsers.
    if len(hostname) > 30:
        report["warnings"].append("Hostname is suspiciously long (>30 chars).")
        report["sub_score"] -= 0.2

    parts = hostname.split('.')
    if len(parts) > 3:
        if any(len(part) > 15 for part in parts[:-2]):
            report["warnings"].append("Contains unusually long subdomains.")
            report["sub_score"] -= 0.2

    # 5. Check for URL encoding in hostname
    # Ref: Section VII.A.1.a - "URL orthographic patterns"
    if '%' in hostname:
        report["warnings"].append("Hostname contains URL-encoded characters (Obfuscation).")
        report["sub_score"] -= 0.4

    # 6. Check for homoglyphs/typosquatting (Simple check)
    # Ref: Section II - "typosquatting... replace English characters with identical looking characters"
    # e.g., paypa1.com, g00gle.com
    if '0' in hostname.replace('.com', '') or '1' in hostname.replace('.com', ''):
        report["warnings"].append("Hostname contains numbers '0' or '1' (potential typosquatting of 'o'/'l').")
        report["sub_score"] -= 0.2

    # 7. Check for 'https' or 'http' token in domain
    # Ref: Section VII.A.1.a - Lexical properties
    # Phishers add "https" to the subdomain to trick users (e.g., https-secure-verify.com)
    if "http" in hostname or "https" in hostname:
        report["warnings"].append("Hostname contains 'http'/'https' token (Deceptive technique).")
        report["sub_score"] -= 0.4

    # 8. Check for '@' symbol in URL (Authority part)
    # Ref: Section VII.A.1.a - "unnecessary punctuation marks"
    # Browsers ignore everything before '@', sending user to the site after it.
    if "@" in hostname:
        report["warnings"].append("Hostname contains '@' symbol (Redirect obfuscation).")
        report["sub_score"] -= 0.5

    # 9. Check for URL Shortening Services (Heuristic)
    # Ref: Section IX (Conclusion) - "An important research gap refers to... URL shortening services"
    # Shorteners mask the real phishing URL.
    shorteners = ["bit.ly", "goo.gl", "tinyurl.com", "t.co", "is.gd", "cli.gs", "yfrog.com", "migre.me", "ff.im"]
    if any(s in hostname for s in shorteners):
        report["warnings"].append("Uses a URL shortening service (Masks destination).")
        # Note: Shorteners aren't inherently malicious, but suspicious in this context.
        report["sub_score"] -= 0.1

    # Finalizing Report - Convert to list format for GUI
    if report["warnings"]:
        report["details"] = [f"<b>WARNING:</b> {warning}" for warning in report["warnings"]]
    else:
        report["details"] = ["<b>Status:</b> Domain pattern appears normal (No obvious lexical anomalies)."]

    report["sub_score"] = max(0.0, report["sub_score"])
    return report


if __name__ == "__main__":
    """
    Main block for testing this module independently.
    """
    import json

    print("--- Testing Domain Pattern Module ---")
    test_domains = [
        "gemini.google.com",
        "242.25.99.24",
        "my-secure-bank-login.com",
        "login-verify.xyz",
        "g00gle.com",
        "very-long-subdomain-name.account-access.com",
        "mb%2dbank.com",
        "bit.ly"  # Shortener
    ]

    for domain in test_domains:
        print(f"\n[Test: {domain}]")
        report = check_domain_pattern(domain)
        print(json.dumps(report, indent=2))
