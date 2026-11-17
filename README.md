# OfferteSmart – Bot offerte Telegram + sito automatico

Sistema a costo zero che ogni 2 ore:
1. trova offerte (Amazon, e facoltativamente eBay);
2. le pubblica nel canale Telegram della nicchia giusta (Tech, Casa, Utensili);
3. inoltra le offerte con sconto alto al canale Hub;
4. aggiorna il messaggio fissato dell'Hub con l'elenco dei canali;
5. rigenera il sito (pagine per nicchia, guide, sitemap) e lo pubblica su GitHub Pages.

Gira tutto su GitHub Actions: il PC può restare spento.

---

## Struttura dei file

```
config.py                  <- nomi, canali, nicchie, parole chiave (l'unico file da modificare)
data/prodotti.csv          <- lista prodotti curata, usata finché non hai la PA-API
data/state.json            <- memoria dei prodotti già pubblicati (gestito dal bot)
data/history.json          <- storico offerte usato dal sito (gestito dal bot)
content/guide/*.md         <- articoli evergreen per Google (uno per file)
bot/main.py                <- programma principale
bot/sources.py             <- fonti: Amazon PA-API, CSV, eBay
bot/telegram.py            <- invio post e messaggio fissato
bot/site.py                <- generatore del sito
site_assets/style.css      <- grafica del sito
.github/workflows/bot.yml  <- esecuzione automatica ogni 2 ore
```

---

## FASE 1 – Account (circa 30 minuti, una volta sola)

### 1.1 Amazon Associates
1. Vai su https://programma-affiliazione.amazon.it e registrati.
2. Come sito/app indica il canale Telegram Hub e il sito (puoi aggiungerli anche dopo averli creati: falli prima, passo 1.2 e FASE 2).
3. Annota il tuo **tag** (formato `nome-21`).
4. Hai 180 giorni per fare 3 vendite valide, altrimenti l'account viene chiuso (puoi ripresentare domanda).

### 1.2 Telegram: bot e canali
1. Apri Telegram, cerca **@BotFather**, scrivi `/newbot`, scegli nome e username (deve finire con `bot`).
2. Copia il **token** che ti restituisce (tipo `123456:ABC-...`). Non condividerlo con nessuno.
3. Crea 4 **canali pubblici** (Nuovo canale -> Pubblico) con username coerenti con `config.py`:
   - `@OfferteSmartIT` (Hub)
   - `@OfferteSmartTech`
   - `@OfferteSmartCasa`
   - `@OfferteSmartUtensili`
   Se gli username sono già presi, scegline altri e aggiornali in `config.py`.
4. In ogni canale: Gestisci canale -> Amministratori -> Aggiungi amministratore -> cerca il tuo bot. Attiva **Pubblica messaggi**, **Modifica messaggi** e **Fissa messaggi**.
5. Nella descrizione di ogni canale incolla:
   `Offerte selezionate ogni giorno. Link affiliati: in qualità di Affiliato Amazon ricevo un guadagno dagli acquisti idonei. Tutti i canali: @OfferteSmartIT`
6. Cartella con tutti i canali: Impostazioni -> Cartelle -> Crea cartella -> aggiungi i 4 canali -> Condividi cartella -> copia il link `t.me/addlist/...` e incollalo in `config.py` alla voce `TELEGRAM_FOLDER_LINK`.

