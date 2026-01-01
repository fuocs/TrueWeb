"""
IP geolocation service using ip-api.com
"""
import requests


def get_ip_geoinfo(ip: str):
    """
    Get geographic information for an IP address
    Returns country, region, city, and ISP
    """
    url = f"http://ip-api.com/json/{ip}"
    try:
        r = requests.get(url, timeout=8)
        data = r.json()
        if data.get("status") == "success":
            return {
                "ip": ip,
                "country": data.get("country"),
                "region": data.get("regionName"),
                "city": data.get("city"),
                "isp": data.get("isp")
            }
        else:
            return {"ip": ip, "error": data.get("message")}
    except Exception as e:
        return {"ip": ip, "error": str(e)}