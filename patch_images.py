#!/usr/bin/env python3
"""
Run this from ~/Downloads/tylerhogge-site:
  python3 patch_images.py

It will:
  1. Find every image URL across all blog post HTML files
  2. Download each image to ./img/
  3. Rewrite the <img src="..."> attributes to point to /img/filename
  4. Save the updated HTML files in place
"""

import os, re, hashlib, time, urllib.request

SITE_DIR = os.path.dirname(os.path.abspath(__file__))
IMG_DIR  = os.path.join(SITE_DIR, 'img')
os.makedirs(IMG_DIR, exist_ok=True)

HEADERS = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'}

img_pattern = re.compile(r'(<img[^>]+src=["\'])([^"\']+)(["\'][^>]*>)')

def safe_filename(url):
    ext = url.split('?')[0].rsplit('.', 1)[-1].lower()
    if ext not in ('png','jpg','jpeg','gif','webp','svg'): ext = 'png'
    name = url.split('?')[0].rsplit('/', 1)[-1]
    name = re.sub(r'[^a-z0-9._-]', '-', name.lower())[:40]
    h    = hashlib.md5(url.encode()).hexdigest()[:8]
    return f"{name}-{h}.{ext}"

def download(url):
    filename  = safe_filename(url)
    local     = os.path.join(IMG_DIR, filename)
    if os.path.exists(local) and os.path.getsize(local) > 200:
        return f"/img/{filename}", True  # already cached
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=12) as r:
            data = r.read()
        if len(data) < 200:
            return None, False
        with open(local, 'wb') as f:
            f.write(data)
        return f"/img/{filename}", True
    except Exception as e:
        print(f"  ✗ {url[:80]}")
        print(f"    {e}")
        return None, False

# Find all HTML files
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

# Download all
url_map = {}
ok, fail = 0, 0
for i, url in enumerate(sorted(all_urls)):
    local_path, success = download(url)
    if success:
        url_map[url] = local_path
        print(f"[{i+1}/{len(all_urls)}] ✓  {os.path.basename(local_path)}")
        ok += 1
    else:
        fail += 1
    time.sleep(0.05)

print(f"\nDownloaded {ok}/{len(all_urls)} images ({fail} failed)\n")

# Rewrite HTML files
patched = 0
for path in html_files:
    with open(path) as f:
        original = f.read()

    def rewrite(m):
        prefix, url, suffix = m.group(1), m.group(2), m.group(3)
        if url in url_map:
            return prefix + url_map[url] + suffix
        return m.group(0)

    updated = img_pattern.sub(rewrite, original)
    if updated != original:
        with open(path, 'w') as f:
            f.write(updated)
        patched += 1

print(f"✅ Patched {patched} HTML files with local image paths")
print(f"\nNext step: git add . && git commit -m 'host images locally' && git push")
