#!/usr/bin/env python3
"""
Generate the static mynd marketing site from config/<slug>/product.yaml.

Output: ops/deploy/vercel/site/  (index.html + one page per product)

This is the Vercel-hostable slice of the platform: pure static branding pages,
no backend. The app itself (chat, settings, API) runs on the EKS/VM deployment;
each product page's CTA links to the app origin (MYND_APP_ORIGIN, default
https://ai.myndlabs.tech).

Usage:
    python3 ops/deploy/vercel/generate_site.py
"""

from __future__ import annotations

import html
import os
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[3]
CONFIG_DIR = REPO_ROOT / "config"
OUT_DIR = Path(__file__).resolve().parent / "site"
APP_ORIGIN = os.environ.get("MYND_APP_ORIGIN", "https://ai.myndlabs.tech")

BASE_CSS = """
:root { --ink:#111827; --muted:#6b7280; --bg:#ffffff; --tint:#f3f4f6; --border:#e5e7eb; }
@media (prefers-color-scheme: dark) {
  :root { --ink:#f9fafb; --muted:#9ca3af; --bg:#0b0f19; --tint:#151b2b; --border:#252d40; }
}
* { box-sizing:border-box; margin:0; }
body { font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Inter,Roboto,sans-serif;
       color:var(--ink); background:var(--bg); line-height:1.6; }
.wrap { max-width:960px; margin:0 auto; padding:48px 24px; }
header.site { display:flex; align-items:center; justify-content:space-between; }
a { color:inherit; }
.brand { font-weight:700; font-size:18px; text-decoration:none; }
.badge { display:inline-block; padding:4px 14px; border-radius:999px; color:#fff;
         font-size:14px; font-weight:600; }
h1 { font-size:clamp(28px,5vw,44px); line-height:1.15; margin:16px 0 12px; }
p.lead { color:var(--muted); font-size:18px; max-width:640px; }
.cta { display:inline-block; margin-top:24px; padding:12px 22px; border-radius:10px;
       color:#fff; font-weight:600; text-decoration:none; }
.cta.secondary { background:transparent; color:var(--ink); border:1px solid var(--border); }
.grid { display:grid; grid-template-columns:repeat(auto-fill,minmax(260px,1fr));
        gap:16px; margin-top:40px; }
.card { border:1px solid var(--border); background:var(--tint); border-radius:14px;
        padding:20px; text-decoration:none; display:block; }
.card h3 { margin-bottom:6px; }
.card p { color:var(--muted); font-size:14px; }
.chips { display:flex; flex-wrap:wrap; gap:8px; margin-top:28px; }
.chip { border:1px solid var(--border); border-radius:8px; padding:4px 12px;
        font-size:13px; color:var(--muted); }
section { margin-top:44px; }
h2 { font-size:20px; margin-bottom:12px; }
footer { margin-top:64px; padding-top:24px; border-top:1px solid var(--border);
         color:var(--muted); font-size:14px; }
"""


def load_products() -> list[dict]:
    products = []
    for pdir in sorted(CONFIG_DIR.iterdir()):
        pfile = pdir / "product.yaml"
        if pdir.is_dir() and pfile.exists():
            data = yaml.safe_load(pfile.read_text()) or {}
            if data.get("slug"):
                products.append(data)
    return products


def page(title: str, body: str) -> str:
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(title)}</title>
<style>{BASE_CSS}</style>
</head>
<body><div class="wrap">{body}</div></body>
</html>
"""


def product_page(p: dict) -> str:
    e = html.escape
    color = p.get("branding", {}).get("primary_color", "#2563EB")
    tagline = p.get("branding", {}).get("marketing_tagline", "")
    slug = p["slug"]
    connectors = "".join(
        f'<span class="chip">{e(c)}</span>' for c in p.get("enabled_connectors", [])
    )
    features = "".join(
        f'<span class="chip">{e(k.replace("_", " "))}</span>'
        for k, v in (p.get("features") or {}).items()
        if v
    )
    body = f"""
<header class="site">
  <a class="brand" href="./index.html">mynd</a>
  <a href="{e(APP_ORIGIN)}/{e(slug)}">Open app →</a>
</header>
<main>
  <section>
    <span class="badge" style="background:{e(color)}">{e(p.get("name", slug))}</span>
    <h1>{e(tagline)}</h1>
    <p class="lead">{e(p.get("description", ""))}</p>
    <a class="cta" style="background:{e(color)}" href="{e(APP_ORIGIN)}/{e(slug)}/app">Open {e(p.get("name", slug))}</a>
    <a class="cta secondary" href="./index.html">All products</a>
  </section>
  <section>
    <h2>Capabilities</h2>
    <div class="chips">{features or '<span class="chip">chat</span>'}</div>
  </section>
  <section>
    <h2>Connects to</h2>
    <div class="chips">{connectors}</div>
  </section>
</main>
<footer>© Mynd Labs · <a href="https://myndlabs.tech">myndlabs.tech</a></footer>
"""
    return page(f'{p.get("name", slug)} — mynd', body)


def index_page(products: list[dict]) -> str:
    e = html.escape
    cards = "".join(
        f"""<a class="card" href="./{e(p["slug"])}.html">
  <span class="badge" style="background:{e(p.get("branding", {}).get("primary_color", "#2563EB"))}">{e(p["slug"])}</span>
  <h3>{e(p.get("name", p["slug"]))}</h3>
  <p>{e(p.get("description", ""))}</p>
</a>"""
        for p in products
    )
    body = f"""
<header class="site">
  <a class="brand" href="./index.html">mynd</a>
  <a href="{e(APP_ORIGIN)}">Open app →</a>
</header>
<main>
  <section>
    <h1>One AI platform.<br>Every team's copilot.</h1>
    <p class="lead">mynd Core serves a family of vertical AI products — engineering,
    compliance, sales, support, people, and SRE — from one shared platform with
    shared login and per-product isolation.</p>
    <a class="cta" style="background:#2563EB" href="{e(APP_ORIGIN)}">Open the app</a>
  </section>
  <div class="grid">{cards}</div>
</main>
<footer>© Mynd Labs · <a href="https://myndlabs.tech">myndlabs.tech</a></footer>
"""
    return page("mynd — AI copilots for every team", body)


def main() -> None:
    products = load_products()
    if not products:
        raise SystemExit(f"No products found under {CONFIG_DIR}")
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "index.html").write_text(index_page(products))
    for p in products:
        (OUT_DIR / f"{p['slug']}.html").write_text(product_page(p))
    print(f"Generated {1 + len(products)} pages into {OUT_DIR}")
    for p in products:
        print(f"  /{p['slug']}.html  <- {p.get('name')}")


if __name__ == "__main__":
    main()
