# XSS Scanner Troubleshooting Guide

## Issue: "No injection points found"

### What This Means

When the scanner reports "No injection points discovered", it means:

✗ The target URL has **no discoverable injection points** (forms, URL parameters, or fragments)

This is **NOT a bug** – it's accurate behavior. The scanner correctly identified that there are no traditional web form inputs or URL parameters to test.

---

## Why This Happens

### Common Reasons:

1. **Modern Single Page App (SPA)**
   - Site uses JavaScript frameworks (React, Vue, Angular)
   - Forms are rendered dynamically by JavaScript
   - Not visible in initial HTML response
   - Example: Most modern web apps

2. **No Query Parameters in URL**
   - You provided just the domain: `https://example.com`
   - No URL parameters like `?search=test`
   - Scanner can't test what doesn't exist

3. **Bot Detection / Rate Limiting**
   - Site blocks automated requests
   - Returns generic HTML without forms
   - Your requests look suspicious to WAF

4. **Authentication Required**
   - Forms only visible after login
   - Scanner doesn't have valid session
   - Can't see protected forms

5. **Dynamic Form Loading**
   - Forms loaded via AJAX after page load
   - Scanner only sees initial HTML
   - JavaScript needs to run first

---

## Solutions

### Solution 1: Use URL with Parameters (⭐ Easiest)

**Test a URL that ALREADY has parameters:**

```bash
# ✓ Good - has a parameter to test
python xssscan.py --url "https://example.com/search?q=test"

# ✓ Good - multiple parameters
python xssscan.py --url "https://example.com/api?id=123&name=john"

# ✗ Bad - just domain, no params
python xssscan.py --url "https://example.com"
```

**Real-world examples:**

```bash
# E-commerce search
python xssscan.py --url "https://shop.example.com/search?query=laptop"

# Blog with tags
python xssscan.py --url "https://blog.example.com/posts?tag=python&sort=date"

# API endpoint
python xssscan.py --url "https://api.example.com/users?id=1&filter=active"
```

---

### Solution 2: Enable Stealth Mode

If the site blocks bot requests:

```bash
# Add stealth mode - random delays + realistic headers
python xssscan.py --url "https://example.com/search?q=test" --stealth

# Customize delay (seconds between requests)
python xssscan.py --url "https://example.com/search?q=test" --stealth --delay 2
```

**What stealth mode does:**
- Randomizes HTTP headers (fake browser user agents)
- Adds variable delays between requests
- Makes requests look like real user activity
- Bypasses simple bot detection

---

### Solution 3: Use Proxy Mode

Route through Burp Suite for manual inspection and testing:

```bash
# 1. Start Burp Suite (port 8080 default)
# 2. Run scanner through Burp
python xssscan.py --url "https://example.com/search?q=test" \
  --proxy http://127.0.0.1:8080
```

**Why use proxy mode:**
- Inspect all requests/responses in Burp
- Manually modify requests
- Capture forms rendered by JavaScript
- Identify actual injection points
- Better understanding of application behavior

---

### Solution 4: Manual Form Discovery

For SPAs and JavaScript-heavy sites:

1. **Open site in browser**
2. **Right-click → Inspect → Network tab**
3. **Use application normally**
4. **Look for form submissions**
5. **Copy URL of form handler**
6. **Add parameter to test:**

```bash
# Found form posts to /api/feedback with "message" param
python xssscan.py --url "https://example.com/api/feedback?message=test" --verbose
```

---

### Solution 5: Increase Timeout

If site is slow to respond:

```bash
# Default timeout: 15 seconds
python xssscan.py --url "https://example.com/search?q=test" --timeout 30

# Very slow sites
python xssscan.py --url "https://example.com/search?q=test" --timeout 60
```

---

### Solution 6: Verbose Mode

Get detailed debugging information:

```bash
python xssscan.py --url "https://example.com/search?q=test" --verbose
```

**Shows:**
- Exact payloads being tested
- Response headers
- Detection methods used
- Partial response content
- Filter bypass attempts

---

## Real-World Scanning Workflow

### Step 1: Identify Target Forms
```bash
# Start here - just domain
python xssscan.py --url "https://example.com" --verbose

# Output: Shows "No injection points" if domain only
# ✓ This is correct behavior
```

### Step 2: Find Actual Form Actions
- Open site in browser
- Right-click → View Page Source
- Search for `<form`
- Find `action="/submit"` or `action="process.php"`
- Look for `<input name="search"` etc.

### Step 3: Construct URL with Parameters
```bash
# You found: form action="/search" with input name="q"
python xssscan.py --url "https://example.com/search?q=test"

# ✓ Now scanner can test this parameter!
```

### Step 4: Full Scan
```bash
# Run complete aggressive scan
python xssscan.py --url "https://example.com/search?q=test" \
  --stealth --verbose --timeout 20
```

