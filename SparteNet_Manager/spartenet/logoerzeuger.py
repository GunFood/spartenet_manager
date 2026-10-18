"""SparteNet Manager – Vereinslogos je Sparte erzeugen (ohne Zusatzpakete) und Bilder für PDFs lesen

Das Logo ist ein rundes Abzeichen: Farbe aus dem Spartennamen, ein Motiv passend zum Namen (Baum bei „Buchenweg“, Blüte bei
„Rosengarten“, Wellen bei „Am See“, Sonne, Berg, sonst ein Blatt) und darunter das Spartenkürzel. Gezeichnet wird mit
Abstandsfeldern (weiche Kanten), gespeichert als PNG mit Transparenz – damit taugt es für E-Mails, PDFs und Webseiten.
"""
import colorsys
import math
import struct
import zlib

from .unterlagen import *  # noqa: F401,F403 – alle Namen der vorherigen Module

LOGO_PIXEL = 256

# Strichschrift: Buchstaben als Linienzüge auf einem Raster 0–4 (breit) × 0–6 (hoch), y nach unten
_SCHRIFT = {
    "A": [[(0, 6), (2, 0), (4, 6)], [(0.7, 4), (3.3, 4)]], "B": [[(0, 6), (0, 0), (3, 0), (4, 1), (4, 2), (3, 3), (0, 3)], [(3, 3), (4, 4), (4, 5), (3, 6), (0, 6)]],
    "C": [[(4, 1), (3, 0), (1, 0), (0, 1), (0, 5), (1, 6), (3, 6), (4, 5)]], "D": [[(0, 0), (0, 6), (2.5, 6), (4, 4.5), (4, 1.5), (2.5, 0), (0, 0)]],
    "E": [[(4, 0), (0, 0), (0, 6), (4, 6)], [(0, 3), (3, 3)]], "F": [[(4, 0), (0, 0), (0, 6)], [(0, 3), (3, 3)]],
    "G": [[(4, 1), (3, 0), (1, 0), (0, 1), (0, 5), (1, 6), (3, 6), (4, 5), (4, 3.2), (2.3, 3.2)]], "H": [[(0, 0), (0, 6)], [(4, 0), (4, 6)], [(0, 3), (4, 3)]],
    "I": [[(2, 0), (2, 6)], [(1, 0), (3, 0)], [(1, 6), (3, 6)]], "J": [[(4, 0), (4, 5), (3, 6), (1, 6), (0, 5)]],
    "K": [[(0, 0), (0, 6)], [(4, 0), (0, 3.6)], [(1.3, 2.6), (4, 6)]], "L": [[(0, 0), (0, 6), (4, 6)]],
    "M": [[(0, 6), (0, 0), (2, 3.5), (4, 0), (4, 6)]], "N": [[(0, 6), (0, 0), (4, 6), (4, 0)]],
    "O": [[(1, 0), (3, 0), (4, 1), (4, 5), (3, 6), (1, 6), (0, 5), (0, 1), (1, 0)]], "P": [[(0, 6), (0, 0), (3, 0), (4, 1), (4, 2), (3, 3), (0, 3)]],
    "Q": [[(1, 0), (3, 0), (4, 1), (4, 5), (3, 6), (1, 6), (0, 5), (0, 1), (1, 0)], [(2.5, 4.5), (4, 6.2)]],
    "R": [[(0, 6), (0, 0), (3, 0), (4, 1), (4, 2), (3, 3), (0, 3)], [(2, 3), (4, 6)]],
    "S": [[(4, 1), (3, 0), (1, 0), (0, 1), (0, 2), (1, 3), (3, 3), (4, 4), (4, 5), (3, 6), (1, 6), (0, 5)]], "T": [[(0, 0), (4, 0)], [(2, 0), (2, 6)]],
    "U": [[(0, 0), (0, 5), (1, 6), (3, 6), (4, 5), (4, 0)]], "V": [[(0, 0), (2, 6), (4, 0)]], "W": [[(0, 0), (1, 6), (2, 2.5), (3, 6), (4, 0)]],
    "X": [[(0, 0), (4, 6)], [(4, 0), (0, 6)]], "Y": [[(0, 0), (2, 3), (4, 0)], [(2, 3), (2, 6)]], "Z": [[(0, 0), (4, 0), (0, 6), (4, 6)]],
    "0": [[(1, 0), (3, 0), (4, 1), (4, 5), (3, 6), (1, 6), (0, 5), (0, 1), (1, 0)]], "1": [[(1, 1), (2.5, 0), (2.5, 6)], [(1, 6), (4, 6)]],
    "2": [[(0, 1), (1, 0), (3, 0), (4, 1), (4, 2), (0, 6), (4, 6)]], "3": [[(0, 0), (4, 0), (2, 2.5), (3, 2.5), (4, 3.5), (4, 5), (3, 6), (1, 6), (0, 5)]],
    "4": [[(3, 6), (3, 0), (0, 4), (4, 4)]], "5": [[(4, 0), (0, 0), (0, 2.6), (3, 2.6), (4, 3.6), (4, 5), (3, 6), (0, 6)]],
    "6": [[(3.5, 0), (1.5, 0), (0, 1.5), (0, 5), (1, 6), (3, 6), (4, 5), (4, 3.8), (3, 2.8), (0, 2.8)]], "7": [[(0, 0), (4, 0), (1.5, 6)]],
    "8": [[(1, 3), (0, 2), (0, 1), (1, 0), (3, 0), (4, 1), (4, 2), (3, 3), (1, 3), (0, 4), (0, 5), (1, 6), (3, 6), (4, 5), (4, 4), (3, 3)]],
    "9": [[(4, 3.2), (1, 3.2), (0, 2.2), (0, 1), (1, 0), (3, 0), (4, 1), (4, 4.5), (2.5, 6), (0.5, 6)]], "-": [[(0.8, 3), (3.2, 3)]],
}
_PUNKTE = {"Ä": "A", "Ö": "O", "Ü": "U"}

