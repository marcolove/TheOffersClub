"""
CONFIGURAZIONE PRINCIPALE
Modifica solo questo file per cambiare nomi, canali, nicchie, orari e parole chiave.
I dati sensibili (token, chiavi) NON vanno qui: vanno nei Secrets di GitHub.
"""
BRAND = "TheOffersClub"                      # nome del brand (usato su sito e post)
SITE_TITLE = "TheOffersClub – Le migliori offerte del giorno"
SITE_TAGLINE = "Solo sconti veri, scelti ogni giorno."
SITE_DESCRIPTION = ("Offerte Amazon selezionate ogni giorno su tecnologia, casa e cucina, "
                    "utensili e cura della persona, con classifiche e guide all'acquisto.")
# False finché il sito è sull'indirizzo gratuito di GitHub: Google non lo indicizza.
# Mettere True SOLO dopo aver collegato il dominio definitivo (es. theoffersclub.it).
SITE_INDEXABLE = False
TELEGRAM_FOLDER_LINK = ""                    # es. "https://t.me/addlist/XXXX" (cartella con tutti i canali)
WHATSAPP_CHANNEL_LINK = ""                   # es. "https://whatsapp.com/channel/XXXX" (facoltativo)
# ------------------------------------------------------------------ Messaggio fissato del General
HUB_DESCRIPTION = ("Qui trovi le offerte migliori di ogni categoria, con sconti dal 25% in su. "
                   "Vuoi tutte le offerte di un tema? Iscriviti al canale che ti interessa.")
