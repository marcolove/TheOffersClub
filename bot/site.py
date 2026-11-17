"""Genera il sito statico (cartella public/) ottimizzato per Google."""
import html
import json
import os
import re
import shutil
from datetime import datetime, timezone

import config

ROOT = os.path.dirname(os.path.dirname(__file__))
OUT = os.path.join(ROOT, "public")
GUIDES = os.path.join(ROOT, "content", "guide")
e = html.escape


def eur(x):
    return f"{x:,.2f} €".replace(",", "X").replace(".", ",").replace("X", ".")


def page(title, desc, body, canonical, site_url):
    nav = "".join(f'<a href="{site_url}/{n["slug"]}/">{n["emoji"]} {e(n["name"])}</a>'
                  for n in config.NICHES.values())
    nav += f'<a href="{site_url}/guide/">📚 Guide</a>'
    return f"""<!doctype html><html lang="it"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{e(title)}</title><meta name="description" content="{e(desc)}">
<link rel="canonical" href="{canonical}"><link rel="stylesheet" href="{site_url}/style.css">
<meta property="og:title" content="{e(title)}"><meta property="og:description" content="{e(desc)}">
</head><body><header><a class="logo" href="{site_url}/">{e(config.BRAND)}</a><nav>{nav}</nav></header>
<main>{body}</main><footer><p>{e(config.DISCLOSURE)}</p>
<p>© {datetime.now().year} {e(config.BRAND)}</p></footer></body></html>"""


def join_box(niche=None):
    if niche:
        link = f"https://t.me/{niche['channel'].lstrip('@')}"
        txt = f"Ricevi le offerte {e(niche['name'])} in tempo reale su Telegram"
    else:
        link = f"https://t.me/{config.HUB['channel'].lstrip('@')}"
        txt = "Ricevi le migliori offerte in tempo reale su Telegram"
    extra = ""
    if config.WHATSAPP_CHANNEL_LINK:
        extra = f' <a class="btn wa" href="{config.WHATSAPP_CHANNEL_LINK}" rel="nofollow">Canale WhatsApp</a>'
    return f'<div class="join"><p>{txt}</p><a class="btn" href="{link}">Unisciti gratis</a>{extra}</div>'


def card(o):
    img = f'<img loading="lazy" src="{e(o["image"])}" alt="{e(o["title"][:80])}">' if o.get("image") else ""
    price = ""
    if o.get("price"):
        price = f'<span class="p">{eur(o["price"])}</span>'
        if o.get("old_price") and o["old_price"] > o["price"]:
            price += f' <s>{eur(o["old_price"])}</s>'
        if o.get("discount"):
            price += f' <span class="d">-{o["discount"]}%</span>'
    seen = o.get("seen", "")[:16].replace("T", " ")
    note = f'<p class="n">{e(o["note"])}</p>' if o.get("note") else ""
    stamp = f'<p class="t">Prezzo rilevato il {seen} UTC, può essere cambiato</p>' if price else ""
    if o.get("price_expired"):          # prezzo Amazon API più vecchio di 24 ore: non si mostra
        stamp = '<p class="t">Controlla il prezzo aggiornato su Amazon</p>'
    return (f'<article class="card">{img}<h3>{e(o["title"][:120])}</h3>{note}<p>{price}</p>{stamp}'
            f'<a class="btn" rel="sponsored nofollow" href="{e(o["url"])}">Vedi offerta</a></article>')


def md_to_html(md):
    """Mini convertitore Markdown (titoli, liste, grassetto, link, paragrafi)."""
    out, in_list = [], False
    for line in md.splitlines():
        s = line.strip()
        s_html = e(s)
        s_html = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", s_html)
        s_html = re.sub(r"\[(.+?)\]\((.+?)\)", r'<a href="\2" rel="sponsored nofollow">\1</a>', s_html)
        if s.startswith(("- ", "* ")):
            if not in_list:
                out.append("<ul>"); in_list = True
            out.append(f"<li>{s_html[2:]}</li>"); continue
        if in_list:
            out.append("</ul>"); in_list = False
        if s.startswith("### "):
            out.append(f"<h3>{s_html[4:]}</h3>")
        elif s.startswith("## "):
            out.append(f"<h2>{s_html[3:]}</h2>")
        elif s.startswith("# "):
            out.append(f"<h1>{s_html[2:]}</h1>")
        elif s:
            out.append(f"<p>{s_html}</p>")
    if in_list:
        out.append("</ul>")
    return "\n".join(out)