_MOTIVE = (
    ("baum", ("buche", "eiche", "linde", "birke", "ahorn", "tanne", "kiefer", "fichte", "erle", "esche", "ulme", "kastanie", "pappel", "weide",
              "wald", "baum", "hain", "holz", "forst", "busch", "heide")),
    ("bluete", ("rose", "blume", "blute", "bluete", "tulpe", "flora", "nelke", "lilie", "flieder", "veilchen", "aster", "dahlie", "jasmin",
                "lavendel", "mohn", "kirsch", "apfel", "obst", "garten", "frucht")),
    ("wellen", ("see", "teich", "bach", "wasser", "fluss", "ufer", "quelle", "aue", "strand", "brunnen", "graben", "kanal", "spree", "elbe",
                "havel", "oder", "rhein", "main", "insel", "hafen")),
    ("sonne", ("sonne", "sonnen", "licht", "morgen", "sommer", "abendrot", "heiter", "frohsinn", "glueck", "gluck")),
    ("berg", ("berg", "hoehe", "hohe", "hang", "hugel", "huegel", "blick", "kuppe", "stein", "fels", "tal")),
)


def _lg_norm(t):
    t = str(t or "").lower()
    for a, b in (("ä", "ae"), ("ö", "oe"), ("ü", "ue"), ("ß", "ss")):
        t = t.replace(a, b)
    return t


def logo_motiv(name):
    n = _lg_norm(name)
    n2 = n.replace("ae", "a").replace("oe", "o").replace("ue", "u")
    for motiv, worte in _MOTIVE:
        if any(w in n or w in n2 for w in worte):
            return motiv
    return "blatt"


def logo_farbe(name):
    """kräftige Grundfarbe aus dem Namen (immer gleich für denselben Namen) – Grün- und Blautöne bevorzugt"""
    h = int(hashlib.sha256(_lg_norm(name).encode()).hexdigest()[:8], 16)
    farbtoene = (0.30, 0.36, 0.42, 0.50, 0.56, 0.60, 0.08, 0.02, 0.75, 0.12)
    r, g, b = colorsys.hls_to_rgb(farbtoene[h % len(farbtoene)], 0.32 + (h >> 8) % 7 * 0.012, 0.55 + (h >> 12) % 5 * 0.05)
    return r, g, b


