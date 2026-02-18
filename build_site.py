#!/usr/bin/env python3
"""Build tylerhogge.com static site from WordPress export."""

import json, re, os

with open('/sessions/kind-quirky-sagan/wp_posts.json') as f:
    posts = json.load(f)

with open('/sessions/kind-quirky-sagan/wp_pages.json') as f:
    pages = json.load(f)

OUT = '/sessions/kind-quirky-sagan/mnt/outputs/tylerhogge-site'

# ── Clean WordPress block editor comments ────────────────────────────────────
def clean_wp(html):
    if not html:
        return ''
    # Remove wp block comments
    html = re.sub(r'<!-- /?(wp:[^\-]+?|wp:[^\-]+?[^>]+?) -->', '', html)
    # Remove class="wp-block-*" attributes
    html = re.sub(r'\s*class="wp-block-[^"]*"', '', html)
    # Fix &amp; in text
    return html.strip()

def make_excerpt(html, max_chars=180):
    text = re.sub(r'<[^>]+>', '', html or '')
    text = text.replace('&amp;', '&').replace('&nbsp;', ' ').strip()
    if len(text) > max_chars:
        text = text[:max_chars].rsplit(' ', 1)[0] + '…'
    return text

def fmt_date(d):
    """2025-12-11 -> December 11, 2025"""
    from datetime import datetime
    try:
        return datetime.strptime(d, '%Y-%m-%d').strftime('%B %-d, %Y')
    except:
        return d

def slug_from_url(url):
    url = url.rstrip('/')
    return url.rsplit('/', 1)[-1]

