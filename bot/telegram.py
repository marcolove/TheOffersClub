"""Invio e modifica dei messaggi nei canali Telegram tramite Bot API."""
import html
import json
import random
import time

import requests

import config
from bot import images

API = "https://api.telegram.org/bot{token}/{method}"
CAPTION_MAX = 950          # limite Telegram 1024: resta spazio per la riga "offerta terminata"


class Telegram:
    def __init__(self, token, dry_run=False):
        self.token, self.dry = token, dry_run
        self.last_error = ""

    def call(self, method, files=None, **data):
        self.last_error = ""
        if self.dry:
            print(f"  [dry-run] {method} -> {data.get('chat_id')}: "
                  f"{(data.get('caption') or data.get('text') or '')[:90]!r}"
                  f"{' +foto' if files or data.get('photo') else ''}")
            return {"message_id": 0}
        for attempt in range(3):
            try:
                r = requests.post(API.format(token=self.token, method=method), data=data,
                                  files=files, timeout=60)
                j = r.json()
            except Exception as e:                   # rete o risposta non valida: riprova
                print(f"  [telegram] {method}: {e}")
                time.sleep(3)
                continue
            if j.get("ok"):
                time.sleep(1.2)                       # rispetta i limiti di Telegram
                return j["result"] if isinstance(j["result"], dict) else {"ok": True}
            if j.get("error_code") == 429:            # troppi messaggi: aspetta
                time.sleep(j.get("parameters", {}).get("retry_after", 5) + 1)
                continue
            self.last_error = j.get("description", "")
            if "message is not modified" not in self.last_error:
                print(f"  [telegram] errore {method} su {data.get('chat_id')}: {self.last_error}")
            return None
        return None

    # ------------------------------------------------------------------ pubblicazione
    def post_offer(self, chat_id, text, image="", markup=None, preview_url=""):
        """Foto (formato fisso, preparata dal bot) con didascalia: nessuna anteprima del link,
        quindi niente scritte aggiunte da Telegram. Se la foto non è utilizzabile pubblica solo
        il testo. Il risultato contiene _kind = "photo" oppure "text"."""
        extra = {"reply_markup": json.dumps(markup)} if markup else {}
        if image and len(text) <= CAPTION_MAX:
            data = images.prepared(image)
            res = None
            if data:
                res = self.call("sendPhoto", files={"photo": ("foto.jpg", data)}, chat_id=chat_id,
                                caption=text, parse_mode="HTML", **extra)
            if not res:                                # ripiego: foto originale dall'indirizzo
                res = self.call("sendPhoto", chat_id=chat_id, photo=image, caption=text,
                                parse_mode="HTML", **extra)
            if res:
                res["_kind"] = "photo"
                return res
            print("  [telegram] foto non pubblicata: invio solo il testo")
        if preview_url:
            lp = {"url": preview_url, "prefer_large_media": True, "show_above_text": True}
            res = self.call("sendMessage", chat_id=chat_id, text=text, parse_mode="HTML",
                            link_preview_options=json.dumps(lp), **extra)
        else:
            res = self.call("sendMessage", chat_id=chat_id, text=text, parse_mode="HTML",
                            disable_web_page_preview="true", **extra)
        if res:
            res["_kind"] = "text"
        return res

    # ------------------------------------------------------------------ offerta terminata
    def mark_expired(self, msg, new_text, image_url="", image_label=""):
        """Modifica un post già pubblicato: testo con la riga di scadenza e, se è una foto,
        immagine grigia con la scritta. Nessuna notifica agli iscritti."""
        chat, mid = msg["chat"], msg["id"]
        extra = {"reply_markup": msg["markup"]} if msg.get("markup") else {}
        if msg.get("kind") == "photo":
            data = images.expired(image_url, image_label) if (image_url and image_label) else None
            if data:
                media = {"type": "photo", "media": "attach://foto", "caption": new_text,
                         "parse_mode": "HTML"}
                if self.call("editMessageMedia", files={"foto": ("foto.jpg", data)}, chat_id=chat,
                             message_id=mid, media=json.dumps(media), **extra):
                    return True
            res = self.call("editMessageCaption", chat_id=chat, message_id=mid, caption=new_text,
                            parse_mode="HTML", **extra)
        else:
            res = self.call("editMessageText", chat_id=chat, message_id=mid, text=new_text,
                            parse_mode="HTML", disable_web_page_preview="true", **extra)
        # post già modificato o cancellato a mano: va bene così, non riprovare
        gone = any(s in self.last_error for s in ("message is not modified", "message to edit not found"))
        return bool(res) or gone

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