class _Leinwand:
    """RGBA-Fläche (Gleitkomma), Formen mit weichen Kanten über Abstandsfelder"""

    def __init__(self, n):
        self.n = n
        self.px = [[0.0, 0.0, 0.0, 0.0] for _ in range(n * n)]

    def _malen(self, x0, y0, x1, y1, deckung, farbe):
        n = self.n
        r, g, b = farbe
        for y in range(max(0, int(y0) - 1), min(n, int(y1) + 2)):
            for x in range(max(0, int(x0) - 1), min(n, int(x1) + 2)):
                a = deckung(x + 0.5, y + 0.5)
                if a <= 0:
                    continue
                a = min(1.0, a)
                p = self.px[y * n + x]
                na = a + p[3] * (1 - a)
                if na > 0:
                    p[0] = (r * a + p[0] * p[3] * (1 - a)) / na
                    p[1] = (g * a + p[1] * p[3] * (1 - a)) / na
                    p[2] = (b * a + p[2] * p[3] * (1 - a)) / na
                p[3] = na

    def kreis(self, cx, cy, rad, farbe):
        self._malen(cx - rad, cy - rad, cx + rad, cy + rad, lambda x, y: rad - ((x - cx) ** 2 + (y - cy) ** 2) ** 0.5 + 0.5, farbe)

    def ring(self, cx, cy, rad, breite, farbe):
        h = breite / 2
        self._malen(cx - rad - h, cy - rad - h, cx + rad + h, cy + rad + h, lambda x, y: h - abs(((x - cx) ** 2 + (y - cy) ** 2) ** 0.5 - rad) + 0.5, farbe)

    def linie(self, punkte, breite, farbe):
        h = breite / 2
        seg = list(zip(punkte, punkte[1:]))
        xs, ys = [p[0] for p in punkte], [p[1] for p in punkte]

        def dist(x, y):
            best = 1e9
            for (ax, ay), (bx, by) in seg:
                dx, dy = bx - ax, by - ay
                ll = dx * dx + dy * dy
                t = 0 if ll == 0 else max(0.0, min(1.0, ((x - ax) * dx + (y - ay) * dy) / ll))
                q = (x - ax - t * dx) ** 2 + (y - ay - t * dy) ** 2
                if q < best:
                    best = q
            return best ** 0.5
        self._malen(min(xs) - h, min(ys) - h, max(xs) + h, max(ys) + h, lambda x, y: h - dist(x, y) + 0.5, farbe)

    def vieleck(self, punkte, farbe):
        kanten = list(zip(punkte, punkte[1:] + punkte[:1]))
        xs, ys = [p[0] for p in punkte], [p[1] for p in punkte]

        def deckung(x, y):
            innen, best = False, 1e9
            for (ax, ay), (bx, by) in kanten:
                if (ay > y) != (by > y) and x < (bx - ax) * (y - ay) / (by - ay) + ax:
                    innen = not innen
                dx, dy = bx - ax, by - ay
                ll = dx * dx + dy * dy
                t = 0 if ll == 0 else max(0.0, min(1.0, ((x - ax) * dx + (y - ay) * dy) / ll))
                best = min(best, (x - ax - t * dx) ** 2 + (y - ay - t * dy) ** 2)
            d = best ** 0.5
            return 0.5 + d if innen else 0.5 - d
        self._malen(min(xs), min(ys), max(xs), max(ys), deckung, farbe)

    def png(self):
        n = self.n
        zeilen = bytearray()
        for y in range(n):
            zeilen.append(0)
            for x in range(n):
                r, g, b, a = self.px[y * n + x]
                zeilen += bytes((int(r * 255 + 0.5), int(g * 255 + 0.5), int(b * 255 + 0.5), int(a * 255 + 0.5)))

        def chunk(typ, inhalt):
            return struct.pack(">I", len(inhalt)) + typ + inhalt + struct.pack(">I", zlib.crc32(typ + inhalt) & 0xFFFFFFFF)
        return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", n, n, 8, 6, 0, 0, 0))
                + chunk(b"IDAT", zlib.compress(bytes(zeilen), 9)) + chunk(b"IEND", b""))


