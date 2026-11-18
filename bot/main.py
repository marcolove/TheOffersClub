"""
Esecuzione completa: controlla le offerte scadute -> pubblica le nuove -> aggiorna il sito.
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
from bot.telegram import Telegram, build_markup, expired_text, format_hub_pinned, format_offer

ROOT = os.path.dirname(os.path.dirname(__file__))
STATE = os.path.join(ROOT, "data", "state.json")
HISTORY = os.path.join(ROOT, "data", "history.json")
ROME = ZoneInfo("Europe/Rome")

# Valori da config.py (con un valore predefinito se la riga manca)
MIN_HOUR = getattr(config, "MIN_HOUR", 8)
MAX_HOUR = getattr(config, "MAX_HOUR", 22)
MIN_POSTS = getattr(config, "MIN_POSTS_PER_NICHE_PER_RUN", 1)
MAX_POSTS = getattr(config, "MAX_POSTS_PER_NICHE_PER_RUN", 2)
MIN_DISCOUNT = getattr(config, "MIN_DISCOUNT", 15)
MIN_SAVING_VALUE = getattr(config, "MIN_SAVING_VALUE", 5)
PRICE_MAX_AGE_HOURS = getattr(config, "PRICE_MAX_AGE_HOURS", 24)
PREVIEW_FALLBACK = getattr(config, "PREVIEW_FALLBACK", False)   # True = senza foto usa l'anteprima del link
# Offerte scadute
EXPIRE_AUTO_HOURS = getattr(config, "EXPIRE_AUTO_HOURS", 24)    # prezzo scritto a mano: dopo N ore "non più garantito" (0 = mai)
TRACK_DAYS = getattr(config, "TRACK_DAYS", 3)                   # per quanti giorni il bot segue un post
PRICE_RISE_TOLERANCE = getattr(config, "PRICE_RISE_TOLERANCE", 0.03)  # +3% sul prezzo = offerta finita
EXPIRED_IMAGE = getattr(config, "EXPIRED_IMAGE", True)          # foto grigia con la scritta
LABEL_END = getattr(config, "EXPIRED_LABEL_END", "TERMINATA")
LABEL_STALE = getattr(config, "EXPIRED_LABEL_STALE", "SCADUTA")


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
    return datetime.now(ROME).hour


def in_active_hours(h):
    if MIN_HOUR <= MAX_HOUR:
        return MIN_HOUR <= h <= MAX_HOUR
    return h >= MIN_HOUR or h <= MAX_HOUR          # fascia a cavallo della mezzanotte (es. 20-2)


def good_enough(o):
    """Filtro di qualità. I prodotti del CSV (senza prezzo o con prezzo a mano) passano sempre."""
    if not o.get("price") or o.get("manual_price"):
        return True
    if (o.get("discount") or 0) < MIN_DISCOUNT:
        return False
    if MIN_SAVING_VALUE >= 0:
        old = o.get("old_price") or 0
        if old - o["price"] < MIN_SAVING_VALUE:       # es. da 10 € a 9 €: non vale un post
            return False
    return True


def expire_prices(history, now):
    """I prezzi non vanno mostrati sul sito oltre PRICE_MAX_AGE_HOURS."""
    limit = (now - timedelta(hours=PRICE_MAX_AGE_HOURS)).isoformat()
    for o in history:
        if o.get("source") == "amazon" and o.get("price") and o.get("seen", "") < limit:
            o["price"] = o["old_price"] = o["discount"] = None
            o["price_expired"] = True


def send(tg, chat_id, o, niche, tag, for_hub=False):
    """Pubblica il post. Restituisce (risultato Telegram, testo, bottoni)."""
    preview = o.get("preview_url", "") if PREVIEW_FALLBACK else ""
    text = format_offer(o, niche, for_hub=for_hub)
    markup = build_markup(o, tag)
    res = tg.post_offer(chat_id, text, o.get("image"), markup, preview_url=preview)
    return res, text, (json.dumps(markup) if markup else "")


def track(state, o, res, chat_id, text, markup, now, new=False):
    """Memorizza il post per poterlo aggiornare quando l'offerta scade."""
    if not res or not res.get("message_id"):
        return
    live = state.setdefault("live", {})
    if new or o["key"] not in live:
        live[o["key"]] = {"posted": now.isoformat(), "origin": o.get("origin", ""),
                          "asin": o.get("asin", ""), "price": o.get("price"),
                          "manual_price": bool(o.get("manual_price")),
                          "image": o.get("image", ""), "msgs": []}
    live[o["key"]]["msgs"].append({"chat": chat_id, "id": res["message_id"],
                                   "kind": res.get("_kind", "text"), "text": text,
                                   "markup": markup})


