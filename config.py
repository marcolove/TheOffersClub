"""
CONFIGURAZIONE PRINCIPALE
Modifica solo questo file per cambiare nomi, canali, nicchie, orari e parole chiave.
I dati sensibili (token, chiavi) NON vanno qui: vanno nei Secrets di GitHub.
"""
BRAND = "TheOffersClub"                      # nome del brand (usato su sito e post)
SITE_TITLE = "TheOffersClub – Le migliori offerte del giorno"
SITE_DESCRIPTION = ("Offerte Amazon selezionate ogni giorno su tecnologia, casa e cucina, "
                    "utensili e cura della persona. Iscriviti ai canali Telegram gratuiti.")
TELEGRAM_FOLDER_LINK = ""                    # es. "https://t.me/addlist/XXXX" (cartella con tutti i canali)
WHATSAPP_CHANNEL_LINK = ""                   # es. "https://whatsapp.com/channel/XXXX" (facoltativo)
# ------------------------------------------------------------------ Messaggio fissato del General
HUB_DESCRIPTION = ("Qui trovi le offerte migliori di ogni categoria, con sconti dal 25% in su. "
                   "Vuoi tutte le offerte di un tema? Iscriviti al canale che ti interessa.")
SHOW_SITE_IN_PINNED = False                  # True per mostrare il link al sito nel messaggio fissato
# ------------------------------------------------------------------ Orari (ora italiana)
# Il bot pubblica solo tra MIN_HOUR e MAX_HOUR compresi (es. 8 e 22 = dalle 8:00 alle 22:59).
MIN_HOUR = 8
MAX_HOUR = 22
# ------------------------------------------------------------------ Quantità e filtri
# Con un giro ogni 30 minuti (cron-job.org) e 0-1 post per canale a giro:
# circa 10-15 post al giorno per canale tematico; nel General solo quelli con sconto >= HUB_MIN_DISCOUNT.
MIN_POSTS_PER_NICHE_PER_RUN = 0              # post per canale a ogni giro: da...
MAX_POSTS_PER_NICHE_PER_RUN = 1              # ...a (numero casuale)
REPOST_AFTER_DAYS = 10                       # non ripubblicare lo stesso prodotto prima di N giorni
MIN_DISCOUNT = 15                            # sconto minimo % nei canali tematici
MIN_SAVING_VALUE = 5                         # risparmio minimo in euro (-1 = disattivato)
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
HUB = {
    "channel": "@theoffersclub_hub",         # canale General (offerte dal 25% in su)
    "name": "TheOffersClub – Le migliori offerte",
}
LAMPO = {
    "enabled": False,                        # canale chiuso: gli sconti top escono nel General con 🔥
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
        "seo_intro": "Le migliori offerte del giorno su PC, monitor, SSD, cuffie, smartphone, smart home e console, aggiornate più volte al giorno.",
        "amazon_search_index": "All",
        "min_price": 10,
        "exclude_words": ["cavo usb", "cavo hdmi", "cavo di ricarica", "cavi usb", "custodia",
                          "supporto per", "adattatore", "protezione schermo"],
        "keywords": [
            # PC e componenti
            "notebook", "laptop gaming", "mini pc", "pc desktop", "monitor 27 pollici",
            "monitor gaming 144hz", "ssd nvme 1tb", "ssd esterno", "hard disk esterno",
            "memoria ram ddr5", "scheda video", "alimentatore pc", "case pc", "dissipatore cpu",
            # Periferiche
            "mouse gaming", "mouse wireless", "tastiera meccanica", "tastiera wireless",
            "webcam", "microfono usb", "docking station usb c",
            "hub usb c", "stampante multifunzione", "stampante 3d",
            # Audio
            "cuffie bluetooth", "cuffie noise cancelling", "auricolari true wireless",
            "cuffie gaming", "soundbar", "cassa bluetooth", "giradischi",
            # Smartphone e tablet
            "smartphone", "tablet", "ebook reader", "caricatore usb c gan", "powerbank",
            "caricatore wireless",
            # Smart home e rete
            "router wifi 6", "mesh wifi", "ripetitore wifi", "videocamera sorveglianza wifi",
            "videocitofono smart", "lampadina smart", "presa smart", "termostato smart",
            "echo dot", "fire tv stick", "chromecast",
            # Wearable e foto
            "smartwatch", "smartband", "action cam", "fotocamera mirrorless", "drone",
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
        "seo_intro": "Friggitrici ad aria, robot aspirapolvere, macchine da caffè, pulizia e scorte per la casa in sconto, selezionati ogni giorno.",
        "amazon_search_index": "All",
        "min_price": 10,
        "exclude_words": ["sacchetti per", "spazzole", "panni", "mop di ricambio", "testine"],
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
            # Bucato
            "detersivo lavatrice", "detersivo lavatrice liquido", "capsule lavatrice",
            "ammorbidente", "smacchiatore bucato", "additivo igienizzante bucato",
            "fogli acchiappacolore", "anticalcare lavatrice",
            # Lavastoviglie e piatti
            "capsule lavastoviglie", "pastiglie lavastoviglie", "brillantante lavastoviglie",
            "sale lavastoviglie", "detersivo piatti", "pulitore lavastoviglie",
            # Pulizia casa
            "detergente pavimenti", "sgrassatore", "anticalcare spray", "candeggina",
            "disinfettante superfici", "salviette igienizzanti", "spugne cucina",
            # Carta e casa
            "carta igienica", "rotoli carta cucina", "fazzoletti di carta",
            "sacchetti spazzatura", "pellicola alimentare", "carta forno", "alluminio alimentare",
            # Caffè e bevande
            "capsule caffè", "cialde caffè", "caffè in grani", "caffè macinato",
            "capsule nespresso compatibili", "capsule dolce gusto compatibili",
            "tè in bustine",
            # Filtri e pile
            "filtri caraffa", "filtri acqua frigorifero", "pile alcaline", "pile ricaricabili",
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
        "seo_intro": "Avvitatori, trapani, saldatrici, smerigliatrici, set di attrezzi, giardino e auto di Bosch, Makita, Einhell, DeWalt e altri marchi, in sconto oggi.",
        "amazon_search_index": "All",
        "min_price": 15,
        "exclude_words": ["set di dischi", "set dischi", "dischi da taglio", "dischi abrasivi",
                          "set di punte", "set punte", "inserti", "lame di ricambio",
                          "spazzole carbone"],
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
            "valigetta attrezzi", "morsa da banco", "banco da lavoro",
            # Giardino
            "tagliaerba a batteria", "decespugliatore", "tagliasiepi", "motosega",
            "motosega a batteria", "soffiatore foglie", "robot tagliaerba", "biotrituratore",
            "potatore telescopico", "tubo irrigazione", "pompa sommersa",
            # Auto e officina
            "avviatore emergenza auto", "caricabatterie auto", "cric idraulico",
            "lucidatrice auto",
            # Kit e marchi (sempre abbinati a un prodotto, per evitare i ricambi)
            "kit batteria caricatore", "bosch professional trapano", "bosch professional avvitatore",
            "bosch verde trapano", "makita trapano", "makita avvitatore", "makita smerigliatrice",
            "dewalt trapano", "dewalt avvitatore", "einhell power x-change kit",
            "ryobi one+ kit", "milwaukee avvitatore", "metabo avvitatore", "parkside kit",
        ],
        "ebay_queries": ["avvitatore batteria", "saldatrice inverter", "set attrezzi",
                         "smerigliatrice", "idropulitrice", "tagliaerba batteria"],
    },
    "persona": {
        "name": "Cura Persona & Salute",
        "emoji": "🧴",
        "emojis": ["🧴", "🪒", "💆", "🦷", "💄", "💅", "💋", "🧼", "💪", "🌿", "✨", "🩺"],
        "channel": "@theoffersclub_persona",   # crea il canale con questo username
        "slug": "offerte-cura-persona",
        "seo_title": "Offerte cura della persona, beauty e salute di oggi",
        "seo_intro": "Trucco, skincare, shampoo e maschere professionali, profumi, piastre, rasoi, spazzolini elettrici e integratori in sconto, selezionati ogni giorno.",
        "amazon_search_index": "All",
        "min_price": 10,
        "exclude_words": ["testine", "lame di ricambio", "beccucci", "campione", "tester",
                          "flacone vuoto", "flaconi vuoti", "dispenser vuoto"],
        "keywords": [
            # Rasatura e depilazione
            "rasoio elettrico", "regolabarba", "tagliacapelli", "rasoio a lamette",
            "rasoio donna", "epilatore", "luce pulsata", "kit ceretta",
            # Styling capelli
            "asciugacapelli", "asciugacapelli professionale", "piastra capelli",
            "arricciacapelli", "spazzola lisciante", "spazzola asciugacapelli",
            "styler multifunzione capelli", "ferro arricciacapelli",
            # Haircare (anche fascia alta)
            "shampoo", "balsamo capelli", "maschera capelli", "olio per capelli",
            "siero capelli", "trattamento ricostruzione capelli", "shampoo professionale",
            "kerastase", "olaplex", "davines", "l'oreal professionnel", "redken",
            "shampoo anticaduta", "lozione anticaduta", "tinta capelli",
            # Skincare viso
            "crema viso", "crema viso antirughe", "siero viso", "siero vitamina c",
            "siero acido ialuronico", "retinolo", "contorno occhi", "maschera viso",
            "patch occhi", "detergente viso", "acqua micellare", "struccante",
            "tonico viso", "esfoliante viso", "crema solare", "crema solare viso spf 50",
            "la roche posay", "cerave", "vichy", "clinique", "estee lauder",
            # Trucco
            "fondotinta", "correttore", "cipria", "primer viso", "blush", "bronzer",
            "illuminante", "palette ombretti", "mascara", "eyeliner", "matita occhi",
            "rossetto", "rossetto liquido", "gloss labbra", "matita sopracciglia",
            "spray fissante trucco", "set pennelli trucco", "spugnetta trucco",
            "kit trucco", "beauty case",
            # Unghie
            "smalto semipermanente", "kit semipermanente", "lampada uv unghie",
            "fresa unghie", "smalto unghie",
            # Corpo
            "crema corpo", "olio corpo", "scrub corpo", "crema anticellulite",
            "autoabbronzante", "bagnoschiuma", "deodorante uomo", "deodorante donna",
            "crema mani",
            # Profumi
            "profumo donna", "profumo uomo", "eau de parfum donna", "eau de parfum uomo",
            "cofanetto profumo",
            # Beauty device
            "spazzola pulizia viso", "dispositivo radiofrequenza viso", "led mask viso",
            "specchio trucco luminoso",
            # Igiene orale
            "spazzolino elettrico", "spazzolino sonico", "idropulsore dentale",
            "dentifricio sbiancante", "kit sbiancamento denti",
            # Uomo
            "cera per capelli", "olio barba", "kit cura barba", "dopobarba",
            # Salute e benessere
            "misuratore di pressione", "bilancia pesapersone smart", "termometro",
            "massaggiatore cervicale", "pistola massaggiante", "cuscino riscaldante",
            # Integratori e sport
            "proteine whey", "creatina", "integratore magnesio", "integratore vitamina d",
            "multivitaminico", "barrette proteiche", "collagene", "integratore capelli",
        ],
        "ebay_queries": ["rasoio elettrico", "spazzolino elettrico", "asciugacapelli",
                         "profumo donna", "piastra capelli", "palette trucco"],
    },
}
# Parole nel titolo che fanno aggiungere l'avviso "batteria non inclusa"
NO_BATTERY_HINTS = ["senza batteria", "solo corpo", "body only", "batteria non inclusa", "tool only"]
DISCLOSURE = ("In qualità di Affiliato Amazon ricevo un guadagno dagli acquisti idonei. "
              "I prezzi possono cambiare: verifica sempre sulla pagina del prodotto.")