def channel_link(channel, label):
    """Testo cliccabile verso il canale: si vede il nome (label), non lo @username."""
    username = channel.lstrip("@")
    return f'<a href="https://t.me/{html.escape(username)}">{html.escape(label, quote=False)}</a>'


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

# Frasi di apertura (usate a caso circa metà delle volte)
OPENERS = [
    "Occhio a questo 👀", "Da tenere d'occhio", "Segnalazione del giorno", "Per chi lo cercava",
    "Questo merita", "Nuovo arrivo nel club", "Ve lo segnalo", "Scelto per voi",
]
OPENERS_HOT = [
    "Sconto pazzesco!", "Questo vola via", "Prezzo da non perdere", "Ribasso forte!",
    "Non capita spesso", "Offerta top di oggi",
]

# Righe prezzo: {p}=prezzo, {o}=prezzo vecchio
PRICE_TEMPLATES = [
    "{e} <b>A {p}</b> invece di <s>{o}</s>",
    "{e} <b>{p}</b> anziché <s>{o}</s>",
    "{e} Ora a <b>{p}</b>, prima <s>{o}</s>",
    "{e} <b>{p}</b> <s>{o}</s>",
    "{e} Scende a <b>{p}</b> (era <s>{o}</s>)",
]
# Riga sconto + risparmio: compare SEMPRE quando c'è uno sconto. {d}=%, {s}=euro risparmiati
SAVING_TEMPLATES = [
    "📉 <b>-{d}%</b> · risparmi {s}",
    "🔻 Sconto <b>{d}%</b> · {s} in meno",
    "🤑 <b>-{d}%</b>, risparmi {s}",
    "📉 Risparmi {s} (<b>-{d}%</b>)",
]

# Avviso affiliato: sempre presente, in una sola riga. {dt} = data del prezzo
DISCLOSURES = [
    "<i>Link affiliato · prezzo soggetto a variazioni</i>",
    "<i>#affiliato · il prezzo può cambiare</i>",
    "<i>Link affiliato Amazon · verifica il prezzo sulla pagina</i>",
    "<i>#ad link affiliato · prezzi soggetti a variazioni</i>",
]
DISCLOSURES_DATED = [
    "<i>Prezzo del {dt} · può variare · link affiliato Amazon</i>",
    "<i>Prezzo del {dt} · #affiliato · verifica sulla pagina</i>",
    "<i>Prezzo rilevato il {dt} · link affiliato · può cambiare</i>",
]

# Riga che rimanda all'Hub, sotto ogni post dei canali tematici. {a} = parte cliccabile.
# Si può cambiare l'elenco da config.py con HUB_PROMO_LINES = [("testo con {a}", "parte cliccabile"), ...]
HUB_PROMO_LINES = [
    ("🌐 Altre categorie? {a}", "Scopri tutti i canali tematici"),
    ("🧭 Ti interessano altri temi? {a}", "Trovi tutti i canali nell'Hub"),
    ("🚀 Più offerte su altri temi: {a}", "vai all'Hub"),
    ("🎯 Cerchi altro? {a}", "Entra nell'Hub e scegli i canali"),
    ("📢 Il club ha anche altri canali: {a}", "scoprili tutti"),
    ("🗂️ Tutte le categorie in un posto solo: {a}", "apri l'Hub"),
]

# Riga del link: il testo è sempre "Apri su Amazon" (o eBay) e il link è nascosto dietro.
# Cambia solo l'emoji davanti.
LINK_EMOJIS = ["👉", "🛒", "🔎", "🛍️"]
CTA_BUTTONS = ["🛒 Vedi su {s}", "👉 Vai all'offerta", "🔎 Scopri su {s}", "🛍️ Apri su {s}", "🛒 Vedi l'offerta"]


def _pick(lst):
    return random.choice(lst) if lst else ""


def short_title(t, n=70):
    """Titolo breve (i titoli dell'API Amazon sono lunghissimi)."""
    t = t.strip()
    if len(t) <= n:
        return t
    cut = t[:n]
    for sep in (" - ", " | ", ", ", " – "):
        i = cut.rfind(sep)
        if i >= 25:
            return cut[:i].strip()
    return cut[:cut.rfind(" ")].strip() if " " in cut else cut


def link_line(o):
    """'👉 Apri su Amazon' cliccabile: nel post non si vede l'indirizzo del link."""
    store = "eBay" if o.get("source") == "ebay" else "Amazon"
    return f'{_pick(LINK_EMOJIS)} <a href="{html.escape(o["url"], quote=True)}">Apri su {store}</a>'


