# Quick Reference Card

## The Issue (Explained Simply)

**Why did the scanner say "No injection points" without testing?**

```
URL: https://omaboostz.com.ng

Problem: No form fields or URL parameters to inject into
Result: Nothing to test = "No injection points"
```

---

## The Fix (One Simple Change)

```
❌ WRONG:  python xssscan.py --url "https://omaboostz.com.ng"
✅ RIGHT:  python xssscan.py --url "https://omaboostz.com.ng?search=test"
                                                             ^^^^^^^^^^^^
                                                        ADD PARAMETERS!
```

---

## How to Scan Properly

### Step 1: Find a URL with parameters

| Type | Example |
|------|---------|
| Search | `https://site.com/search?q=test` |
| Product | `https://site.com/product?id=123` |
| Blog | `https://site.com/posts?category=news` |
| API | `https://api.site.com/users?page=1` |

### Step 2: Run scanner with that URL

```bash
python xssscan.py --url "https://site.com/search?q=test" --verbose
```

### Step 3: Watch scanner actively test

```
[*] Scanning URL_PARAM GET https://site.com/search?q=test
    Parameters: q
    Payloads to test: 3338
  [   1/3338] <script>alert(1)</script>...
  [   2/3338] <img src=x onerror=alert(1)>...
  [   3/3338] ...
```

✓ **Scanner is working!**

---

## What Each Output Means

### ✓ VULNERABLE!
```
[   5/3338] <img src=x onerror=alert(1)>... ✓ VULNERABLE!
            Detection: Direct reflection
```
**Meaning:** Site is vulnerable to XSS

### [-]
```
[   1/3338] <script>alert(1)</script>... [-]
```
**Meaning:** This payload didn't work, testing next

### [HTTP 403]
```
[   1/3338] <script>alert(1)</script>... [HTTP 403]
```
**Meaning:** Site blocked the request (try with `--stealth`)

### [HTTP 200]
```
[   1/3338] <script>alert(1)</script>... [HTTP 200]
```
**Meaning:** Site accepted request, analyzing response

### No injection points found
```
No injection points found.
```
**Meaning:** URL has no `?param=value` to test → Add parameters!

---

## Quick Commands

### Basic Scan
```bash
python xssscan.py --url "https://site.com/search?q=test"
```

### Verbose (See Details)
```bash
python xssscan.py --url "https://site.com/search?q=test" --verbose
```

### Stealth Mode (Less Blocking)
```bash
python xssscan.py --url "https://site.com/search?q=test" --stealth
```

### Stealth + Verbose
```bash
python xssscan.py --url "https://site.com/search?q=test" --stealth --verbose
```

### Through Proxy (Burp Suite)
```bash
python xssscan.py --url "https://site.com/search?q=test" --proxy http://127.0.0.1:8080
```

### Slow Site (More Timeout)
```bash
python xssscan.py --url "https://site.com/search?q=test" --timeout 30
```

### Blind XSS Mode
```bash
python xssscan.py --url "https://site.com/contact?message=test" --mode blind
```

---

## Test Right Now (Vulnerable App)

### Setup (1 minute)
```bash
docker run --rm -p 80:80 vulnerables/web-dvwa
```

### Scan (See vulnerabilities found)
```bash
python xssscan.py --url "http://localhost/dvwa/vulnerabilities/xss_r/?name=test" --verbose
```

### Expected Result
```
✓ VULNERABLE!
Detection: Direct reflection
```

---

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| `--url "site.com"` | Add param: `--url "site.com?q=test"` |
| 403 errors | Add: `--stealth` |
| Timeout errors | Add: `--timeout 30` |
| "No injection points" | Missing `?param=value` in URL |
| Can't find forms | Manual URL: `site.com?search=test` |

---

## Documentation Files

| File | Purpose |
|------|---------|
| `README.md` | Complete guide |
| `QUICKSTART.md` | Quick reference |
| `TROUBLESHOOTING_GUIDE.md` | Solve problems |
| `EXAMPLES.md` | Real examples |
| `FIX_SUMMARY.md` | What was fixed |
| `ENHANCEMENTS.md` | Technical details |

**Start here:** `FIX_SUMMARY.md` → `EXAMPLES.md` → Scan!

---

## Remember

```
✅ Scanner works perfectly
✅ Just needs parameters in URL
✅ Add ?param=value format
✅ Then scanner tests actively
```

---

**TL;DR:**
```bash
# Add ?search=test to URL
python xssscan.py --url "https://omaboostz.com.ng?search=test" --verbose
# Scanner now actively tests!
```
