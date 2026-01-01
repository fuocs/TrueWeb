from datetime import datetime
from collections import Counter
from .pattern_analysis import check_domain_pattern
from .protocol import check_protocol_security
from .ssl_certificate import check_ssl_certificate
from .html_heuristic import check_html_heuristics
from .reputation import check_reputation
from .AI_confidence import check_ai_confidence
from .utils.url_utils import extract_parent_url

def _create_report():
    return {
        "score": 0.0,
        "details": []
    }

def _safe_get_details(result):
    """Safely extract details from module result"""
    details = result.get("details", [])
    if isinstance(details, list):
        return details if details else ["<b>Status:</b> No data available"]
    elif isinstance(details, str):
        return [details] if details else ["<b>Status:</b> No data available"]
    else:
        return ["<b>Status:</b> No data available"]

def certificate_score(url: str):
    """SSL Certificate check - returns score 0.0-1.0"""
    try:
        from urllib.parse import urlparse
        hostname = urlparse(url).hostname or url.replace('https://', '').replace('http://', '').split('/')[0]
        
        result = check_ssl_certificate(hostname)
        report = {
            "score": result.get("sub_score", 0.0),
            "details": _safe_get_details(result)
        }
        return report
    except Exception as e:
        print(f"[ERROR] certificate_score: {e}")
        return {"score": 0.0, "details": [f"<b>ERROR:</b> {str(e)}"]}

def domain_pattern_score(url: str): 
    """Domain pattern analysis - returns score 0.0-1.0"""
    try:
        from urllib.parse import urlparse
        hostname = urlparse(url).hostname or url.replace('https://', '').replace('http://', '').split('/')[0]
        
        result = check_domain_pattern(hostname)
        report = {
            "score": result.get("sub_score", 0.0),
            "details": _safe_get_details(result)
        }
        return report
    except Exception as e:
        print(f"[ERROR] domain_pattern_score: {e}")
        return {"score": 0.0, "details": [f"<b>ERROR:</b> {str(e)}"]}

def html_score(url:str, html_content: str = None):
    """HTML heuristic check - returns score 0.0-1.0"""
    try:
        # If HTML content not provided, fetch it
        if not html_content:
            from .DAandSR import fetch_website_content
            html_content = fetch_website_content(url)
        
        result = check_html_heuristics(html_content, url)
        report = {
            "score": result.get("sub_score", 0.0),
            "details": _safe_get_details(result)
        }
        return report
    except Exception as e:
        print(f"[ERROR] html_score: {e}")
        return {"score": 0.0, "details": [f"<b>ERROR:</b> {str(e)}"]}

def protocol_score(url:str):
    """Protocol security check - returns score 0.0-1.0"""
    try:
        from urllib.parse import urlparse
        hostname = urlparse(url).hostname or url.replace('https://', '').replace('http://', '').split('/')[0]
        
        result = check_protocol_security(hostname)
        report = {
            "score": result.get("sub_score", 0.0),
            "details": _safe_get_details(result)
        }
        return report
    except Exception as e:
        print(f"[ERROR] protocol_score: {e}")
        return {"score": 0.0, "details": [f"<b>ERROR:</b> {str(e)}"]}

def reputationDB_score(url: str):
    """Reputation database check - returns score 0.0-1.0"""
    try:
        from urllib.parse import urlparse
        hostname = urlparse(url).hostname or url.replace('https://', '').replace('http://', '').split('/')[0]
        
        result = check_reputation(hostname, url)
        report = {
            "score": result.get("sub_score", 0.0),
            "details": _safe_get_details(result)
        }
        return report
    except Exception as e:
        print(f"[ERROR] reputationDB_score: {e}")
        return {"score": 0.0, "details": [f"<b>ERROR:</b> {str(e)}"]}

