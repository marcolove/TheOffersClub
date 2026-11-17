"""Invio messaggi ai canali Telegram tramite Bot API."""
import html
import json
import random
import time

import requests

import config

API = "https://api.telegram.org/bot{token}/{method}"

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
            print("  [telegram] immagine non accettata: pubblico solo il testo")
        return self.call("sendMessage", chat_id=chat_id, text=text, parse_mode="HTML",
                         disable_web_page_preview="true", **extra)

    def upsert_pinned(self, chat_id, text, message_id=None):
        """Aggiorna il messaggio fissato dell'hub; se non esiste lo crea e lo fissa."""
        if message_id:
            res = self.call("editMessageText", chat_id=chat_id, message_id=message_id, text=text,
                            parse_mode="HTML", disable_web_page_preview="true")
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


def channel_link(channel, label):
    """Testo cliccabile verso il canale: si vede il nome (label), non lo @username."""
    username = channel.lstrip("@")
    return f'<a href="https://t.me/{html.escape(username)}">{html.escape(label)}</a>'


# ------------------------------------------------------------------ Varietà dei post
# Emoji a tema per nicchia (chiave = id nicchia in config.NICHES). Si possono
# sovrascrivere aggiungendo "emojis": [...] alla nicchia in config.py.
THEME_EMOJIS = {
    "tech": ["💻", "🎮", "🎧", "🖥️", "📱", "⌨️", "🖱️", "🔌", "📡", "🕹️"],
    "casa": ["🏠", "🛋️", "🍳", "🧺", "🧼", "☕", "🍽️", "🧽", "🪴", "🛁"],
    "utensili": ["🔧", "🔨", "🪛", "🧰", "⚙️", "🪚", "🔩", "🛠️", "🏗️", "🪜"],
    "bimbi": ["🧸", "🎲", "🧩", "🎈", "🪀", "🚂", "🎨"],
}
HOT_EMOJIS = ["🔥", "💣", "🚨", "⚡", "😱", "🤑"]
PRICE_EMOJIS = ["💰", "💶", "🏷️", "💸"]
NOTE_EMOJIS = ["✅", "👉", "💡", "⭐", "📌"]

# Frasi di apertura (facoltative, usate a caso circa metà delle volte)
OPENERS = [
    "Occhio a questo 👀", "Da tenere d'occhio", "Segnalazione del giorno", "Per chi lo cercava",
    "Questo merita", "Nuovo arrivo nel club", "Ve lo segnalo", "Scelto per voi",
]
OPENERS_HOT = [
    "Sconto pazzesco!", "Questo vola via", "Prezzo da non perdere", "Ribasso forte!",
    "Non capita spesso", "Offerta top di oggi",
]

# Righe prezzo: {p}=prezzo, {o}=prezzo vecchio, {d}=sconto %
PRICE_TEMPLATES = [
    "{e} <b>A {p}</b> invece di <s>{o}</s>",
    "{e} <b>{p}</b> anziché <s>{o}</s> (-{d}%)",
    "{e} Ora a <b>{p}</b>, prima <s>{o}</s>",
    "{e} <b>{p}</b> <s>{o}</s> · -{d}%",
    "{e} Scende a <b>{p}</b> (era <s>{o}</s>)",
]
SAVING_TEMPLATES = [
    "📉 Risparmi {s}", "📉 {s} in meno", "🤑 Risparmio di {s}", "", "",
]

PHRASES_BASE = [
    "Prezzo interessante: controlla le recensioni prima di acquistare.",
    "Un buon prezzo per questo prodotto.",
    "Vale un'occhiata se lo stavi cercando.",
    "", "",
]
PHRASES_35 = [
    "Sconto importante: da guardare.",
    "Ribasso notevole rispetto al prezzo di listino.",
    "Bel taglio di prezzo.", "",
]
PHRASES_50 = [
    "Sconto molto alto: da guardare subito.",
    "Ribasso davvero forte, controlla i dettagli.",
    "Metà prezzo o quasi!", "",
]