# ── CSS ───────────────────────────────────────────────────────────────────────
CSS = """
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

html { font-size: 18px; }

body {
  font-family: Georgia, 'Times New Roman', serif;
  background: #fff;
  color: #1a1a1a;
  line-height: 1.7;
  -webkit-font-smoothing: antialiased;
}

a { color: inherit; }
a:hover { opacity: 0.65; }

/* ── NAV ── */
nav {
  border-bottom: 1px solid #e8e8e8;
  padding: 0 1.5rem;
}
.nav-inner {
  max-width: 720px;
  margin: 0 auto;
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 56px;
}
.nav-brand {
  font-size: 1rem;
  font-weight: 700;
  letter-spacing: -0.01em;
  text-decoration: none;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
}
.nav-links {
  display: flex;
  gap: 1.75rem;
  list-style: none;
}
.nav-links a {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  font-size: 0.85rem;
  text-decoration: none;
  color: #555;
  letter-spacing: 0.01em;
}
.nav-links a:hover { color: #1a1a1a; opacity: 1; }

/* ── MAIN ── */
main {
  max-width: 720px;
  margin: 0 auto;
  padding: 3rem 1.5rem 5rem;
}

/* ── HOME ── */
.home-bio {
  margin-bottom: 4rem;
}
.home-bio p {
  font-size: 1.15rem;
  color: #222;
  line-height: 1.75;
  margin-bottom: 1rem;
}
.home-bio a { text-decoration: underline; text-decoration-color: #ccc; }
.home-bio a:hover { text-decoration-color: #999; opacity: 1; }

.section-heading {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  font-size: 0.75rem;
  font-weight: 600;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  color: #999;
  margin-bottom: 1.5rem;
}

/* ── POST LIST ── */
.post-list { list-style: none; }
.post-list li {
  border-bottom: 1px solid #f0f0f0;
  padding: 1.5rem 0;
  position: relative;
  cursor: pointer;
}
.post-list li:first-child { border-top: 1px solid #f0f0f0; }
.post-list li:hover { opacity: 0.7; }

.post-title {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  font-size: 1.05rem;
  font-weight: 600;
  line-height: 1.35;
  margin-bottom: 0.35rem;
  letter-spacing: -0.01em;
}
.post-title a { text-decoration: none; }
.post-title a::after {
  content: '';
  position: absolute;
  inset: 0;
}

.post-meta {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  font-size: 0.8rem;
  color: #999;
  margin-bottom: 0.5rem;
}
.post-excerpt {
  font-size: 0.95rem;
  color: #555;
  line-height: 1.6;
}

.view-all {
  display: inline-block;
  margin-top: 2rem;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  font-size: 0.9rem;
  color: #555;
  text-decoration: none;
  border-bottom: 1px solid #ddd;
  padding-bottom: 2px;
}
.view-all:hover { color: #1a1a1a; border-color: #999; opacity: 1; }

/* ── SINGLE POST ── */
.post-header {
  margin-bottom: 2.5rem;
}
.post-header h1 {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  font-size: 2rem;
  font-weight: 700;
  line-height: 1.2;
  letter-spacing: -0.03em;
  margin-bottom: 0.75rem;
}
.post-header .post-date {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  font-size: 0.85rem;
  color: #999;
}

.post-body {
  font-size: 1.05rem;
  line-height: 1.78;
  color: #222;
}
.post-body p { margin-bottom: 1.4rem; }
.post-body h1, .post-body h2, .post-body h3 {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  margin: 2rem 0 0.75rem;
  letter-spacing: -0.02em;
}
.post-body h2 { font-size: 1.4rem; }
.post-body h3 { font-size: 1.15rem; }
.post-body ul, .post-body ol {
  padding-left: 1.5rem;
  margin-bottom: 1.4rem;
}
.post-body li { margin-bottom: 0.4rem; }
.post-body a { text-decoration: underline; text-decoration-color: #bbb; }
.post-body a:hover { text-decoration-color: #666; opacity: 1; }
.post-body strong { font-weight: 600; }
.post-body em { font-style: italic; }
.post-body blockquote {
  border-left: 3px solid #e0e0e0;
  padding-left: 1.25rem;
  color: #555;
  margin: 1.5rem 0;
  font-style: italic;
}
.post-body figure { margin: 2rem 0; }
.post-body img { max-width: 100%; border-radius: 4px; }
.post-body hr { border: none; border-top: 1px solid #e8e8e8; margin: 2.5rem 0; }

.post-nav {
  margin-top: 4rem;
  padding-top: 2rem;
  border-top: 1px solid #f0f0f0;
  display: flex;
  justify-content: space-between;
  gap: 1rem;
}
.post-nav a {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  font-size: 0.85rem;
  color: #555;
  text-decoration: none;
}
.post-nav a:hover { color: #1a1a1a; opacity: 1; }

/* ── BLOG INDEX ── */
.blog-header {
  margin-bottom: 2.5rem;
}
.blog-header h1 {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  font-size: 2rem;
  font-weight: 700;
  letter-spacing: -0.03em;
}

/* ── SIMPLE PAGES ── */
.page-body {
  font-size: 1.05rem;
  line-height: 1.78;
}
.page-body p { margin-bottom: 1.2rem; }
.page-body h3 {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  font-size: 1.1rem;
  margin: 1.5rem 0 0.5rem;
}
.page-body a { text-decoration: underline; text-decoration-color: #bbb; }
.page-body a:hover { text-decoration-color: #666; opacity: 1; }
.page-body strong { font-weight: 600; }
.page-header { margin-bottom: 2.5rem; }
.page-header h1 {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  font-size: 2rem;
  font-weight: 700;
  letter-spacing: -0.03em;
}

/* ── FOOTER ── */
footer {
  border-top: 1px solid #e8e8e8;
  padding: 2rem 1.5rem;
  text-align: center;
}
footer p {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  font-size: 0.8rem;
  color: #bbb;
}
footer a { color: #999; text-decoration: none; }
footer a:hover { color: #555; }

/* ── SEARCH ── */
.search-wrap {
  position: relative;
  margin-left: 1.25rem;
  width: 200px;
  flex-shrink: 0;
  display: flex;
  justify-content: flex-end;
}
.search-input {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  font-size: 0.8rem;
  border: 1px solid #e0e0e0;
  border-radius: 20px;
  padding: 0.25rem 0.75rem 0.25rem 1.85rem;
  width: 110px;
  outline: none;
  background: #f7f7f7 url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='13' height='13' viewBox='0 0 24 24' fill='none' stroke='%23999' stroke-width='2'%3E%3Ccircle cx='11' cy='11' r='8'/%3E%3Cpath d='m21 21-4.35-4.35'/%3E%3C/svg%3E") no-repeat 0.6rem center;
  transition: width 0.2s, border-color 0.2s;
  color: #1a1a1a;
}
.search-input:focus {
  width: 195px;
  border-color: #bbb;
  background-color: #fff;
}
.search-input::placeholder { color: #aaa; }

.search-results {
  display: none;
  position: absolute;
  top: calc(100% + 6px);
  right: 0;
  width: 320px;
  background: #fff;
  border: 1px solid #e8e8e8;
  border-radius: 8px;
  box-shadow: 0 4px 20px rgba(0,0,0,0.08);
  z-index: 100;
  overflow: hidden;
  max-height: 400px;
  overflow-y: auto;
}
.search-results.active { display: block; }
.search-result-item {
  display: block;
  padding: 0.85rem 1rem;
  text-decoration: none;
  border-bottom: 1px solid #f5f5f5;
  color: inherit;
}
.search-result-item:last-child { border-bottom: none; }
.search-result-item:hover { background: #f9f9f9; opacity: 1; }
.search-result-title {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  font-size: 0.9rem;
  font-weight: 600;
  margin-bottom: 0.2rem;
  color: #1a1a1a;
}
.search-result-date {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  font-size: 0.75rem;
  color: #999;
}
.search-no-results {
  padding: 1rem;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  font-size: 0.85rem;
  color: #999;
  text-align: center;
}

/* ── RESPONSIVE ── */

/* Tablet: compress nav slightly */
@media (max-width: 800px) {
  .nav-links { gap: 1.1rem; }
  .nav-links a { font-size: 0.8rem; }
  .search-wrap { width: 170px; }
  .search-input { width: 100px; }
  .search-input:focus { width: 160px; }
}

/* Mobile: two-row nav, hide search in nav */
@media (max-width: 600px) {
  html { font-size: 16px; }

  nav { padding: 0; }
  .nav-inner {
    flex-wrap: wrap;
    height: auto;
    padding: 0.75rem 1rem 0;
    gap: 0;
  }
  .nav-brand {
    flex: 1;
    padding-bottom: 0.6rem;
  }
  .search-wrap {
    order: 3;
    width: 100%;
    margin: 0;
    padding: 0.5rem 1rem;
    border-top: 1px solid #f0f0f0;
    justify-content: flex-start;
  }
  .search-input { width: 100%; }
  .search-input:focus { width: 100%; }
  .search-results { width: 100%; left: 0; right: 0; }

  .nav-links {
    order: 2;
    gap: 1.1rem;
    padding-bottom: 0.6rem;
  }
  .nav-links a { font-size: 0.8rem; }

  main { padding: 2rem 1rem 4rem; }
  .home-bio p { font-size: 1rem; }
  .post-header h1, .blog-header h1, .page-header h1 { font-size: 1.5rem; }
  .post-body { font-size: 1rem; }
}
"""

