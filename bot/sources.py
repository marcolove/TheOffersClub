"""
Fonti delle offerte.
 - Amazon Creators API (automatica, attiva quando inserisci le credenziali Creators API)
 - Lista prodotti data/prodotti.csv (fase di avvio): link, prezzo, data, immagine,
   scadenza e terminata facoltativi
 - eBay Browse API (facoltativa, prezzi reali da subito)
Ogni fonte restituisce offerte nello STESSO formato: il post che ne esce è identico.
"""
import base64
import csv
import os
import random
import time
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import requests

import config

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
ROME = ZoneInfo("Europe/Rome")


def _offer(**kw):
    base = {"key": "", "source": "", "origin": "", "asin": "", "niche": "", "title": "", "url": "",
            "image": "", "price": None, "old_price": None, "discount": None, "note": "", "brand": "",
            "manual_price": False, "preview_url": "", "price_date": "", "rating": None, "reviews": None}
    base.update(kw)
    return base


def amazon_link(asin, tag):
    return f"https://www.amazon.it/dp/{asin}?tag={tag}"


def today_label():
    return datetime.now(ROME).strftime("%d/%m")


# --------------------------------------------------------------------------- scelta delle ricerche
def pick_searches(n):
    """Sceglie n ricerche (nicchia, parola chiave) senza ripetizioni.
    Le parole in "top_keywords" pesano TOP_KEYWORD_WEIGHT volte di più. Siccome ogni nicchia
    ha lo stesso numero di parole e di top_keywords, l'equilibrio tra canali resta invariato."""
    w_top = getattr(config, "TOP_KEYWORD_WEIGHT", 1)
    pool = []
    for nid, ni in config.NICHES.items():
        top = set(ni.get("top_keywords", []))
        for kw in ni["keywords"]:
            pool.append(((nid, kw), w_top if kw in top else 1))
    chosen = []
    while pool and len(chosen) < n:
        items, weights = zip(*pool)
        pick = random.choices(items, weights=weights, k=1)[0]
        chosen.append(pick)
        pool = [p for p in pool if p[0] != pick]
    return chosen


# --------------------------------------------------------------------------- Amazon Creators API
_API = None


def _api(tag):
    """Client Creators API (creato una volta per giro). None se mancano le credenziali."""
    global _API
    if _API is not None:
        return _API or None
    cid = os.getenv("AMAZON_CREDENTIAL_ID")
    secret = os.getenv("AMAZON_CREDENTIAL_SECRET")
    version = (os.getenv("AMAZON_API_VERSION") or "").strip()
    if not (cid and secret and version and tag):
        _API = False
        return None
    try:
        from amazon_creatorsapi import AmazonCreatorsApi
    except ImportError:
        print("[amazon-api] libreria python-amazon-paapi >= 7 non installata")
        _API = False
        return None
    try:
        _API = AmazonCreatorsApi(credential_id=cid, credential_secret=secret, version=version,
                                 tag=tag, country="IT")
    except Exception as e:
        print(f"[amazon-api] client non creato (controlla AMAZON_API_VERSION): {e}")
        _API = False
        return None
    return _API


def api_available(tag):
    return bool(_api(tag))


def rating_ok(o):
    """Filtro valutazioni (solo offerte automatiche):
    - valutazione nota e sotto MIN_RATING -> scartata
    - numero di recensioni noto e sotto MIN_REVIEWS -> scartata
    - dato non fornito dall'API -> l'offerta passa (lo segnala il log)."""
    min_r = getattr(config, "MIN_RATING", 0) or 0
    min_n = getattr(config, "MIN_REVIEWS", 0) or 0
    r, n = o.get("rating"), o.get("reviews")
    if r is not None and r < min_r:
        return False
    if n is not None and n < min_n:
        return False
    return True


def from_amazon_api(tag):
    api = _api(tag)
    if not api:
        print("[amazon-api] credenziali assenti: salto (normale prima delle 10 vendite)")
        return []
    # Poche ricerche per giro: il limite di richieste dipende dalle vendite fatte via API
    n = getattr(config, "AMAZON_SEARCHES_PER_ROUND", 3)
    offers, low_rated, no_rating = [], 0, 0
    for niche_id, kw in pick_searches(n):
        niche = config.NICHES[niche_id]
        try:
            # Nessun filtro di sconto lato Amazon: lo sconto minimo si applica dopo, in main.py.
            res = api.search_items(keywords=kw, search_index=niche.get("amazon_search_index", "All"),
                                   item_count=10)
            items = getattr(res, "items", None) or []
        except Exception as e:                      # nessun risultato o limite superato
            print(f"[amazon-api] {niche_id}/{kw}: {e}")
            continue
        for it in items:
            o = _parse_amazon_item(it, niche_id, tag)
            if not o:
                continue
            if o["rating"] is None:
                no_rating += 1
            if not rating_ok(o):
                low_rated += 1
                continue
            offers.append(o)
        time.sleep(1.1)                             # massimo 1 richiesta al secondo
    print(f"[amazon-api] trovate {len(offers)} offerte · scartate per valutazione/recensioni: {low_rated}"
          f" · senza valutazione dall'API: {no_rating}")
    return offers


