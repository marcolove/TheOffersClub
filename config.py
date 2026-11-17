"""
CONFIGURAZIONE PRINCIPALE
Modifica solo questo file per cambiare nomi, canali, nicchie e parole chiave.
I dati sensibili (token, chiavi) NON vanno qui: vanno nei Secrets di GitHub.
"""

BRAND = "OfferteSmart"                       # nome del brand (usato su sito e post)
SITE_TITLE = "OfferteSmart – Le migliori offerte del giorno"
SITE_DESCRIPTION = ("Offerte Amazon selezionate ogni giorno su tecnologia, casa, "
                    "utensili e fai da te. Iscriviti ai canali Telegram gratuiti.")
TELEGRAM_FOLDER_LINK = ""                    # es. "https://t.me/addlist/XXXX" (passo 2.6 del README)
WHATSAPP_CHANNEL_LINK = ""                   # es. "https://whatsapp.com/channel/XXXX" (facoltativo)

# Quante offerte al massimo per canale a ogni esecuzione (ogni 2 ore)
MAX_POSTS_PER_NICHE_PER_RUN = 2
# Non ripubblicare lo stesso prodotto prima di N giorni
REPOST_AFTER_DAYS = 10
# Sconto minimo per finire anche nel canale HUB
HUB_MIN_DISCOUNT = 40
# Sconto minimo per finire nel canale LAMPO (se configurato)
LAMPO_MIN_DISCOUNT = 60
# Quante offerte tenere in ogni pagina del sito
SITE_OFFERS_PER_PAGE = 60

HUB = {
    "channel": "@OfferteSmartIT",            # <-- il tuo canale principale
    "name": "Hub OfferteSmart",
}

LAMPO = {
    "enabled": False,                        # metti True quando apri il canale
    "channel": "@OfferteSmartLampo",
}

# Le nicchie: una = un canale Telegram + una pagina del sito
NICHES = {
    "tech": {
        "name": "Tech & Gaming",
        "emoji": "💻",
        "channel": "@OfferteSmartTech",
        "slug": "offerte-tecnologia",
        "seo_title": "Offerte tecnologia e gaming di oggi",
        "seo_intro": "Le migliori offerte del giorno su PC, monitor, SSD, cuffie, smartphone e console, aggiornate automaticamente più volte al giorno.",
        "amazon_search_index": "Electronics",
        "keywords": ["ssd", "monitor", "cuffie bluetooth", "mouse gaming", "tastiera meccanica",
                     "smartwatch", "powerbank", "router wifi", "chiavetta usb", "webcam"],
        "ebay_queries": ["ssd nvme", "monitor 27", "cuffie bluetooth"],
    },
    "casa": {
        "name": "Casa & Cucina",
        "emoji": "🏠",
        "channel": "@OfferteSmartCasa",
        "slug": "offerte-casa-cucina",
        "seo_title": "Offerte casa e cucina di oggi",
        "seo_intro": "Friggitrici ad aria, robot aspirapolvere, macchine da caffè e tutto per la casa in sconto, selezionati ogni giorno.",
        "amazon_search_index": "HomeAndKitchen",
        "keywords": ["friggitrice ad aria", "robot aspirapolvere", "macchina caffè", "frullatore",
                     "set pentole", "aspirapolvere senza fili", "deumidificatore", "bilancia cucina"],
        "ebay_queries": ["friggitrice ad aria", "robot aspirapolvere"],
    },
    "utensili": {
        "name": "Utensili & Fai da te",
        "emoji": "🔧",
        "channel": "@OfferteSmartUtensili",
        "slug": "offerte-utensili-fai-da-te",
        "seo_title": "Offerte utensili e fai da te di oggi",
        "seo_intro": "Avvitatori, trapani, smerigliatrici, set di attrezzi e giardinaggio di Bosch, Makita, Einhell, DeWalt e altri marchi, in sconto oggi.",
        "amazon_search_index": "Tools",
        "keywords": ["avvitatore batteria", "trapano percussione", "smerigliatrice", "set cacciaviti",
                     "cassetta attrezzi", "idropulitrice", "compressore", "levigatrice",
                     "bosch professional", "makita", "einhell", "dewalt"],
        "ebay_queries": ["avvitatore batteria", "set attrezzi"],
    },
    # Esempio di nicchia da attivare più avanti: togli il commento
    # "bimbi": {
    #     "name": "Bimbi & Giocattoli", "emoji": "🧸", "channel": "@OfferteSmartBimbi",
    #     "slug": "offerte-giocattoli-bambini", "seo_title": "Offerte giocattoli e bambini di oggi",
    #     "seo_intro": "LEGO, giochi, pannolini e articoli per l'infanzia in sconto.",
    #     "amazon_search_index": "Toys", "keywords": ["lego", "pannolini", "gioco da tavolo"],
    #     "ebay_queries": ["lego"],
    # },
}

# Parole nel titolo che fanno aggiungere l'avviso "batteria non inclusa"
NO_BATTERY_HINTS = ["senza batteria", "solo corpo", "body only", "batteria non inclusa", "tool only"]

DISCLOSURE = ("In qualità di Affiliato Amazon ricevo un guadagno dagli acquisti idonei. "
              "I prezzi possono cambiare: verifica sempre sulla pagina del prodotto.")