---

## Common URLs to Test

### Example 1: Blog Search
```bash
python xssscan.py --url "https://myblog.com/search?q=hello"
```

### Example 2: E-commerce Product
```bash
python xssscan.py --url "https://shop.com/products?id=123&sort=price"
```

### Example 3: API Endpoint
```bash
python xssscan.py --url "https://api.example.com/search?term=python&limit=10"
```

### Example 4: User Profile
```bash
python xssscan.py --url "https://forum.com/profile?user=john&format=html"
```

### Example 5: Feedback Form
```bash
python xssscan.py --url "https://company.com/contact?subject=issue&email=test"
```

---

## Verification: How to Know Scanner is Actually Testing

### Look for these indicators:

✓ **Good - Scanner is testing:**
```
[*] Scanning URL_PARAM GET https://example.com/search?q=test
    Parameters: q
    Payloads to test: 3338
  [   1/3338] <script>alert(1)</script>... 
  [   2/3338] <img src=x onerror=alert(1)>...
  [   3/3338] "><script>alert(1)</script>...
```

✗ **Bad - Scanner not testing:**
```
[+] Fetching: https://example.com
    No injection points found.
```

**Key difference:**
- Good: Shows "Payloads to test: 3338" and progress counter
- Bad: Says "No injection points" immediately

---

## Testing Against Intentionally Vulnerable Apps

### Option 1: DVWA (Damn Vulnerable Web App)

```bash
# 1. Download & run DVWA locally
# docker run --rm -p 80:80 vulnerables/web-dvwa

# 2. Test reflected XSS page
python xssscan.py --url "http://localhost/dvwa/vulnerabilities/xss_r/?name=test"

# ✓ Should find vulnerabilities
```

### Option 2: WebGoat

```bash
# 1. Download & run WebGoat
# docker run --rm -p 8080:8080 webgoat/goatandwolf

# 2. Test XSS lesson
python xssscan.py --url "http://localhost:8080/WebGoat/start.mvc?test=param"
```

### Option 3: bWAPP

```bash
# 1. Run bWAPP vulnerable app
# 2. Test XSS modules
python xssscan.py --url "http://localhost/bwapp/xss_get.php?firstname=test"
```

---

## FAQ

**Q: Why does the scanner not test if there are no parameters?**
A: Because there's nothing to inject into! Injection requires an input field or URL parameter. Scanner only tests if something actually exists to test.

**Q: Does the scanner work on modern web apps?**
A: Not on initial page load, because forms are rendered by JavaScript. Use proxy mode or manually provide a URL with parameters.

**Q: How do I know if a parameter is vulnerable?**
A: Scanner will report "✓ VULNERABLE!" with detection method and filter bypasses used.

**Q: Should I use stealth mode all the time?**
A: Only if site blocks bots. Stealth mode slows down scanning. Use if you get timeouts or blocked errors.

**Q: Can I test multiple parameters at once?**
A: Yes, scanner automatically tests all discovered parameters. Just provide a URL with multiple params: `?q=test&sort=date&page=1`

**Q: What if I get "Connection refused"?**
A: Site is blocking your IP or requests. Try:
- `--stealth` mode (slower but more stealthy)
- `--proxy` through your local machine first
- Wait and retry later
- Use different network

**Q: Why is scanning slow?**
A: Scanner tests 3300+ payloads per parameter to maximize detection. Each test needs network round-trip time. Normal: 2-5 minutes per site.

---

## Quick Reference

| Problem | Solution | Command |
|---------|----------|---------|
| No injection points | Add URL parameter | `--url "...?param=test"` |
| Site blocks bot | Enable stealth | `--stealth --delay 2` |
| Slow responses | Increase timeout | `--timeout 30` |
| Need to debug | Enable verbose | `--verbose` |
| Behind proxy/WAF | Route through proxy | `--proxy http://...` |
| Want to inspect requests | Use Burp Suite | `--proxy http://127.0.0.1:8080` |

---

## Still Having Issues?

**Checklist:**
- [ ] Using a URL with parameters? (not just domain)
- [ ] Site is accessible from browser?
- [ ] No authentication required?
- [ ] Not rate-limited? (try --stealth)
- [ ] Network connection working? (try ping)
- [ ] Trying against vulnerable app first? (DVWA/WebGoat)

**Debug steps:**
```bash
# 1. Test with verbose + stealth
python xssscan.py --url "http://test.local/search?q=test" \
  --stealth --verbose --timeout 30

# 2. Test against known vulnerable app first
python xssscan.py --url "http://localhost/dvwa/vulnerabilities/xss_r/?name=test"

# 3. Use proxy to inspect traffic
python xssscan.py --url "http://test.local/search?q=test" \
  --proxy http://127.0.0.1:8080
```

---

**Key Takeaway:** The scanner works perfectly – it just needs actual injection points to test!
