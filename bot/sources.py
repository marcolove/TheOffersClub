"""
Fonti delle offerte.
 - Amazon PA-API (automatica, attiva quando inserisci le chiavi dopo le 3 vendite)
 - Lista prodotti data/prodotti.csv (fase di avvio): link, prezzo e data facoltativi
 - eBay Browse API (facoltativa, prezzi reali da subito)
Ogni fonte restituisce una lista di dict "offerta" con lo stesso formato.
"""
import base64
import csv
import os
import random
import time
from datetime import datetime, timedelta

import requests

import config

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")


def _offer(**kw):
    base = {"key": "", "source": "", "niche": "", "title": "", "url": "", "image": "",
            "price": None, "old_price": None, "discount": None, "note": "", "brand": "",
            "manual_price": False, "preview_url": "", "price_date": ""}
    base.update(kw)
    return base


def amazon_link(asin, tag):
    return f"https://www.amazon.it/dp/{asin}?tag={tag}"


# --------------------------------------------------------------------------- Amazon PA-API
def from_amazon_api(tag):
    key, secret = os.getenv("AMAZON_ACCESS_KEY"), os.getenv("AMAZON_SECRET_KEY")
    if not (key and secret and tag):
        print("[amazon-api] chiavi assenti: salto (normale prima delle 3 vendite)")
        return []
    try:
        from amazon_paapi import AmazonApi
    except ImportError:
        print("[amazon-api] libreria python-amazon-paapi non installata")
        return []

    api = AmazonApi(key, secret, tag, "IT", throttling=1.1)
    offers = []
    for niche_id, niche in config.NICHES.items():
        for kw in random.sample(niche["keywords"], k=min(3, len(niche["keywords"]))):
            try:
                # Nessun filtro di sconto lato Amazon: a volte scarta offerte valide.
                # Lo sconto minimo si applica dopo, in main.py.
                res = api.search_items(keywords=kw, search_index=niche.get("amazon_search_index", "All"),
                                       item_count=10)
                items = getattr(res, "items", None) or []
            except Exception as e:                      # nessun risultato o limite superato
                print(f"[amazon-api] {niche_id}/{kw}: {e}")
                continue
            for it in items:
                o = _parse_amazon_item(it, niche_id, tag)
                if o:
                    offers.append(o)
    print(f"[amazon-api] trovate {len(offers)} offerte")
    return offers


def _g(obj, path):
    for p in path.split("."):
        if obj is None:
            return None
        if p.isdigit():
            obj = obj[int(p)] if len(obj) > int(p) else None
        else:
            obj = getattr(obj, p, None)
    return obj


def _parse_amazon_item(it, niche_id, tag):
    title = _g(it, "item_info.title.display_value")
    price = _g(it, "offers.listings.0.price.amount")
    if not title or not price:
        return None
    old = _g(it, "offers.listings.0.saving_basis.amount")
    disc = _g(it, "offers.listings.0.price.savings.percentage")
    if disc is None and old and old > price:
        disc = round((1 - price / old) * 100)
    url = _g(it, "detail_page_url") or amazon_link(it.asin, tag)
    return _offer(key=f"amz:{it.asin}", source="amazon", niche=niche_id, title=title, url=url,
                  image=_g(it, "images.primary.large.url") or "", price=float(price),
                  old_price=float(old) if old else None, discount=int(disc) if disc else None,
                  brand=_g(it, "item_info.by_line_info.brand.display_value") or "")


# --------------------------------------------------------------------------- Lista prodotti (CSV)
def _num(s):
    """'14,99' / '14.99' / '14,99 €' -> 14.99 (None se vuoto o non valido)."""
    s = (s or "").replace("€", "").replace(" ", "").strip()
    if not s:
        return None
    if "," in s and "." in s:                      # 1.234,56
        s = s.replace(".", "").replace(",", ".")
    else:
        s = s.replace(",", ".")
    try:
        v = float(s)
        return v if v > 0 else None
    except ValueError:
        return None


def _date(s):
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y"):
        try:
            return datetime.strptime((s or "").strip(), fmt)
        except ValueError:
            pass
    return None


def _link(r, asin, tag):
    """Usa il link della colonna 'link' (es. link.amazon / amzn.to da SiteStripe) se presente."""
    link = (r.get("link") or "").strip()
    return link if link.startswith("http") else amazon_link(asin, tag)


