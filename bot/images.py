"""
Preparazione delle immagini dei post.
 - Formato fisso orizzontale (IMAGE_RATIO in config.py, di default 16:9), così tutti i post
   hanno la stessa altezza.
 - Toglie il bianco in eccesso intorno al prodotto.
 - Foto alta/quadrata  -> aggiunge sfondo bianco ai lati.
 - Foto molto larga    -> taglia i lati, ma al massimo IMAGE_MAX_CROP; se non basta,
                          aggiunge bianco sopra e sotto (il prodotto non viene mai deformato).
 - Versione "offerta terminata": grigia con la scritta TERMINATA.
 - Gli indirizzi immagine di Amazon con parametri strani (AVIF, "FMavif", "PQ60", ecc.)
   vengono ripuliti automaticamente: si prova prima la foto originale .jpg.
"""
import io
import re

import requests
from PIL import Image, ImageChops, ImageDraw, ImageFont, ImageOps

import config

RATIO = getattr(config, "IMAGE_RATIO", 16 / 9)          # larghezza / altezza
MAX_CROP = getattr(config, "IMAGE_MAX_CROP", 0.20)      # quota massima di larghezza tagliabile
WIDTH = getattr(config, "IMAGE_WIDTH", 1280)            # larghezza finale in pixel
MARGIN = getattr(config, "IMAGE_MARGIN", 0.06)          # bordo bianco intorno al prodotto
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
      "Accept": "image/jpeg,image/png,image/webp;q=0.9,*/*;q=0.5"}   # niente AVIF
WHITE = (255, 255, 255)

_cache = {}
_AMZ = re.compile(r"^(https?://(?:m\.media-amazon\.com|images-[a-z]+\.ssl-images-amazon\.com|"
                  r"[a-z0-9-]+\.media-amazon\.com)/images/I/[A-Za-z0-9%+\-]+)\.[^/]*$")


def candidates(url):
    """Indirizzi da provare, in ordine. Per le immagini Amazon: foto originale, poi versione
    1000 px, poi l'indirizzo com'è. Per gli altri siti: solo l'indirizzo com'è."""
    url = (url or "").strip().split("?")[0] if "media-amazon" in (url or "") else (url or "").strip()
    m = _AMZ.match(url)
    if not m:
        return [url] if url else []
    base = m.group(1)
    out = [f"{base}.jpg", f"{base}._AC_SL1000_.jpg"]
    if url not in out:
        out.append(url)
    return out


def clean_url(url):
    """Primo indirizzo consigliato (per mostrarlo/salvarlo)."""
    c = candidates(url)
    return c[0] if c else ""


def _open(content):
    img = Image.open(io.BytesIO(content))
    img.load()
    return img


def download(url):
    if url in _cache:
        return _cache[url]
    img = None
    for cand in candidates(url):
        try:
            r = requests.get(cand, headers=UA, timeout=30)
            r.raise_for_status()
            if len(r.content) < 1000:
                raise ValueError("immagine vuota")
            img = _open(r.content)
            break
        except Exception as e:
            print(f"  [immagini] {cand[-60:]}: {e}")
    if img is None:
        print("  [immagini] nessun indirizzo ha funzionato")
    _cache[url] = img
    return img


def _to_rgb(img):
    img = ImageOps.exif_transpose(img)
    if img.mode in ("RGBA", "LA", "P"):
        img = img.convert("RGBA")
        bg = Image.new("RGB", img.size, WHITE)
        bg.paste(img, mask=img.split()[-1])
        return bg
    return img.convert("RGB")


def _trim_white(img):
    """Toglie i bordi bianchi (o quasi bianchi) intorno al prodotto."""
    diff = ImageChops.difference(img, Image.new("RGB", img.size, WHITE)).convert("L")
    bbox = diff.point(lambda p: 255 if p > 14 else 0).getbbox()
    return img.crop(bbox) if bbox else img


def _pad(img, w, h):
    canvas = Image.new("RGB", (w, h), WHITE)
    canvas.paste(img, ((w - img.width) // 2, (h - img.height) // 2))
    return canvas


def fit(img):
    """Restituisce l'immagine nel formato fisso RATIO, larga WIDTH pixel."""
    img = _trim_white(_to_rgb(img))
    m = int(max(img.size) * MARGIN)
    img = _pad(img, img.width + 2 * m, img.height + 2 * m)
    w, h = img.size
    if w / h < RATIO:                                   # alta o quadrata: bianco ai lati
        img = _pad(img, int(round(h * RATIO)), h)
    elif w / h > RATIO:                                 # molto larga: taglia i lati (con limite)
        new_w = max(int(round(h * RATIO)), int(round(w * (1 - MAX_CROP))))
        left = (w - new_w) // 2
        img = img.crop((left, 0, left + new_w, h))
        if img.width / img.height > RATIO + 0.01:       # ancora troppo larga: bianco sopra/sotto
            img = _pad(img, img.width, int(round(img.width / RATIO)))
    return img.resize((WIDTH, int(round(WIDTH / RATIO))), Image.LANCZOS)


def _jpeg(img):
    buf = io.BytesIO()
    img.save(buf, "JPEG", quality=88, optimize=True)
    return buf.getvalue()


def _font(size):
    for name in ("DejaVuSans-Bold.ttf", "LiberationSans-Bold.ttf", "Arial Bold.ttf", "arialbd.ttf"):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            pass
    try:
        return ImageFont.load_default(size=size)
    except TypeError:
        return ImageFont.load_default()


def stamp(img, label):
    """Versione grigia con la scritta (es. TERMINATA) al centro."""
    gray = ImageOps.grayscale(img).convert("RGB")
    gray = Image.blend(gray, Image.new("RGB", gray.size, WHITE), 0.35)
    draw = ImageDraw.Draw(gray)
    size = int(gray.height * 0.24)
    while size > 10:
        font = _font(size)
        x0, y0, x1, y1 = draw.textbbox((0, 0), label, font=font, stroke_width=max(2, size // 12))
        if x1 - x0 <= gray.width * 0.85:
            break
        size -= 4
    stroke = max(2, size // 12)
    x0, y0, x1, y1 = draw.textbbox((0, 0), label, font=font, stroke_width=stroke)
    pos = ((gray.width - (x1 - x0)) // 2 - x0, (gray.height - (y1 - y0)) // 2 - y0)
    draw.text(pos, label, font=font, fill=(220, 20, 20), stroke_width=stroke, stroke_fill=WHITE)
    return gray


def prepared(url):
    """JPEG pronto per il post, oppure None se l'immagine non si scarica."""
    img = download(url) if url else None
    if img is None:
        return None
    try:
        return _jpeg(fit(img))
    except Exception as e:
        print(f"  [immagini] elaborazione non riuscita: {e}")
        return None


def expired(url, label):
    """JPEG grigio con la scritta, oppure None."""
    img = download(url) if url else None
    if img is None:
        return None
    try:
        return _jpeg(stamp(fit(img), label))
    except Exception as e:
        print(f"  [immagini] elaborazione non riuscita: {e}")
        return None