def write(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


def build(history, site_url, tag=""):
    site_url = site_url.rstrip("/")
    if os.path.exists(OUT):
        shutil.rmtree(OUT)
    os.makedirs(OUT)
    shutil.copy(os.path.join(ROOT, "site_assets", "style.css"), os.path.join(OUT, "style.css"))
    urls = [f"{site_url}/"]
    today = datetime.now(timezone.utc).strftime("%d/%m/%Y")

    # Home
    blocks = []
    for nid, n in config.NICHES.items():
        offers = [o for o in history if o["niche"] == nid][:6]
        cards = "".join(card(o) for o in offers) or "<p>Nuove offerte in arrivo.</p>"
        blocks.append(f'<section><h2><a href="{site_url}/{n["slug"]}/">{n["emoji"]} {e(n["name"])}</a></h2>'
                      f'<div class="grid">{cards}</div>'
                      f'<p><a href="{site_url}/{n["slug"]}/">Tutte le offerte {e(n["name"])} →</a></p></section>')
    body = (f"<h1>Le migliori offerte di oggi ({today})</h1><p>{e(config.SITE_DESCRIPTION)}</p>"
            + join_box() + "".join(blocks))
    write(os.path.join(OUT, "index.html"), page(config.SITE_TITLE, config.SITE_DESCRIPTION, body,
                                                f"{site_url}/", site_url))

    # Pagine nicchia
    for nid, n in config.NICHES.items():
        offers = [o for o in history if o["niche"] == nid][:config.SITE_OFFERS_PER_PAGE]
        cards = "".join(card(o) for o in offers) or "<p>Nuove offerte in arrivo.</p>"
        body = (f"<h1>{e(n['seo_title'])} – {today}</h1><p>{e(n['seo_intro'])}</p>"
                + join_box(n) + f'<div class="grid">{cards}</div>' + join_box(n))
        url = f"{site_url}/{n['slug']}/"
        write(os.path.join(OUT, n["slug"], "index.html"),
              page(f"{n['seo_title']} | {config.BRAND}", n["seo_intro"], body, url, site_url))
        urls.append(url)

    # Guide (articoli evergreen in content/guide/*.md)
    items = []
    if os.path.isdir(GUIDES):
        for fn in sorted(os.listdir(GUIDES)):
            if not fn.endswith(".md"):
                continue
            md = open(os.path.join(GUIDES, fn), encoding="utf-8").read().replace("{{TAG}}", tag)
            title = next((l[2:].strip() for l in md.splitlines() if l.startswith("# ")), fn[:-3])
            slug = fn[:-3]
            first_p = next((l.strip() for l in md.splitlines() if l.strip() and not l.startswith("#")), "")
            body = md_to_html(md) + join_box()
            url = f"{site_url}/guide/{slug}/"
            write(os.path.join(OUT, "guide", slug, "index.html"),
                  page(f"{title} | {config.BRAND}", first_p[:155], body, url, site_url))
            items.append(f'<li><a href="{url}">{e(title)}</a></li>')
            urls.append(url)
    write(os.path.join(OUT, "guide", "index.html"),
          page(f"Guide all'acquisto | {config.BRAND}", "Guide e confronti per scegliere il prodotto giusto.",
               f"<h1>Guide all'acquisto</h1><ul>{''.join(items)}</ul>", f"{site_url}/guide/", site_url))
    urls.append(f"{site_url}/guide/")

    # Sitemap, robots, dati
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    sm = "".join(f"<url><loc>{u}</loc><lastmod>{now}</lastmod></url>" for u in urls)
    write(os.path.join(OUT, "sitemap.xml"),
          f'<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{sm}</urlset>')
    write(os.path.join(OUT, "robots.txt"), f"User-agent: *\nAllow: /\nSitemap: {site_url}/sitemap.xml\n")
    gsc = os.getenv("GOOGLE_VERIFICATION_FILE", "")      # es. google1234abcd.html
    if gsc:
        write(os.path.join(OUT, gsc), f"google-site-verification: {gsc}")
    write(os.path.join(OUT, ".nojekyll"), "")
    print(f"[sito] generate {len(urls)} pagine in public/")