def _text(lw, text, cx, cy, hoehe, farbe):
    zeichen = [c for c in str(text).upper() if c in _SCHRIFT or c in _PUNKTE][:4]
    if not zeichen:
        return
    s = hoehe / 6
    staerke = max(3.0, hoehe * 0.17)
    breite = len(zeichen) * 4 * s + (len(zeichen) - 1) * 1.6 * s
    x0, y0 = cx - breite / 2, cy - hoehe / 2
    for i, c in enumerate(zeichen):
        ox = x0 + i * 5.6 * s
        for zug in _SCHRIFT[_PUNKTE.get(c, c)]:
            lw.linie([(ox + px * s, y0 + py * s) for px, py in zug], staerke, farbe)
        if c in _PUNKTE:
            for px in (1.1, 2.9):
                lw.kreis(ox + px * s, y0 - 1.3 * s, staerke * 0.55, farbe)


def _motiv(lw, motiv, cx, cy, gr, weiss, grund):
    """Motiv in Weiß, mittig um (cx, cy), Größe gr (≈ Durchmesser)"""
    h = gr / 2
    if motiv == "baum":
        lw.vieleck([(cx - h * 0.12, cy + h * 0.95), (cx - h * 0.08, cy + h * 0.15), (cx + h * 0.08, cy + h * 0.15), (cx + h * 0.12, cy + h * 0.95)], weiss)
        for dx, dy, rr in ((0, -0.35, 0.52), (-0.42, -0.02, 0.4), (0.42, -0.02, 0.4), (-0.22, 0.25, 0.32), (0.22, 0.25, 0.32)):
            lw.kreis(cx + dx * h, cy + dy * h, rr * h, weiss)
    elif motiv == "bluete":
        for k in range(6):
            w = k * math.pi / 3 - math.pi / 2
            lw.kreis(cx + math.cos(w) * h * 0.5, cy + math.sin(w) * h * 0.5, h * 0.36, weiss)
        lw.kreis(cx, cy, h * 0.27, grund)
        lw.kreis(cx, cy, h * 0.17, (1.0, 0.86, 0.35))
    elif motiv == "wellen":
        for zeile in range(3):
            y = cy - h * 0.5 + zeile * h * 0.5
            lw.linie([(cx - h * 0.95 + i * h * 0.1, y + math.sin(i * 0.63) * h * 0.13) for i in range(20)], max(3.0, h * 0.13), weiss)
    elif motiv == "sonne":
        lw.kreis(cx, cy, h * 0.45, weiss)
        for k in range(10):
            w = k * math.pi / 5
            lw.linie([(cx + math.cos(w) * h * 0.62, cy + math.sin(w) * h * 0.62), (cx + math.cos(w) * h * 0.92, cy + math.sin(w) * h * 0.92)], max(3.0, h * 0.11), weiss)
    elif motiv == "berg":
        lw.vieleck([(cx - h, cy + h * 0.7), (cx - h * 0.3, cy - h * 0.55), (cx + h * 0.1, cy + h * 0.1), (cx + h * 0.4, cy - h * 0.3), (cx + h, cy + h * 0.7)], weiss)
        lw.vieleck([(cx - h * 0.3, cy - h * 0.55), (cx - h * 0.12, cy - h * 0.2), (cx - h * 0.3, cy - h * 0.28), (cx - h * 0.48, cy - h * 0.2)], grund)
    else:   # Blatt
        pkt = [(cx + math.sin(t / 20 * math.pi) * h * 0.55, cy - h * 0.95 + t / 20 * h * 1.9) for t in range(21)]
        pkt += [(cx - math.sin(t / 20 * math.pi) * h * 0.55, cy + h * 0.95 - t / 20 * h * 1.9) for t in range(1, 20)]
        lw.vieleck(pkt, weiss)
        lw.linie([(cx, cy - h * 0.8), (cx, cy + h * 1.05)], max(2.5, h * 0.07), grund)
        for k in (-0.4, 0.0, 0.4):
            lw.linie([(cx, cy + k * h + h * 0.1), (cx + h * 0.32, cy + k * h - h * 0.18)], max(2.0, h * 0.05), grund)
            lw.linie([(cx, cy + k * h + h * 0.1), (cx - h * 0.32, cy + k * h - h * 0.18)], max(2.0, h * 0.05), grund)