def from_curated_csv(tag, per_niche=3):
    """Legge data/prodotti.csv. Colonne:
       asin, nicchia, titolo                                    (obbligatorie)
       nota, link, prezzo, prezzo_vecchio, data_prezzo, immagine (facoltative)
    Il prezzo scritto a mano viene usato SOLO se data_prezzo è recente
    (MANUAL_PRICE_MAX_AGE_DAYS, di default 2 giorni): oltre, il post esce senza prezzo."""
    path = os.path.join(DATA_DIR, "prodotti.csv")
    if not os.path.exists(path) or not tag:
        return []
    max_age = getattr(config, "MANUAL_PRICE_MAX_AGE_DAYS", 2)
    today = datetime.now()
    rows = list(csv.DictReader(open(path, encoding="utf-8-sig")))
    offers = []
    for niche_id in config.NICHES:
        pool = [r for r in rows if (r.get("nicchia") or "").strip() == niche_id and (r.get("asin") or "").strip()]
        random.shuffle(pool)
        for r in pool[:per_niche * 3]:
            asin = r["asin"].strip()
            price, old = _num(r.get("prezzo")), _num(r.get("prezzo_vecchio"))
            d = _date(r.get("data_prezzo"))
            fresh = bool(price and d and today - d <= timedelta(days=max_age))
            disc = None
            if fresh and old and old > price:
                disc = round((1 - price / old) * 100)
            offers.append(_offer(
                key=f"amz:{asin}", source="amazon" if fresh else "curated", niche=niche_id,
                title=(r.get("titolo") or "").strip(), url=_link(r, asin, tag),
                image=(r.get("immagine") or "").strip(),
                price=price if fresh else None, old_price=old if fresh else None,
                discount=disc, note=(r.get("nota") or "").strip(), manual_price=fresh,
                preview_url=amazon_link(asin, tag), price_date=d.strftime("%d/%m") if fresh else ""))
    print(f"[csv] {len(offers)} prodotti candidati")
    return offers


# --------------------------------------------------------------------------- eBay Browse API
def _ebay_token(cid, secret):
    auth = base64.b64encode(f"{cid}:{secret}".encode()).decode()
    r = requests.post("https://api.ebay.com/identity/v1/oauth2/token", timeout=20,
                      headers={"Authorization": f"Basic {auth}",
                               "Content-Type": "application/x-www-form-urlencoded"},
                      data={"grant_type": "client_credentials",
                            "scope": "https://api.ebay.com/oauth/api_scope"})
    r.raise_for_status()
    return r.json()["access_token"]


def from_ebay():
    cid, secret, campaign = (os.getenv("EBAY_CLIENT_ID"), os.getenv("EBAY_CLIENT_SECRET"),
                             os.getenv("EBAY_CAMPAIGN_ID"))
    if not (cid and secret and campaign):
        return []
    try:
        token = _ebay_token(cid, secret)
    except Exception as e:
        print(f"[ebay] token non ottenuto: {e}")
        return []
    headers = {"Authorization": f"Bearer {token}", "X-EBAY-C-MARKETPLACE-ID": "EBAY_IT",
               "X-EBAY-C-ENDUSERCTX": f"affiliateCampaignId={campaign}"}
    offers = []
    for niche_id, niche in config.NICHES.items():
        for q in niche.get("ebay_queries", [])[:2]:
            try:
                r = requests.get("https://api.ebay.com/buy/browse/v1/item_summary/search", timeout=20,
                                 headers=headers,
                                 params={"q": q, "limit": 20,
                                         "filter": "buyingOptions:{FIXED_PRICE},conditions:{NEW}"})
                r.raise_for_status()
            except Exception as e:
                print(f"[ebay] {q}: {e}")
                continue
            for it in r.json().get("itemSummaries", []):
                mp = it.get("marketingPrice") or {}
                disc = mp.get("discountPercentage")
                if not disc:
                    continue
                url = it.get("itemAffiliateWebUrl") or it.get("itemWebUrl")
                offers.append(_offer(
                    key=f"ebay:{it['itemId']}", source="ebay", niche=niche_id, title=it.get("title", ""),
                    url=url, image=(it.get("image") or {}).get("imageUrl", ""),
                    price=float(it["price"]["value"]),
                    old_price=float(mp.get("originalPrice", {}).get("value", 0)) or None,
                    discount=int(float(disc))))
            time.sleep(0.5)
    print(f"[ebay] trovate {len(offers)} offerte")
    return offers


def collect_all(tag):
    offers = from_amazon_api(tag)
    if not offers:                       # finché non c'è l'API usa la lista CSV
        offers = from_curated_csv(tag)
    offers += from_ebay()
    return offers
