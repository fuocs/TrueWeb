"""
DNS lookup service
"""
import dns.resolver


def get_a_records(domain: str):
    """
    Get A records (IP addresses) for a domain
    """
    ips = []
    try:
        answers = dns.resolver.resolve(domain, "A")
        for r in answers:
            ips.append(r.to_text())
    except Exception as e:
        return {"error": f"DNS lookup failed: {e}"}
    return ips