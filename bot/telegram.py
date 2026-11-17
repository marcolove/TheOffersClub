"""Invio messaggi ai canali Telegram tramite Bot API."""
import html
import os
import time

import requests

import config

API = "https://api.telegram.org/bot{token}/{method}"


class Telegram:
    def __init__(self, token, dry_run=False):
        self.token, self.dry = token, dry_run

    def call(self, method, **data):
        if self.dry:
            print(f"  [dry-run] {method} -> {data.get('chat_id')}: "
                  f"{(data.get('caption') or data.get('text') or '')[:90]!r}")
            return {"message_id": 0}
        for attempt in range(3):
            r = requests.post(API.format(token=self.token, method=method), data=data, timeout=30)
            j = r.json()
            if j.get("ok"):
                time.sleep(1.2)                       # rispetta i limiti di Telegram
                return j["result"]
            if j.get("error_code") == 429:            # troppi messaggi: aspetta
                time.sleep(j.get("parameters", {}).get("retry_after", 5) + 1)
                continue
            print(f"  [telegram] errore {method}: {j.get('description')}")
            return None
        return None

    def post_offer(self, chat_id, text, image=""):
        if image:
            res = self.call("sendPhoto", chat_id=chat_id, photo=image, caption=text, parse_mode="HTML")
            if res:
                return res
        return self.call("sendMessage", chat_id=chat_id, text=text, parse_mode="HTML",
                         disable_web_page_preview="false")

    def upsert_pinned(self, chat_id, text, message_id=None):
        """Aggiorna il messaggio fissato dell'hub; se non esiste lo crea e lo fissa."""
        if message_id:
            res = self.call("editMessageText", chat_id=chat_id, message_id=message_id, text=text,
                            parse_mode="HTML", disable_web_page_preview="true")
            if res or self.dry:
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
    lines = [f"{niche['emoji']} <b>{e(title)}</b>", ""]
    if o.get("price"):
        p = f"💰 <b>{eur(o['price'])}</b>"
        if o.get("old_price") and o["old_price"] > o["price"]:
            p += f"  <s>{eur(o['old_price'])}</s>"
        if o.get("discount"):
            p += f"  🔻 -{o['discount']}%"
        lines.append(p)
    if o.get("note"):
        lines.append(f"✅ {e(o['note'])}")
    low = o["title"].lower()
    if niche.get("name", "").startswith("Utensili") and any(h in low for h in config.NO_BATTERY_HINTS):
        lines.append("⚠️ Batteria e caricatore NON inclusi")
    store = "Amazon" if o["source"] in ("amazon", "curated") else "eBay"
    lines += ["", f"👉 <a href=\"{e(o['url'])}\">Vedi l'offerta su {store}</a>"]
    if for_hub:
        lines.append(f"📢 Altre offerte {e(niche['name'])}: {niche['channel']}")
    lines += ["", "<i>Link affiliato · prezzo soggetto a variazioni</i>"]
    return "\n".join(lines)


def format_hub_pinned(site_url):
    lines = [f"📌 <b>Benvenuto in {html.escape(config.BRAND)}!</b>",
             "Scegli i canali che ti interessano 👇", ""]
    for n in config.NICHES.values():
        lines.append(f"{n['emoji']} {html.escape(n['name'])} → {n['channel']}")
    if config.LAMPO.get("enabled"):
        lines.append(f"⚡ Offerte lampo (solo sconti top) → {config.LAMPO['channel']}")
    if config.TELEGRAM_FOLDER_LINK:
        lines += ["", f"➕ <a href=\"{config.TELEGRAM_FOLDER_LINK}\">Iscriviti a tutti con un clic</a>"]
    if site_url:
        lines.append(f"🌐 Sito: {site_url}")
    lines += ["", f"<i>{html.escape(config.DISCLOSURE)}</i>"]
    return "\n".join(lines)
