"""Invio messaggi ai canali Telegram tramite Bot API."""
import html
import json
import random
import time

import requests

import config

API = "https://api.telegram.org/bot{token}/{method}"

# Frasi brevi per rendere i post meno uniformi. Nessuna promessa non verificabile
# (niente "minimo storico", niente "scorte in esaurimento").
PHRASES_BASE = [
    "Prezzo interessante: controlla le recensioni prima di acquistare.",
    "Un buon prezzo per questo prodotto.",
    "Vale un'occhiata se lo stavi cercando.",
]
PHRASES_35 = [
    "Sconto importante: da guardare.",
    "Ribasso notevole rispetto al prezzo di listino.",
]
PHRASES_50 = [
    "Sconto molto alto: da guardare subito.",
    "Ribasso davvero forte, controlla i dettagli.",
]


class Telegram:
    def __init__(self, token, dry_run=False):
        self.token, self.dry = token, dry_run
        self.last_error = ""

    def call(self, method, **data):
        self.last_error = ""
        if self.dry:
            print(f"  [dry-run] {method} -> {data.get('chat_id')}: "
                  f"{(data.get('caption') or data.get('text') or '')[:90]!r}"
                  f"{' +bottoni' if data.get('reply_markup') else ''}")
            return {"message_id": 0}
        for attempt in range(3):
            try:
                r = requests.post(API.format(token=self.token, method=method), data=data, timeout=30)
                j = r.json()
            except Exception as e:                   # rete o risposta non valida: riprova
                print(f"  [telegram] {method}: {e}")
                time.sleep(3)
                continue
            if j.get("ok"):
                time.sleep(1.2)                       # rispetta i limiti di Telegram
                return j["result"]
            if j.get("error_code") == 429:            # troppi messaggi: aspetta
                time.sleep(j.get("parameters", {}).get("retry_after", 5) + 1)
                continue
            self.last_error = j.get("description", "")
            if "message is not modified" not in self.last_error:
                print(f"  [telegram] errore {method} su {data.get('chat_id')}: {self.last_error}")
            return None
        return None

    def post_offer(self, chat_id, text, image="", markup=None):
        extra = {"reply_markup": json.dumps(markup)} if markup else {}
        if image:
            res = self.call("sendPhoto", chat_id=chat_id, photo=image, caption=text,
                            parse_mode="HTML", **extra)
            if res:
                return res
        return self.call("sendMessage", chat_id=chat_id, text=text, parse_mode="HTML",
                         disable_web_page_preview="true", **extra)

    def upsert_pinned(self, chat_id, text, message_id=None):
        """Aggiorna il messaggio fissato dell'hub; se non esiste lo crea e lo fissa."""
        if message_id:
            res = self.call("editMessageText", chat_id=chat_id, message_id=message_id, text=text,
                            parse_mode="HTML", disable_web_page_preview="true")
            # "message is not modified" = testo identico: va bene, non ricrearlo
            if res or self.dry or "message is not modified" in self.last_error:
                return message_id
        res = self.call("sendMessage", chat_id=chat_id, text=text, parse_mode="HTML",
                        disable_web_page_preview="true")
        if res and res.get("message_id"):
            self.call("pinChatMessage", chat_id=chat_id, message_id=res["message_id"],
                      disable_notification="true")
            return res["message_id"]
        return message_id


def eur(x):
    return f"{x:,.2f} €".replace(",", "X").replace(".", ",").replace("X", ".")


def format_offer(o, niche, for_hub=False):
    e = html.escape
    title = o["title"] if len(o["title"]) < 140 else o["title"][:137] + "…"
    d = o.get("discount") or 0
    icon = "🔥" if d >= 50 else "💣" if d >= 35 else niche["emoji"]
    lines = [f"{icon} <b>{e(title)}</b>", ""]
    if o.get("price"):
        p = f"💶 <b>{eur(o['price'])}</b>"
        if o.get("old_price") and o["old_price"] > o["price"]:
            p += f" invece di <s>{eur(o['old_price'])}</s>"
            if d:
                p += f" <b>(-{d}%)</b>"
            lines.append(p)
            lines.append(f"📉 Risparmi {eur(o['old_price'] - o['price'])}")
        else:
            lines.append(p)
        pool = PHRASES_50 if d >= 50 else PHRASES_35 if d >= 35 else PHRASES_BASE
        lines += ["", random.choice(pool)]
    if o.get("note"):
        lines.append(f"✅ {e(o['note'])}")
    low = o["title"].lower()
    if niche.get("name", "").startswith("Utensili") and any(h in low for h in config.NO_BATTERY_HINTS):
        lines.append("⚠️ Batteria e caricatore NON inclusi")
    if for_hub:
        lines += ["", f"📢 Altre offerte {e(niche['name'])}: {niche['channel']}"]
    lines += ["", "<i>Link affiliato · prezzo soggetto a variazioni</i>"]
    return "\n".join(lines)


def build_markup(o, tag=""):
    """Bottoni sotto al post: offerta + prova Prime (solo per prodotti Amazon)."""
    is_amazon = o["source"] in ("amazon", "curated")
    store = "Amazon" if is_amazon else "eBay"
    rows = [[{"text": f"🛒 Vedi su {store}", "url": o["url"]}]]
    if is_amazon and tag and getattr(config, "PRIME_BUTTON", True):
        rows.append([{"text": "👑 Prova Prime gratis", "url": f"https://www.amazon.it/provaprime?tag={tag}"}])
    return {"inline_keyboard": rows}


def format_hub_pinned(site_url):
    e = html.escape
    lines = [f"📌 <b>Benvenuto in {e(config.BRAND)}!</b>"]
    desc = getattr(config, "HUB_DESCRIPTION", "")
    if desc:
        lines += ["", e(desc)]
    lines += ["", "Scegli i canali che ti interessano 👇", ""]
    for n in config.NICHES.values():
        lines.append(f"{n['emoji']} {e(n['name'])} → {n['channel']}")
    if config.LAMPO.get("enabled"):
        lines.append(f"⚡ Offerte lampo (solo sconti top) → {config.LAMPO['channel']}")
    if config.TELEGRAM_FOLDER_LINK:
        lines += ["", f"➕ <a href=\"{config.TELEGRAM_FOLDER_LINK}\">Iscriviti a tutti con un clic</a>"]
    if site_url and getattr(config, "SHOW_SITE_IN_PINNED", False):
        lines.append(f"🌐 Sito: {site_url}")
    lines += ["", f"<i>{e(config.DISCLOSURE)}</i>"]
    return "\n".join(lines)
