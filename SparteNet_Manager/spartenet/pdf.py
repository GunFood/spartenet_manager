"""SparteNet Manager – kleines PDF ohne Zusatzpakete: Text (Helvetica, Umlaute), Linien, Flächen, Zeilenumbruch, QR-Code

Für Rechnungen und Zugangskarten per E-Mail. Koordinaten in Punkt (1 mm = 2,835 pt), y von oben gemessen.
"""
import zlib

from .tickets import *  # noqa: F401,F403 – alle Namen der vorherigen Module

MM = 72 / 25.4
_W = {False: dict(zip(range(32, 127), [278, 278, 355, 556, 556, 889, 667, 191, 333, 333, 389, 584, 278, 333, 278, 278] + [556] * 10 +
                         [278, 278, 584, 584, 584, 556, 1015, 667, 667, 722, 722, 667, 611, 778, 722, 278, 500, 667, 556, 833, 722, 778, 667, 778, 722, 667,
                          611, 722, 667, 944, 667, 667, 611, 278, 278, 278, 469, 556, 333, 556, 556, 500, 556, 556, 278, 556, 556, 222, 222, 500, 222, 833,
                          556, 556, 556, 556, 333, 500, 278, 556, 500, 722, 500, 500, 500, 334, 260, 334, 584])),
      True: dict(zip(range(32, 127), [278, 333, 474, 556, 556, 889, 722, 238, 333, 333, 389, 584, 278, 333, 278, 278] + [556] * 10 +
                        [333, 333, 584, 584, 584, 611, 975, 722, 722, 722, 722, 667, 611, 778, 722, 278, 556, 722, 611, 833, 722, 778, 667, 778, 722, 667,
                         611, 722, 667, 944, 667, 667, 611, 333, 278, 333, 584, 556, 333, 556, 611, 556, 611, 556, 333, 611, 611, 278, 278, 556, 278, 889,
                         611, 611, 611, 611, 389, 556, 333, 611, 556, 778, 556, 556, 500, 389, 280, 389, 584]))}
_ERSATZ = {"ä": "a", "ö": "o", "ü": "u", "Ä": "A", "Ö": "O", "Ü": "U", "é": "e", "è": "e", "á": "a", "à": "a"}
_SONDER = {"ß": 611, "€": 556, "–": 556, "—": 1000, "„": 333, "“": 333, "”": 333, "‚": 222, "‘": 222, "’": 222, "·": 278, "°": 400, "§": 556, "×": 584, "•": 350}


def _farbe(f):
    if isinstance(f, str) and re.fullmatch(r"#[0-9a-fA-F]{6}", f):
        return tuple(int(f[i:i + 2], 16) / 255 for i in (1, 3, 5))
    return f or (0, 0, 0)


