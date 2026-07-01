#!/usr/bin/env python3
"""
Generate a static, backend-free marketing site for the mynd products from the
per-product config in /config. Output is plain HTML+CSS (no JS, no build tools),
so it deploys to Vercel as static assets with zero runtime dependencies.

    python3 ops/deploy/vercel/build_marketing.py

Output: /marketing (index + one page per product). Committed so Vercel serves it
directly with no build step.
"""

from __future__ import annotations

import html
import shutil
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[3]
CONFIG = ROOT / "config"
OUT = ROOT / "marketing"

# App base — where the real (backend-backed) app will live. Products link here.
APP_BASE = "https://ai.myndlabs.tech"

CSS = """
:root { --fg:#0b1020; --muted:#5b6472; --bg:#ffffff; --card:#f6f8fb; --border:#e6e9ef; }
* { box-sizing:border-box; }
body { margin:0; font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Inter,Roboto,Helvetica,Arial,sans-serif;
       color:var(--fg); background:var(--bg); line-height:1.5; }
a { color:inherit; text-decoration:none; }
.wrap { max-width:1040px; margin:0 auto; padding:48px 24px; }
.nav { display:flex; align-items:center; gap:12px; font-weight:700; }
.dot { width:12px; height:12px; border-radius:50%; }
.pill { display:inline-block; padding:6px 14px; border-radius:999px; color:#fff; font-size:14px; font-weight:600; }
h1 { font-size:44px; line-height:1.1; margin:20px 0 12px; letter-spacing:-0.02em; }
h2 { font-size:22px; margin:40px 0 12px; }
p.lead { font-size:19px; color:var(--muted); max-width:680px; }
.grid { display:grid; grid-template-columns:repeat(auto-fill,minmax(300px,1fr)); gap:16px; margin-top:24px; }
.card { display:block; background:var(--card); border:1px solid var(--border); border-radius:16px; padding:20px;
        transition:transform .08s ease, box-shadow .08s ease; }
.card:hover { transform:translateY(-2px); box-shadow:0 8px 30px rgba(11,16,32,.08); }
.card .accent { width:36px; height:6px; border-radius:6px; margin-bottom:12px; }
.card h3 { margin:0 0 6px; font-size:18px; }
.card p { margin:0; color:var(--muted); font-size:15px; }
.tags { display:flex; flex-wrap:wrap; gap:8px; margin-top:14px; }
.tag { border:1px solid var(--border); border-radius:8px; padding:5px 10px; font-size:13px; color:var(--muted); background:#fff; }
.btn { display:inline-block; padding:12px 20px; border-radius:12px; color:#fff; font-weight:600; margin-top:24px; }
.btn.secondary { background:transparent; border:1px solid var(--border); color:var(--fg); margin-left:8px; }
.footer { margin-top:56px; padding-top:24px; border-top:1px solid var(--border); color:var(--muted); font-size:14px; }
.back { color:var(--muted); font-size:14px; }
"""


def esc(s: str) -> str:
    return html.escape(str(s), quote=True)


def load_products() -> list[dict]:
    products = []
    for d in sorted(CONFIG.iterdir()):
        pf = d / "product.yaml"
        if d.is_dir() and pf.exists():
            with pf.open() as fh:
                products.append(yaml.safe_load(fh) or {})
    return products


def page(title: str, body: str) -> str:
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)}</title>
<style>{CSS}</style></head>
<body><div class="wrap">{body}
<div class="footer">Mynd Labs · <a href="https://myndlabs.tech">myndlabs.tech</a> · one platform, many AI products</div>
</div></body></html>"""


def index_page(products: list[dict]) -> str:
    cards = []
    for p in products:
        b = p.get("branding", {}) or {}
        color = esc(b.get("primary_color", "#2563EB"))
        cards.append(f"""<a class="card" href="/{esc(p.get('slug'))}/">
  <div class="accent" style="background:{color}"></div>
  <h3>{esc(p.get('name'))}</h3>
  <p>{esc(p.get('description',''))}</p>
</a>""")
    body = f"""
<div class="nav"><span class="dot" style="background:#2563EB"></span> Mynd</div>
<h1>AI, built for the way your team works.</h1>
<p class="lead">One shared platform, many purpose-built products — engineering, compliance,
sales, support, people, and SRE. Bring your own model keys or use ours.</p>
<div class="grid">{''.join(cards)}</div>
"""
    return page("Mynd — AI products for every team", body)


def product_page(p: dict) -> str:
    b = p.get("branding", {}) or {}
    color = esc(b.get("primary_color", "#2563EB"))
    name = esc(p.get("name"))
    slug = esc(p.get("slug"))
    tagline = esc(b.get("marketing_tagline", "") or p.get("description", ""))
    desc = esc(p.get("description", ""))
    features = [k for k, v in (p.get("features", {}) or {}).items() if v]
    connectors = p.get("enabled_connectors", []) or []

    feat_html = "".join(
        f'<span class="tag">{esc(f.replace("_"," "))}</span>' for f in features
    )
    conn_html = "".join(f'<span class="tag">{esc(c)}</span>' for c in connectors)

    body = f"""
<div class="nav"><a class="back" href="/">← Mynd</a></div>
<span class="pill" style="background:{color}">{name}</span>
<h1>{tagline}</h1>
<p class="lead">{desc}</p>
<a class="btn" style="background:{color}" href="{APP_BASE}/{slug}">Open {name}</a>
<a class="btn secondary" href="{APP_BASE}/{slug}/settings/models">Bring your own model key</a>

<h2>Capabilities</h2>
<div class="tags">{feat_html or '<span class="tag">chat · agents · knowledge</span>'}</div>

<h2>Connects to</h2>
<div class="tags">{conn_html or '<span class="tag">your tools</span>'}</div>
"""
    return page(f"{p.get('name')} — Mynd", body)


def main() -> None:
    products = load_products()
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)

    (OUT / "index.html").write_text(index_page(products), encoding="utf-8")
    for p in products:
        d = OUT / str(p.get("slug"))
        d.mkdir(parents=True, exist_ok=True)
        (d / "index.html").write_text(product_page(p), encoding="utf-8")

    print(f"Generated {len(products)} product pages + index into {OUT}")


if __name__ == "__main__":
    main()