def AI_score(url: str, extracted_text: str = None):
    """AI confidence check - returns score 0.0-1.0"""
    try:
        ai_response =  check_ai_confidence(url, extracted_text=extracted_text)
        report = _create_report()

        if not ai_response['status']:
            error_detail = ai_response['details'] if isinstance(ai_response['details'], list) else [ai_response['details']]
            error_msg = error_detail[0] if error_detail else 'Unknown error'
            
            # Check if it's NO DATA state (no content extracted)
            if ai_response.get('no_data') or error_msg == 'NO_DATA':
                # Return NO DATA state (yellow, like user review with no data)
                report['score'] = None  # None means no data, will be excluded from scoring
                report['details'] = ["<b>No data available</b> - Unable to extract website content"]
                return report
            
            # Check if it's rate limiting (return no data like user review)
            if 'rate limit' in error_msg.lower():
                # Return NO DATA state (same as user review with no data)
                report['score'] = None  # None means no data, will be excluded from scoring
                report['details'] = ["<b>No data available</b> - AI service rate limited"]
                return report
            
            # Other errors: return neutral score
            report['score'] = 0.5  # Neutral score
            report['details'] = [
                "<b>AI Analysis Status:</b> Unable to analyze (service unavailable)",
                f"<b>Reason:</b> {error_msg}"
            ]
            return report

        details = []
        
        # Lấy dữ liệu từ AI response
        scores = ai_response.get("scores", {})
        brand = ai_response.get("impersonated_brand", "N/A")
        summary = ai_response.get("content_summary", "")
        reasoning = ai_response.get("reasoning", "")
        keywords = ai_response.get("content_keywords", [])
        recommendations = ai_response.get("alternative_recommendations", [])

        # 2. Lấy các điểm thành phần (Giả định đầu vào thang 0-4)
        sexual_score = float(scores.get("sexual", 0))
        violence_score = float(scores.get("violence", 0))
        hate_score = float(scores.get("hate", 0))
        self_harm_score = float(scores.get("self_harm", 0))
        
        # 3. Tính điểm an toàn
        # Bước A: Tính an toàn cho từng tiêu chí (4 - điểm)
        safe_sexual = max(0, 4.0 - sexual_score)
        safe_violence = max(0, 4.0 - violence_score)
        safe_hate = max(0, 4.0 - hate_score)
        safe_self_harm = max(0, 4.0 - self_harm_score)

        # Bước B: Tính trung bình cộng
        avg_safety_raw = (safe_sexual + safe_violence + safe_hate + safe_self_harm) / 4.0
        
        # Bước C: Quy đổi sang thang 1.0 (4 điểm raw = 1.0 điểm final => chia 4)
        safety_score = avg_safety_raw / 4.0  # 0.0 - 1.0

        # Xử lý hiển thị "Notable Risks"
        notable_risks = []
        
        if sexual_score >= 2: notable_risks.append(f"Sexual ({sexual_score})")
        if violence_score >= 2: notable_risks.append(f"Violence ({violence_score})")
        if hate_score >= 2: notable_risks.append(f"Hate ({hate_score})")
        if self_harm_score >= 2: notable_risks.append(f"Self-harm ({self_harm_score})")

        if notable_risks:
            details.append(f"<b>⚠️ Notable Risks (Level >= 2):</b> {', '.join(notable_risks)}")
        elif safety_score < 1.0:
            details.append("<b>Content Status:</b> Minor flags detected")
        else:
            details.append("<b>Content Status:</b> Safe content")

        # 4. Xử lý Mạo danh thương hiệu
        if brand and brand.lower() not in ["none", "n/a", "unknown", "null"]:
            safety_score = min(safety_score, 0.2)  # Cap điểm tối đa là 0.2 nếu mạo danh
            details.append(f"<b>CRITICAL:</b> Potential impersonation of brand '{brand}'")
        
        # 5. Thêm thông tin bổ sung
        if summary:
            details.append(f"<b>Summary:</b> {summary}")
        
        if reasoning:
            details.append(f"<b>AI Analysis:</b> {reasoning}")
            
        if keywords:
            details.append(f"<b>Keywords:</b> {', '.join(keywords[:5])}")

        if recommendations:
            rec_names = [rec.get("name", "Unknown") for rec in recommendations]
            details.append(f"<b>Alternatives:</b> {', '.join(rec_names)}")

        # 6. Đóng gói kết quả (0.0 - 1.0)
        final_score = max(0.0, min(1.0, safety_score))
        
        report["score"] = round(final_score, 2)
        report["details"] = details
        
        return report
    except Exception as e:
        print(f"[ERROR] AI_score: {e}")
        import traceback
        traceback.print_exc()
        # Return neutral score on unexpected errors
        return {
            "score": 0.5, 
            "details": [
                "<b>AI Analysis Status:</b> Analysis failed unexpectedly",
                f"<b>Error:</b> {str(e)}"
            ]
        }

def domain_age_score(website_info:dict):
    """Domain age check - returns score 0.0-1.0"""
    reg_date = website_info.get("Registration Date")

    report = _create_report()
    details = []
    domain_age_score = 0.0

    if reg_date and reg_date != "Not available":
        try:
            # Parse registration date
            reg_datetime = datetime.strptime(reg_date, "%Y-%m-%d")
            current_date = datetime.now()
            
            # Calculate domain age in days
            age_days = (current_date - reg_datetime).days
            age_years = age_days / 365.25
            
            # Calculate score: 1.0 for >= 1 year, proportional for < 1 year
            if age_years >= 1.0:
                domain_age_score = 1.0
                details.append(f"<b>Domain Age:</b> {age_years:.2f} years (>= 1 year)")
                details.append(f"<b>Score:</b> {domain_age_score:.2f}/1.0 (maximum)")
            else:
                # Proportional score for domains < 1 year old
                domain_age_score = age_years
                details.append(f"<b>Domain Age:</b> {age_years:.2f} years (< 1 year)")
                details.append(f"<b>Score:</b> {domain_age_score:.2f}/1.0 (proportional)")
            
            # Format date as dd-mm-yyyy
            formatted_date = reg_datetime.strftime("%d-%m-%Y")
            details.append(f"<b>Registered:</b> {formatted_date}")
            details.append(f"<b>Age:</b> {age_days} days ({age_years:.2f} years)")
            
        except Exception as e:
            details.append(f"<b>ERROR:</b> Domain age parsing failed ({e})")
            details.append("<b>Score:</b> 0.00/1.0")
    else:
        # Treat "not available" as an error to exclude from scoring
        details.append("<b>ERROR:</b> Domain age registration date not available")
        details.append("<b>Note:</b> Module excluded from final score calculation")
    
    report["score"] = domain_age_score
    report["details"] = details
    return report