SHOW_SITE_IN_PINNED = True                   # link al sito nei messaggi fissati (Hub e canali)
# ------------------------------------------------------------------ Orari (ora italiana)
# Il bot pubblica solo tra MIN_HOUR e MAX_HOUR compresi (es. 8 e 22 = dalle 8:00 alle 22:59).
MIN_HOUR = 8
MAX_HOUR = 22
# ------------------------------------------------------------------ Fasce orarie di punta
# Nelle ore di punta il bot pubblica di più, nelle altre meno (ora italiana).
PEAK_HOURS = [12, 13, 19, 20, 21]            # pranzo e sera
PEAK_MAX_POSTS = 2                           # post massimi per canale a giro nelle ore di punta
OFFPEAK_POST_CHANCE = 0.6                    # fuori punta: probabilità di pubblicare a ogni giro
# ------------------------------------------------------------------ Parole chiave prioritarie
# Le parole in "top_keywords" di ogni nicchia vengono cercate TOP_KEYWORD_WEIGHT volte più spesso
# (prodotti che vendono di più: consumabili, marchi noti). Non cambiano l'equilibrio tra canali.
TOP_KEYWORD_WEIGHT = 3
# ------------------------------------------------------------------ Quantità e filtri
# Con un giro ogni 30 minuti (cron-job.org) e 0-1 post per canale a giro:
# circa 10-15 post al giorno per canale tematico; nel General solo quelli con sconto >= HUB_MIN_DISCOUNT.
MIN_POSTS_PER_NICHE_PER_RUN = 0              # post per canale a ogni giro: da...
MAX_POSTS_PER_NICHE_PER_RUN = 1              # ...a (numero casuale)
REPOST_AFTER_DAYS = 10                       # non ripubblicare lo stesso prodotto prima di N giorni
MIN_DISCOUNT = 15                            # sconto minimo % nei canali tematici
MIN_SAVING_VALUE = 5                         # risparmio minimo in euro (-1 = disattivato); per nicchia: "min_saving"
HUB_MIN_DISCOUNT = 25                        # sconto minimo % per uscire anche nel General
LAMPO_MIN_DISCOUNT = 60                      # non usato (canale Lampo chiuso)
PRICE_MAX_AGE_HOURS = 24                     # i prezzi Amazon API non si mostrano sul sito oltre N ore
EXPIRE_AUTO_HOURS = 0                        # 0 = i post del CSV non scadono mai da soli
TRACK_DAYS = 3                               # giorni in cui il bot ricontrolla i post via API
AMAZON_SEARCHES_PER_ROUND = 3                # ricerche Creators API per giro (limite richieste)
PRIME_BUTTON = True                          # bottone "Prova Prime gratis" (solo con POST_STYLE = "bottoni")
SITE_OFFERS_PER_PAGE = 60                    # offerte per pagina del sito
# Filtro "prodotti veri" (solo offerte automatiche da API Amazon / eBay, non il CSV):
# per ogni nicchia "min_price" = prezzo minimo in euro, "exclude_words" = parole che, se
# compaiono nel titolo, fanno scartare il prodotto (ricambi, accessori). L'elenco generale
# (ricambio, compatibile con, adatto per, cover per, pellicola, usato...) è già nel bot.
# Ogni nicchia ha lo STESSO numero di parole chiave (60): il bot sceglie le ricerche a caso
# tra tutte, quindi così ogni canale viene cercato con la stessa frequenza.
HUB = {
    "channel": "@theoffersclub_hub",         # canale General (offerte dal 25% in su)
    "name": "TheOffersClub – Le migliori offerte",
    "color": "#c04dff",                      # colori del brand sul sito (viola e azzurro neon)
    "color2": "#2fa8ff",
    "logo": "hub",                           # immagine site_assets/img/hub-*.webp
}
LAMPO = {
    "enabled": False,                        # canale chiuso: gli sconti top escono nel General con 🔥
    "channel": "@theoffersclub_lampo",
}
# Le nicchie: una = un canale Telegram + una pagina del sito
# "color" e "logo" = colore e immagine del canale sul sito (site_assets/img/<logo>-*.webp)
NICHES = {
    "tech": {
        "name": "Tech & Gaming",
        "pinned_desc": "PC, monitor, SSD, cuffie, smartphone, smart home, console e accessori gaming: solo offerte con sconto reale, selezionate ogni giorno.",
        "color": "#2fa8ff",
        "logo": "tech",
        "emoji": "💻",
        "channel": "@TheOffersClub_Tech",
        "slug": "offerte-tecnologia",
        "seo_title": "Offerte tecnologia e gaming di oggi",
        "seo_intro": "Le migliori offerte del giorno su PC, monitor, SSD, cuffie, smartphone, smart home e console, aggiornate più volte al giorno.",
        "amazon_search_index": "All",
        "min_price": 10,
        "min_saving": 5,                          # risparmio minimo in euro
        "top_keywords": ["cuffie bluetooth", "auricolari true wireless", "ssd esterno", "powerbank",
                         "echo dot", "fire tv stick", "smartwatch", "mouse wireless", "tablet",
                         "smartphone", "caricatore usb c gan", "presa smart"],
        "exclude_words": ["cavo usb", "cavo hdmi", "cavo di ricarica", "cavi usb", "custodia",
                          "supporto per", "adattatore", "protezione schermo"],
        "keywords": [
            # PC e componenti
            "notebook", "laptop gaming", "mini pc", "pc desktop", "monitor 27 pollici",
            "monitor gaming 144hz", "ssd nvme 1tb", "ssd esterno", "hard disk esterno",
            "memoria ram ddr5", "scheda video", "alimentatore pc",
            # Periferiche
            "mouse gaming", "mouse wireless", "tastiera meccanica", "tastiera wireless",
            "webcam", "microfono usb", "docking station usb c", "stampante multifunzione",
            "stampante 3d",
            # Audio
            "cuffie bluetooth", "cuffie noise cancelling", "auricolari true wireless",
            "cuffie gaming", "soundbar", "cassa bluetooth",
            # Smartphone e tablet
            "smartphone", "tablet", "ebook reader", "caricatore usb c gan", "powerbank",
            "caricatore wireless",
            # Smart home e rete
            "router wifi 6", "mesh wifi", "ripetitore wifi", "videocamera sorveglianza wifi",
            "videocitofono smart", "lampadina smart", "presa smart", "termostato smart",
            "echo dot", "fire tv stick",
            # Wearable e foto
            "smartwatch", "smartband", "action cam", "fotocamera mirrorless", "drone",
            # Gaming
            "console", "controller wireless", "nintendo switch", "ps5", "xbox series",
            "sedia gaming", "visore vr",
            # TV
            "smart tv 55 pollici", "smart tv 65 pollici", "proiettore", "supporto tv da parete",
            "chromecast",
        ],
        "ebay_queries": ["ssd nvme", "monitor 27", "cuffie bluetooth", "smartwatch",
                         "notebook", "router wifi"],
    },
    "casa": {
        "name": "Casa & Cucina",
        "pinned_desc": "Piccoli elettrodomestici, pulizia, clima, pentole e le scorte per la casa (detersivi, capsule caffè, carta) in sconto, selezionati ogni giorno.",
        "color": "#5cff3a",
        "logo": "casa",
        "emoji": "🏠",
        "channel": "@theoffersclub_casa",
        "slug": "offerte-casa-cucina",
        "seo_title": "Offerte casa e cucina di oggi",
        "seo_intro": "Friggitrici ad aria, robot aspirapolvere, macchine da caffè, pulizia e scorte per la casa in sconto, selezionati ogni giorno.",
        "amazon_search_index": "All",
        "min_price": 10,
        "min_saving": 3,                          # risparmio minimo in euro
        "top_keywords": ["capsule lavastoviglie", "detersivo lavatrice", "capsule lavatrice",
                         "ammorbidente", "carta igienica", "capsule caffè", "cialde caffè",
                         "friggitrice ad aria", "robot aspirapolvere", "aspirapolvere senza fili",
                         "pile alcaline", "sacchetti spazzatura"],
        "exclude_words": ["sacchetti per", "spazzole", "panni", "mop di ricambio", "testine"],
        "keywords": [
            # Piccoli elettrodomestici cucina
            "friggitrice ad aria", "macchina caffè espresso", "macchina caffè capsule",
            "macchina caffè automatica", "montalatte", "bollitore elettrico", "tostapane",
            "frullatore", "frullatore a immersione", "robot da cucina", "planetaria",
            "estrattore di succo", "macchina sottovuoto", "forno microonde", "fornetto elettrico",
            "multicooker", "macinacaffè",
            # Pentole e accessori
            "set pentole antiaderenti", "padella antiaderente", "set coltelli cucina",
            "contenitori ermetici", "bilancia da cucina", "borraccia termica",
            # Pulizia
            "robot aspirapolvere", "aspirapolvere senza fili", "lavapavimenti",
            "pulitore a vapore", "lavavetri elettrico",
            # Clima e aria
            "deumidificatore", "purificatore d'aria", "condizionatore portatile",
            "ventilatore a colonna", "stufetta elettrica", "umidificatore",
            # Bucato e stiro
            "ferro da stiro a vapore", "ferro con caldaia", "stiratore verticale",
            # Arredo e comfort
            "materasso memory", "cuscino memory", "set lenzuola", "piumone",
            "luci led striscia",
            # Consumabili (si vendono molto)
            "detersivo lavatrice", "capsule lavatrice", "ammorbidente", "smacchiatore bucato",
            "capsule lavastoviglie", "brillantante lavastoviglie", "detersivo piatti",
            "detergente pavimenti", "sgrassatore", "carta igienica", "rotoli carta cucina",
            "sacchetti spazzatura", "capsule caffè", "cialde caffè", "caffè in grani",
            "capsule nespresso compatibili", "filtri caraffa", "pile alcaline",
        ],
        "ebay_queries": ["friggitrice ad aria", "robot aspirapolvere", "macchina caffè",
                         "aspirapolvere senza fili", "set pentole"],
    },
    "utensili": {
        "name": "Utensili & Fai da te",
        "pinned_desc": "Trapani, avvitatori, saldatrici, attrezzi manuali, giardino e auto dei migliori marchi: solo kit completi e prodotti veri, niente ricambi.",
        "color": "#ff8a00",
        "logo": "utensili",
        "emoji": "🔧",
        "channel": "@theoffersclub_Utensili",
        "slug": "offerte-utensili-fai-da-te",
        "seo_title": "Offerte utensili e fai da te di oggi",
        "seo_intro": "Avvitatori, trapani, saldatrici, smerigliatrici, set di attrezzi, giardino e auto di Bosch, Makita, Einhell, DeWalt e altri marchi, in sconto oggi.",
        "amazon_search_index": "All",
        "min_price": 15,
        "min_saving": 5,                          # risparmio minimo in euro
        "top_keywords": ["avvitatore a batteria", "trapano avvitatore", "bosch professional avvitatore",
                         "makita avvitatore", "einhell power x-change kit", "set chiavi a bussola",
                         "valigetta attrezzi", "idropulitrice", "compressore auto",
                         "avviatore emergenza auto", "livella laser", "tagliaerba a batteria"],
        "exclude_words": ["set di dischi", "set dischi", "dischi da taglio", "dischi abrasivi",
                          "set di punte", "set punte", "inserti", "lame di ricambio",
                          "spazzole carbone"],
        "keywords": [
            # Elettroutensili
            "avvitatore a batteria", "trapano avvitatore", "trapano a percussione",
            "tassellatore", "avvitatore a impulsi", "chiave a impulsi",
            "smerigliatrice angolare", "levigatrice orbitale", "multiutensile oscillante",
            "sega circolare", "seghetto alternativo", "sega a gattuccio", "troncatrice",
            "pistola termica", "pistola colla a caldo", "pistola per verniciare",
            # Saldatura
            "saldatrice inverter", "saldatrice a filo continuo", "saldatore a stagno",
            "stazione saldante", "maschera per saldatura",
            # Compressori, idropulitrici, aspiratori
            "compressore", "compressore portatile", "idropulitrice", "aspiratore solidi liquidi",
            # Misura e laser
            "livella laser", "metro laser", "multimetro digitale",
            # Attrezzi manuali
            "set cacciaviti", "set chiavi a bussola", "chiave dinamometrica",
            "cassetta attrezzi", "carrello porta attrezzi", "valigetta attrezzi", "morsa da banco",
            # Giardino
            "tagliaerba a batteria", "decespugliatore", "tagliasiepi", "motosega a batteria",
            "soffiatore foglie", "robot tagliaerba", "potatore telescopico",
            # Auto e officina
            "avviatore emergenza auto", "caricabatterie auto", "compressore auto",
            "cric idraulico", "lucidatrice auto", "aspirapolvere auto",
            # Kit e marchi (sempre abbinati a un prodotto, per evitare i ricambi)
            "kit batteria caricatore", "bosch professional trapano", "bosch professional avvitatore",
            "makita trapano", "makita avvitatore", "dewalt trapano", "dewalt avvitatore",
            "einhell power x-change kit", "ryobi one+ kit", "milwaukee avvitatore",
            "metabo avvitatore", "parkside kit",
        ],
        "ebay_queries": ["avvitatore batteria", "saldatrice inverter", "set attrezzi",
                         "smerigliatrice", "idropulitrice", "tagliaerba batteria"],
    },
    "persona": {
        "name": "Cura Persona & Salute",
        "pinned_desc": "Trucco, skincare, shampoo e maschere professionali, profumi, piastre, rasoi, spazzolini elettrici e integratori in sconto, selezionati ogni giorno.",
        "color": "#ff2d55",
        "logo": "persona",
        "emoji": "🧴",
        "emojis": ["🧴", "🪒", "💆", "🦷", "💄", "💅", "💋", "🧼", "💪", "🌿", "✨", "🩺"],
        "channel": "@theoffersclub_persona",
        "slug": "offerte-cura-persona",
        "seo_title": "Offerte cura della persona, beauty e salute di oggi",
        "seo_intro": "Trucco, skincare, shampoo e maschere professionali, profumi, piastre, rasoi, spazzolini elettrici e integratori in sconto, selezionati ogni giorno.",
        "amazon_search_index": "All",
        "min_price": 6,
        "min_saving": 2,                          # risparmio minimo in euro
        "top_keywords": ["spazzolino elettrico", "rasoio elettrico", "regolabarba", "asciugacapelli",
                         "piastra capelli", "profumo donna", "profumo uomo", "mascara",
                         "crema viso antirughe", "shampoo professionale",
                         "kerastase", "proteine whey"],
        "exclude_words": ["testine", "lame di ricambio", "beccucci", "campione", "tester",
                          "flacone vuoto", "flaconi vuoti", "dispenser vuoto"],
        "keywords": [
            # Rasatura, depilazione e styling (10)
            "rasoio elettrico", "regolabarba", "tagliacapelli", "epilatore", "luce pulsata",
            "asciugacapelli", "piastra capelli", "arricciacapelli", "spazzola asciugacapelli",
            "styler multifunzione capelli",
            # Haircare, anche fascia alta (10)
            "shampoo", "balsamo capelli", "maschera capelli", "olio per capelli",
            "shampoo professionale", "kerastase", "olaplex", "davines", "shampoo anticaduta",
            "tinta capelli",
            # Skincare viso (10)
            "crema viso antirughe", "siero viso", "siero vitamina c", "retinolo",
            "contorno occhi", "maschera viso", "detergente viso", "acqua micellare",
            "crema solare viso spf 50", "la roche posay",
            # Trucco e unghie (12)
            "fondotinta", "correttore", "cipria", "palette ombretti", "mascara", "eyeliner",
            "rossetto", "matita sopracciglia", "set pennelli trucco", "kit trucco",
            "smalto semipermanente", "lampada uv unghie",
            # Corpo e profumi (8)
            "crema corpo", "crema anticellulite", "deodorante donna", "deodorante uomo",
            "profumo donna", "profumo uomo", "cofanetto profumo", "kit cura barba",
            # Igiene orale (3)
            "spazzolino elettrico", "idropulsore dentale", "kit sbiancamento denti",
            # Salute e integratori (7)
            "misuratore di pressione", "bilancia pesapersone smart", "pistola massaggiante",
            "proteine whey", "creatina", "integratore magnesio", "collagene",
        ],
        "ebay_queries": ["rasoio elettrico", "spazzolino elettrico", "asciugacapelli",
                         "profumo donna", "piastra capelli", "palette trucco"],
    },
}
# Parole nel titolo che fanno aggiungere l'avviso "batteria non inclusa"
NO_BATTERY_HINTS = ["senza batteria", "solo corpo", "body only", "batteria non inclusa", "tool only"]
DISCLOSURE = ("In qualità di Affiliato Amazon ricevo un guadagno dagli acquisti idonei. "
              "I prezzi possono cambiare: verifica sempre sulla pagina del prodotto.")
