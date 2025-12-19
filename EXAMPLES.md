# XSS Scanner Examples - Step by Step

## Why Your First Scan Didn't Work

```bash
# ❌ This won't test anything
python xssscan.py --url https://omaboostz.com.ng

# Output: "No injection points discovered"
# Why: No form fields or URL parameters to test
```

---

## ✅ Correct Way to Test

### Requirement: URL must have parameters

```bash
# ✅ Correct - URL has a parameter
python xssscan.py --url "https://omaboostz.com.ng/search?keyword=test"

# ✅ Correct - Multiple parameters
python xssscan.py --url "https://omaboostz.com.ng/products?id=1&name=shoes"
```

---

## Real Examples You Can Try Right Now

### Example 1: Vulnerable Test Site (DVWA)

**Setup:**
```bash
# Install Docker first, then:
docker run --rm -p 80:80 vulnerables/web-dvwa
```

**Scan:**
```bash
# This WILL find XSS vulnerabilities (intentionally vulnerable site)
python xssscan.py --url "http://localhost/dvwa/vulnerabilities/xss_r/?name=test" --verbose
```

**Expected Output:**
```
[+] Loaded 3197 payloads from payloads.txt
[+] Total payloads after variant generation: 3338
[+] Fetching: http://localhost/dvwa/vulnerabilities/xss_r/?name=test
    [URL PARAM] GET → http://localhost/dvwa/vulnerabilities/xss_r/?name=test
        Parameters: name

[*] Scanning URL_PARAM GET http://localhost/dvwa/vulnerabilities/xss_r/?name=test
    Parameters: name
    Payloads to test: 3338
  [   1/3338] <script>alert(1)</script>... ✓ VULNERABLE!
      Detection: Direct reflection
```

---

### Example 2: WebGoat (OWASP)

**Setup:**
```bash
docker run --rm -p 8080:8080 webgoat/goatandwolf
```

**Scan:**
```bash
python xssscan.py --url "http://localhost:8080/WebGoat/attack?Screen=20&menu=false" --stealth --verbose
```

---

### Example 3: bWAPP (buggy web application)

**Setup:**
```bash
docker run --rm -p 80:80 raesene/bwapp
```

**Scan:**
```bash
# XSS Stored
python xssscan.py --url "http://localhost/bwapp/xss_stored_1.php?firstname=john" --verbose

# XSS Reflected
python xssscan.py --url "http://localhost/bwapp/xss_get.php?firstname=john" --verbose
```

---

### Example 4: JUICE SHOP (Modern Vulnerable App)

**Setup:**
```bash
docker run --rm -p 3000:3000 bkimminich/juice-shop
```

**Scan:**
```bash
# Test search
python xssscan.py --url "http://localhost:3000/?q=test" --stealth --verbose

# Test with multiple params
python xssscan.py --url "http://localhost:3000/api/Products?pageSize=10&sort=rating" --stealth --verbose
```

---

## Real Website Scanning (With Permission)

### Important: Only test sites you own!

**For your own WordPress blog:**
```bash
# Test search parameter
python xssscan.py --url "https://myblog.com/?s=test" --stealth --verbose

# Test comment form
python xssscan.py --url "https://myblog.com/post-name/?comment=test" --stealth --verbose
```

**For your own e-commerce shop:**
```bash
# Test product search
python xssscan.py --url "https://myshop.com/products?q=laptop" --stealth --verbose

# Test filter/sort
python xssscan.py --url "https://myshop.com/category?sort=price&filter=electronics" --stealth --verbose
```

---

## Step-by-Step Workflow

### Step 1: Find a Target URL with Parameters

**Open site in browser:**
1. Navigate to search page
2. Search for something: "test"
3. Look at URL bar

**You see:**
```
https://mysite.com/search?q=test
                          ^^^^^^^^
                          This is the parameter!
```

### Step 2: Copy That URL and Test

```bash
python xssscan.py --url "https://mysite.com/search?q=test" --verbose
```

**Scanner output will show:**
```
[+] Fetching: https://mysite.com/search?q=test
    [URL PARAM] GET → https://mysite.com/search?q=test
        Parameters: q

[*] Scanning URL_PARAM GET https://mysite.com/search?q=test
    Parameters: q
    Payloads to test: 3338
  [   1/3338] <script>alert(1)</script>... 
```

✓ **Scanner is now actively testing!**

### Step 3: Wait for Results

```bash
# If vulnerable (will show):
  ✓ VULNERABLE!

# If safe (will show):
  [-]

# After all payloads are tested:
[+] VULNERABILITIES FOUND: 1
```

---

## Common Parameter Names to Test

### Search/Query Parameters
```bash
# Search
python xssscan.py --url "https://site.com/search?q=test"
python xssscan.py --url "https://site.com/search?keyword=test"
python xssscan.py --url "https://site.com/search?query=test"
python xssscan.py --url "https://site.com/search?term=test"

# ID/Category
python xssscan.py --url "https://site.com/products?id=123"
python xssscan.py --url "https://site.com/posts?category=news"
```

