#!/usr/bin/env python3
"""
DataDomine — Article Restyler
==============================
Reads every HTML file in Website/Blog/, strips the old design,
and rewrites each file with the DataDomine visual identity.

Usage (run from the repo root, i.e. the folder that contains Website/):
    python3 restyle_articles.py

Output goes to Website/Blog/restyled/ so you can diff before committing.
To overwrite in-place instead, change OUTPUT_DIR to equal INPUT_DIR.
"""

import os
import re
from pathlib import Path
from bs4 import BeautifulSoup

# ── Paths ─────────────────────────────────────────────────────────────────────
# Run the script from the repo root (the folder that contains "Website/").
SCRIPT_DIR  = Path(__file__).parent
INPUT_DIR   = SCRIPT_DIR / "Website" / "Blog"
OUTPUT_DIR  = SCRIPT_DIR / "Website" / "Blog" / "restyled"

# Relative path from Website/Blog/ up to the root where datadomine.css lives.
# If you move the Blog folder, adjust this.
ROOT        = "../../"

# ── Category → DataDomine track mapping ───────────────────────────────────────
TRACK_MAP = {
    "curriculum design":       "practice-enablement",
    "learner psychology":      "practice-enablement",
    "learning measurement":    "practice-enablement",
    "applied machine learning":"ml-engineering",
    "multi-agent systems":     "architecture",
    "agent architecture":      "architecture",
    "ai governance":           "architecture",
    "eu ai act":               "architecture",
    "zero-trust":              "architecture",
    "security architecture":   "architecture",
    "gcp infrastructure":      "architecture",
    "supply chain ai":         "architecture",
    "mlops":                   "architecture",
    "business architecture":   "architecture",
    "architecture":            "architecture",
    "design thinking":         "architecture",
    "togaf":                   "architecture",
    "memory systems":          "ml-engineering",
    "google adk":              "architecture",
}

TRACK_LABELS = {
    "architecture":         "Architecture",
    "ml-engineering":       "ML Engineering",
    "practice-enablement":  "Practice Enablement",
}

def category_to_track(raw_category: str) -> tuple[str, str]:
    """Return (track_slug, track_label) from a raw category string."""
    # Category may contain multiple tags separated by · or ,
    parts = re.split(r"[·,]", raw_category)
    for part in parts:
        key = part.strip().lower()
        if key in TRACK_MAP:
            slug  = TRACK_MAP[key]
            label = TRACK_LABELS[slug]
            return slug, label
    # Fallback
    return "architecture", "Architecture"


