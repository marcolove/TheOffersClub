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
HUB_MIN_DISCOUNT = 101                        # sconto minimo per finire anche nel canale HUB
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
        "amazon_search_index": "All",
        "keywords": [
            # PC e componenti
            "notebook", "laptop gaming", "mini pc", "pc desktop", "monitor 27 pollici",
            "monitor gaming 144hz", "ssd nvme 1tb", "ssd esterno", "hard disk esterno",
            "memoria ram ddr5", "scheda video", "alimentatore pc", "case pc", "dissipatore cpu",
            # Periferiche
            "mouse gaming", "mouse wireless", "tastiera meccanica", "tastiera wireless",
            "webcam", "microfono usb", "tappetino mouse xxl", "docking station usb c",
            "hub usb c", "stampante multifunzione", "stampante 3d",
            # Audio
            "cuffie bluetooth", "cuffie noise cancelling", "auricolari true wireless",
            "cuffie gaming", "soundbar", "cassa bluetooth", "giradischi",
            # Smartphone e tablet
            "smartphone", "tablet", "ebook reader", "caricatore usb c gan", "powerbank",
            "cavo usb c", "caricatore wireless", "cover smartphone", "pellicola vetro temperato",
            # Smart home e rete
            "router wifi 6", "mesh wifi", "ripetitore wifi", "videocamera sorveglianza wifi",
            "videocitofono smart", "lampadina smart", "presa smart", "termostato smart",
            "echo dot", "fire tv stick", "chromecast",
            # Wearable e foto
            "smartwatch", "smartband", "action cam", "fotocamera mirrorless", "drone",
            "scheda microsd", "chiavetta usb",
            # Gaming
            "console", "controller wireless", "nintendo switch", "ps5", "xbox series",
            "sedia gaming", "visore vr",
            # TV
            "smart tv 55 pollici", "proiettore", "supporto tv da parete",
        ],
        "ebay_queries": ["ssd nvme", "monitor 27", "cuffie bluetooth", "smartwatch",
                         "notebook", "router wifi"],
    },
    "casa": {
        "name": "Casa & Cucina",
        "emoji": "🏠",
        "channel": "@theoffersclub_casa",
        "slug": "offerte-casa-cucina",
        "seo_title": "Offerte casa e cucina di oggi",
        "seo_intro": "Friggitrici ad aria, robot aspirapolvere, macchine da caffè e tutto per la casa in sconto, selezionati ogni giorno.",
        "amazon_search_index": "All",
        "keywords": [
            # Piccoli elettrodomestici cucina
            "friggitrice ad aria", "macchina caffè espresso", "macchina caffè capsule",
            "macchina caffè automatica", "montalatte", "bollitore elettrico", "tostapane",
            "frullatore", "frullatore a immersione", "robot da cucina", "planetaria",
            "impastatrice", "sbattitore elettrico", "estrattore di succo", "centrifuga",
            "macchina sottovuoto", "macchina del pane", "piastra per waffle", "griglia elettrica",
            "forno microonde", "fornetto elettrico", "pentola a pressione", "multicooker",
            "yogurtiera", "macinacaffè",
            # Pentole e accessori
            "set pentole antiaderenti", "padella antiaderente", "set coltelli cucina",
            "tagliere", "contenitori ermetici", "bilancia da cucina", "borraccia termica",
            "set piatti", "bicchieri vetro",
            # Pulizia
            "robot aspirapolvere", "aspirapolvere senza fili", "aspirapolvere senza sacco",
            "lavapavimenti", "scopa elettrica", "pulitore a vapore", "lavavetri elettrico",
            "aspirabriciole",
            # Clima e aria
            "deumidificatore", "purificatore d'aria", "condizionatore portatile",
            "ventilatore a colonna", "stufetta elettrica", "termoventilatore", "umidificatore",
            # Bucato e stiro
            "ferro da stiro a vapore", "ferro con caldaia", "stiratore verticale",
            "asciugatrice", "stendibiancheria",
            # Arredo e comfort
            "materasso memory", "cuscino memory", "set lenzuola", "piumone", "coperta",
            "tende oscuranti", "lampada da terra", "luci led striscia", "organizer armadio",
            # Consumabili (si vendono molto)
            "detersivo lavatrice", "capsule lavastoviglie", "ammorbidente", "carta igienica",
            "sacchetti spazzatura", "capsule caffè", "cialde caffè",
        ],
        "ebay_queries": ["friggitrice ad aria", "robot aspirapolvere", "macchina caffè",
                         "aspirapolvere senza fili", "set pentole"],
    },
    "utensili": {
        "name": "Utensili & Fai da te",
        "emoji": "🔧",
        "channel": "@theoffersclub_Utensili",
        "slug": "offerte-utensili-fai-da-te",
        "seo_title": "Offerte utensili e fai da te di oggi",
        "seo_intro": "Avvitatori, trapani, saldatrici, smerigliatrici, set di attrezzi e giardinaggio di Bosch, Makita, Einhell, DeWalt e altri marchi, in sconto oggi.",
        "amazon_search_index": "All",
        "keywords": [
            # Elettroutensili
            "avvitatore a batteria", "trapano avvitatore", "trapano a percussione",
            "tassellatore", "martello demolitore", "avvitatore a impulsi",
            "chiave a impulsi", "smerigliatrice angolare", "levigatrice orbitale",
            "levigatrice roto orbitale", "pialla elettrica", "fresatrice",
            "multiutensile oscillante", "utensile multifunzione", "sega circolare",
            "seghetto alternativo", "sega a gattuccio", "troncatrice", "sega da banco",
            "pistola termica", "pistola colla a caldo", "pistola per verniciare",
            # Saldatura
            "saldatrice inverter", "saldatrice a filo continuo", "saldatrice mig",
            "saldatrice tig", "saldatore a stagno", "stazione saldante",
            "maschera per saldatura", "saldatrice ad elettrodo",
            # Compressori, idropulitrici, aspiratori
            "compressore", "compressore portatile", "compressore auto", "idropulitrice",
            "aspiratore solidi liquidi", "bidone aspiratutto",
            # Misura e laser
            "livella laser", "metro laser", "rilevatore di metalli", "multimetro digitale",
            "tester elettrico",
            # Attrezzi manuali
            "set cacciaviti", "set chiavi a bussola", "chiave dinamometrica",
            "set chiavi combinate", "pinze", "cassetta attrezzi", "carrello porta attrezzi",
            "valigetta attrezzi", "morsa da banco", "banco da lavoro", "set punte trapano",
            "set inserti avvitatore", "dischi smerigliatrice", "lame sega circolare",
            # Giardino
            "tagliaerba a batteria", "decespugliatore", "tagliasiepi", "motosega",
            "motosega a batteria", "soffiatore foglie", "robot tagliaerba", "biotrituratore",
            "potatore telescopico", "tubo irrigazione", "pompa sommersa",
            # Auto e officina
            "avviatore emergenza auto", "caricabatterie auto", "cric idraulico",
            "lucidatrice auto",
            # Batterie e marchi (offerte su kit e batterie)
            "batteria 18v", "kit batteria caricatore", "bosch professional", "bosch verde",
            "makita", "dewalt", "einhell power x-change", "ryobi one+", "milwaukee",
            "metabo", "stanley", "wera", "parkside",
        ],
        "ebay_queries": ["avvitatore batteria", "saldatrice inverter", "set attrezzi",
                         "smerigliatrice", "idropulitrice", "tagliaerba batteria"],
    },
}
# Parole nel titolo che fanno aggiungere l'avviso "batteria non inclusa"
NO_BATTERY_HINTS = ["senza batteria", "solo corpo", "body only", "batteria non inclusa", "tool only"]

DISCLOSURE = ("In qualità di Affiliato Amazon ricevo un guadagno dagli acquisti idonei. "
              "I prezzi possono cambiare: verifica sempre sulla pagina del prodotto.")