def end_label(when, posted):
    t = when.astimezone(ROME)
    if t.date() == posted.astimezone(ROME).date():
        return f"❌ <b>Offerta terminata alle {t:%H:%M}</b>"
    return f"❌ <b>Offerta terminata il {t:%d/%m} alle {t:%H:%M}</b>"


def check_expired(tg, state, history, tag, now):
    """Aggiorna i post delle offerte finite (testo + foto grigia). Non manda notifiche."""
    live = state.setdefault("live", {})
    if not live:
        return
    status = sources.csv_status()
    api_asins = [e["asin"] for e in live.values() if e.get("origin") == "api" and e.get("asin")]
    api_prices = sources.amazon_current_prices(api_asins, tag)
    done = 0
    for key, e in list(live.items()):
        posted = datetime.fromisoformat(e["posted"])
        asin = e.get("asin", "")
        st = status.get(asin) if e.get("origin") == "csv" else None
        reason, when = None, now
        if st and st["terminata"]:
            reason = "end"
        elif st and st["scadenza"] and st["scadenza"] <= now:
            reason, when = "end", st["scadenza"]
        elif e.get("origin") == "api" and asin in api_prices:
            cur = api_prices[asin]
            if cur == 0 or (e.get("price") and cur > e["price"] * (1 + PRICE_RISE_TOLERANCE) + 0.01):
                reason = "end"
        elif (e.get("manual_price") and EXPIRE_AUTO_HOURS > 0
              and now - posted >= timedelta(hours=EXPIRE_AUTO_HOURS)):
            reason = "stale"

        if reason:
            if reason == "end":
                label, img_label = end_label(when, posted), LABEL_END
            else:
                label, img_label = "⌛ <b>Prezzo non più garantito</b>: verifica su Amazon", LABEL_STALE
            for m in e["msgs"]:
                tg.mark_expired(m, expired_text(m["text"], label),
                                e.get("image") if EXPIRED_IMAGE else "", img_label)
            for o in history:                            # sul sito niente più prezzo
                if o.get("key") == key and o.get("seen") == e["posted"]:
                    o["price"] = o["old_price"] = o["discount"] = None
                    o["price_expired"] = True
            del live[key]
            done += 1
        elif now - posted > timedelta(days=TRACK_DAYS):
            del live[key]                                # troppo vecchio: non lo seguo più
    if done:
        print(f"Offerte segnate come scadute: {done}")


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

    state = load(STATE, {"posted": {}, "hub_pin_id": None, "live": {}})
    state.setdefault("posted", {})
    state.setdefault("live", {})
    history = load(HISTORY, [])
    now = datetime.now(timezone.utc)

    # pulizia prodotti pubblicati da più di N giorni (così possono tornare)
    cutoff = (now - timedelta(days=config.REPOST_AFTER_DAYS)).isoformat()
    state["posted"] = {k: v for k, v in state["posted"].items() if v > cutoff}

    if not site_only:
        # 1) offerte scadute: si aggiornano a ogni giro, anche fuori fascia (le modifiche non notificano)
        check_expired(tg, state, history, tag, now)

        # 2) nuovi post
        h = italy_hour()
        if not in_active_hours(h) and "--force" not in sys.argv:
            print(f"Ora italiana {h}: fuori fascia ({MIN_HOUR}-{MAX_HOUR}), niente post")
        else:
            offers = [o for o in sources.collect_all(tag) if good_enough(o)]
            random.shuffle(offers)
            # prima i prodotti con prezzo/sconto, poi gli altri
            offers.sort(key=lambda o: (o.get("discount") or 0, o.get("price") is not None), reverse=True)
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
                res, text, mk = send(tg, niche["channel"], o, niche, tag)
                if not res:
                    continue
                track(state, o, res, niche["channel"], text, mk, now, new=True)
                seen_now.add(o["key"])
                count[nid] += 1
                state["posted"][o["key"]] = now.isoformat()
                o["seen"] = now.isoformat()
                history.insert(0, o)
                d = o.get("discount") or 0
                if d >= config.HUB_MIN_DISCOUNT:
                    res, text, mk = send(tg, config.HUB["channel"], o, niche, tag, for_hub=True)
                    track(state, o, res, config.HUB["channel"], text, mk, now)
                if config.LAMPO.get("enabled") and d >= config.LAMPO_MIN_DISCOUNT:
                    res, text, mk = send(tg, config.LAMPO["channel"], o, niche, tag, for_hub=True)
                    track(state, o, res, config.LAMPO["channel"], text, mk, now)
            print(f"Pubblicate: {count}")

        state["hub_pin_id"] = tg.upsert_pinned(config.HUB["channel"], format_hub_pinned(site_url),
                                               state.get("hub_pin_id"))

    expire_prices(history, now)

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