def extract_article_data(soup: BeautifulSoup, filename: str) -> dict:
    """Pull the key fields out of the old HTML."""
    data = {}

    # Title — from <title> tag, strip " | Siddharth …" suffix
    raw_title = soup.find("title")
    data["page_title"] = re.sub(r"\s*\|.*$", "", raw_title.get_text()).strip() if raw_title else filename

    hero = soup.find("div", class_="hero")

    # Category
    cat_el = hero.find("span", class_="category") if hero else None
    raw_category = cat_el.get_text(strip=True) if cat_el else "Architecture"
    data["raw_category"] = raw_category
    data["track_slug"], data["track_label"] = category_to_track(raw_category)

    # H1
    h1 = hero.find("h1") if hero else soup.find("h1")
    data["h1"] = h1.decode_contents().strip() if h1 else data["page_title"]

    # Deck / subtitle
    deck = hero.find("p", class_="deck") if hero else None
    data["deck"] = deck.decode_contents().strip() if deck else ""

    # Meta line (author · date · read time)
    meta = hero.find("span", class_="meta") if hero else None
    if meta:
        raw_meta = meta.get_text()
        # Replace Potukuchi → Rao everywhere
        raw_meta = raw_meta.replace("Potukuchi", "Rao")
        # Parse out the three parts
        parts = [p.strip() for p in re.split(r"·", raw_meta)]
        data["author"]    = parts[0] if len(parts) > 0 else "Siddharth Rao"
        data["date"]      = parts[1] if len(parts) > 1 else ""
        data["read_time"] = parts[2] if len(parts) > 2 else ""
    else:
        data["author"]    = "Siddharth Rao"
        data["date"]      = ""
        data["read_time"] = ""

    # Article body — everything inside article-wrap
    wrap = soup.find("div", class_="article-wrap")
    if wrap:
        body_html = wrap.decode_contents().strip()
    else:
        # Fallback: grab everything after the hero
        body_html = ""

    # Replace Potukuchi → Rao in body
    body_html = body_html.replace("Potukuchi", "Rao")

    # Normalise internal elements to DataDomine equivalents:
    # .section-rule → <hr class="article-rule">
    body_html = re.sub(
        r'<div\s+class="section-rule"[^>]*>\s*</div>',
        '<hr class="article-rule">',
        body_html
    )
    # .callout label → styled aside
    body_html = re.sub(
        r'<div\s+class="callout">(.*?)</div>',
        lambda m: '<aside class="article-callout">' + m.group(1) + '</aside>',
        body_html, flags=re.DOTALL
    )
    body_html = re.sub(
        r'<div\s+class="label">(.*?)</div>',
        r'<div class="callout-label">\1</div>',
        body_html
    )
    # .key-point → aside
    body_html = re.sub(
        r'<div\s+class="key-point">(.*?)</div>',
        lambda m: '<aside class="article-callout">' + m.group(1) + '</aside>',
        body_html, flags=re.DOTALL
    )
    # .pull-quote → blockquote
    body_html = re.sub(
        r'<div\s+class="pull-quote">(.*?)</div>',
        lambda m: '<blockquote class="article-blockquote">' + m.group(1) + '</blockquote>',
        body_html, flags=re.DOTALL
    )
    # Existing blockquotes → article-blockquote class
    body_html = re.sub(r'<blockquote(?!\s+class)', '<blockquote class="article-blockquote"', body_html)

    data["body_html"] = body_html
    return data


