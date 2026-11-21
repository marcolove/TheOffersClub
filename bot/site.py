"""Genera il sito statico (cartella public/).

Struttura:
  /                              home: offerte top, canali, classifiche, guide
  /<slug-canale>/                offerte del canale + classifiche e guide del canale
  /classifiche/                  elenco classifiche
  /classifiche/<slug>/           classifica (content/classifiche/*.md) + offerte attive collegate
  /guide/                        elenco guide
  /guide/<slug>/                 guida (content/guide/*.md) + offerte attive collegate
  /come-funziona/                come selezioniamo le offerte + affiliazione
  sitemap.xml, robots.txt, 404.html

I file .md possono avere un'intestazione tra due righe "---":
  titolo: I migliori trapani avvitatori economici
  descrizione: frase per Google (max ~155 caratteri)
  canale: utensili                      (id della nicchia in config.NICHES)
  cerca: trapano avvitatore, avvitatore a batteria     (parole: offerte attive e filtro classifica)
  auto: si                              (classifica compilata dal bot con la Creators API)
  amazon: trapano avvitatore batteria   (ricerca Amazon per la classifica automatica)
  prezzo_min: 30   prezzo_max: 150      (facoltativi)
  escludi: solo corpo, senza batteria   (parole che escludono un prodotto dalla classifica)
  bozza: si                             (facoltativo: pagina non pubblicata)
  prodotti:                             (facoltativo: classifica scritta a mano)
  - ASIN | Nome prodotto | Perché è in classifica
"""
import html
import json
import os
import re
import shutil
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

import config

ROOT = os.path.dirname(os.path.dirname(__file__))
OUT = os.path.join(ROOT, "public")
CONTENT = os.path.join(ROOT, "content")
ASSETS = os.path.join(ROOT, "site_assets")
DATA = os.path.join(ROOT, "data")
e = html.escape
ROME = ZoneInfo("Europe/Rome")
MIN_WORDS_INDEX = 250          # pagine editoriali più corte (e senza prodotti) restano noindex


# ------------------------------------------------------------------ utilità
def eur(x):
    return f"{x:,.2f} €".replace(",", "X").replace(".", ",").replace("X", ".")


