"""
Classifiche automatiche e aggiornamento prezzi del sito (solo con la Creators API attiva).

 - data/classifiche.json : prodotti scelti per ogni classifica con "auto: si"
 - data/prices.json      : prezzi aggiornati dei prodotti mostrati sul sito

Come viene scelto un prodotto per la classifica:
 1. ricerca Amazon con le parole "amazon:" della classifica, nella categoria Amazon.it adatta,
    solo prodotti da MIN_RATING stelle in su (filtro di Amazon), ordinati per valutazioni medie;
 2. scarta prodotti fuori fascia di prezzo, ricambi/accessori e titoli con le parole "escludi:";
 3. punteggio = posizione nei risultati (ordinati per valutazioni) + bonus posizione nelle vendite;
 4. massimo 2 prodotti dello stesso marchio, poi i primi RANK_SIZE.
La Creators API non restituisce stelle né numero di recensioni: il filtro e l'ordinamento per
valutazioni li fa Amazon nella ricerca.
"""
import json
import math
import os
from datetime import datetime, timedelta, timezone

import config
from bot import sources

ROOT = os.path.dirname(os.path.dirname(__file__))
RANKS = os.path.join(ROOT, "data", "classifiche.json")
PRICES = os.path.join(ROOT, "data", "prices.json")


def load(path):
    try:
        return json.load(open(path, encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def save(path, obj):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=1)


def _score(p):
    s = 1 - min(p.get("position", 20), 20) / 20                 # 1 = primo risultato
    rank = p.get("sales_rank")
    if rank and rank > 0:
        s += 0.6 * (1 - min(math.log10(rank), 6) / 6)          # più venduto = bonus più alto
    return round(s, 4)


def _auto_rankings():
    from bot import site                           # import qui: evita dipendenze circolari
    return [a for a in site.load_articles("classifiche", "") if a.get("auto")]


def update(tag, now=None):
    """Ricalcola le classifiche più vecchie (al massimo RANKS_PER_RUN per giro)."""
    if not sources.api_available(tag):
        return
    from bot.main import is_real_product            # stesso filtro anti-ricambi delle offerte
    now = now or datetime.now(timezone.utc)
    data = load(RANKS)
    days = getattr(config, "RANK_REFRESH_DAYS", 7)
    size = getattr(config, "RANK_SIZE", 10)
    todo = []
    for a in _auto_rankings():
        upd = data.get(a["slug"], {}).get("updated", "")
        if not upd or datetime.fromisoformat(upd) < now - timedelta(days=days):
            todo.append((upd, a))
    todo.sort(key=lambda x: x[0])
    for _, a in todo[:getattr(config, "RANKS_PER_RUN", 1)]:
        query = a.get("amazon") or (a["search"][0] if a["search"] else a["title"])
        found = sources.amazon_search_ranked(tag, query, a["niche"])
        ok = []
        for p in found:
            if a.get("min_price") and p["price"] < a["min_price"]:
                continue
            if a.get("max_price") and p["price"] > a["max_price"]:
                continue
            t = p["title"].lower()
            if any(w in t for w in a.get("exclude", [])):
                continue
            if a.get("search") and not any(w in t for w in a["search"]):
                continue
            if not is_real_product({"niche": a["niche"], "title": p["title"], "price": p["price"],
                                    "origin": "api"}):
                continue
            p["score"] = _score(p)
            ok.append(p)
        ok.sort(key=lambda p: p["score"], reverse=True)
        chosen, brands = [], {}
        for p in ok:
            b = (p.get("brand") or "").lower()
            if b and brands.get(b, 0) >= 2:
                continue
            brands[b] = brands.get(b, 0) + 1
            chosen.append(p)
            if len(chosen) >= size:
                break
        if len(chosen) >= 5:                         # troppo pochi: si tiene la classifica precedente
            data[a["slug"]] = {"updated": now.isoformat(), "items": chosen}
            cache = load(PRICES)
            for p in chosen:                         # i prezzi appena letti valgono come aggiornamento
                cache[p["asin"]] = {"price": p["price"], "old_price": p["old_price"],
                                    "discount": p["discount"], "at": now.isoformat()}
            save(PRICES, cache)
            print(f"[classifiche] {a['slug']}: {len(chosen)} prodotti")
        else:
            data.setdefault(a["slug"], {})["updated"] = now.isoformat()   # riprova tra N giorni
            print(f"[classifiche] {a['slug']}: solo {len(chosen)} prodotti validi, tengo la precedente")
    save(RANKS, data)


def refresh_prices(tag, history, state, now=None):
    """Aggiorna i prezzi dei prodotti mostrati sul sito, al massimo ogni PRICE_REFRESH_HOURS ore."""
    if not sources.api_available(tag):
        return
    now = now or datetime.now(timezone.utc)
    last = state.get("last_price_refresh", "")
    if last and datetime.fromisoformat(last) > now - timedelta(hours=getattr(config, "PRICE_REFRESH_HOURS", 6)):
        return
    asins = []
    for r in load(RANKS).values():
        asins += [p["asin"] for p in r.get("items", [])]
    asins += [o["asin"] for o in history if o.get("asin") and o.get("source") in ("amazon", "curated")]
    asins = list(dict.fromkeys(asins))[:getattr(config, "PRICE_REFRESH_MAX_ASINS", 300)]
    details = sources.amazon_offer_details(asins, tag)
    if not details:
        return
    cache = load(PRICES)
    for asin, d in details.items():
        if d is None:
            cache[asin] = {"gone": True, "at": now.isoformat()}
        else:
            cache[asin] = {"price": d["price"], "old_price": d["old_price"], "discount": d["discount"],
                           "at": now.isoformat()}
    limit = (now - timedelta(days=30)).isoformat()
    cache = {k: v for k, v in cache.items() if v.get("at", "") > limit}
    save(PRICES, cache)
    state["last_price_refresh"] = now.isoformat()
    print(f"[prezzi] aggiornati {len(details)} prodotti del sito")