### 1.3 GitHub
1. Crea un account su https://github.com (gratis).
2. New repository -> nome ad esempio `offerte` -> **Public** (con l'account gratuito GitHub Pages funziona solo sui repository pubblici, e le Actions sono gratuite senza limiti di minuti) -> Create.
3. Add file -> Upload files -> trascina **tutto il contenuto dello zip** (inclusa la cartella nascosta `.github`; se il browser non la carica, crea a mano il file `.github/workflows/bot.yml` con Add file -> Create new file e incolla il contenuto).
4. Commit changes.

---

## FASE 2 – Configurazione del repository

### 2.1 Secrets (dati riservati)
Settings -> Secrets and variables -> Actions -> **New repository secret**:

| Nome | Valore | Quando |
|---|---|---|
| `AMAZON_TAG` | il tuo tag, es. `nome-21` | subito |
| `TELEGRAM_TOKEN` | token di BotFather | subito |
| `AMAZON_ACCESS_KEY` | chiave PA-API | dopo le 3 vendite |
| `AMAZON_SECRET_KEY` | segreto PA-API | dopo le 3 vendite |
| `EBAY_CLIENT_ID` | App ID eBay | facoltativo (FASE 5) |
| `EBAY_CLIENT_SECRET` | Cert ID eBay | facoltativo |
| `EBAY_CAMPAIGN_ID` | ID campagna eBay Partner Network | facoltativo |

### 2.2 Variables (dati non riservati)
Stessa pagina, scheda **Variables** -> New repository variable:

| Nome | Valore |
|---|---|
| `SITE_URL` | `https://TUOUSERNAME.github.io/offerte` (oppure il tuo dominio, FASE 4) |

### 2.3 GitHub Pages
Settings -> Pages -> Build and deployment -> Source: **GitHub Actions**.

### 2.4 Permessi
Settings -> Actions -> General -> Workflow permissions -> **Read and write permissions** -> Save.

### 2.5 Primo avvio
Actions -> "Bot offerte" -> **Run workflow**. Dopo 1-2 minuti:
- il canale Hub ha il messaggio fissato con i canali;
- il sito è online su `SITE_URL`.

Da qui in poi parte da solo ogni 2 ore (posta solo tra le 7 e le 22).

---

## FASE 3 – Riempire la lista prodotti (finché non hai la PA-API)

Senza PA-API il bot non può leggere prezzi da Amazon (copiarli a mano o tramite scraping è vietato dalle regole Associates). Quindi pubblica **prodotti selezionati senza prezzo**, con una nota utile.

Apri `data/prodotti.csv` su GitHub (icona matita) e aggiungi righe così:

```
asin,nicchia,titolo,nota
B0XXXXXXXX,utensili,Einhell TE-CD 18/40 Li avvitatore con 2 batterie,Kit completo: 2 batterie e valigetta
B0YYYYYYYY,casa,Cosori friggitrice ad aria 5,5 L,Tra le più vendute della categoria
```

- **asin**: il codice nell'indirizzo del prodotto, dopo `/dp/` (10 caratteri).
- **nicchia**: `tech`, `casa` o `utensili` (devono coincidere con le chiavi in `config.py`).
- Bastano 20-30 prodotti per nicchia: il bot ne pesca alcuni a caso e non ripete lo stesso prima di 10 giorni.
- Scegli prodotti molto venduti e con tante recensioni: è il modo più rapido per fare le prime 3 vendite.

---

## FASE 4 – Google (posizionamento)

1. Vai su https://search.google.com/search-console -> Aggiungi proprietà -> **Prefisso URL** -> incolla `SITE_URL`.
2. Metodo di verifica **File HTML**: scarica il file (es. `google1234abcd.html`), e in GitHub crea la variabile `GOOGLE_VERIFICATION_FILE` con quel nome esatto. Rilancia il workflow, poi clicca Verifica.
3. In Search Console -> Sitemap -> inserisci `sitemap.xml` -> Invia.
4. **Dominio proprio (consigliato, circa 10 €/anno):** compra un `.it` (es. su Cloudflare, Aruba, Porkbun), poi Settings -> Pages -> Custom domain, e imposta i record DNS indicati da GitHub. Aggiorna `SITE_URL`. Un dominio proprio si posiziona meglio di `github.io`.
5. **Articoli guida:** ogni file `.md` in `content/guide/` diventa una pagina. C'è già un esempio sugli avvitatori. Obiettivo: 1-2 articoli al mese su ricerche tipo "migliori X sotto Y €" o "X vs Y". Il segnaposto `{{TAG}}` nei link viene sostituito col tuo tag.

---

## FASE 5 – eBay (facoltativo, prezzi reali da subito)

1. Iscriviti a https://partnernetwork.ebay.it e crea una campagna: annota il **Campaign ID**.
2. Su https://developer.ebay.com crea un account -> Application Keys -> crea le chiavi **Production**: annota App ID (Client ID) e Cert ID (Client Secret).
3. Inserisci i 3 Secrets `EBAY_...`. Il bot inizierà a pubblicare anche offerte eBay con sconto reale (≥ 15%).

---

## FASE 6 – Dopo le 3 vendite: Amazon PA-API

1. Su Amazon Associates -> Strumenti -> **Product Advertising API** -> Aggiungi credenziali.
2. Copia Access Key e Secret Key nei Secrets `AMAZON_ACCESS_KEY` e `AMAZON_SECRET_KEY`.
3. Fatto: dal giro successivo il bot cerca da solo le offerte per le parole chiave di ogni nicchia (sconto minimo 15%), con prezzo, prezzo barrato, sconto e immagine. La lista CSV resta come riserva.
4. Attenzione: Amazon ti limita le chiamate API in base alle vendite degli ultimi 30 giorni, e le revoca se per 30 giorni non generi vendite. Se nei log vedi errori di limite, abbassa le parole chiave per nicchia.

Nota: Amazon sta progressivamente aggiornando la PA-API. Se nei log compaiono errori di autenticazione o di formato, scrivimi il messaggio d'errore e adeguo `bot/sources.py`.

---

## FASE 7 – WhatsApp (manuale, 10-15 minuti a settimana)

L'invio automatico su WhatsApp con strumenti non ufficiali porta al ban del numero. Quindi:
1. WhatsApp -> Aggiornamenti -> Canali -> Crea canale (es. "OfferteSmart").
2. Incolla il link in `config.py` alla voce `WHATSAPP_CHANNEL_LINK`: comparirà come pulsante sul sito.
3. 2-3 volte a settimana inoltra lì le offerte migliori prese dal canale Hub.

---

## FASE 8 – Crescita (le uniche attività manuali)

| Quando | Cosa fare |
|---|---|
| Settimana 1 | Condividi il link della cartella Telegram a amici e colleghi interessati; storia Instagram/Facebook con 2-3 offerte forti (indica che sono link affiliati) |
| Settimane 1-4 | Iscrivi i canali alle directory (tgstat.com, telegram-group.com, telegramchannels.me); pubblica nei gruppi Facebook di offerte, fai da te, bricolage, cucina (rispettando le regole del gruppo) |
| Ogni mese | 1-2 nuove guide in `content/guide/` (chiedimi di scriverle) |
| Ogni mese | Controlla quali nicchie crescono di più; apri nuove nicchie (es. Bimbi, già pronta in `config.py`) solo quando una supera circa 500 iscritti |
| Black Friday / primavera | Aumenta `MAX_POSTS_PER_NICHE_PER_RUN` a 3-4 e aggiungi parole chiave stagionali |

---

## Modifiche frequenti

- **Cambiare frequenza:** in `.github/workflows/bot.yml` la riga `cron: "5 */2 * * *"` (ogni 2 ore). Per ogni ora: `"5 * * * *"`.
- **Post per giro:** `MAX_POSTS_PER_NICHE_PER_RUN` in `config.py`.
- **Soglia Hub:** `HUB_MIN_DISCOUNT` (default 40%).
- **Aggiungere una nicchia:** copia un blocco in `NICHES`, crea il canale, aggiungi il bot come admin.
- **Prova in locale (facoltativo):** `pip install -r requirements.txt` poi `python -m bot.main --dry-run --force` (non invia nulla, genera il sito in `public/`).

## Problemi comuni

| Sintomo | Causa / soluzione |
|---|---|
| Nessun post, log "chat not found" | Username canale errato in `config.py` o bot non admin |
| Messaggio fissato non aggiornato | Al bot manca il permesso "Modifica messaggi" / "Fissa messaggi" |
| Sito 404 | Pages non impostato su "GitHub Actions" (passo 2.3) o `SITE_URL` sbagliato |
| Errore al push dello stato | Permessi "Read and write" non attivi (passo 2.4) |
| Il workflow non parte più da solo | GitHub sospende i cron dopo 60 giorni senza attività: basta un Run workflow manuale |
| "Fuori orario" nei log | Normale tra le 22 e le 7: in quel caso aggiorna solo il sito |

## Regole da rispettare (importante)
- Nessun acquisto tramite i tuoi link da parte tua, di familiari o conviventi.
- Indicazione di affiliazione sempre visibile (già inclusa nei post, nel sito e nel messaggio fissato).
- Niente link accorciati che nascondono la destinazione Amazon; niente prezzi copiati a mano o tramite scraping.
- Fisco: le prime entrate occasionali vanno dichiarate come redditi diversi; se l'attività diventa continuativa serve la partita IVA (forfettario). Sentire un commercialista.