def amazon_offer_details(asins, tag):
    """Dati aggiornati dei prodotti: {asin: {"price", "old_price", "discount", "title", "image",
    "url"}} oppure {asin: None} se non più disponibile. Gli ASIN non controllati (errore,
    limite, credenziali assenti) non compaiono: per quelli non si decide nulla."""
    api = _api(tag)
    out = {}
    if not api or not asins:
        return out
    asins = list(dict.fromkeys(asins))
    for i in range(0, len(asins), 10):                 # l'API accetta 10 ASIN per volta
        chunk = asins[i:i + 10]
        try:
            items = api.get_items(chunk) or []
        except Exception as e:
            if type(e).__name__ == "ItemsNotFoundError":   # nessuno dei prodotti esiste più
                for a in chunk:
                    out[a] = None
            else:                                       # errore o limite: non si decide nulla
                print(f"[amazon-api] controllo prezzi: {e}")
            continue
        found = set()
        for it in items:
            found.add(it.asin)
            lst = _listing(it)
            price = _g(lst, "price.money.amount")
            if not price:
                out[it.asin] = None
                continue
            old = _g(lst, "price.saving_basis.money.amount")
            disc = _g(lst, "price.savings.percentage")
            if disc is None and old and old > price:
                disc = round((1 - price / old) * 100)
            out[it.asin] = {"price": float(price), "old_price": float(old) if old else None,
                            "discount": int(disc) if disc else None,
                            "title": _g(it, "item_info.title.display_value") or "",
                            "image": _g(it, "images.primary.large.url") or "",
                            "url": getattr(it, "detail_page_url", None) or amazon_link(it.asin, tag)}
        for a in chunk:
            if a not in found:
                out[a] = None
        time.sleep(1.1)
    return out


def amazon_current_prices(asins, tag):
    """Prezzo attuale dei prodotti già pubblicati: {asin: prezzo}, 0 = non più disponibile."""
    return {a: (d["price"] if d else 0.0) for a, d in amazon_offer_details(asins, tag).items()}


def amazon_search_ranked(tag, keywords, search_index="All", pages=2):
    """Prodotti per le classifiche: fino a 10 x pages risultati, con i dati utili al punteggio
    (valutazione, recensioni, posizione nelle vendite). I campi non forniti dall'API restano None."""
    api = _api(tag)
    if not api:
        return []
    out, pos = [], 0
    for page in range(1, pages + 1):
        res = None
        for extra in ({"sort_by": "AvgCustomerReviews"}, {}):   # se l'ordinamento non è accettato, senza
            try:
                res = api.search_items(keywords=keywords, search_index=search_index, item_count=10,
                                       item_page=page, **extra)
                break
            except TypeError:
                continue
            except Exception as e:
                print(f"[amazon-api] classifica '{keywords}' pagina {page}: {e}")
                res = None
                break
        items = getattr(res, "items", None) or []
        if not items:
            break
        for it in items:
            pos += 1
            lst = _listing(it)
            price = _g(lst, "price.money.amount")
            title = _g(it, "item_info.title.display_value")
            if not title or not price:
                continue
            old = _g(lst, "price.saving_basis.money.amount")
            disc = _g(lst, "price.savings.percentage")
            if disc is None and old and old > price:
                disc = round((1 - price / old) * 100)
            p = {
                "asin": it.asin, "title": title, "position": pos,
                "url": getattr(it, "detail_page_url", None) or amazon_link(it.asin, tag),
                "image": _g(it, "images.primary.large.url") or "",
                "brand": _g(it, "item_info.by_line_info.brand.display_value") or "",
                "price": float(price), "old_price": float(old) if old else None,
                "discount": int(disc) if disc else None,
                "rating": _num_or_none(_g(it, "customer_reviews.star_rating.value")),
                "reviews": _num_or_none(_g(it, "customer_reviews.count")),
                "sales_rank": _num_or_none(_g(it, "browse_node_info.website_sales_rank.sales_rank")),
            }
            if not rating_ok(p):                     # stessa soglia delle offerte (es. 4 stelle)
                continue
            out.append(p)
        time.sleep(1.1)
    return out


def _num_or_none(x):
    try:
        return float(x) if x is not None else None
    except (TypeError, ValueError):
        return None


def _g(obj, path):
    for p in path.split("."):
        if obj is None:
            return None
        if p.isdigit():
            obj = obj[int(p)] if obj and len(obj) > int(p) else None
        else:
            obj = getattr(obj, p, None)
    return obj


def _listing(it):
    """Offerta principale: quella che vince la Buy Box, altrimenti la prima."""
    listings = _g(it, "offers_v2.listings") or []
    for l in listings:
        if getattr(l, "is_buy_box_winner", False):
            return l
    return listings[0] if listings else None