# ── HTML shell ────────────────────────────────────────────────────────────────
def html_page(title, content, active=''):
    nav_items = [
        ('/', 'Home'),
        ('/blog/', 'Writing'),
        ('/investments/', 'Investments'),
        ('/podcast/', 'Podcast'),
    ]
    active_style = ' style="color:#1a1a1a;font-weight:600"'
    nav_html = '\n'.join(
        '<li><a href="{}"{}>{}</a></li>'.format(href, active_style if active==href else '', label)
        for href, label in nav_items
    )
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{title}</title>
  <meta name="description" content="Tyler Hogge — Partner at Pelion. Writing about startups, VC, and leadership.">
  <link rel="stylesheet" href="/style.css">
  <link rel="icon" href="/favicon.ico" sizes="32x32">
  <link rel="icon" href="/favicon.png" type="image/png">
</head>
<body>
<nav>
  <div class="nav-inner">
    <a class="nav-brand" href="/">Tyler Hogge</a>
    <ul class="nav-links">
      {nav_html}
    </ul>
    <div class="search-wrap">
      <input class="search-input" type="search" placeholder="Search…" id="search-input" autocomplete="off" aria-label="Search posts">
      <div class="search-results" id="search-results"></div>
    </div>
  </div>
</nav>
<script>
(function() {{
  var input = document.getElementById('search-input');
  var results = document.getElementById('search-results');
  var index = null;

  function loadIndex(cb) {{
    if (index) {{ cb(); return; }}
    fetch('/search.json').then(function(r) {{ return r.json(); }}).then(function(data) {{
      index = data;
      cb();
    }});
  }}

  function search(q) {{
    q = q.toLowerCase().trim();
    if (!q) {{ results.classList.remove('active'); return; }}
    var matches = index.filter(function(p) {{
      return p.title.toLowerCase().includes(q) || p.body.toLowerCase().includes(q);
    }}).slice(0, 8);

    if (matches.length === 0) {{
      results.innerHTML = '<div class="search-no-results">No results for "' + q + '"</div>';
    }} else {{
      results.innerHTML = matches.map(function(p) {{
        return '<a class="search-result-item" href="/blog/' + p.slug + '/">' +
          '<div class="search-result-title">' + p.title + '</div>' +
          '<div class="search-result-date">' + p.date + '</div>' +
          '</a>';
      }}).join('');
    }}
    results.classList.add('active');
  }}

  input.addEventListener('focus', function() {{
    loadIndex(function() {{ if (input.value) search(input.value); }});
  }});
  input.addEventListener('input', function() {{
    loadIndex(function() {{ search(input.value); }});
  }});
  document.addEventListener('click', function(e) {{
    if (!e.target.closest('.search-wrap')) results.classList.remove('active');
  }});
  input.addEventListener('keydown', function(e) {{
    if (e.key === 'Escape') {{ results.classList.remove('active'); input.blur(); }}
  }});
}})();
</script>
<main>
{content}
</main>
<footer>
  <p>
    <a href="https://x.com/thogge" target="_blank" rel="noopener">@thogge</a> ·
    <a href="mailto:tylerhogge@gmail.com">Email</a>
  </p>
