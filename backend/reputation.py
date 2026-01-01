# TrueWeb-GUI - Reputation Checker Module
# Adapted from TrueWeb-demo with new scoring system

import requests
import urllib3
import concurrent.futures
from typing import Dict, Any
import os
from pathlib import Path

# Disable SSL warnings when verify=False
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ---------------------------------------------------------
# LOAD ENVIRONMENT VARIABLES
# ---------------------------------------------------------
try:
    from .env_loader import load_env
    load_env()
except ImportError:
    print("[WARNING] env_loader not available. Using system environment variables only.")

# API Keys - Load from environment variables
VIRUSTOTAL_API_KEY = os.getenv("VIRUSTOTAL_API_KEY")
GOOGLE_SAFE_BROWSING_API_KEY = os.getenv("GOOGLE_SAFE_BROWSING_API_KEY")

# API Endpoints
VIRUSTOTAL_API_URL = "https://www.virustotal.com/api/v3/domains/{domain}"
GOOGLE_SAFE_BROWSING_API_URL = f"https://safebrowsing.googleapis.com/v4/threatMatches:find?key={GOOGLE_SAFE_BROWSING_API_KEY}"


# --- Reputation Scores (VirusTotal & Google Safe Browsing) ---
REPUTATION_SCORES = {
    "MALICIOUS": 0.0,
    "SUSPICIOUS": 0.3,
    "CLEAN": 1.0,
    "NOT_FOUND": 0.7,  # Neutral to good
    "API_ERROR": 0.5,
    "CONNECTION_ERROR": 0.5,
    "DEFAULT_NEUTRAL": 0.5,
}


def calculate_reputation_score(malicious_count: int, suspicious_count: int, total_vendors: int = 90) -> float:
    """
    Calculate reputation score based on vendor flagging counts.

    Formula:
    - Uses weighted penalty system
    - Malicious flags are heavily weighted (0.15 per flag)
    - Suspicious flags are moderately weighted (0.05 per flag)
    - Score = 1.0 - (malicious_penalty + suspicious_penalty)
    - Minimum score: 0.0

    Args:
        malicious_count: Number of vendors flagging as malicious
        suspicious_count: Number of vendors flagging as suspicious
        total_vendors: Total number of vendors (default: 90 for VirusTotal)

    Returns:
        float: Score between 0.0 and 1.0
    """
    if malicious_count == 0 and suspicious_count == 0:
        return 1.0  # Clean

    # Weight penalties
    malicious_penalty = min(malicious_count * 0.15, 1.0)  # Heavy penalty
    suspicious_penalty = min(suspicious_count * 0.05, 0.5)  # Moderate penalty

    score = 1.0 - malicious_penalty - suspicious_penalty
    return max(0.0, score)  # Ensure non-negative


def _check_virustotal(hostname: str) -> Dict[str, Any]:
    """
    Internal function to check VirusTotal. Returns a standard dict.
    """
    report = {"source": "VirusTotal", "sub_score": REPUTATION_SCORES["DEFAULT_NEUTRAL"], "details": "N/A"}

    if not VIRUSTOTAL_API_KEY or VIRUSTOTAL_API_KEY == "YOUR_API_KEY_HERE":
        report["details"] = "VT API key not configured."
        return report

    headers = {"x-apikey": VIRUSTOTAL_API_KEY}
    url = VIRUSTOTAL_API_URL.format(domain=hostname)

    try:
        response = requests.get(url, headers=headers, timeout=10, verify=False)

        if response.status_code == 200:
            stats = response.json().get("data", {}).get("attributes", {}).get("last_analysis_stats", {})
            malicious = stats.get("malicious", 0)
            suspicious = stats.get("suspicious", 0)

            if malicious > 0:
                report["details"] = f"Flagged as MALICIOUS by {malicious} vendors."
                report["sub_score"] = REPUTATION_SCORES["MALICIOUS"]
            elif suspicious > 0:
                report["details"] = f"Flagged as SUSPICIOUS by {suspicious} vendors."
                report["sub_score"] = REPUTATION_SCORES["SUSPICIOUS"]
            else:
                report["details"] = "Clean."
                report["sub_score"] = REPUTATION_SCORES["CLEAN"]

        elif response.status_code == 404:
            report["details"] = "Domain not found in database."
            report["sub_score"] = REPUTATION_SCORES["NOT_FOUND"]  # Not found is neutral-to-good
        else:
            report["details"] = f"API Error (Status {response.status_code})"
            report["sub_score"] = REPUTATION_SCORES["API_ERROR"]  # Neutral on API error

    except requests.exceptions.RequestException:
        report["details"] = "Connection error."
        report["sub_score"] = REPUTATION_SCORES["CONNECTION_ERROR"]

    return report