# Avviso affiliato: sempre presente, cambia solo la forma
DISCLOSURES = [
    "<i>Link affiliato · prezzo soggetto a variazioni</i>",
    "<i>#affiliato · il prezzo può cambiare</i>",
    "<i>Link affiliato Amazon · verifica il prezzo sulla pagina</i>",
    "<i>#ad link affiliato · prezzi soggetti a variazioni</i>",
]


def _pick(lst):
    return random.choice(lst) if lst else ""


def format_offer(o, niche, for_hub=False):
    e = html.escape
    title = o["title"] if len(o["title"]) < 140 else o["title"][:137] + "…"
    d = o.get("discount") or 0
    hot = d >= 35
    nid = next((k for k, v in config.NICHES.items() if v is niche), "")
    theme = niche.get("emojis") or THEME_EMOJIS.get(nid) or [niche.get("emoji", "🛒")]
    icon = _pick(HOT_EMOJIS) if hot and random.random() < 0.7 else _pick(theme)

    lines = []
    if random.random() < 0.5:                                   # apertura solo a volte
        lines.append(f"<b>{e(_pick(OPENERS_HOT if hot else OPENERS))}</b>")
    lines.append(f"{icon} {e(title)}" if random.random() < 0.4 else f"{icon} <b>{e(title)}</b>")
    if o.get("note"):
        lines.append(f"{_pick(NOTE_EMOJIS)} {e(o['note'])}")
    low = o["title"].lower()
    if niche.get("name", "").startswith("Utensili") and any(h in low for h in config.NO_BATTERY_HINTS):
        lines.append("⚠️ Batteria e caricatore NON inclusi")

    if o.get("price"):
        pe = _pick(PRICE_EMOJIS)
        if o.get("old_price") and o["old_price"] > o["price"]:
            tpl = _pick(PRICE_TEMPLATES)
            if not d:
                tpl = PRICE_TEMPLATES[0]
            lines.append(tpl.format(e=pe, p=eur(o["price"]), o=eur(o["old_price"]), d=d))
            sv = _pick(SAVING_TEMPLATES)
            if sv:
                lines.append(sv.format(s=eur(o["old_price"] - o["price"])))
        else:
            lines.append(f"{pe} <b>{eur(o['price'])}</b>")
        if o.get("manual_price"):
            lines.append("<i>Prezzo al momento della pubblicazione</i>")
        else:
            ph = _pick(PHRASES_50 if d >= 50 else PHRASES_35 if d >= 35 else PHRASES_BASE)
            if ph:
                lines.append(ph)
    if for_hub:
        lines += ["", f"📢 Altre offerte: {channel_link(niche['channel'], niche['name'])}"]
    lines += ["", _pick(DISCLOSURES)]
    return "\n".join(lines)


CTA_BUTTONS = ["🛒 Vedi su {s}", "👉 Vai all'offerta", "🔎 Scopri su {s}", "🛍️ Apri su {s}", "🛒 Vedi l'offerta"]


def build_markup(o, tag=""):
    """Bottoni sotto al post: offerta + prova Prime (solo per prodotti Amazon)."""
    is_amazon = o["source"] in ("amazon", "curated")
    store = "Amazon" if is_amazon else "eBay"
    rows = [[{"text": random.choice(CTA_BUTTONS).format(s=store), "url": o["url"]}]]
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
        lines.append(f"{n['emoji']} {channel_link(n['channel'], n['name'])}")
    if config.LAMPO.get("enabled"):
        lines.append(f"⚡ {channel_link(config.LAMPO['channel'], 'Offerte lampo')} (solo sconti top)")
    if config.TELEGRAM_FOLDER_LINK:
        lines += ["", f"➕ <a href=\"{config.TELEGRAM_FOLDER_LINK}\">Iscriviti a tutti con un clic</a>"]
    if site_url and getattr(config, "SHOW_SITE_IN_PINNED", False):
        lines.append(f"🌐 Sito: {site_url}")
    lines += ["", f"<i>{e(config.DISCLOSURE)}</i>"]
    return "\n".join(lines)