</footer>
</body>
</html>"""

# ── Write CSS ─────────────────────────────────────────────────────────────────
with open(f'{OUT}/style.css', 'w') as f:
    f.write(CSS)
print("✓ style.css")

# ── Search index ──────────────────────────────────────────────────────────────
search_index = []
for p in posts:
    body_text = re.sub(r'<[^>]+>', '', p['content'] or '')
    body_text = body_text.replace('&amp;', '&').replace('&nbsp;', ' ').strip()
    search_index.append({
        'title': p['title'],
        'slug': slug_from_url(p['link']),
        'date': fmt_date(p['date']),
        'body': body_text[:2000]  # enough text to search, not bloated
    })
with open(f'{OUT}/search.json', 'w') as f:
    json.dump(search_index, f, separators=(',', ':'))
print("✓ search.json")

# ── HOME PAGE ─────────────────────────────────────────────────────────────────
recent = posts[:8]
post_list_html = '\n'.join(f"""
<li>
  <div class="post-title"><a href="/blog/{slug_from_url(p['link'])}/">{p['title']}</a></div>
  <div class="post-meta">{fmt_date(p['date'])}</div>
  <div class="post-excerpt">{make_excerpt(p['content'])}</div>
</li>""" for p in recent)

home_content = f"""
<div class="home-bio">
  <p>Howdy. I'm <a href="https://x.com/thogge" target="_blank" rel="noopener">Tyler Hogge</a> — first and foremost a husband and father in a tribe called Hogge.</p>
  <p>I'm a Partner at <a href="https://pelionvp.com/" target="_blank" rel="noopener">Pelion</a>, where I lead Seed and Series A investments in <a href="http://exceptionalstartups.com" target="_blank" rel="noopener">exceptional startups</a>.</p>
  <p>Previously I led the product and risk organizations at <a href="https://getdivvy.com" target="_blank" rel="noopener">Divvy</a> (acquired by BILL for $2.5B), product teams at <a href="https://wealthfront.com" target="_blank" rel="noopener">Wealthfront</a>, interned at <a href="https://a16z.com" target="_blank" rel="noopener">a16z</a>, and led sales at <a href="https://clearwateranalytics.com" target="_blank" rel="noopener">Clearwater</a>. I've also invested out of my own fund, <a href="http://kindlingcapital.co" target="_blank" rel="noopener">Kindling Capital</a>.</p>
  <p>I graduated in finance from SUU (the MIT of Southern Utah, where I was captain of the D1 baseball team), and with an MBA from Cornell. I'm also a CFA Charterholder.</p>
</div>

<div class="section-heading">Recent Writing</div>
<ul class="post-list">
{post_list_html}
</ul>
<a class="view-all" href="/blog/">View all posts →</a>
"""

with open(f'{OUT}/index.html', 'w') as f:
    f.write(html_page('Tyler Hogge', home_content, '/'))
print("✓ index.html")

# ── BLOG INDEX ───────────────────────────────────────────────────────────────
all_posts_html = '\n'.join(f"""
<li>
  <div class="post-title"><a href="/blog/{slug_from_url(p['link'])}/">{p['title']}</a></div>
  <div class="post-meta">{fmt_date(p['date'])}</div>
  <div class="post-excerpt">{make_excerpt(p['content'])}</div>
