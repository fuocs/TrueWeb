# TrueWeb - SSL Certificate Checker
#
# Validates SSL certificate and analyzes certificate attributes.
# Focused on certificate quality and trustworthiness.
#
# References:
# 1. "A State-of-the-Art Review..." (Li et al., 2024) - Section IV.A.2: Certificate-based methods.
#    - Phishing sites often use DV certificates from free providers (Let's Encrypt, cPanel).
#    - Legitimate organizations often use OV or EV certificates.

import ssl
import socket
from datetime import datetime
from typing import Dict, Any


# List of Free/Automated CAs often abused by phishers (Li et al., 2024)
# Note: Using these is not inherently bad, but suspicious for high-profile sites (banks).
SUSPICIOUS_ISSUERS = [
    "Let's Encrypt",
    "cPanel",
    "ZeroSSL"
]

# Trusted/Premium CAs (high reputation)
TRUSTED_ISSUERS = [
    "Google Trust Services",
    "DigiCert",
    "Sectigo",
    "GlobalSign",
    "Entrust",
    "GoDaddy",
    "Cloudflare"  # Cloudflare is actually trusted
]


def check_ssl_certificate(hostname: str, timeout: int = 5) -> Dict[str, Any]:
    """
    Validates the SSL certificate and performs deep analysis of certificate attributes.

    Returns:
    Dict[str, Any]: A report dictionary with certificate assessment.
    """
    report = {
        "sub_score": 0.0,
        "details": "N/A",
        "certificate_valid": False,
        "certificate_issuer": "N/A",
        "certificate_expiry": "N/A",
        "validation_type": "Unknown",  # DV, OV, or EV
        "is_free_ca": False,
        "days_until_expiry": 0
    }

    try:
        # Try to establish SSL connection on port 443
        context = ssl.create_default_context()
        with socket.create_connection((hostname, 443), timeout=timeout) as sock:
            with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                cert = ssock.getpeercert()

                # --- 1. Expiry Analysis ---
                not_after_str = cert.get('notAfter')
                days_left = 0
                if not_after_str:
                    expiry_date = datetime.strptime(not_after_str, '%b %d %H:%M:%S %Y %Z')
                    report["certificate_expiry"] = expiry_date.isoformat()
                    days_left = (expiry_date - datetime.now()).days
                    report["days_until_expiry"] = days_left

                    if days_left < 0:
                        report["details"] = ["<b>ERROR:</b> Certificate is EXPIRED."]
                        report["sub_score"] = 0.1
                        report["certificate_valid"] = False
                        return report  # Stop if expired
                    else:
                        report["certificate_valid"] = True

                # --- 2. Issuer Analysis (Ref: Li et al., 2024) ---
                issuer_info = cert.get('issuer', [])
                issuer_org = "Unknown"
                issuer_common_name = "Unknown"

                for item in issuer_info:
                    key, value = item[0]
                    if key == 'organizationName':
                        issuer_org = value
                    if key == 'commonName':
                        issuer_common_name = value

                report["certificate_issuer"] = issuer_org

                # Check if issuer is a common free/automated CA
                if any(sus in issuer_org for sus in SUSPICIOUS_ISSUERS) or \
                        any(sus in issuer_common_name for sus in SUSPICIOUS_ISSUERS):
                    report["is_free_ca"] = True

                # --- 3. Validation Type Analysis (DV vs OV/EV) ---
                # Ref: Li et al., 2024 - "Phishers can easily obtain valid certificates... (DV)"
                # EV/OV certs usually contain 'subject' > 'organizationName' or 'serialNumber'.
                # DV certs usually ONLY have 'commonName' (domain name) in the subject.

                subject_info = cert.get('subject', [])
                subject_dict = {key: value for (key, value) in [item[0] for item in subject_info]}

                has_org_name = 'organizationName' in subject_dict
                has_serial = 'serialNumber' in subject_dict  # Often indicates EV

                if has_org_name and has_serial:
                    report["validation_type"] = "EV (Extended Validation)"
                    score_base = 1.0
                    desc = "High assurance (EV)."
                elif has_org_name:
                    report["validation_type"] = "OV (Organization Validation)"
                    score_base = 1.0
                    desc = "Verified organization (OV)."
                else:
                    report["validation_type"] = "DV (Domain Validated)"
                    score_base = 0.8  # Slightly lower because it's easy to get
                    desc = "Domain control only (DV)."

                # --- Scoring Logic ---
                report["sub_score"] = score_base
                
                # Build details list
                details_list = []
                details_list.append(f"<b>Status:</b> Valid certificate ({report['validation_type']})")
                details_list.append(f"<b>Issuer:</b> {issuer_org}")
                details_list.append(f"<b>Expires in:</b> {days_left} days")

                # Check if issuer is trusted (bonus for premium CAs)
                is_trusted = any(trusted in issuer_org for trusted in TRUSTED_ISSUERS) or \
                             any(trusted in issuer_common_name for trusted in TRUSTED_ISSUERS)
                
                if is_trusted:
                    # Bonus for trusted CA
                    report["sub_score"] = min(1.0, report["sub_score"] + 0.1)
                    details_list.append("<b>TRUSTED:</b> Certificate from reputable CA")
                elif report["validation_type"] == "DV (Domain Validated)" and report["is_free_ca"]:
                    # Penalty only for DV + Free CA (common in phishing)
                    report["sub_score"] -= 0.2
                    details_list.append("<b>WARNING:</b> Issued by a free/automated CA")

                # Penalty only for VERY short expiry (<7 days = urgent renewal needed)
                if days_left < 7:
                    report["sub_score"] -= 0.2
                    details_list.append(f"<b>CRITICAL:</b> Certificate expires in {days_left} days!")
                elif days_left < 30:
                    # No penalty, just informational (modern best practice = short-lived certs)
                    details_list.append(f"<b>INFO:</b> Short-lived certificate (security best practice)")

                report["details"] = details_list
                # Ensure sub_score doesn't go below 0
                report["sub_score"] = max(0.0, report["sub_score"])

    except ssl.SSLCertVerificationError:
        report["details"] = ["<b>ERROR:</b> Certificate verification FAILED (e.g., self-signed, hostname mismatch)."]
        report["sub_score"] = 0.2

    except ssl.SSLError:
        report["details"] = ["<b>ERROR:</b> SSL Protocol Error (Certificate issue)."]
        report["sub_score"] = 0.2

    except socket.timeout:
        # Port 443 timeout - likely HTTP-only site
        try:
            with socket.create_connection((hostname, 80), timeout=timeout):
                report["details"] = ["<b>Status:</b> No SSL certificate (HTTP-only website)."]
                report["sub_score"] = 0.0
                report["certificate_valid"] = False
        except:
            report["details"] = ["<b>ERROR:</b> Connection timed out - website is unreachable."]
            report["sub_score"] = 0.0

    except ConnectionRefusedError:
        # Port 443 refused - likely HTTP-only site
        try:
            with socket.create_connection((hostname, 80), timeout=timeout):
                report["details"] = ["<b>Status:</b> No SSL certificate (HTTP-only website)."]
                report["sub_score"] = 0.0
                report["certificate_valid"] = False
        except:
            report["details"] = ["<b>ERROR:</b> Connection refused - website is unreachable."]
            report["sub_score"] = 0.0

    except Exception as e:
        # No HTTPS/SSL available - check if HTTP works
        try:
            with socket.create_connection((hostname, 80), timeout=timeout):
                report["details"] = ["<b>Status:</b> No SSL certificate (HTTP-only website)."]
                report["sub_score"] = 0.0
                report["certificate_valid"] = False
        except:
            report["details"] = [f"<b>ERROR:</b> No SSL certificate available: {str(e)}"]
            report["sub_score"] = 0.0

    return report


if __name__ == "__main__":
    """
    Main block for testing this module independently.
    """
    import json

    print("--- Testing SSL Certificate Module ---")

    # Test 1: High assurance site (likely OV/EV)
    print("\n[Test 1: Bank/PayPal]")
    print(json.dumps(check_ssl_certificate("www.paypal.com"), indent=2))

    # Test 2: Standard site (DV - Let's Encrypt)
    print("\n[Test 2: Standard DV Certificate]")
    print(json.dumps(check_ssl_certificate("www.wikipedia.org"), indent=2))

    # Test 3: Expired certificate
    print("\n[Test 3: Expired Certificate]")
    print(json.dumps(check_ssl_certificate("expired.badssl.com"), indent=2))