def _check_google_safebrowsing(full_url: str) -> Dict[str, Any]:
    """
    Internal function to check Google Safe Browsing. Returns a standard dict.
    """
    report = {"source": "Google Safe Browsing", "sub_score": REPUTATION_SCORES["DEFAULT_NEUTRAL"], "details": "N/A"}

    if not GOOGLE_SAFE_BROWSING_API_KEY or GOOGLE_SAFE_BROWSING_API_KEY == "YOUR_GOOGLE_CLOUD_API_KEY_HERE":
        report["details"] = "GSB API key not configured."
        return report

    payload = {
        "client": {"clientId": "trueweb-gui-app", "clientVersion": "1.0.0"},
        "threatInfo": {
            "threatTypes": ["MALWARE", "SOCIAL_ENGINEERING", "UNWANTED_SOFTWARE", "POTENTIALLY_HARMFUL_APPLICATION"],
            "platformTypes": ["ANY_PLATFORM"],
            "threatEntryTypes": ["URL"],
            "threatEntries": [{"url": full_url}]
        }
    }

    try:
        response = requests.post(GOOGLE_SAFE_BROWSING_API_URL, json=payload, timeout=10, verify=False)

        if response.status_code == 200:
            data = response.json()
            if data.get("matches"):
                threat_type = data["matches"][0]["threatType"]
                report["details"] = f"Flagged as: {threat_type}"
                report["sub_score"] = REPUTATION_SCORES["MALICIOUS"]  # Google flagging is high confidence
            else:
                report["details"] = "Clean."
                report["sub_score"] = REPUTATION_SCORES["CLEAN"]
        else:
            report["details"] = f"API Error (Status {response.status_code})"
            report["sub_score"] = REPUTATION_SCORES["API_ERROR"]  # Neutral on API error

    except requests.exceptions.RequestException:
        report["details"] = "Connection error."
        report["sub_score"] = REPUTATION_SCORES["CONNECTION_ERROR"]

    return report


def check_reputation(hostname: str, full_url: str) -> Dict[str, Any]:
    """
    Orchestrates reputation checks from multiple sources (VT, GSB).
    
    NEW SCORING SYSTEM (TrueWeb-GUI):
    - Start at 1.0 (clean)
    - Each vendor flag deducts 0.2
    - >= 5 vendors flagged = 0.0 score
    
    Returns:
    Dict[str, Any]: {
        "sub_score": float (0.0-1.0),
        "details": list of strings for display
    }
    """
    report = {
        "sub_score": 1.0,  # Default to max score (no data = assume clean)
        "details": [],
    }

    # --- Run checks in parallel ---
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        future_vt = executor.submit(_check_virustotal, hostname)
        future_gsb = executor.submit(_check_google_safebrowsing, full_url)

        vt_report = future_vt.result()
        gsb_report = future_gsb.result()

    # Extract vendor counts from VirusTotal
    malicious_count = 0
    suspicious_count = 0
    
    if "MALICIOUS by" in vt_report["details"]:
        try:
            # Extract number from "Flagged as MALICIOUS by X vendors."
            parts = vt_report["details"].split("by")
            if len(parts) > 1:
                malicious_count = int(parts[1].split()[0])
        except:
            pass
    
    if "SUSPICIOUS by" in vt_report["details"]:
        try:
            parts = vt_report["details"].split("by")
            if len(parts) > 1:
                suspicious_count = int(parts[1].split()[0])
        except:
            pass

    # Calculate total flags
    total_flags = malicious_count + suspicious_count
    
    # Check if GSB flagged (count as 1 additional vendor)
    if gsb_report["sub_score"] == REPUTATION_SCORES["MALICIOUS"]:
        total_flags += 1
    
    # NEW SCORING: 1.0 - (total_flags * 0.2), minimum 0.0
    # 1 vendor = -0.2, 2 vendors = -0.4, ..., >= 5 vendors = 0.0
    score_deduction = total_flags * 0.2
    final_score = max(0.0, 1.0 - score_deduction)
    
    # Build details list (each item on separate line)
    report["details"].append(f"<b>VirusTotal:</b> {vt_report['details']}")
    report["details"].append(f"<b>Google Safe Browsing:</b> {gsb_report['details']}")
    
    if total_flags >= 5:
        report["details"].append(f"<b>Verdict:</b> HIGH RISK - Flagged by {total_flags} sources (Score: 0.0)")
    elif total_flags > 0:
        report["details"].append(f"<b>Verdict:</b> WARNING - Flagged by {total_flags} source(s) (Score: {final_score:.1f})")
    elif vt_report["sub_score"] == REPUTATION_SCORES["CLEAN"] or gsb_report["sub_score"] == REPUTATION_SCORES["CLEAN"]:
        report["details"].append("<b>Verdict:</b> Clean - No threats detected")
    else:
        report["details"].append("<b>Verdict:</b> No data from reputation databases (assumed clean)")
    
    report["sub_score"] = final_score

    return report


if __name__ == "__main__":
    """
    Main block for testing this module independently.
    """
    import json

    print("--- Testing Reputation Module ---")

    # Test 1: Clean site
    print("\n[Test: google.com]")
    report_1 = check_reputation("google.com", "https://google.com")
    print(json.dumps(report_1, indent=2))

    # Test 2: Malicious site (Test URL from Google)
    print("\n[Test: malware.testing.google.test]")
    report_2 = check_reputation("malware.testing.google.test", "http://malware.testing.google.test/testing/malware/")
    print(json.dumps(report_2, indent=2))
