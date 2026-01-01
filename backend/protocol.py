# TrueWeb - Protocol Security Checker
#
# Checks for HTTPS vs HTTP and TLS version security.
# Focused on protocol-level security (separate from certificate details).
#
# References:
# 1. "A State-of-the-Art Review..." (Li et al., 2024) - Section IV.A.2: Traffic properties.
# 2. "Phishing or Not Phishing?..." (Zieni et al., 2023) - Section VII.A.2.c: Traffic properties.

import ssl
import socket
from typing import Dict, Any


def check_protocol_security(hostname: str, timeout: int = 5) -> Dict[str, Any]:
    """
    Checks for HTTPS availability and TLS version security.

    Returns:
    Dict[str, Any]: A report dictionary with protocol security assessment.
    """
    report = {
        "sub_score": 0.0,
        "details": "N/A",
        "protocol": "N/A",
        "tls_version": "N/A",
        "is_secure": False
    }

    try:
        # Try HTTPS connection
        context = ssl.create_default_context()
        with socket.create_connection((hostname, 443), timeout=timeout) as sock:
            with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                report["protocol"] = "HTTPS"
                report["is_secure"] = True

                # Get TLS version (Ref: Zieni et al., 2023)
                tls_version = ssock.version()
                report["tls_version"] = tls_version

                # Score based on TLS version
                if tls_version in ["SSLv3", "TLSv1", "TLSv1.1"]:
                    # Insecure/deprecated TLS versions
                    report["details"] = [f"<b>Status:</b> HTTPS connection with INSECURE TLS version ({tls_version})."]
                    report["sub_score"] = 0.2
                    report["is_secure"] = False
                elif tls_version == "TLSv1.2":
                    # Acceptable but not optimal
                    report["details"] = [f"<b>Status:</b> HTTPS connection with acceptable TLS version ({tls_version})."]
                    report["sub_score"] = 0.9
                elif tls_version == "TLSv1.3":
                    # Modern and secure
                    report["details"] = [f"<b>Status:</b> HTTPS connection with modern TLS version ({tls_version})."]
                    report["sub_score"] = 1.0
                else:
                    # Unknown TLS version - assume acceptable
                    report["details"] = [f"<b>Status:</b> HTTPS connection with TLS version ({tls_version})."]
                    report["sub_score"] = 0.8

    except ssl.SSLCertVerificationError:
        # Certificate verification failed, but HTTPS is attempted
        report["protocol"] = "HTTPS"
        report["details"] = ["<b>WARNING:</b> HTTPS available but certificate verification failed."]
        report["sub_score"] = 0.4

    except ssl.SSLError:
        # SSL protocol error
        report["protocol"] = "HTTPS"
        report["details"] = ["<b>ERROR:</b> HTTPS available but SSL protocol error occurred."]
        report["sub_score"] = 0.3

    except socket.timeout:
        # Connection timeout on port 443 - try HTTP
        try:
            with socket.create_connection((hostname, 80), timeout=timeout):
                report["protocol"] = "HTTP"
                report["details"] = ["<b>Status:</b> Only insecure HTTP connection available (No SSL/TLS)."]
                report["sub_score"] = 0.0  # HTTP only = 0 points
                report["is_secure"] = False
        except:
            # Neither HTTPS nor HTTP available
            report["details"] = ["<b>ERROR:</b> Connection failed - website is unreachable."]
            report["sub_score"] = 0.0

    except Exception:
        # HTTPS not available, try HTTP
        try:
            with socket.create_connection((hostname, 80), timeout=timeout):
                report["protocol"] = "HTTP"
                report["details"] = ["<b>Status:</b> Only insecure HTTP connection available (No SSL/TLS)."]
                report["sub_score"] = 0.0  # HTTP only = 0 points
                report["is_secure"] = False
        except:
            # Neither HTTPS nor HTTP available
            report["details"] = ["<b>ERROR:</b> Connection failed - website is unreachable."]
            report["sub_score"] = 0.0

    return report


if __name__ == "__main__":
    """
    Main block for testing this module independently.
    """
    import json

    print("--- Testing Protocol Security Module ---")

    # Test 1: Modern HTTPS site
    print("\n[Test 1: Google (TLS 1.3)]")
    print(json.dumps(check_protocol_security("www.google.com"), indent=2))

    # Test 2: HTTP site
    print("\n[Test 2: HTTP Only Site]")
    print(json.dumps(check_protocol_security("neverssl.com"), indent=2))

    # Test 3: Invalid site
    print("\n[Test 3: Non-existent Site]")
    print(json.dumps(check_protocol_security("nonexistent-site-12345.com"), indent=2))

