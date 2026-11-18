"""
CONFIGURAZIONE PRINCIPALE
Modifica solo questo file per cambiare nomi, canali, nicchie, orari e parole chiave.
I dati sensibili (token, chiavi) NON vanno qui: vanno nei Secrets di GitHub.
"""

BRAND = "TheOffersClub"                      # nome del brand (usato su sito e post)
SITE_TITLE = "TheOffersClub – Le migliori offerte del giorno"
SITE_DESCRIPTION = ("Offerte Amazon selezionate ogni giorno su tecnologia, casa, "
                    "utensili e fai da te. Iscriviti ai canali Telegram gratuiti.")
TELEGRAM_FOLDER_LINK = ""                    # es. "https://t.me/addlist/XXXX" (cartella con tutti i canali)
WHATSAPP_CHANNEL_LINK = ""                   # es. "https://whatsapp.com/channel/XXXX" (facoltativo)

# ------------------------------------------------------------------ Messaggio fissato dell'Hub
# Breve descrizione mostrata sotto il titolo di benvenuto
HUB_DESCRIPTION = ("Ogni giorno selezioniamo le offerte più interessanti, divise per categoria. "
                   "Iscriviti solo ai canali che ti interessano: niente spam, solo sconti utili.")
SHOW_SITE_IN_PINNED = False                  # True per mostrare il link al sito nel messaggio fissato

# ------------------------------------------------------------------ Orari (ora italiana)
# Il bot pubblica solo tra MIN_HOUR e MAX_HOUR compresi (es. 8 e 22 = dalle 8:00 alle 22:59).
# Il sito si aggiorna comunque a ogni giro.
MIN_HOUR = 8
MAX_HOUR = 22

# ------------------------------------------------------------------ Quantità e filtri
MIN_POSTS_PER_NICHE_PER_RUN = 1              # post per nicchia a ogni giro (ogni 2 ore): da...
MAX_POSTS_PER_NICHE_PER_RUN = 1              # ...a (numero casuale)
REPOST_AFTER_DAYS = 10                       # non ripubblicare lo stesso prodotto prima di N giorni
MIN_DISCOUNT = 15                            # sconto minimo % per le offerte con prezzo
MIN_SAVING_VALUE = 5                         # risparmio minimo in euro (-1 = disattivato)
HUB_MIN_DISCOUNT = 40                        # sconto minimo per finire anche nel canale HUB
LAMPO_MIN_DISCOUNT = 60                      # sconto minimo per il canale LAMPO (se attivo)
PRICE_MAX_AGE_HOURS = 24                     # i prezzi Amazon API non si mostrano sul sito oltre N ore
PRIME_BUTTON = True                          # bottone "Prova Prime gratis" sotto i post Amazon
SITE_OFFERS_PER_PAGE = 60                    # offerte per pagina del sito

HUB = {
    "channel": "@theoffersclub_hub",         # canale principale
    "name": "Hub TheOffersClub",
}

LAMPO = {
    "enabled": False,                        # metti True quando apri il canale
    "channel": "@theoffersclub_lampo",
}

# Le nicchie: una = un canale Telegram + una pagina del sito
NICHES = {
    "tech": {
        "name": "Tech & Gaming",
        "emoji": "💻",
        "channel": "@TheOffersClub_Tech",
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
        "channel": "@theoffersclub_casa",
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
        "channel": "@theoffersclub_Utensili",
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
    #     "name": "Bimbi & Giocattoli", "emoji": "🧸", "channel": "@theoffersclub_kids",
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