def _parse_amazon_item(it, niche_id, tag):
    title = _g(it, "item_info.title.display_value")
    lst = _listing(it)
    price = _g(lst, "price.money.amount")
    if not title or not price:
        return None
    old = _g(lst, "price.saving_basis.money.amount")
    disc = _g(lst, "price.savings.percentage")
    if disc is None and old and old > price:
        disc = round((1 - price / old) * 100)
    brand = _g(it, "item_info.by_line_info.brand.display_value") or ""
    # Link ESATTAMENTE come lo restituisce l'API: se si modifica si perde l'attribuzione
    url = getattr(it, "detail_page_url", None) or amazon_link(it.asin, tag)
    return _offer(key=f"amz:{it.asin}", source="amazon", origin="api", asin=it.asin, niche=niche_id,
                  title=title, url=url, preview_url=url,
                  image=_g(it, "images.primary.large.url") or "", price=float(price),
                  old_price=float(old) if old else None, discount=int(disc) if disc else None,
                  brand=brand, price_date=today_label(),
                  rating=_num_or_none(_g(it, "customer_reviews.star_rating.value")),
                  reviews=_num_or_none(_g(it, "customer_reviews.count")))


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


def _deadline(s):
    """'2026-11-18 22:00', '18/11/2026 22:00', '18/11/2026' (= fine giornata) -> datetime italiana."""
    s = (s or "").strip()
    if not s:
        return None
    for fmt in ("%Y-%m-%d %H:%M", "%d/%m/%Y %H:%M", "%d-%m-%Y %H:%M"):
        try:
            return datetime.strptime(s, fmt).replace(tzinfo=ROME)
        except ValueError:
            pass
    d = _date(s)
    return d.replace(hour=23, minute=59, tzinfo=ROME) if d else None


def _yes(s):
    return (s or "").strip().lower() in ("si", "sì", "x", "1", "true", "yes", "terminata")


def _rows():
    path = os.path.join(DATA_DIR, "prodotti.csv")
    if not os.path.exists(path):
        return []
    return list(csv.DictReader(open(path, encoding="utf-8-sig")))


def csv_status():
    """{asin: {"terminata": bool, "scadenza": datetime|None}} per il controllo delle scadenze."""
    out = {}
    for r in _rows():
        asin = (r.get("asin") or "").strip()
        if asin:
            out[asin] = {"terminata": _yes(r.get("terminata")), "scadenza": _deadline(r.get("scadenza"))}
    return out


def _link(r, asin, tag):
    """Usa il link della colonna 'link' (es. link.amazon / amzn.to da SiteStripe) se presente."""
    link = (r.get("link") or "").strip()
    return link if link.startswith("http") else amazon_link(asin, tag)


def from_curated_csv(tag, per_niche=3):
    """Legge data/prodotti.csv. Colonne:
       asin, nicchia, titolo                                     (obbligatorie)
       nota, link, prezzo, prezzo_vecchio, data_prezzo, immagine,
       scadenza, terminata                                       (facoltative)
    Il prezzo scritto a mano viene usato SOLO se data_prezzo è recente
    (MANUAL_PRICE_MAX_AGE_DAYS, di default 2 giorni): oltre, il post esce senza prezzo.
    I prodotti terminati o con scadenza passata non vengono pubblicati."""
    rows = _rows()
    if not rows or not tag:
        return []
    max_age = getattr(config, "MANUAL_PRICE_MAX_AGE_DAYS", 2)
    today = datetime.now()
    now = datetime.now(ROME)
    offers = []
    for niche_id in config.NICHES:
        pool = [r for r in rows if (r.get("nicchia") or "").strip() == niche_id and (r.get("asin") or "").strip()]
        pool = [r for r in pool if not _yes(r.get("terminata"))
                and not ((_deadline(r.get("scadenza")) or now + timedelta(days=1)) <= now)]
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
                key=f"amz:{asin}", source="amazon" if fresh else "curated", origin="csv", asin=asin,
                niche=niche_id, title=(r.get("titolo") or "").strip(), url=_link(r, asin, tag),
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
                    key=f"ebay:{it['itemId']}", source="ebay", origin="ebay", niche=niche_id,
                    title=it.get("title", ""), url=url, image=(it.get("image") or {}).get("imageUrl", ""),
                    price=float(it["price"]["value"]),
                    old_price=float(mp.get("originalPrice", {}).get("value", 0)) or None,
                    discount=int(float(disc)), price_date=today_label()))
            time.sleep(0.5)
    print(f"[ebay] trovate {len(offers)} offerte")
    return offers


def collect_all(tag):
    offers = from_amazon_api(tag)
    if not offers:                       # finché non c'è l'API usa la lista CSV
        offers = from_curated_csv(tag)
    offers += from_ebay()
    return offers