### User Input Parameters
```bash
# Comments/Messages
python xssscan.py --url "https://site.com/contact?message=test"
python xssscan.py --url "https://site.com/post?comment=test"

# User data
python xssscan.py --url "https://site.com/profile?username=john"
python xssscan.py --url "https://site.com/user?email=test@test.com"
```

### Navigation Parameters
```bash
# Pagination/Sorting
python xssscan.py --url "https://site.com/posts?page=1&sort=date"
python xssscan.py --url "https://site.com/products?sort=price&filter=sale"

# Navigation
python xssscan.py --url "https://site.com/admin?page=users&action=list"
```

---

## Scanning Combinations

### Scan with Stealth Mode (Avoids Detection)
```bash
python xssscan.py --url "https://site.com/search?q=test" \
  --stealth \
  --delay 1 \
  --verbose
```

**Use when:**
- Site blocks fast requests
- You see "Connection refused" errors
- You want to be less obvious

### Scan with Increased Timeout (Slow Sites)
```bash
python xssscan.py --url "https://site.com/search?q=test" \
  --timeout 30 \
  --verbose
```

**Use when:**
- Site responds slowly
- You see "Timeout" errors
- Site is geographically far away

### Scan Through Proxy (For Analysis)
```bash
# With Burp Suite
python xssscan.py --url "https://site.com/search?q=test" \
  --proxy http://127.0.0.1:8080 \
  --verbose
```

**Use when:**
- Want to inspect all requests in Burp
- Need to debug what scanner is doing
- Want to modify payloads manually

### Scan in Blind Mode (No Reflection)
```bash
python xssscan.py --url "https://site.com/contact?message=test" \
  --mode blind \
  --verbose
```

**Use when:**
- Site stores input without reflection
- You have a callback server to monitor
- Testing stored/blind XSS

### Full Aggressive Scan
```bash
python xssscan.py --url "https://site.com/search?q=test" \
  --stealth \
  --delay 0.5 \
  --timeout 30 \
  --verbose
```

---

## Understanding Output

### When Scanner Finds Vulnerability

```
[*] Scanning URL_PARAM GET https://site.com/search?q=test
    Parameters: q
    Payloads to test: 3338
  [   5/3338] <img src=x onerror=alert(1)>... ✓ VULNERABLE!
      Detection: Direct reflection
      Bypasses: 
```

**Means:**
- ✓ The site IS vulnerable to XSS
- Payload: `<img src=x onerror=alert(1)>`
- Detection method: The injected code was reflected in response
- No filter bypasses needed (site has no filtering)

### When Scanner Finds No Vulnerabilities

```
[*] Scanning URL_PARAM GET https://site.com/search?q=test
    Parameters: q
    Payloads to test: 3338
  [   1/3338] <script>alert(1)</script>... [-]
  [   2/3338] <img src=x onerror=alert(1)>... [-]
  [   3/3338] <svg onload=alert(1)>... [-]
  ...
  [3338/3338] ... [-]

[+] No vulnerabilities found after testing all payloads
```

**Means:**
- Site appears to be protected or properly sanitized
- No XSS vulnerabilities detected
- Either site is safe or uses advanced filtering

### When Scanner Can't Test

```
[+] Fetching: https://omaboostz.com.ng
    No injection points found.

[-] No injection points discovered.
```

**Means:**
- ✓ Scanner is working correctly
- ✗ URL has no parameters to test
- Solution: Add parameters to URL

---

## Quick Test: Verify Scanner Works

### Use this vulnerable URL to verify your setup:

```bash
# This DVWA URL is intentionally vulnerable
python xssscan.py --url "http://localhost/dvwa/vulnerabilities/xss_r/?name=<script>" --verbose
```

**If you see:**
```
✓ VULNERABLE!
```

✓ Your scanner works perfectly!

**If you see:**
```
Connection refused
```

❌ DVWA not running. Start it:
```bash
docker run --rm -p 80:80 vulnerables/web-dvwa
```

---

## Summary: The One Key Rule

| This | Result |
|------|--------|
| `https://site.com` | ❌ "No injection points" |
| `https://site.com/search?q=test` | ✅ Scanner tests actively |
| `https://site.com/products?id=123&category=shoes` | ✅ Tests both parameters |

**The URL MUST have `?param=value` format to be tested.**

---

Ready to scan? Start here:

```bash
# 1. Get DVWA running
docker run --rm -p 80:80 vulnerables/web-dvwa

# 2. Run scanner
python xssscan.py --url "http://localhost/dvwa/vulnerabilities/xss_r/?name=test" --verbose

# 3. Watch for ✓ VULNERABLE!
```

Go find XSS vulnerabilities! 🎯