</li>""" for p in posts)

blog_content = f"""
<div class="blog-header"><h1>Writing</h1></div>
<ul class="post-list">
{all_posts_html}
</ul>
"""

with open(f'{OUT}/blog/index.html', 'w') as f:
    f.write(html_page('Writing — Tyler Hogge', blog_content, '/blog/'))
print("✓ blog/index.html")

# ── INDIVIDUAL POSTS ──────────────────────────────────────────────────────────
for i, post in enumerate(posts):
    slug = slug_from_url(post['link'])
    if not slug:
        continue
    post_dir = f'{OUT}/blog/{slug}'
    os.makedirs(post_dir, exist_ok=True)

    body = clean_wp(post['content'])

    prev_post = posts[i+1] if i+1 < len(posts) else None
    next_post = posts[i-1] if i > 0 else None

    nav_parts = []
    if prev_post:
        ps = slug_from_url(prev_post['link'])
        nav_parts.append(f'<a href="/blog/{ps}/">← {prev_post["title"]}</a>')
    if next_post:
        ns = slug_from_url(next_post['link'])
        nav_parts.append(f'<a href="/blog/{ns}/">{next_post["title"]} →</a>')
    nav_html = f'<div class="post-nav">{chr(10).join(nav_parts)}</div>' if nav_parts else ''

    post_content = f"""
<div class="post-header">
  <h1>{post['title']}</h1>
  <div class="post-date">{fmt_date(post['date'])}</div>
</div>
<div class="post-body">
{body}
</div>
{nav_html}
<div style="margin-top:3rem;padding-top:1.5rem;border-top:1px solid #f0f0f0">
  <a href="/blog/" style="font-family:-apple-system,sans-serif;font-size:.85rem;color:#555;text-decoration:none">← All posts</a>
</div>
"""
    with open(f'{post_dir}/index.html', 'w') as f:
        f.write(html_page(f'{post["title"]} — Tyler Hogge', post_content))

print(f"✓ {len(posts)} post pages")

# ── INVESTMENTS ───────────────────────────────────────────────────────────────
inv_content = f"""
<div class="page-header"><h1>Investments</h1></div>
<div class="page-body">
  <p><a href="https://kindlingcapital.notion.site/kindlingcapital/Kindling-Capital-a1da3c6d0a6d47e6b1cca9e1cad185cb" target="_blank" rel="noopener">Here's the link to Kindling Capital, my $500k fund with about 30 angel investments.</a></p>
</div>
"""
with open(f'{OUT}/investments/index.html', 'w') as f:
    f.write(html_page('Investments — Tyler Hogge', inv_content, '/investments/'))
print("✓ investments/index.html")

# ── PODCAST ──────────────────────────────────────────────────────────────────
podcast_content = """
<div class="page-header"><h1>Podcast</h1></div>
<div class="page-body">
  <p>The <a href="http://www.investoroperator.io" target="_blank" rel="noopener">IO Podcast</a> — a monthly conversation with the world's best investors and operators.</p>
  <p><a href="https://www.investoroperator.io/" target="_blank" rel="noopener">Listen at investoroperator.io →</a></p>
</div>
"""
with open(f'{OUT}/podcast/index.html', 'w') as f:
    f.write(html_page('Podcast — Tyler Hogge', podcast_content, '/podcast/'))
print("✓ podcast/index.html")

# ── QUOTES ────────────────────────────────────────────────────────────────────
os.makedirs(f'{OUT}/quotes', exist_ok=True)
quotes_raw = clean_wp(pages.get('Quotes', {}).get('content', ''))
quotes_content = f"""
<div class="page-header"><h1>Quotes</h1></div>
<div class="page-body">
{quotes_raw}
</div>
"""
with open(f'{OUT}/quotes/index.html', 'w') as f:
    f.write(html_page('Quotes — Tyler Hogge', quotes_content))
print("✓ quotes/index.html")

# ── NETLIFY CONFIG ────────────────────────────────────────────────────────────
netlify_toml = """[build]
  publish = "."

[[redirects]]
  from = "/*"
  to = "/index.html"
  status = 404
"""
with open(f'{OUT}/netlify.toml', 'w') as f:
    f.write(netlify_toml)
print("✓ netlify.toml")

print(f"\n✅ Site built successfully in {OUT}")
print(f"   - 1 home page")
print(f"   - 1 blog index")
print(f"   - {len(posts)} blog posts")
print(f"   - investments, podcast, quotes pages")
