"""
Esecuzione completa: raccoglie offerte -> pubblica sui canali -> aggiorna il sito.
Uso:  python -m bot.main            (pubblica davvero)
      python -m bot.main --dry-run  (prova senza inviare nulla)
      python -m bot.main --site-only
      python -m bot.main --force    (ignora la fascia oraria)
"""
import json
import os
import random
import sys
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

import config
from bot import site, sources
from bot.telegram import Telegram, build_markup, format_hub_pinned, format_offer

ROOT = os.path.dirname(os.path.dirname(__file__))
STATE = os.path.join(ROOT, "data", "state.json")
HISTORY = os.path.join(ROOT, "data", "history.json")

# Valori da config.py (con un valore predefinito se la riga manca)
MIN_HOUR = getattr(config, "MIN_HOUR", 8)
MAX_HOUR = getattr(config, "MAX_HOUR", 22)
MIN_POSTS = getattr(config, "MIN_POSTS_PER_NICHE_PER_RUN", 1)
MAX_POSTS = getattr(config, "MAX_POSTS_PER_NICHE_PER_RUN", 2)
MIN_DISCOUNT = getattr(config, "MIN_DISCOUNT", 15)
MIN_SAVING_VALUE = getattr(config, "MIN_SAVING_VALUE", 5)
PRICE_MAX_AGE_HOURS = getattr(config, "PRICE_MAX_AGE_HOURS", 24)


def load(path, default):
    try:
        return json.load(open(path, encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return default


def save(path, obj):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=1)


def italy_hour():
    """Ora italiana esatta (gestisce ora legale/solare)."""
    return datetime.now(ZoneInfo("Europe/Rome")).hour


def in_active_hours(h):
    if MIN_HOUR <= MAX_HOUR:
        return MIN_HOUR <= h <= MAX_HOUR
    return h >= MIN_HOUR or h <= MAX_HOUR          # fascia a cavallo della mezzanotte (es. 20-2)


def good_enough(o):
    """Filtro di qualità. I prodotti senza prezzo (lista curata) passano sempre."""
    if not o.get("price"):
        return True
    if (o.get("discount") or 0) < MIN_DISCOUNT:
        return False
    if MIN_SAVING_VALUE >= 0:
        old = o.get("old_price") or 0
        if old - o["price"] < MIN_SAVING_VALUE:       # es. da 10 € a 9 €: non vale un post
            return False
    return True


def expire_prices(history, now):
    """Le offerte Amazon API non vanno mostrate con prezzo oltre PRICE_MAX_AGE_HOURS."""
    limit = (now - timedelta(hours=PRICE_MAX_AGE_HOURS)).isoformat()
    for o in history:
        if o.get("source") == "amazon" and o.get("price") and o.get("seen", "") < limit:
            o["price"] = o["old_price"] = o["discount"] = None
            o["price_expired"] = True


def main():
    dry = "--dry-run" in sys.argv
    site_only = "--site-only" in sys.argv
    tag = os.getenv("AMAZON_TAG", "").strip()
    site_url = os.getenv("SITE_URL", "").strip()
    token = os.getenv("TELEGRAM_TOKEN", "").strip()
    if not token and not dry:
        print("ATTENZIONE: TELEGRAM_TOKEN mancante, eseguo in modalità prova")
    if not tag:
        print("ATTENZIONE: AMAZON_TAG mancante, nessun prodotto Amazon verrà pubblicato")
    tg = Telegram(token, dry_run=dry or not token)

    state = load(STATE, {"posted": {}, "hub_pin_id": None})
    state.setdefault("posted", {})
    history = load(HISTORY, [])
    now = datetime.now(timezone.utc)

    # pulizia prodotti pubblicati da più di N giorni (così possono tornare)
    cutoff = (now - timedelta(days=config.REPOST_AFTER_DAYS)).isoformat()
    state["posted"] = {k: v for k, v in state["posted"].items() if v > cutoff}

    if not site_only:
        h = italy_hour()
        if not in_active_hours(h) and "--force" not in sys.argv:
            print(f"Ora italiana {h}: fuori fascia ({MIN_HOUR}-{MAX_HOUR}), niente post")
        else:
            offers = [o for o in sources.collect_all(tag) if good_enough(o)]
            random.shuffle(offers)                                    # ordine casuale tra pari merito...
            offers.sort(key=lambda o: o.get("discount") or 0, reverse=True)   # ...poi sconto più alto prima
            # numero di post casuale per nicchia (più naturale di un numero fisso)
            limit = {n: random.randint(MIN_POSTS, max(MIN_POSTS, MAX_POSTS)) for n in config.NICHES}
            count = {n: 0 for n in config.NICHES}
            seen_now = set()
            for o in offers:
                nid = o["niche"]
                if nid not in config.NICHES or o["key"] in state["posted"] or o["key"] in seen_now:
                    continue
                if count[nid] >= limit[nid]:
                    continue
                niche = config.NICHES[nid]
                res = tg.post_offer(niche["channel"], format_offer(o, niche), o.get("image"),
                                    build_markup(o, tag))
                if not res:
                    continue
                seen_now.add(o["key"])
                count[nid] += 1
                state["posted"][o["key"]] = now.isoformat()
                o["seen"] = now.isoformat()
                history.insert(0, o)
                d = o.get("discount") or 0
                if d >= config.HUB_MIN_DISCOUNT:
                    tg.post_offer(config.HUB["channel"], format_offer(o, niche, for_hub=True),
                                  o.get("image"), build_markup(o, tag))
                if config.LAMPO.get("enabled") and d >= config.LAMPO_MIN_DISCOUNT:
                    tg.post_offer(config.LAMPO["channel"], format_offer(o, niche, for_hub=True),
                                  o.get("image"), build_markup(o, tag))
            print(f"Pubblicate: {count}")

        # messaggio fissato dell'hub (aggiornato a ogni giro, anche fuori fascia: non notifica)
        state["hub_pin_id"] = tg.upsert_pinned(config.HUB["channel"], format_hub_pinned(site_url),
                                               state.get("hub_pin_id"))

    expire_prices(history, now)

    # tieni lo storico compatto (max 80 offerte per nicchia, ultime 30 giornate)
    old = (now - timedelta(days=30)).isoformat()
    kept, per = [], {}
    for o in history:
        if o.get("seen", "") < old:
            continue
        per[o["niche"]] = per.get(o["niche"], 0) + 1
        if per[o["niche"]] <= 80:
            kept.append(o)
    history = kept

    if not dry:
        save(STATE, state)
        save(HISTORY, history)
    site.build(history, site_url or "http://localhost:8000", tag)


if __name__ == "__main__":
    main()