def write(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


def load_json(name):
    try:
        return json.load(open(os.path.join(DATA, name), encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def unique(history):
    """Una sola card per prodotto: la più recente (history è già in ordine dal più nuovo)."""
    seen, out = set(), []
    for o in history:
        k = o.get("key")
        if not k or k in seen or o.get("niche") not in config.NICHES:
            continue
        seen.add(k)
        out.append(o)
    return out


def img(name, size=192):
    return f"img/{name}-{size}.webp"


def amazon_link(asin, tag):
    return f"https://www.amazon.it/dp/{asin}?tag={tag}"


def tg_link(channel):
    return f"https://t.me/{channel.lstrip('@')}"


def _num(s):
    try:
        return float(str(s).replace(",", ".")) if str(s).strip() else None
    except ValueError:
        return None


def fmt_when(iso):
    try:
        return datetime.fromisoformat(iso).astimezone(ROME).strftime("%d/%m alle %H:%M")
    except (TypeError, ValueError):
        return ""


class Prices:
    """Prezzo da mostrare: solo se rilevato nelle ultime PRICE_MAX_AGE_HOURS ore.
    Fonte: data/prices.json (aggiornato dal bot con la Creators API) o il prezzo del post."""

    def __init__(self):
        self.cache = load_json("prices.json")
        self.limit = (datetime.now(timezone.utc)
                      - timedelta(hours=getattr(config, "PRICE_MAX_AGE_HOURS", 24))).isoformat()

    def get(self, asin=None, o=None):
        c = self.cache.get(asin) if asin else None
        if c and c.get("at", "") > self.limit:
            if c.get("gone"):
                return None
            return {"price": c["price"], "old_price": c.get("old_price"),
                    "discount": c.get("discount"), "at": c["at"]}
        if o and o.get("price") and not o.get("price_expired") and o.get("seen", "") > self.limit:
            return {"price": o["price"], "old_price": o.get("old_price"),
                    "discount": o.get("discount"), "at": o.get("seen")}
        return None


# ------------------------------------------------------------------ markdown
def parse_md(text):
    """Restituisce (meta, corpo). meta["prodotti"] = lista di (asin, nome, nota)."""
    meta, body = {"prodotti": []}, text
    lines = text.splitlines()
    if lines and lines[0].strip() == "---":
        end = next((i for i in range(1, len(lines)) if lines[i].strip() == "---"), None)
        if end:
            key = None
            for l in lines[1:end]:
                s = l.strip()
                if not s or s.startswith("#"):
                    continue
                if s.startswith("- ") and key == "prodotti":
                    parts = [p.strip() for p in s[2:].split("|")]
                    if parts and re.fullmatch(r"[A-Z0-9]{10}", parts[0]):
                        parts += ["", ""]
                        meta["prodotti"].append((parts[0], parts[1], parts[2]))
                    continue
                if ":" in s:
                    key, val = s.split(":", 1)
                    key = key.strip().lower()
                    if key != "prodotti":
                        meta[key] = val.strip()
            body = "\n".join(lines[end + 1:])
    return meta, body


def inline(s, tag):
    s = e(s, quote=False)
    s = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)

    def link(m):
        url = m.group(2).replace("{{TAG}}", tag)
        rel = ' rel="sponsored nofollow noopener" target="_blank"' if "amazon." in url or "amzn" in url else ""
        return f'<a href="{e(url)}"{rel}>{m.group(1)}</a>'

    return re.sub(r"\[(.+?)\]\((.+?)\)", link, s)


def md_to_html(md, tag=""):
    """Markdown semplice: titoli ##/###, elenchi, grassetto, link, paragrafi. Il # iniziale si salta."""
    out, in_list = [], False
    for line in md.splitlines():
        s = line.strip()
        if s.startswith(("- ", "* ")):
            if not in_list:
                out.append("<ul>"); in_list = True
            out.append(f"<li>{inline(s[2:], tag)}</li>"); continue
        if in_list:
            out.append("</ul>"); in_list = False
        if s.startswith("### "):
            out.append(f"<h3>{inline(s[4:], tag)}</h3>")
        elif s.startswith("## "):
            out.append(f"<h2>{inline(s[3:], tag)}</h2>")
        elif s.startswith("# "):
            continue
        elif s:
            out.append(f"<p>{inline(s, tag)}</p>")
    if in_list:
        out.append("</ul>")
    return "\n".join(out)


def md_title(md, fallback):
    for l in md.splitlines():
        s = l.strip()
        if s.startswith("# "):
            return s[2:].strip()
        if s.startswith("## "):
            return s[3:].strip()
    return fallback


def first_paragraph(md):
    for l in md.splitlines():
        s = l.strip()
        if s and not s.startswith(("#", "-", "*")):
            return re.sub(r"\[(.+?)\]\(.+?\)", r"\1", s).replace("**", "")
    return ""


def _words(s):
    return [w.strip().lower() for w in (s or "").split(",") if w.strip()]


def load_articles(kind, tag=""):
    """Legge content/<kind>/*.md e restituisce le pagine pubblicabili."""
    folder = os.path.join(CONTENT, kind)
    items = []
    if not os.path.isdir(folder):
        return items
    for fn in sorted(os.listdir(folder)):
        if not fn.endswith(".md") or fn.startswith("_"):
            continue
        raw = open(os.path.join(folder, fn), encoding="utf-8").read()
        meta, body = parse_md(raw)
        if meta.get("bozza", "").lower() in ("si", "sì", "true", "1"):
            continue
        slug = fn[:-3]
        title = meta.get("titolo") or md_title(body, slug.replace("-", " ").capitalize())
        niche = meta.get("canale", "")
        items.append({
            "kind": kind, "slug": slug, "title": title, "body": body,
            "desc": (meta.get("descrizione") or first_paragraph(body))[:158],
            "niche": niche if niche in config.NICHES else "",
            "search": _words(meta.get("cerca")),
            "exclude": _words(meta.get("escludi")),
            "auto": meta.get("auto", "").lower() in ("si", "sì", "true", "1"),
            "amazon": meta.get("amazon", ""),
            "min_price": _num(meta.get("prezzo_min", "")),
            "max_price": _num(meta.get("prezzo_max", "")),
            "products": meta["prodotti"],
            "words": len(re.findall(r"\w+", body)),
            "mtime": datetime.fromtimestamp(os.path.getmtime(os.path.join(folder, fn)), timezone.utc),
        })
    return items


# ------------------------------------------------------------------ layout
class Site:
    def __init__(self, site_url, tag):
        self.url = site_url.rstrip("/")
        self.tag = tag
        self.sitemap = []               # (url, lastmod)
        self.prices = Prices()

    def abs(self, path):
        return f"{self.url}/{path.lstrip('/')}"

    def head_nav(self, active=""):
        items = []
        for nid, n in config.NICHES.items():
            cls = ' class="on"' if nid == active else ""
            items.append(f'<a{cls} style="--c:{n["color"]}" href="{self.abs(n["slug"] + "/")}">'
                         f'<img src="{self.abs(img(n["logo"]))}" alt="" width="26" height="26">'
                         f'<span>{e(n["name"])}</span></a>')
        for key, label in (("classifiche", "🏆 Classifiche"), ("guide", "📚 Guide")):
            cls = ' class="on"' if active == key else ""
            items.append(f'<a{cls} href="{self.abs(key + "/")}"><span>{label}</span></a>')
        return "".join(items)

    def page(self, path, title, desc, body, active="", color=None, crumbs=None,
             index=True, schema=None, lastmod=None):
        url = self.abs(path)
        color = color or config.HUB["color"]
        indexable = getattr(config, "SITE_INDEXABLE", False) and index
        robots = "index,follow" if indexable else "noindex,follow"
        ld = []
        if crumbs:
            ld.append({"@context": "https://schema.org", "@type": "BreadcrumbList",
                       "itemListElement": [{"@type": "ListItem", "position": i + 1, "name": c[0],
                                            "item": self.abs(c[1])} for i, c in enumerate(crumbs)]})
        if schema:
            ld.append(schema)
        ld_html = "".join(f'<script type="application/ld+json">{json.dumps(x, ensure_ascii=False)}</script>'
                          for x in ld)
        bc = ""
        if crumbs:
            parts = [f'<a href="{self.abs(c[1])}">{e(c[0])}</a>' for c in crumbs[:-1]]
            parts.append(f"<span>{e(crumbs[-1][0])}</span>")
            bc = f'<nav class="crumbs" aria-label="Percorso">{" › ".join(parts)}</nav>'
        if index and path != "404.html":
            self.sitemap.append((url, (lastmod or datetime.now(timezone.utc)).strftime("%Y-%m-%d")))
        hub = config.HUB
        return f"""<!doctype html><html lang="it"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{e(title)}</title><meta name="description" content="{e(desc)}">
<meta name="robots" content="{robots}"><link rel="canonical" href="{url}">
<meta name="theme-color" content="#0a0614">
<meta property="og:type" content="website"><meta property="og:site_name" content="{e(config.BRAND)}">
<meta property="og:title" content="{e(title)}"><meta property="og:description" content="{e(desc)}">
<meta property="og:url" content="{url}"><meta property="og:image" content="{self.abs('img/og.jpg')}">
<meta name="twitter:card" content="summary_large_image">
<link rel="icon" href="{self.abs('img/favicon.png')}"><link rel="apple-touch-icon" href="{self.abs('img/apple-touch-icon.png')}">
<link rel="stylesheet" href="{self.abs('style.css')}">{ld_html}
</head><body style="--accent:{color}">
<header class="top"><div class="wrap top-in">
<a class="brand" href="{self.abs('')}"><img src="{self.abs(img(hub['logo']))}" alt="{e(config.BRAND)}" width="42" height="42">
<span>The<b>Offers</b>Club</span></a>
<a class="btn btn-tg small" href="{tg_link(hub['channel'])}">Telegram</a>
</div><nav class="wrap nav">{self.head_nav(active)}</nav></header>
<main class="wrap">{bc}{body}</main>
<footer class="foot"><div class="wrap">
<div class="foot-grid">
<div><a class="brand" href="{self.abs('')}"><img src="{self.abs(img(hub['logo']))}" alt="" width="40" height="40"><span>The<b>Offers</b>Club</span></a>
<p>{e(config.SITE_TAGLINE)}</p></div>
<div><h4>Canali</h4>{''.join(f'<a href="{self.abs(n["slug"] + "/")}">{e(n["name"])}</a>' for n in config.NICHES.values())}</div>
<div><h4>Approfondimenti</h4><a href="{self.abs('classifiche/')}">Classifiche</a><a href="{self.abs('guide/')}">Guide all'acquisto</a>
<a href="{self.abs('come-funziona/')}">Come selezioniamo le offerte</a></div>
<div><h4>Telegram</h4><a href="{tg_link(hub['channel'])}">{e(hub.get('short', hub['name']))}</a>
{''.join(f'<a href="{tg_link(n["channel"])}">{e(n["name"])}</a>' for n in config.NICHES.values())}</div>
</div>
<p class="disc">{e(config.DISCLOSURE)}</p>
<p class="copy">© {datetime.now().year} {e(config.BRAND)}</p>
</div></footer></body></html>"""

    # -------------------------------------------------------------- componenti
    def price_html(self, pr):
        """(badge, riga prezzo, riga data) per un prezzo valido, oppure il ripiego senza prezzo."""
        if not pr:
            return "", '<span class="p muted">Prezzo aggiornato su Amazon</span>', ""
        d = pr.get("discount") or 0
        badge = f'<span class="badge{" hot" if d >= 35 else ""}">-{d}%</span>' if d else ""
        line = f'<span class="p">{eur(pr["price"])}</span>'
        if pr.get("old_price") and pr["old_price"] > pr["price"]:
            line += f' <s>{eur(pr["old_price"])}</s>'
            line += f' <span class="save">risparmi {eur(pr["old_price"] - pr["price"])}</span>'
        when = fmt_when(pr.get("at"))
        stamp = f'<p class="t">Prezzo rilevato il {when}: può cambiare</p>' if when else ""
        return badge, line, stamp

    def picture(self, src, alt, logo):
        src = (src or "").strip()
        if src.startswith("http"):
            return f'<img loading="lazy" src="{e(src)}" alt="{e(alt[:90])}" onerror="this.style.display=\'none\'">'
        return f'<img loading="lazy" class="ph" src="{self.abs(img(logo))}" alt="">'

    def card(self, o):
        n = config.NICHES[o["niche"]]
        pr = self.prices.get(o.get("asin"), o)
        badge, price, stamp = self.price_html(pr)
        note = f'<p class="n">{e(o["note"])}</p>' if o.get("note") else ""
        label = "Vedi offerta" if pr else "Vedi prezzo"
        return (f'<article class="card" style="--c:{n["color"]}"><div class="pic">'
                f'{self.picture(o.get("image"), o["title"], n["logo"])}{badge}</div>'
                f'<div class="body"><span class="tag">{n["emoji"]} {e(n["name"])}</span>'
                f'<h3>{e(o["title"][:110])}</h3>{note}<p class="pr">{price}</p>{stamp}'
                f'<a class="btn" rel="sponsored nofollow noopener" target="_blank" href="{e(o["url"])}">{label}</a>'
                f'</div></article>')

    def grid(self, offers, empty="Nuove offerte in arrivo: iscriviti al canale per riceverle subito."):
        if not offers:
            return f'<p class="empty">{e(empty)}</p>'
        return '<div class="grid">' + "".join(self.card(o) for o in offers) + "</div>"

    def join(self, niche=None):
        if niche:
            ch, logo, color = niche["channel"], niche["logo"], niche["color"]
            txt, btn = f"Le offerte {e(niche['name'])} arrivano prima su Telegram.", "Unisciti al canale"
        else:
            h = config.HUB
            ch, logo, color = h["channel"], h["logo"], h["color"]
            txt, btn = "Le offerte migliori di ogni categoria arrivano prima su Telegram.", "Entra nel club"
        folder = (f'<a class="btn ghost" href="{config.TELEGRAM_FOLDER_LINK}">Tutti i canali</a>'
                  if config.TELEGRAM_FOLDER_LINK else "")
        return (f'<aside class="join" style="--c:{color}"><img src="{self.abs(img(logo))}" alt="" width="64" height="64">'
                f'<div class="join-t"><strong>{txt}</strong><p>Gratis, senza spam, si esce con un clic.</p></div>'
                f'<div class="join-b"><a class="btn btn-tg" href="{tg_link(ch)}">{btn}</a>{folder}</div></aside>')

    def art_links(self, arts, title):
        if not arts:
            return ""
        li = "".join(
            f'<a class="art" style="--c:{config.NICHES[a["niche"]]["color"] if a["niche"] else config.HUB["color"]}" '
            f'href="{self.abs(a["kind"] + "/" + a["slug"] + "/")}"><span class="k">'
            f'{"🏆 Classifica" if a["kind"] == "classifiche" else "📚 Guida"}</span><strong>{e(a["title"])}</strong>'
            f'<span class="d">{e(a["desc"])}</span></a>' for a in arts)
        return f'<section><h2>{e(title)}</h2><div class="arts">{li}</div></section>'


def matching_offers(history, art, prices, limit=6):
    """Offerte attive (con prezzo valido) collegate a una classifica/guida."""
    if not art["search"]:
        return []
    out = []
    for o in history:
        pr = prices.get(o.get("asin"), o)
        if not pr:
            continue
        if art["niche"] and o.get("niche") != art["niche"]:
            continue
        t = o.get("title", "").lower()
        if not any(w in t for w in art["search"]) or any(w in t for w in art["exclude"]):
            continue
        if art["max_price"] and pr["price"] > art["max_price"]:
            continue
        out.append((pr.get("discount") or 0, o))
    out.sort(key=lambda x: x[0], reverse=True)
    return [o for _, o in out[:limit]]


# ------------------------------------------------------------------ pagine
def build(history, site_url, tag=""):
    s = Site(site_url, tag)
    history = unique(history)
    if os.path.exists(OUT):
        shutil.rmtree(OUT)
    os.makedirs(OUT)
    shutil.copy(os.path.join(ASSETS, "style.css"), os.path.join(OUT, "style.css"))
    if os.path.isdir(os.path.join(ASSETS, "img")):
        shutil.copytree(os.path.join(ASSETS, "img"), os.path.join(OUT, "img"))
    today = datetime.now(ROME).strftime("%d/%m/%Y")
    auto_data = load_json("classifiche.json")
    ranks = load_articles("classifiche", tag)
    guides = load_articles("guide", tag)
    for a in ranks:
        a["auto_items"] = auto_data.get(a["slug"], {}).get("items", []) if a["auto"] else []
        a["auto_updated"] = auto_data.get(a["slug"], {}).get("updated", "")
    for a in ranks + guides:
        a["indexable"] = bool(a["products"] or a.get("auto_items")) or a["words"] >= MIN_WORDS_INDEX
    arts = ranks + guides
    P = s.prices

    # ---------------- Home
    top = [o for o in history if (P.get(o.get("asin"), o) or {}).get("discount", 0) or 0]
    top = sorted([o for o in top if (P.get(o.get("asin"), o)["discount"] or 0) >= config.HUB_MIN_DISCOUNT],
                 key=lambda o: P.get(o.get("asin"), o)["discount"], reverse=True)[:8]
    tiles = "".join(
        f'<a class="tile" style="--c:{n["color"]}" href="{s.abs(n["slug"] + "/")}">'
        f'<img src="{s.abs(img(n["logo"], 400))}" alt="{e(n["name"])}" width="150" height="150">'
        f'<strong>{e(n["name"])}</strong><span>{e(n["pinned_desc"][:90].rsplit(" ", 1)[0])}…</span></a>'
        for n in config.NICHES.values())
    latest = ""
    for nid, n in config.NICHES.items():
        offers = [o for o in history if o["niche"] == nid][:4]
        if offers:
            latest += (f'<section class="band" style="--c:{n["color"]}"><div class="band-h"><h2>{n["emoji"]} {e(n["name"])}</h2>'
                       f'<a href="{s.abs(n["slug"] + "/")}">Tutte →</a></div>{s.grid(offers)}</section>')
    hero = (f'<section class="hero"><img src="{s.abs(img(config.HUB["logo"], 400))}" alt="{e(config.BRAND)}" width="210" height="210">'
            f'<div><h1>Le migliori offerte di oggi, <span>scelte una per una</span></h1>'
            f'<p>{e(config.SITE_DESCRIPTION)} Aggiornato il {today}.</p>'
            f'<div class="hero-b"><a class="btn btn-tg" href="{tg_link(config.HUB["channel"])}">Entra nel club su Telegram</a>'
            f'<a class="btn ghost" href="#canali">Scegli la categoria</a></div></div></section>')
    body = (hero
            + (f'<section><h2>🔥 Sconti top di oggi</h2>{s.grid(top)}</section>' if top else "")
            + f'<section id="canali"><h2>Scegli il tuo canale</h2><div class="tiles">{tiles}</div></section>'
            + latest
            + s.art_links(ranks[:8], "🏆 Classifiche")
            + s.art_links(guides[:6], "📚 Guide all'acquisto")
            + s.join())
    org = {"@context": "https://schema.org", "@type": "Organization", "name": config.BRAND, "url": s.abs(""),
           "logo": s.abs(img(config.HUB["logo"], 400)), "sameAs": [tg_link(config.HUB["channel"])]}
    write(os.path.join(OUT, "index.html"), s.page("", config.SITE_TITLE, config.SITE_DESCRIPTION, body, schema=org))

    # ---------------- Pagine canale
    for nid, n in config.NICHES.items():
        offers = [o for o in history if o["niche"] == nid][:config.SITE_OFFERS_PER_PAGE]
        offers.sort(key=lambda o: ((P.get(o.get("asin"), o) or {}).get("discount") or 0), reverse=True)
        mine = [a for a in arts if a["niche"] == nid]
        head = (f'<section class="cat-h" style="--c:{n["color"]}"><img src="{s.abs(img(n["logo"], 400))}" alt="" width="130" height="130">'
                f'<div><h1>{e(n["seo_title"])}</h1><p>{e(n["seo_intro"])}</p>'
                f'<p class="upd">Aggiornato il {today} · sconto minimo {config.MIN_DISCOUNT}%</p></div></section>')
        body = (head + s.join(n)
                + f'<section><h2>Offerte attive</h2>{s.grid(offers)}</section>'
                + s.art_links([a for a in mine if a["kind"] == "classifiche"], f"🏆 Classifiche {n['name']}")
                + s.art_links([a for a in mine if a["kind"] == "guide"], f"📚 Guide {n['name']}"))
        write(os.path.join(OUT, n["slug"], "index.html"),
              s.page(n["slug"] + "/", f"{n['seo_title']} | {config.BRAND}", n["seo_intro"], body,
                     active=nid, color=n["color"],
                     crumbs=[("Home", ""), (n["name"], n["slug"] + "/")]))

    # ---------------- Classifiche e guide
    for a in arts:
        n = config.NICHES.get(a["niche"])
        color = n["color"] if n else config.HUB["color"]
        logo = n["logo"] if n else config.HUB["logo"]
        path = f'{a["kind"]}/{a["slug"]}/'
        label = "Classifiche" if a["kind"] == "classifiche" else "Guide"
        crumbs = [("Home", ""), (label, a["kind"] + "/")]
        if n:
            crumbs = [("Home", ""), (n["name"], n["slug"] + "/"), (label, a["kind"] + "/")]
        crumbs.append((a["title"], path))

        # elenco della classifica: automatico (bot + API) oppure scritto a mano
        rows, items_ld = [], []
        if a.get("auto_items"):
            for i, p in enumerate(a["auto_items"], 1):
                pr = P.get(p["asin"])
                badge, price, stamp = s.price_html(pr)
                btn = "Vedi offerta" if pr and pr.get("discount") else "Vedi su Amazon"
                rows.append(f'<li><span class="num">{i}</span><div class="rpic">{s.picture(p.get("image"), p["title"], logo)}{badge}</div>'
                            f'<div class="rtxt"><h3>{e(p["title"][:120])}</h3><p class="pr">{price}</p>{stamp}</div>'
                            f'<a class="btn" rel="sponsored nofollow noopener" target="_blank" href="{e(p["url"])}">{btn}</a></li>')
                items_ld.append({"@type": "ListItem", "position": i, "name": p["title"][:120]})
        elif a["products"]:
            by_asin = {o.get("asin"): o for o in history if o.get("asin")}
            for i, (asin, name, why) in enumerate(a["products"], 1):
                o = by_asin.get(asin)
                pr = P.get(asin, o)
                badge, price, stamp = s.price_html(pr)
                url = o["url"] if o else amazon_link(asin, tag)
                why_html = f'<p class="n">{e(why)}</p>' if why else ""
                rows.append(f'<li><span class="num">{i}</span><div class="rpic">{s.picture(o.get("image") if o else "", name, logo)}{badge}</div>'
                            f'<div class="rtxt"><h3>{e(name or asin)}</h3>{why_html}<p class="pr">{price}</p>{stamp}</div>'
                            f'<a class="btn" rel="sponsored nofollow noopener" target="_blank" href="{e(url)}">'
                            f'{"Vedi offerta" if pr else "Vedi su Amazon"}</a></li>')
                items_ld.append({"@type": "ListItem", "position": i, "name": name or asin})
        plist = ""
        if rows:
            upd = fmt_when(a.get("auto_updated")) if a.get("auto_items") else ""
            note = (f'<p class="muted small">Classifica aggiornata il {upd} in base a valutazioni, numero di recensioni, '
                    f'vendite e prezzo su Amazon.</p>') if upd else ""
            plist = f'<section><h2>La classifica</h2>{note}<ol class="rank">{"".join(rows)}</ol></section>'
        elif a["kind"] == "classifiche":
            plist = ('<section class="soon"><h2>La classifica</h2><p>I prodotti della classifica vengono '
                     'selezionati e aggiornati in automatico. Nel frattempo trovi qui sotto i criteri per '
                     'scegliere e, quando ci sono, le offerte attive.</p></section>')
        live = matching_offers(history, a, P)
        live_html = (f'<section class="live-box"><h2>🔥 Offerte attive collegate</h2>'
                     "<p class=\"muted\">Compaiono solo quando c'è uno sconto reale.</p>"
                     f'{s.grid(live)}</section>') if live else ""
        related = [x for x in arts if x is not a and x["niche"] == a["niche"]][:4]
        kind_label = "🏆 Classifica" if a["kind"] == "classifiche" else "📚 Guida all'acquisto"
        body = (f'<article class="post" style="--c:{color}"><header class="post-h">'
                f'<span class="k">{kind_label}</span>'
                f'<h1>{e(a["title"])}</h1><p class="upd">Aggiornato il {a["mtime"].astimezone(ROME):%d/%m/%Y}</p></header>'
                + plist + live_html
                + f'<div class="prose">{md_to_html(a["body"], tag)}</div>'
                + "</article>" + s.join(n) + s.art_links(related, "Leggi anche"))
        schema = None
        if items_ld:
            schema = {"@context": "https://schema.org", "@type": "ItemList", "name": a["title"],
                      "itemListElement": items_ld}
        write(os.path.join(OUT, a["kind"], a["slug"], "index.html"),
              s.page(path, f"{a['title']} | {config.BRAND}", a["desc"], body, active=a["kind"],
                     color=color, crumbs=crumbs, index=a["indexable"], schema=schema, lastmod=a["mtime"]))

    for kind, label, intro, lst in (
            ("classifiche", "Classifiche", "I prodotti migliori per categoria e fascia di prezzo, con le offerte attive.", ranks),
            ("guide", "Guide all'acquisto", "Cosa guardare prima di comprare: spiegato semplice.", guides)):
        groups = ""
        for nid, n in config.NICHES.items():
            groups += s.art_links([a for a in lst if a["niche"] == nid], f'{n["emoji"]} {n["name"]}')
        groups += s.art_links([a for a in lst if not a["niche"]], "Altro")
        body = (f'<section class="post-h"><h1>{label}</h1><p>{e(intro)}</p></section>'
                + (groups or '<p class="empty">In arrivo.</p>') + s.join())
        write(os.path.join(OUT, kind, "index.html"),
              s.page(kind + "/", f"{label} | {config.BRAND}", intro, body, active=kind,
                     crumbs=[("Home", ""), (label, kind + "/")], index=bool(lst)))

    # ---------------- Come funziona
    how = f"""<article class="post"><header class="post-h"><h1>Come selezioniamo le offerte</h1></header><div class="prose">
<p>{e(config.BRAND)} segnala ogni giorno prodotti in sconto su Amazon, divisi per categoria, sul sito e sui canali Telegram.</p>
<h2>Le offerte</h2><ul>
<li>Nei canali tematici pubblichiamo solo offerte con almeno il <strong>{config.MIN_DISCOUNT}% di sconto</strong>; nel canale principale solo quelle dal <strong>{config.HUB_MIN_DISCOUNT}%</strong> in su.</li>
<li>Scartiamo ricambi, accessori generici e prodotti sotto una soglia minima di prezzo e di risparmio.</li>
<li>Lo stesso prodotto non viene ripubblicato prima di {config.REPOST_AFTER_DAYS} giorni.</li>
<li>Sul sito un prezzo compare solo se è stato rilevato nelle ultime {config.PRICE_MAX_AGE_HOURS} ore, con data e ora del controllo.</li>
<li>Quando un'offerta finisce, lo segnaliamo sul post.</li></ul>
<h2>Le classifiche</h2><p>Le classifiche si aggiornano in automatico: i prodotti vengono scelti tra quelli disponibili su Amazon in base alla valutazione media, al numero di recensioni (pochi voti contano meno), alle vendite e alla fascia di prezzo della classifica. Non includiamo ricambi né accessori, e al massimo due prodotti dello stesso marchio. I testi con i criteri di scelta sono scritti a mano.</p>
<h2>Affiliazione</h2><p>{e(config.DISCLOSURE)} Per te il prezzo non cambia, e la posizione in classifica non dipende dalla commissione.</p></div></article>"""
    write(os.path.join(OUT, "come-funziona", "index.html"),
          s.page("come-funziona/", f"Come selezioniamo le offerte | {config.BRAND}",
                 "Criteri di selezione delle offerte e delle classifiche, automazione e affiliazione Amazon.", how,
                 crumbs=[("Home", ""), ("Come funziona", "come-funziona/")]))

    # ---------------- 404, sitemap, robots
    write(os.path.join(OUT, "404.html"),
          s.page("404.html", f"Pagina non trovata | {config.BRAND}", "Pagina non trovata",
                 "<section class=\"post-h\"><h1>Pagina non trovata</h1><p>L'offerta potrebbe essere terminata.</p>"
                 f'<a class="btn" href="{s.abs("")}">Torna alle offerte</a></section>', index=False))
    sm = "".join(f"<url><loc>{u}</loc><lastmod>{d}</lastmod></url>" for u, d in s.sitemap)
    write(os.path.join(OUT, "sitemap.xml"),
          f'<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{sm}</urlset>')
    write(os.path.join(OUT, "robots.txt"), f"User-agent: *\nAllow: /\nSitemap: {s.abs('sitemap.xml')}\n")
    gsc = os.getenv("GOOGLE_VERIFICATION_FILE", "")      # es. google1234abcd.html
    if gsc:
        write(os.path.join(OUT, gsc), f"google-site-verification: {gsc}")
    write(os.path.join(OUT, ".nojekyll"), "")
    print(f"[sito] generate {len(s.sitemap)} pagine indicizzabili, {len(arts)} articoli in public/")