def server_reliability_score(website_info: dict):
    """Server reliability check - returns score 0.0-1.0"""

    report = _create_report()
    details = []

    # Total score components (normalized to 1.0)
    # IP: 0.35, Location: 0.25, ISP: 0.25, Redirection: 0.15
    
    # 1. IP Address (0.35)
    ip_score = 0.0
    ip_address = website_info.get("IP Address")
    if ip_address and ip_address != "Not found":
        ip_score = 0.35
        if isinstance(ip_address, list) and len(ip_address) > 1:
            details.append(f"<b>IP Address:</b> {len(ip_address)} IPs found (multiple)")
        else:
            details.append("<b>IP Address:</b> Found")
        details.append(f"<b>Score:</b> {ip_score:.2f}/0.35")
    else:
        details.append("<b>IP Address:</b> Not found")
        details.append(f"<b>Score:</b> {ip_score:.2f}/0.35")
    
    # 2. Hosting Location (0.25)
    location_score = 0.0
    location = website_info.get("Hosting Location")
    if location and location != "Unknown":
        components = [c.strip() for c in location.split(",") if c.strip()]
        if len(components) >= 3:
            location_score = 0.25
            details.append(f"<b>Hosting Location:</b> Full info ({location})")
        elif len(components) >= 2:
            location_score = 0.15
            details.append(f"<b>Hosting Location:</b> Partial info ({location})")
        elif len(components) >= 1:
            location_score = 0.05
            details.append(f"<b>Hosting Location:</b> Minimal info ({location})")
        details.append(f"<b>Score:</b> {location_score:.2f}/0.25")
    else:
        details.append("<b>Hosting Location:</b> Unknown")
        details.append(f"<b>Score:</b> {location_score:.2f}/0.25")
    
    # 3. ISP (0.25)
    isp_score = 0.0
    isp = website_info.get("ISP")
    if isp and isp != "Unknown":
        isp_score = 0.25
        details.append(f"<b>ISP:</b> {isp}")
        details.append(f"<b>Score:</b> {isp_score:.2f}/0.25")
    else:
        details.append("<b>ISP:</b> Unknown")
        details.append(f"<b>Score:</b> {isp_score:.2f}/0.25")
    
    # 4. Redirection (0.15)
    redirection_score = 0.0
    redirection = website_info.get("Redirection")
    if redirection:
        if "Unable to check" in redirection or "server may block" in redirection:
            redirection_score = 0.075
            details.append("<b>Redirection:</b> Unable to check completely")
        elif redirection == "No redirection":
            redirection_score = 0.15
            details.append("<b>Redirection:</b> No redirection")
        elif "->" in redirection:
            redirect_count = redirection.count("->")
            redirection_score = 0.15
            details.append(f"<b>Redirection:</b> Chain detected ({redirect_count} redirect(s))")
        else:
            redirection_score = 0.15
            details.append("<b>Redirection:</b> Checked")
        details.append(f"<b>Score:</b> {redirection_score:.2f}/0.15")
    else:
        details.append("<b>Redirection:</b> Not available")
        details.append(f"<b>Score:</b> {redirection_score:.2f}/0.15")
    
    # Calculate total score
    total_score = ip_score + location_score + isp_score + redirection_score
    
    report["score"] = round(total_score, 2)
    report["details"] = details
    return report

def review_score(list_of_review: list):
    """User review score - returns score 0.0-1.0"""

    report = _create_report()

    # When no reviews exist, mark as no-data to exclude from weight calculation
    # This way websites without reviews aren't penalized or rewarded
    if(len(list_of_review) == 0):
        report['score'] = 0.0
        report['details'] = [
            "<b>NO-DATA:</b> No user reviews yet",
            "<b>Note:</b> Module excluded from final score calculation"
        ]
        return report

    for review in list_of_review:
        report['score'] += review["score"]
    report['score'] /= len(list_of_review)
    
    # Normalize to 0.0-1.0 (reviews are already 0-10 scale)
    report['score'] = report['score'] / 10.0

    list_scores = [review['score'] for review in list_of_review]
    stats = Counter(list_scores)

    for score, count in sorted(stats.items(), key=lambda x: x[0], reverse=True):
        report["details"].append(f"<b>Rated {score}:</b> by {count} users")
    return report