def build_html(d: dict) -> str:
    """Assemble the complete DataDomine-styled article HTML."""

    r = ROOT  # relative path to root

    # Deck line — only render if present
    deck_html = ""
    if d["deck"]:
        deck_html = f'        <p class="article-hero__deck">{d["deck"]}</p>'

    # Meta items
    meta_parts = []
    if d["track_label"]:
        meta_parts.append(f'<span class="article-hero__track">{d["track_label"]}</span>')
    if d["date"]:
        meta_parts.append(f'<span class="article-hero__date">{d["date"]}</span>')
    if d["read_time"]:
        meta_parts.append(f'<span class="article-hero__read-time">{d["read_time"]}</span>')
    meta_html = "\n          ".join(meta_parts)

    return f"""<!DOCTYPE html>
<html lang="en-GB">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{d["page_title"]} — DataDomine Field Notes</title>
  <meta name="description" content="{re.sub(r'<[^>]+>', '', d['deck'])[:160]}">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Serif:ital,wght@0,300;0,400;0,700;1,300&family=Inter:wght@300;400;500&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="{r}datadomine.css">
  <style>
    /* ── Tokens ── */
    :root {{
      --deep-ink:   #0D1117;
      --arch-white: #F8F6F1;
      --slate:      #64748B;
      --amber:      #D97706;
      --nav-height: 64px;
      --article-max: 720px;
    }}

    *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}

    html, body {{ height: 100%; }}

    body {{
      font-family: 'Inter', sans-serif;
      background: var(--arch-white);
      color: var(--deep-ink);
      -webkit-font-smoothing: antialiased;
      display: flex;
      flex-direction: column;
      min-height: 100vh;
    }}

    /* ── Navigation ── */
    .site-nav {{
      position: fixed;
      top: 0; left: 0; right: 0;
      height: var(--nav-height);
      background: var(--arch-white);
      border-bottom: 1px solid rgba(13,17,23,0.08);
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 0 48px;
      z-index: 100;
    }}
    .nav-wordmark {{
      display: flex;
      align-items: baseline;
      text-decoration: none;
      line-height: 1;
    }}
    .nav-wordmark .word-data {{
      font-family: 'IBM Plex Serif', Georgia, serif;
      font-weight: 300;
      font-size: 18px;
      color: var(--deep-ink);
      letter-spacing: -0.01em;
    }}
    .nav-wordmark .word-domine {{
      font-family: 'IBM Plex Serif', Georgia, serif;
      font-weight: 700;
      font-size: 18px;
      color: var(--deep-ink);
      letter-spacing: -0.01em;
    }}
    .nav-wordmark .word-domine .initial-d {{ color: var(--amber); }}
    .nav-links {{
      display: flex;
      align-items: center;
      gap: 36px;
      list-style: none;
    }}
    .nav-links a {{
      font-family: 'Inter', sans-serif;
      font-weight: 400;
      font-size: 14px;
      color: var(--slate);
      text-decoration: none;
      letter-spacing: 0.01em;
      transition: color 0.15s ease;
    }}
    .nav-links a:hover {{ color: var(--deep-ink); }}
    .nav-links a.active {{
      color: var(--deep-ink);
      font-weight: 500;
    }}

    /* ── Main ── */
    .site-main {{
      flex: 1;
      padding-top: var(--nav-height);
    }}

    /* ── Back bar ── */
    .back-bar {{
      padding: 20px 48px;
      border-bottom: 1px solid rgba(13,17,23,0.08);
    }}
    .back-bar a {{
      font-family: 'Inter', sans-serif;
      font-weight: 400;
      font-size: 13px;
      color: var(--slate);
      text-decoration: none;
      display: inline-flex;
      align-items: center;
      gap: 8px;
      letter-spacing: 0.01em;
      transition: color 0.15s ease;
    }}
    .back-bar a:hover {{ color: var(--deep-ink); }}
    .back-bar a::before {{
      content: '←';
      font-size: 14px;
    }}

    /* ── Article Hero ── */
    .article-hero {{
      padding: 64px 48px 56px;
      border-bottom: 1px solid rgba(13,17,23,0.08);
      max-width: calc(var(--article-max) + 96px);
    }}
    .article-hero__eyebrow {{
      display: flex;
      align-items: center;
      gap: 10px;
      margin-bottom: 24px;
    }}
    .article-hero__eyebrow-rule {{
      width: 24px;
      height: 2px;
      background: var(--amber);
      flex-shrink: 0;
    }}
    .article-hero__track-label {{
      font-family: 'Inter', sans-serif;
      font-weight: 500;
      font-size: 11px;
      letter-spacing: 0.18em;
      text-transform: uppercase;
      color: var(--slate);
    }}
    .article-hero__title {{
      font-family: 'IBM Plex Serif', Georgia, serif;
      font-weight: 700;
      font-size: clamp(28px, 4vw, 46px);
      line-height: 1.1;
      letter-spacing: -0.02em;
      color: var(--deep-ink);
      margin-bottom: 20px;
    }}
    .article-hero__deck {{
      font-family: 'IBM Plex Serif', Georgia, serif;
      font-weight: 300;
      font-style: italic;
      font-size: 18px;
      line-height: 1.65;
      color: var(--deep-ink);
      max-width: var(--article-max);
      margin-bottom: 28px;
      opacity: 0.8;
    }}
    .article-hero__meta {{
      display: flex;
      align-items: center;
      flex-wrap: wrap;
      gap: 8px 20px;
    }}
    .article-hero__track {{
      font-family: 'Inter', sans-serif;
      font-weight: 500;
      font-size: 11px;
      letter-spacing: 0.14em;
      text-transform: uppercase;
      color: var(--amber);
    }}
    .article-hero__date,
    .article-hero__read-time {{
      font-family: 'Inter', sans-serif;
      font-weight: 300;
      font-size: 13px;
      color: var(--slate);
    }}
    .article-hero__date::before,
    .article-hero__read-time::before {{
      content: '·';
      margin-right: 20px;
      color: rgba(13,17,23,0.2);
    }}

    /* ── Article Body ── */
    .article-body {{
      padding: 56px 48px 80px;
      max-width: calc(var(--article-max) + 96px);
    }}

    /* Typography */
    .article-body p {{
      font-family: 'IBM Plex Serif', Georgia, serif;
      font-weight: 300;
      font-size: 17px;
      line-height: 1.85;
      color: var(--deep-ink);
      margin-bottom: 24px;
    }}
    .article-body h2 {{
      font-family: 'IBM Plex Serif', Georgia, serif;
      font-weight: 700;
      font-size: 22px;
      line-height: 1.25;
      letter-spacing: -0.01em;
      color: var(--deep-ink);
      margin-top: 52px;
      margin-bottom: 20px;
    }}
    .article-body h3 {{
      font-family: 'IBM Plex Serif', Georgia, serif;
      font-weight: 400;
      font-size: 18px;
      line-height: 1.3;
      color: var(--deep-ink);
      margin-top: 36px;
      margin-bottom: 16px;
    }}
    .article-body em {{
      font-style: italic;
    }}
    .article-body strong {{
      font-weight: 600;
    }}
    .article-body a {{
      color: var(--deep-ink);
      text-decoration: underline;
      text-underline-offset: 3px;
      text-decoration-color: rgba(13,17,23,0.3);
      transition: text-decoration-color 0.15s ease;
    }}
    .article-body a:hover {{
      text-decoration-color: var(--amber);
    }}

    /* Lists */
    .article-body ul,
    .article-body ol {{
      font-family: 'IBM Plex Serif', Georgia, serif;
      font-weight: 300;
      font-size: 17px;
      line-height: 1.8;
      color: var(--deep-ink);
      margin-bottom: 24px;
      padding-left: 24px;
    }}
    .article-body li {{
      margin-bottom: 8px;
    }}

    /* Blockquote */
    .article-body blockquote,
    .article-body .article-blockquote {{
      border-left: 3px solid var(--amber);
      margin: 40px 0;
      padding: 4px 0 4px 28px;
    }}
    .article-body blockquote p,
    .article-body .article-blockquote p {{
      font-family: 'IBM Plex Serif', Georgia, serif;
      font-weight: 300;
      font-style: italic;
      font-size: 18px;
      line-height: 1.75;
      color: var(--deep-ink);
      margin-bottom: 0;
    }}

    /* Horizontal rule */
    .article-body hr,
    .article-body .article-rule {{
      border: none;
      border-top: 1px solid rgba(13,17,23,0.1);
      margin: 48px 0;
    }}

    /* Callout / aside */
    .article-body aside,
    .article-body .article-callout {{
      background: rgba(13,17,23,0.04);
      border-left: 3px solid rgba(13,17,23,0.15);
      padding: 24px 28px;
      margin: 40px 0;
      border-radius: 0 2px 2px 0;
    }}
    .article-body .callout-label {{
      font-family: 'Inter', sans-serif;
      font-weight: 500;
      font-size: 11px;
      letter-spacing: 0.14em;
      text-transform: uppercase;
      color: var(--slate);
      margin-bottom: 10px;
    }}
    .article-body aside p,
    .article-body .article-callout p {{
      font-size: 15px;
      line-height: 1.75;
      margin-bottom: 12px;
    }}
    .article-body aside p:last-child,
    .article-body .article-callout p:last-child {{
      margin-bottom: 0;
    }}

    /* Code */
    .article-body code {{
      font-family: 'IBM Plex Mono', 'Courier New', monospace;
      font-size: 13px;
      background: rgba(13,17,23,0.06);
      padding: 2px 6px;
      border-radius: 2px;
    }}
    .article-body pre {{
      background: var(--deep-ink);
      color: var(--arch-white);
      padding: 24px 28px;
      border-radius: 2px;
      overflow-x: auto;
      margin-bottom: 28px;
      font-size: 13px;
      line-height: 1.7;
    }}
    .article-body pre code {{
      background: none;
      padding: 0;
      color: inherit;
      font-size: inherit;
    }}

    /* ── Closing CTA ── */
    .article-cta {{
      margin: 64px 0 0;
      padding-top: 48px;
      border-top: 1px solid rgba(13,17,23,0.1);
      display: flex;
      flex-direction: column;
      gap: 20px;
    }}
    .article-cta__label {{
      font-family: 'Inter', sans-serif;
      font-weight: 500;
      font-size: 11px;
      letter-spacing: 0.18em;
      text-transform: uppercase;
      color: var(--slate);
    }}
    .article-cta__text {{
      font-family: 'IBM Plex Serif', Georgia, serif;
      font-weight: 300;
      font-size: 16px;
      line-height: 1.65;
      color: var(--deep-ink);
      max-width: 480px;
    }}
    .article-cta__links {{
      display: flex;
      align-items: center;
      flex-wrap: wrap;
      gap: 12px 28px;
    }}
    .article-cta__link {{
      font-family: 'Inter', sans-serif;
      font-weight: 400;
      font-size: 14px;
      color: var(--deep-ink);
      text-decoration: none;
      border-bottom: 1px solid rgba(13,17,23,0.25);
      padding-bottom: 2px;
      transition: border-color 0.15s ease, color 0.15s ease;
    }}
    .article-cta__link:hover {{
      color: var(--amber);
      border-color: var(--amber);
    }}

    /* ── Footer ── */
    .site-footer {{
      background: var(--deep-ink);
      padding: 36px 48px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      flex-wrap: wrap;
      gap: 24px;
      margin-top: auto;
    }}
    .footer-left {{
      display: flex;
      flex-direction: column;
      gap: 6px;
    }}
    .footer-wordmark {{
      display: flex;
      align-items: baseline;
      text-decoration: none;
      line-height: 1;
    }}
    .footer-wordmark .word-data {{
      font-family: 'IBM Plex Serif', Georgia, serif;
      font-weight: 300;
      font-size: 16px;
      color: var(--arch-white);
      letter-spacing: -0.01em;
    }}
    .footer-wordmark .word-domine {{
      font-family: 'IBM Plex Serif', Georgia, serif;
      font-weight: 700;
      font-size: 16px;
      color: var(--arch-white);
      letter-spacing: -0.01em;
    }}
    .footer-wordmark .word-domine .initial-d {{ color: var(--amber); }}
    .footer-tagline {{
      font-family: 'Inter', sans-serif;
      font-weight: 300;
      font-size: 12px;
      color: rgba(248,246,241,0.4);
      letter-spacing: 0.04em;
    }}
    .footer-right {{
      display: flex;
      flex-direction: column;
      align-items: flex-end;
      gap: 12px;
    }}
    .footer-links {{
      display: flex;
      align-items: center;
      flex-wrap: wrap;
      gap: 6px 24px;
      list-style: none;
      justify-content: flex-end;
    }}
    .footer-links a {{
      font-family: 'Inter', sans-serif;
      font-weight: 300;
      font-size: 13px;
      color: rgba(248,246,241,0.55);
      text-decoration: none;
      transition: color 0.15s ease;
    }}
    .footer-links a:hover {{ color: var(--arch-white); }}
    .footer-copy {{
      font-family: 'Inter', sans-serif;
      font-weight: 300;
      font-size: 12px;
      color: rgba(248,246,241,0.3);
    }}

    /* ── Responsive ── */
    @media (max-width: 768px) {{
      .site-nav {{ padding: 0 24px; }}
      .back-bar {{ padding: 16px 24px; }}
      .article-hero {{ padding: 48px 24px 40px; }}
      .article-body {{ padding: 40px 24px 64px; }}
      .site-footer {{ padding: 32px 24px; flex-direction: column; align-items: flex-start; }}
      .footer-right {{ align-items: flex-start; }}
      .footer-links {{ justify-content: flex-start; }}
      .nav-links li:not(:last-child):not(:nth-last-child(2)) {{ display: none; }}
    }}
  </style>
</head>
<body>

  <!-- ── Navigation ── -->
  <nav class="site-nav" id="site-nav" aria-label="Site navigation">
    <a href="{r}index.html" class="nav-wordmark" aria-label="DataDomine — home">
      <svg width="14" height="36" viewBox="0 0 14 38" xmlns="http://www.w3.org/2000/svg" aria-hidden="true" style="margin-right:10px;">
        <circle cx="7" cy="7" r="7" fill="#D97706"/>
        <rect x="5.5" y="7" width="3" height="26" fill="#0D1117"/>
      </svg>
      <span class="word-data">Data</span><span class="word-domine"><span class="initial-d">D</span>omine</span>
    </a>
    <ul class="nav-links">
      <li><a href="{r}index.html">Home</a></li>
      <li><a href="{r}about.html">About</a></li>
      <li><a href="{r}framework.html">The Framework</a></li>
      <li><a href="{r}programmes.html">Programmes</a></li>
      <li><a href="{r}field-notes.html" class="active">Field Notes</a></li>
      <li><a href="{r}contact.html">Contact</a></li>
    </ul>
  </nav>

  <main class="site-main">

    <!-- ── Back bar ── -->
    <div class="back-bar">
      <a href="{r}field-notes.html">Field Notes</a>
    </div>

    <!-- ── Article Hero ── -->
    <header class="article-hero">
      <div class="article-hero__eyebrow">
        <div class="article-hero__eyebrow-rule"></div>
        <span class="article-hero__track-label">Field Notes</span>
      </div>
      <h1 class="article-hero__title">{d["h1"]}</h1>
{deck_html}
      <div class="article-hero__meta">
        {meta_html}
      </div>
    </header>

    <!-- ── Article Body ── -->
    <article class="article-body" aria-label="Article content">

{d["body_html"]}

      <!-- ── Closing CTA ── -->
      <div class="article-cta">
        <span class="article-cta__label">Continue reading</span>
        <p class="article-cta__text">These notes are published when there is something worth saying. To receive new Field Notes directly, write to hello@datadomine.com with the subject line: Field Notes.</p>
        <div class="article-cta__links">
          <a href="{r}field-notes.html" class="article-cta__link">All Field Notes</a>
          <a href="{r}programmes.html" class="article-cta__link">Programmes</a>
          <a href="{r}contact.html" class="article-cta__link">Get in touch</a>
        </div>
      </div>

    </article>

  </main>

  <!-- ── Footer ── -->
  <footer class="site-footer">
    <div class="footer-left">
      <a href="{r}index.html" class="footer-wordmark" aria-label="DataDomine — home">
        <span class="word-data">Data</span><span class="word-domine"><span class="initial-d">D</span>omine</span>
      </a>
      <span class="footer-tagline">Production-Ready. By Design.</span>
    </div>
    <div class="footer-right">
      <ul class="footer-links" aria-label="Footer navigation">
        <li><a href="{r}index.html">Home</a></li>
        <li><a href="{r}about.html">About</a></li>
        <li><a href="{r}framework.html">The Framework</a></li>
        <li><a href="{r}programmes.html">Programmes</a></li>
        <li><a href="{r}field-notes.html">Field Notes</a></li>
        <li><a href="{r}contact.html">Contact</a></li>
      </ul>
      <span class="footer-copy">&copy; <span id="footer-year"></span> DataDomine. All rights reserved.</span>
    </div>
  </footer>

  <script src="{r}datadomine.js"></script>
  <script>
    (function () {{
      var el = document.getElementById('footer-year');
      if (el) el.textContent = new Date().getFullYear();
    }}());
  </script>

</body>
</html>"""