def vereinslogo_png(name, kuerzel, n=LOGO_PIXEL):
    """rundes Vereinsabzeichen als PNG (Bytes) – Farbe und Motiv aus dem Namen, Kürzel unten"""
    lw = _Leinwand(n)
    f = n / 256
    grund = logo_farbe(name)
    hell = tuple(min(1.0, c + (1 - c) * 0.75) for c in grund)
    weiss = (1.0, 1.0, 1.0)
    lw.kreis(128 * f, 128 * f, 124 * f, grund)
    lw.ring(128 * f, 128 * f, 110 * f, 5 * f, hell)
    _motiv(lw, logo_motiv(name), 128 * f, 90 * f, 92 * f, weiss, grund)
    k = re.sub(r"[^A-Za-z0-9ÄÖÜäöü-]", "", str(kuerzel or name))[:3] or "SN"
    _text(lw, k, 128 * f, 172 * f, (40 if len(k) <= 2 else 32) * f, weiss)
    lw.linie([(86 * f, 205 * f), (170 * f, 205 * f)], 3 * f, hell)
    return lw.png()


def akt_sparten_logo_erzeugen(d, b, wer, erlaubt=None):
    """Vereinslogo aus dem Spartennamen erzeugen, unter Unterlagen → Logos ablegen (der Sparte zugeordnet) und als Spartenlogo wählen.
    {"sparte": kz} für eine Sparte, {"alle": true} für alle Sparten ohne Logo."""
    sparten = kalk_sparten(d)
    if b.get("alle"):
        ziele = [kz for kz in sparten if (erlaubt is None or kz in erlaubt) and not sparten_logo_id(d, kz)]
    else:
        kz = str(b.get("sparte") or "")
        if kz not in sparten or (erlaubt is not None and kz not in erlaubt):
            raise Fehler("Sparte unbekannt oder ohne Recht.")
        ziele = [kz]
    fertig = []
    for kz in ziele:
        name = sparten[kz].get("name") or kz
        png = vereinslogo_png(name, kz)
        akt_unterlage_hochladen(d, {"name": [f"Vereinslogo {name.rstrip('. ')}.png"], "ordner": [LOGO_ORDNER], "sparte": [kz],
                                    "beschreibung": [f"Automatisch erzeugt aus dem Spartennamen „{name}“ (Motiv: {logo_motiv(name)})"]}, png, wer, erlaubt)
        neu = max(((k, v) for k, v in unterlagen_daten(d)["dateien"].items() if v.get("sparte") == kz and v.get("ordner") == LOGO_ORDNER),
                  key=lambda x: x[1].get("zeit", ""), default=(None, None))[0]
        roh = d.get("sparten_logos") if isinstance(d.get("sparten_logos"), dict) else {}
        if neu:
            roh[kz] = neu
        d["sparten_logos"] = roh
        fertig.append(kz)
    speichere(d)
    if fertig:
        journal(f"Vereinslogo(s) erzeugt für {', '.join(fertig)} durch {wer}")
    r = akt_sparten_logos(d, None, wer, erlaubt)
    r["log"] = [f"✔ Logo erzeugt und als Spartenlogo gewählt: {', '.join(fertig)}." if fertig else "Alle Sparten haben schon ein Logo."]
    return r