def hub_promo():
    """Riga breve che porta all'Hub (vuota se HUB_PROMO = False in config.py)."""
    if not getattr(config, "HUB_PROMO", True):
        return ""
    hub = config.HUB.get("channel", "")
    if not hub:
        return ""
    tpl, label = _pick(getattr(config, "HUB_PROMO_LINES", HUB_PROMO_LINES))
    return tpl.format(a=channel_link(hub, label))


def format_offer(o, niche, for_hub=False):
    """Stesso formato per tutte le fonti (CSV, API Amazon, eBay).
    for_hub=True: copia inoltrata sull'Hub (o sul canale Lampo)."""
    e = lambda x: html.escape(x, quote=False)   # gli apostrofi restano apostrofi
    title = short_title(o["title"])
    d = o.get("discount") or 0
    hot = d >= 35
    nid = next((k for k, v in config.NICHES.items() if v is niche), "")
    theme = niche.get("emojis") or THEME_EMOJIS.get(nid) or [niche.get("emoji", "🛒")]
    icon = _pick(HOT_EMOJIS) if hot and random.random() < 0.7 else _pick(theme)

    lines = []
    if random.random() < 0.5:                                   # apertura solo a volte
        lines.append(e(_pick(OPENERS_HOT if hot else OPENERS)))
    lines.append(f"{icon} <b>{e(title)}</b>")                    # titolo sempre in grassetto
    if o.get("note"):
        lines.append(f"{_pick(NOTE_EMOJIS)} {e(o['note'])}")
    low = o["title"].lower()
    if niche.get("name", "").startswith("Utensili") and any(h in low for h in config.NO_BATTERY_HINTS):
        lines.append("⚠️ Batteria e caricatore NON inclusi")

    if o.get("price"):
        lines.append("")                                        # aria prima del prezzo
        pe = _pick(PRICE_EMOJIS)
        if o.get("old_price") and o["old_price"] > o["price"]:
            lines.append(_pick(PRICE_TEMPLATES).format(e=pe, p=eur(o["price"]), o=eur(o["old_price"])))
            if d:
                lines.append(_pick(SAVING_TEMPLATES).format(d=d, s=eur(o["old_price"] - o["price"])))
        else:
            lines.append(f"{pe} <b>{eur(o['price'])}</b>")

    if getattr(config, "POST_STYLE", "testo") == "testo":
        lines += ["", link_line(o)]                             # aria prima del link
    if for_hub:
        lines += ["", f"📢 Altre offerte: {channel_link(niche['channel'], niche['name'])}"]
    else:
        promo = hub_promo()                                     # nei canali tematici: rimando all'Hub
        if promo:
            lines += ["", promo]

    # una sola riga finale: data del prezzo (se c'è un prezzo) + avviso affiliato
    if o.get("price") and o.get("price_date"):
        foot = _pick(DISCLOSURES_DATED).format(dt=o["price_date"])
    else:
        foot = _pick(DISCLOSURES)
    lines += ["", foot]
    return "\n".join(lines)


def expired_text(text, label):
    """Inserisce la riga di scadenza subito sotto "Apri su ...", prima del resto."""
    lines = text.split("\n")
    for i, ln in enumerate(lines):
        if "Apri su " in ln and "<a href" in ln:
            return "\n".join(lines[:i + 1] + ["", label] + lines[i + 1:])
    if len(lines) >= 2 and lines[-2] == "":                     # post vecchio formato: prima del footer
        return "\n".join(lines[:-2] + ["", label] + lines[-2:])
    return f"{text}\n\n{label}"


def build_markup(o, tag=""):
    """Bottoni sotto al post (solo se POST_STYLE = "bottoni")."""
    if getattr(config, "POST_STYLE", "testo") != "bottoni":
        return None
    is_amazon = o["source"] in ("amazon", "curated")
    store = "Amazon" if is_amazon else "eBay"
    rows = [[{"text": random.choice(CTA_BUTTONS).format(s=store), "url": o["url"]}]]
    if is_amazon and tag and getattr(config, "PRIME_BUTTON", False):
        rows.append([{"text": "👑 Prova Prime gratis", "url": f"https://www.amazon.it/provaprime?tag={tag}"}])
    return {"inline_keyboard": rows}


def format_hub_pinned(site_url):
    e = lambda x: html.escape(x, quote=False)
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