def restyle_file(src_path: Path, out_path: Path) -> None:
    html = src_path.read_text(encoding="utf-8")
    soup = BeautifulSoup(html, "html.parser")
    data = extract_article_data(soup, src_path.stem)
    new_html = build_html(data)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(new_html, encoding="utf-8")
    print(f"  ✓  {src_path.name}  →  {out_path.relative_to(SCRIPT_DIR)}")


def main():
    if not INPUT_DIR.exists():
        print(f"\n❌  Input folder not found: {INPUT_DIR}")
        print("    Run this script from the repo root (the folder that contains Website/).\n")
        return

    files = sorted(INPUT_DIR.glob("*.html"))
    # Skip any files already in a restyled/ subfolder
    files = [f for f in files if f.parent == INPUT_DIR]

    if not files:
        print(f"\n⚠️  No HTML files found in {INPUT_DIR}\n")
        return

    print(f"\nDataDomine Article Restyler")
    print(f"Input:  {INPUT_DIR}")
    print(f"Output: {OUTPUT_DIR}")
    print(f"Files:  {len(files)}\n")

    for src in files:
        out = OUTPUT_DIR / src.name
        try:
            restyle_file(src, out)
        except Exception as e:
            print(f"  ✗  {src.name}  —  {e}")

    print(f"\nDone. {len(files)} files written to Website/Blog/restyled/\n")
    print("Review the output, then copy to Website/Blog/ when ready:")
    print("    cp Website/Blog/restyled/*.html Website/Blog/\n")


if __name__ == "__main__":
    main()