# ---- Bilder für PDFs: PNG (8 Bit, nicht verschachtelt) und JPEG ------------------------------------------------------
def bild_fuer_pdf(roh):
    """{"breite", "hoehe", "farben": 1|3, "daten" (unkomprimiert bzw. JPEG), "jpeg": bool, "alpha": bytes|None} oder None"""
    if roh[:2] == b"\xff\xd8":
        i = 2
        while i + 9 < len(roh):
            if roh[i] != 0xFF:
                return None
            m, laenge = roh[i + 1], struct.unpack(">H", roh[i + 2:i + 4])[0]
            if m in (0xC0, 0xC1, 0xC2):
                h, w, k = struct.unpack(">HHB", roh[i + 5:i + 10])
                return {"breite": w, "hoehe": h, "farben": 1 if k == 1 else 3, "daten": roh, "jpeg": True, "alpha": None} if k in (1, 3) else None
            i += 2 + laenge
        return None
    if roh[:8] != b"\x89PNG\r\n\x1a\n":
        return None
    i, idat, plte, trns, kopf = 8, bytearray(), b"", b"", None
    while i + 8 <= len(roh):
        laenge, typ = struct.unpack(">I", roh[i:i + 4])[0], roh[i + 4:i + 8]
        teil = roh[i + 8:i + 8 + laenge]
        if typ == b"IHDR":
            kopf = struct.unpack(">IIBBBBB", teil)
        elif typ == b"IDAT":
            idat += teil
        elif typ == b"PLTE":
            plte = teil
        elif typ == b"tRNS":
            trns = teil
        elif typ == b"IEND":
            break
        i += 12 + laenge
    if not kopf:
        return None
    w, h, tiefe, art, _k, _f, verschachtelt = kopf
    kanaele = {0: 1, 2: 3, 3: 1, 4: 2, 6: 4}.get(art)
    if tiefe != 8 or verschachtelt or not kanaele or w * h > 4_000_000:
        return None
    try:
        roh_px = zlib.decompress(bytes(idat))
    except zlib.error:
        return None
    bpp, zeile = kanaele, w * kanaele
    aus, vorher, pos = bytearray(), bytearray(zeile), 0
    for _ in range(h):
        filt = roh_px[pos]
        z = bytearray(roh_px[pos + 1:pos + 1 + zeile])
        pos += 1 + zeile
        if filt == 1:
            for x in range(bpp, zeile):
                z[x] = (z[x] + z[x - bpp]) & 255
        elif filt == 2:
            for x in range(zeile):
                z[x] = (z[x] + vorher[x]) & 255
        elif filt == 3:
            for x in range(zeile):
                z[x] = (z[x] + ((z[x - bpp] if x >= bpp else 0) + vorher[x]) // 2) & 255
        elif filt == 4:
            for x in range(zeile):
                a = z[x - bpp] if x >= bpp else 0
                b_, c = vorher[x], (vorher[x - bpp] if x >= bpp else 0)
                p = a + b_ - c
                pa, pb, pc = abs(p - a), abs(p - b_), abs(p - c)
                z[x] = (z[x] + (a if pa <= pb and pa <= pc else b_ if pb <= pc else c)) & 255
        aus += z
        vorher = z
    if art == 3:
        pal = [plte[k:k + 3] for k in range(0, len(plte), 3)]
        farbe = b"".join(pal[v] if v < len(pal) else b"\0\0\0" for v in aus)
        alpha = bytes(trns[v] if v < len(trns) else 255 for v in aus) if trns else None
        return {"breite": w, "hoehe": h, "farben": 3, "daten": farbe, "jpeg": False, "alpha": alpha}
    if art in (4, 6):
        n = kanaele - 1
        farbe = bytearray(w * h * n)
        for k in range(n):
            farbe[k::n] = aus[k::kanaele]
        alpha = bytes(aus[n::kanaele])
        return {"breite": w, "hoehe": h, "farben": n, "daten": farbe, "jpeg": False, "alpha": alpha}
    return {"breite": w, "hoehe": h, "farben": kanaele, "daten": bytes(aus), "jpeg": False, "alpha": None}


__all__ = [_n for _n in dict(globals()) if not _n.startswith("__")]  # alle Namen an die folgenden Module weitergeben
