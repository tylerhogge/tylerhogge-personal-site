#!/usr/bin/env python3
"""
Run this from ~/Downloads/tylerhogge-site:
  pip3 install requests browser-cookie3
  python3 patch_images.py

It will:
  1. Load your WordPress.com session cookies from Chrome/Safari
  2. Find every image URL across all blog post HTML files
  3. Download each image to ./img/  (skips already-downloaded ones)
  4. Rewrite the <img src="..."> attributes to point to /img/filename
  5. Save the updated HTML files in place
"""

import os, re, hashlib, time, sys, subprocess

# ── auto-install dependencies ──────────────────────────────────────────────
for pkg, imp in [('requests', 'requests'), ('browser-cookie3', 'browser_cookie3')]:
    try:
        __import__(imp)
    except ImportError:
        print(f"Installing {pkg}...")
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', pkg, '--quiet'])

import requests
try:
    import browser_cookie3
    HAS_COOKIE_LIB = True
except ImportError:
    HAS_COOKIE_LIB = False

# ── set up requests session with browser cookies ───────────────────────────
session = requests.Session()
session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Referer':    'https://tylerhogge.com/',
    'Accept':     'image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8',
})

if HAS_COOKIE_LIB:
    loaded = False
    for browser_fn, name in [
        (browser_cookie3.chrome,  'Chrome'),
        (browser_cookie3.safari,  'Safari'),
        (browser_cookie3.firefox, 'Firefox'),
    ]:
        if loaded:
            break
        try:
            for domain in ['wordpress.com', 'tylerhogge.com']:
                cj = browser_fn(domain_name=domain)
                session.cookies.update(cj)
            print(f"✓ Loaded {name} cookies for WordPress.com\n")
            loaded = True
        except Exception as e:
            print(f"  {name} cookies unavailable: {e}")
    if not loaded:
        print("⚠️  Could not load browser cookies – will try without (may still get 403s)\n")
else:
    print("⚠️  browser-cookie3 not available – will try without cookies\n")

# ── paths ──────────────────────────────────────────────────────────────────
SITE_DIR = os.path.dirname(os.path.abspath(__file__))
IMG_DIR  = os.path.join(SITE_DIR, 'img')
os.makedirs(IMG_DIR, exist_ok=True)

img_pattern = re.compile(r'(<img[^>]+src=["\'])([^"\']+)(["\'][^>]*>)')

def safe_filename(url):
    ext  = url.split('?')[0].rsplit('.', 1)[-1].lower()
    if ext not in ('png','jpg','jpeg','gif','webp','svg'): ext = 'png'
    name = url.split('?')[0].rsplit('/', 1)[-1]
    name = re.sub(r'[^a-z0-9._-]', '-', name.lower())[:40]
    h    = hashlib.md5(url.encode()).hexdigest()[:8]
    return f"{name}-{h}.{ext}"

def download(url):
    filename = safe_filename(url)
    local    = os.path.join(IMG_DIR, filename)
    if os.path.exists(local) and os.path.getsize(local) > 200:
        return f"/img/{filename}", True   # already cached
    try:
        r = session.get(url, timeout=15, stream=True)
        r.raise_for_status()
        data = r.content
        if len(data) < 200:
            return None, False
        with open(local, 'wb') as f:
            f.write(data)
        return f"/img/{filename}", True
    except Exception as e:
        print(f"  ✗ {url[:80]}")
        print(f"    {e}")
        return None, False

# ── scan HTML files ────────────────────────────────────────────────────────
html_files = []
for root, dirs, files in os.walk(SITE_DIR):
    for f in files:
        if f.endswith('.html'):
            html_files.append(os.path.join(root, f))

print(f"Scanning {len(html_files)} HTML files...\n")

all_urls = set()
for path in html_files:
    with open(path) as f:
        content = f.read()
    for _, url, _ in img_pattern.findall(content):
        if not url.startswith('data:') and not url.startswith('/'):
            all_urls.add(url)

print(f"Found {len(all_urls)} unique external image URLs\n")

# ── download ───────────────────────────────────────────────────────────────
url_map = {}
ok = fail = skipped = 0
for i, url in enumerate(sorted(all_urls)):
    local_path, success = download(url)
    if success:
        url_map[url] = local_path
        cached = "(cached)" if os.path.exists(os.path.join(SITE_DIR, local_path.lstrip('/'))) else ""
        print(f"[{i+1}/{len(all_urls)}] ✓  {os.path.basename(local_path)} {cached}")
        ok += 1
    else:
        fail += 1
    time.sleep(0.05)

print(f"\n✓ {ok} downloaded / {fail} failed\n")

# ── rewrite HTML ───────────────────────────────────────────────────────────
patched = 0
for path in html_files:
    with open(path) as f:
        original = f.read()

    def rewrite(m):
        prefix, url, suffix = m.group(1), m.group(2), m.group(3)
        return prefix + url_map.get(url, url) + suffix

    updated = img_pattern.sub(rewrite, original)
    if updated != original:
        with open(path, 'w') as f:
            f.write(updated)
        patched += 1

print(f"✅ Patched {patched} HTML files with local image paths")
if fail:
    print(f"⚠️  {fail} images still failed (likely Twitter/deleted images — nothing we can do)")
print(f"\nNext step: deploy-site \"host all images locally\"")