class PDF:
    def __init__(self, breite=210 * MM, hoehe=297 * MM, titel="SparteNet"):
        self.b, self.h, self.titel, self.seiten, self.s = breite, hoehe, titel, [], None
        self.bilder = []          # [(Name, Bilddaten aus bild_fuer_pdf)]
        self.seite()

    def seite(self):
        self.s = []
        self.seiten.append(self.s)

    @staticmethod
    def textbreite(text, groesse=10, fett=False):
        w = 0
        for ch in str(text):
            ch2 = _ERSATZ.get(ch, ch)
            w += _SONDER.get(ch) or _W[fett].get(ord(ch2), 556)
        return w * groesse / 1000

    @staticmethod
    def _esc(text):
        roh = str(text).encode("cp1252", errors="replace")
        return roh.replace(b"\\", b"\\\\").replace(b"(", b"\\(").replace(b")", b"\\)").replace(b"\r", b"").replace(b"\n", b" ")

    def text(self, x, y, text, groesse=10, fett=False, farbe=(0, 0, 0), ausrichtung="l"):
        if ausrichtung == "r":
            x -= self.textbreite(text, groesse, fett)
        elif ausrichtung == "m":
            x -= self.textbreite(text, groesse, fett) / 2
        r, g, b = _farbe(farbe)
        self.s.append(b"BT /" + (b"F2" if fett else b"F1") + f" {groesse:.2f} Tf {r:.3f} {g:.3f} {b:.3f} rg {x:.2f} {self.h - y:.2f} Td (".encode()
                      + self._esc(text) + b") Tj ET")

    def absatz(self, x, y, breite, text, groesse=10, fett=False, farbe=(0, 0, 0), zeilenabstand=1.35):
        """Text mit Zeilenumbruch; gibt das y unter dem Absatz zurück"""
        for zeile in str(text).split("\n"):
            worte, aktuell = zeile.split(" "), ""
            for w in worte:
                probe = (aktuell + " " + w).strip()
                if self.textbreite(probe, groesse, fett) > breite and aktuell:
                    self.text(x, y, aktuell, groesse, fett, farbe)
                    y += groesse * zeilenabstand
                    aktuell = w
                else:
                    aktuell = probe
            self.text(x, y, aktuell, groesse, fett, farbe)
            y += groesse * zeilenabstand
        return y

    def linie(self, x1, y1, x2, y2, staerke=0.5, farbe=(0.7, 0.7, 0.7)):
        r, g, b = _farbe(farbe)
        self.s.append(f"{r:.3f} {g:.3f} {b:.3f} RG {staerke:.2f} w {x1:.2f} {self.h - y1:.2f} m {x2:.2f} {self.h - y2:.2f} l S".encode())

    def rechteck(self, x, y, w, h, fuellung=None, rand=None, staerke=0.5):
        teile = []
        if fuellung is not None:
            teile.append("{:.3f} {:.3f} {:.3f} rg".format(*_farbe(fuellung)))
        if rand is not None:
            teile.append("{:.3f} {:.3f} {:.3f} RG {:.2f} w".format(*_farbe(rand), staerke))
        op = "B" if fuellung is not None and rand is not None else ("f" if fuellung is not None else "S")
        teile.append(f"{x:.2f} {self.h - y - h:.2f} {w:.2f} {h:.2f} re {op}")
        self.s.append(" ".join(teile).encode())

    def qr(self, x, y, groesse, text, ecl="M"):
        m = qr_matrix(text, ecl)
        n = len(m) + 8
        z = groesse / n
        teile = [f"1 1 1 rg {x:.2f} {self.h - y - groesse:.2f} {groesse:.2f} {groesse:.2f} re f 0 0 0 rg"]
        for r, zeile in enumerate(m):
            c = 0
            while c < len(zeile):
                if zeile[c]:
                    s = c
                    while c < len(zeile) and zeile[c]:
                        c += 1
                    teile.append(f"{x + (s + 4) * z:.3f} {self.h - y - (r + 5) * z:.3f} {(c - s) * z:.3f} {z:.3f} re")
                else:
                    c += 1
        teile.append("f")
        self.s.append("\n".join(teile).encode())

    def bild(self, x, y, max_b, max_h, roh, ausrichtung="l"):
        """Bild (PNG/JPEG) in ein Feld einpassen (Seitenverhältnis bleibt); gibt die gezeichnete Breite zurück, 0 wenn nicht lesbar"""
        try:
            b = bild_fuer_pdf(roh) if roh else None
        except Exception:
            b = None
        if not b or not b["breite"] or not b["hoehe"]:
            return 0
        f = min(max_b / b["breite"], max_h / b["hoehe"])
        w, h = b["breite"] * f, b["hoehe"] * f
        if ausrichtung == "r":
            x -= w
        elif ausrichtung == "m":
            x -= w / 2
        name = f"Im{len(self.bilder)}"
        self.bilder.append((name, b))
        self.s.append(f"q {w:.2f} 0 0 {h:.2f} {x:.2f} {self.h - y - h:.2f} cm /{name} Do Q".encode())
        return w

    def ausgabe(self):
        obj = [b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>",
               b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold /Encoding /WinAnsiEncoding >>", b""]   # 1, 2, 3 = /Pages
        kinder, xobj = [], []
        for name, b in self.bilder:
            maske = ""
            if b["alpha"] and any(v != 255 for v in b["alpha"]):
                daten = zlib.compress(b["alpha"])
                obj.append(f"<< /Type /XObject /Subtype /Image /Width {b['breite']} /Height {b['hoehe']} /ColorSpace /DeviceGray /BitsPerComponent 8 "
                           f"/Filter /FlateDecode /Length {len(daten)} >>\nstream\n".encode() + daten + b"\nendstream")
                maske = f" /SMask {len(obj)} 0 R"
            daten = b["daten"] if b["jpeg"] else zlib.compress(b["daten"])
            raum = "/DeviceGray" if b["farben"] == 1 else "/DeviceRGB"
            obj.append(f"<< /Type /XObject /Subtype /Image /Width {b['breite']} /Height {b['hoehe']} /ColorSpace {raum} /BitsPerComponent 8 "
                       f"/Filter /{'DCTDecode' if b['jpeg'] else 'FlateDecode'} /Length {len(daten)}{maske} >>\nstream\n".encode() + daten + b"\nendstream")
            xobj.append(f"/{name} {len(obj)} 0 R")
        xres = f" /XObject << {' '.join(xobj)} >>" if xobj else ""
        for s in self.seiten:
            daten = zlib.compress(b"\n".join(s))
            obj.append(f"<< /Length {len(daten)} /Filter /FlateDecode >>\nstream\n".encode() + daten + b"\nendstream")
            inhalt = len(obj)
            obj.append(f"<< /Type /Page /Parent 3 0 R /MediaBox [0 0 {self.b:.2f} {self.h:.2f}] "
                       f"/Resources << /Font << /F1 1 0 R /F2 2 0 R >>{xres} >> /Contents {inhalt} 0 R >>".encode())
            kinder.append(len(obj))
        obj[2] = f"<< /Type /Pages /Kids [{' '.join(f'{k} 0 R' for k in kinder)}] /Count {len(kinder)} >>".encode()
        obj.append(b"<< /Title (" + self._esc(self.titel) + b") /Producer (SparteNet Manager) >>")
        info = len(obj)
        obj.append(b"<< /Type /Catalog /Pages 3 0 R >>")
        katalog = len(obj)
        aus = bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
        lage = []
        for i, o in enumerate(obj, start=1):
            lage.append(len(aus))
            aus += f"{i} 0 obj\n".encode() + o + b"\nendobj\n"
        xref = len(aus)
        aus += f"xref\n0 {len(obj) + 1}\n0000000000 65535 f \n".encode() + b"".join(f"{p:010d} 00000 n \n".encode() for p in lage)
        aus += f"trailer\n<< /Size {len(obj) + 1} /Root {katalog} 0 R /Info {info} 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode()
        return bytes(aus)


def geld(betrag):
    return f"{float(betrag):,.2f} €".replace(",", "X").replace(".", ",").replace("X", ".")


def pdf_logos(d, kz):
    """(Vereinslogo, Spartenlogo) als Bytes für PDFs – Vereinslogo wie in den E-Mails gewählt"""
    v = _logo_teil(d)
    sp = sparten_logo(d, kz) if kz else None
    return (v[0] if v else None), (sp[0] if sp else None)


def zugangskarte_pdf(d, kz, zeile, sparte_name):
    """eine Zugangskarte als PDF (A5) – für den Versand per E-Mail (Kontakt-Seite)"""
    g = design_pruefen(d.get("design"))
    p = PDF(148 * MM, 210 * MM, f"Zugang Parzelle {zeile['Parzelle']}")
    akz = g["farbe_akzent"]
    b = p.b
    verein, sparte = pdf_logos(d, kz)
    if verein:
        p.bild(12 * MM, 5 * MM, 30 * MM, 12 * MM, verein)
    if sparte:
        p.bild(b - 12 * MM, 5 * MM, 30 * MM, 12 * MM, sparte, "r")
    p.text(b / 2, 22 * MM, f"SparteNet.de · {sparte_name}", 12, True, akz, "m")
    p.text(b / 2, 36 * MM, f"Parzelle {zeile['Parzelle']}", 26, True, g["farbe_text"], "m")
    p.text(b / 2, 44 * MM, "Ihr persönlicher WLAN-Zugang", 11, False, g["farbe_hell"], "m")
    p.qr(b / 2 - 40 * MM, 52 * MM, 80 * MM, wlan_qr_text(zeile["WLAN"], zeile["Passwort"]))
    p.text(b / 2, 140 * MM, "Handy-Kamera auf den Code richten – verbindet automatisch", 9, False, g["farbe_hell"], "m")
    p.text(b / 2, 152 * MM, "WLAN", 8, False, g["farbe_hell"], "m")
    p.text(b / 2, 159 * MM, zeile["WLAN"], 13, True, g["farbe_text"], "m")
    p.text(b / 2, 169 * MM, "PASSWORT", 8, False, g["farbe_hell"], "m")
    w = p.textbreite(zeile["Passwort"], 16, True) + 8 * MM
    p.rechteck(b / 2 - w / 2, 172 * MM, w, 10 * MM, fuellung=g["farbe_pw_hinter"])
    p.text(b / 2, 179.5 * MM, zeile["Passwort"], 16, True, g["farbe_text"], "m")
    p.absatz(15 * MM, 195 * MM, b - 30 * MM, "Bitte vertraulich behandeln und nicht weitergeben.", 8, False, g["farbe_hell"])
    return p.ausgabe()


__all__ = [_n for _n in dict(globals()) if not _n.startswith("__")]  # alle Namen an die folgenden Module weitergeben
