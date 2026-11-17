"""
Esecuzione completa: raccoglie offerte -> pubblica sui canali -> aggiorna il sito.
Uso:  python -m bot.main            (pubblica davvero)
      python -m bot.main --dry-run  (prova senza inviare nulla)
      python -m bot.main --site-only
"""
import json
import os
import sys
from datetime import datetime, timedelta, timezone

import config
from bot import site, sources
from bot.telegram import Telegram, format_hub_pinned, format_offer

ROOT = os.path.dirname(os.path.dirname(__file__))
STATE = os.path.join(ROOT, "data", "state.json")
HISTORY = os.path.join(ROOT, "data", "history.json")


def load(path, default):
    try:
        return json.load(open(path, encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return default


def save(path, obj):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=1)


def italy_hour():
    # approssimazione ora italiana (UTC+1 / +2 d'estate)
    now = datetime.now(timezone.utc)
    return (now.hour + (2 if 4 <= now.month <= 10 else 1)) % 24


def main():
    dry = "--dry-run" in sys.argv
    site_only = "--site-only" in sys.argv
    tag = os.getenv("AMAZON_TAG", "")
    site_url = os.getenv("SITE_URL", "")
    tg = Telegram(os.getenv("TELEGRAM_TOKEN", ""), dry_run=dry or not os.getenv("TELEGRAM_TOKEN"))

    state = load(STATE, {"posted": {}, "hub_pin_id": None})
    history = load(HISTORY, [])
    now = datetime.now(timezone.utc)

    # pulizia prodotti pubblicati da più di N giorni (così possono tornare)
    cutoff = (now - timedelta(days=config.REPOST_AFTER_DAYS)).isoformat()
    state["posted"] = {k: v for k, v in state["posted"].items() if v > cutoff}

    if not site_only:
        if not 7 <= italy_hour() <= 22 and "--force" not in sys.argv:
            print("Fuori orario (7-22): niente post, aggiorno solo il sito")
        else:
            offers = sources.collect_all(tag)
            # migliori prima: sconto più alto, poi prodotti con prezzo
            offers.sort(key=lambda o: (o.get("discount") or 0, o.get("price") is not None), reverse=True)
            count = {n: 0 for n in config.NICHES}
            for o in offers:
                nid = o["niche"]
                if nid not in config.NICHES or o["key"] in state["posted"]:
                    continue
                if count[nid] >= config.MAX_POSTS_PER_NICHE_PER_RUN:
                    continue
                niche = config.NICHES[nid]
                res = tg.post_offer(niche["channel"], format_offer(o, niche), o.get("image"))
                if not res:
                    continue
                count[nid] += 1
                state["posted"][o["key"]] = now.isoformat()
                o["seen"] = now.isoformat()
                history.insert(0, o)
                d = o.get("discount") or 0
                if d >= config.HUB_MIN_DISCOUNT:
                    tg.post_offer(config.HUB["channel"], format_offer(o, niche, for_hub=True), o.get("image"))
                if config.LAMPO.get("enabled") and d >= config.LAMPO_MIN_DISCOUNT:
                    tg.post_offer(config.LAMPO["channel"], format_offer(o, niche, for_hub=True), o.get("image"))
            print(f"Pubblicate: {count}")

        # messaggio fissato dell'hub (aggiornato a ogni giro)
        state["hub_pin_id"] = tg.upsert_pinned(config.HUB["channel"], format_hub_pinned(site_url),
                                               state.get("hub_pin_id"))

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
