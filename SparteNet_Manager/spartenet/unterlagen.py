"""SparteNet Manager – Unterlagen: Dateien hinterlegen (Verträge, Pläne, Protokolle …), allgemein oder je Sparte

Gespeichert wie alle Daten (Datenordner bzw. MariaDB, Name „Unterlage_<id>“), die Angaben dazu unter „unterlagen“.
Nur bekannte Dateiarten; Webseiten, SVG und Programme werden abgelehnt. Angezeigt im Browser werden nur PDF und Bilder,
und nur wenn der Inhalt wirklich dazu passt – alles andere wird heruntergeladen.
"""
from .update import *  # noqa: F401,F403 – alle Namen der vorherigen Module

UNTERLAGEN_MAX_MB = max(1, int(os.environ.get("SPARTENET_UNTERLAGEN_MAX_MB", "15") or 15))
UNTERLAGEN_GESAMT_MB = max(10, int(os.environ.get("SPARTENET_UNTERLAGEN_GESAMT_MB", "2048") or 2048))
UNTERLAGEN_TYPEN = {
    "pdf": "application/pdf", "png": "image/png", "jpg": "image/jpeg", "jpeg": "image/jpeg", "gif": "image/gif", "webp": "image/webp",
    "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    "odt": "application/vnd.oasis.opendocument.text", "ods": "application/vnd.oasis.opendocument.spreadsheet",
    "odp": "application/vnd.oasis.opendocument.presentation", "doc": "application/msword", "xls": "application/vnd.ms-excel",
    "ppt": "application/vnd.ms-powerpoint", "csv": "text/csv", "txt": "text/plain", "zip": "application/zip",
}
_ANSEHEN = {"pdf": (b"%PDF",), "png": (b"\x89PNG",), "jpg": (b"\xff\xd8",), "jpeg": (b"\xff\xd8",), "gif": (b"GIF87a", b"GIF89a"), "webp": (b"RIFF",)}
_ID_RE = re.compile(r"^[0-9a-f]{16}$")
ORDNER_STANDARD = ["Allgemein", "Verträge", "Pläne", "Protokolle", "Rechnungen"]


def _ordnername(n):
    n = text_einzeilig(n, 60).strip().replace("/", "-").replace("\\", "-")
    return n or "Allgemein"


def unterlagen_ordner(d, sichtbare=None):
    """Standard-Ordner, selbst angelegte und alle, in denen Dateien liegen"""
    u = unterlagen_daten(d)
    eigene = [o for o in (u.get("ordner") or []) if isinstance(o, str)]
    benutzt = {x.get("ordner") for x in (sichtbare if sichtbare is not None else u["dateien"].values()) if x.get("ordner")}
    return sorted(set(ORDNER_STANDARD) | set(eigene) | benutzt, key=lambda o: (o != "Allgemein", o.lower()))


def unterlagen_daten(d):
    u = d.get("unterlagen") if isinstance(d.get("unterlagen"), dict) else {}
    if not isinstance(u.get("dateien"), dict):
        u["dateien"] = {}
    d["unterlagen"] = u
    return u


def _sichtbar(x, erlaubt):
    return erlaubt is None or not x.get("sparte") or x.get("sparte") in erlaubt


def _darf_schreiben(x, erlaubt):
    return erlaubt is None or bool(x.get("sparte") and x.get("sparte") in erlaubt)


def _anzeigename(name):
    n = os.path.basename(str(name or "").replace("\\", "/"))
    n = re.sub(r"[\x00-\x1f\x7f<>:\"|?*]+", "_", n).strip(" .")
    return n[:120] or "Datei"


def akt_unterlagen(d, erlaubt):
    u = unterlagen_daten(d)
    liste = [{"id": k, **{f: v.get(f) for f in ("name", "ordner", "sparte", "groesse", "typ", "beschreibung", "von", "zeit", "sha256")},
              "ansehen": v.get("ansehen", False), "schreiben": _darf_schreiben(v, erlaubt)}
             for k, v in u["dateien"].items() if _sichtbar(v, erlaubt)]
    liste.sort(key=lambda x: ((x["ordner"] or "").lower(), (x["name"] or "").lower()))
    belegt = sum(v.get("groesse", 0) for v in u["dateien"].values())
    ordner = unterlagen_ordner(d, liste)
    anzahl = {o: sum(1 for x in liste if x["ordner"] == o) for o in ordner}
    return {"dateien": liste, "ordner": ordner, "anzahl": anzahl, "standard": ORDNER_STANDARD, "max_datei_mb": UNTERLAGEN_MAX_MB, "gesamt_mb": UNTERLAGEN_GESAMT_MB,
            "belegt_mb": round(belegt / 1_000_000, 1), "endungen": sorted(UNTERLAGEN_TYPEN), "sparten_erlaubt": sorted(erlaubt) if erlaubt else None,
            "log": [f"{len(liste)} Datei(en) · {belegt / 1_000_000:.1f} von {UNTERLAGEN_GESAMT_MB} MB belegt"]}


def akt_unterlage_hochladen(d, q, roh, wer, erlaubt):
    name = _anzeigename(q.get("name", [""])[0])
    endung = name.rsplit(".", 1)[-1].lower() if "." in name else ""
    if endung not in UNTERLAGEN_TYPEN:
        raise Fehler(f"Dateiart „.{endung}“ ist nicht erlaubt. Erlaubt: " + ", ".join(sorted(UNTERLAGEN_TYPEN)) + ".")
    if not roh:
        raise Fehler("Leere Datei.")
    if len(roh) > UNTERLAGEN_MAX_MB * 1_000_000:
        raise Fehler(f"Datei zu groß ({len(roh) / 1_000_000:.1f} MB) – höchstens {UNTERLAGEN_MAX_MB} MB je Datei.")
    u = unterlagen_daten(d)
    if sum(v.get("groesse", 0) for v in u["dateien"].values()) + len(roh) > UNTERLAGEN_GESAMT_MB * 1_000_000:
        raise Fehler(f"Speicher für Unterlagen voll ({UNTERLAGEN_GESAMT_MB} MB) – bitte alte Dateien löschen.")
    kopf = roh[:512].lstrip().lower()
    if kopf.startswith((b"<!doctype html", b"<html", b"<svg", b"<?xml")) or b"<script" in kopf:
        raise Fehler("Die Datei sieht wie eine Webseite oder ein Skript aus – das ist aus Sicherheitsgründen nicht erlaubt.")
    if roh[:2] == b"MZ" or roh[:4] == b"\x7fELF":
        raise Fehler("Programme sind nicht erlaubt.")
    sparte = str(q.get("sparte", [""])[0] or "").strip().upper()
    if sparte and not KZ_RE.match(sparte):
        raise Fehler("Ungültiges Kürzel.")
    if erlaubt is not None and sparte not in erlaubt:
        raise Fehler("Ihr Konto darf nur in die eigenen Sparten hochladen – bitte eine Sparte wählen.")
    ordner = _ordnername(q.get("ordner", [""])[0])
    if ordner.lower() not in {o.lower() for o in unterlagen_ordner(d)}:      # neuer Ordner beim Hochladen → bleibt auch leer erhalten
        u["ordner"] = sorted([o for o in (u.get("ordner") or []) if isinstance(o, str)] + [ordner], key=str.lower)
    i = secrets.token_hex(8)
    ablage_schreiben(f"Unterlage_{i}", roh)
    ansehen = endung in _ANSEHEN and roh.startswith(_ANSEHEN[endung]) and (endung != "webp" or roh[8:12] == b"WEBP")
    u["dateien"][i] = {"name": name, "ordner": ordner, "sparte": sparte, "groesse": len(roh), "typ": endung, "ansehen": ansehen,
                       "beschreibung": text_einzeilig(q.get("beschreibung", [""])[0], 300), "von": wer, "zeit": time.strftime("%Y-%m-%d %H:%M"),
                       "sha256": hashlib.sha256(roh).hexdigest()}
    speichere(d)
    journal(f"Unterlage hochgeladen: {name} ({len(roh) // 1024} KB, Ordner {ordner}{', Sparte ' + sparte if sparte else ''})")
    r = akt_unterlagen(d, erlaubt)
    r["log"] = [f"✔ „{name}“ hochgeladen."] + r["log"]
    return r


def _datei(d, i, erlaubt, schreiben=False):
    i = str(i or "")
    x = unterlagen_daten(d)["dateien"].get(i) if _ID_RE.match(i) else None
    if not x or not _sichtbar(x, erlaubt):
        raise Fehler("Datei nicht gefunden.")
    if schreiben and not _darf_schreiben(x, erlaubt):
        raise Fehler("Allgemeine Unterlagen kann nur ein Konto ohne Sparten-Beschränkung ändern.")
    return i, x


def akt_unterlage_datei(d, q, erlaubt):
    i, x = _datei(d, q.get("id", [""])[0], erlaubt)
    roh = ablage_lesen(f"Unterlage_{i}")
    if roh is None:
        raise Fehler("Datei fehlt im Speicher.")
    typ = UNTERLAGEN_TYPEN.get(x["typ"], "application/octet-stream") if x.get("ansehen") else "application/octet-stream"
    return {"_datei": roh, "typ": typ, "name": x["name"]}


def akt_unterlage_aendern(d, b, erlaubt):
    i, x = _datei(d, b.get("id"), erlaubt, schreiben=True)
    if "beschreibung" in b:
        x["beschreibung"] = text_einzeilig(b["beschreibung"], 300)
    if "ordner" in b:
        x["ordner"] = _ordnername(b["ordner"])
    if "name" in b:
        neu = _anzeigename(b["name"])
        if neu.rsplit(".", 1)[-1].lower() != x["typ"]:
            raise Fehler("Die Dateiendung darf sich nicht ändern.")
        x["name"] = neu
    if "sparte" in b:
        sp = str(b["sparte"] or "").strip().upper()
        if (sp and not KZ_RE.match(sp)) or (erlaubt is not None and sp not in erlaubt):
            raise Fehler("Diese Sparte ist für Ihr Konto nicht erlaubt.")
        x["sparte"] = sp
    speichere(d)
    r = akt_unterlagen(d, erlaubt)
    r["log"] = [f"✔ „{x['name']}“ gespeichert."]
    return r


def akt_unterlage_ordner(d, b, erlaubt):
    """Ordner anlegen ({"neu": Name}) oder einen leeren, selbst angelegten Ordner entfernen ({"loeschen": Name})"""
    u = unterlagen_daten(d)
    eigene = [o for o in (u.get("ordner") or []) if isinstance(o, str)]
    if b.get("neu") is not None:
        n = _ordnername(b["neu"])
        if n.lower() in {o.lower() for o in unterlagen_ordner(d)}:
            raise Fehler(f"Den Ordner „{n}“ gibt es schon.")
        if len(eigene) >= 100:
            raise Fehler("Höchstens 100 eigene Ordner.")
        u["ordner"] = sorted(eigene + [n], key=str.lower)
        text = f"✔ Ordner „{n}“ angelegt."
    elif b.get("loeschen"):
        n = str(b["loeschen"])
        if n in ORDNER_STANDARD:
            raise Fehler("Standard-Ordner bleiben.")
        if any(x.get("ordner") == n for x in u["dateien"].values()):
            raise Fehler(f"Im Ordner „{n}“ liegen noch Dateien – erst verschieben oder löschen.")
        u["ordner"] = [o for o in eigene if o != n]
        text = f"✔ Ordner „{n}“ entfernt."
    else:
        raise Fehler("Nichts angegeben.")
    speichere(d)
    journal("Unterlagen: " + text[2:])
    r = akt_unterlagen(d, erlaubt)
    r["log"] = [text]
    return r


def akt_unterlage_loeschen(d, b, erlaubt):
    i, x = _datei(d, b.get("id"), erlaubt, schreiben=True)
    ablage_loeschen(f"Unterlage_{i}")
    del unterlagen_daten(d)["dateien"][i]
    speichere(d)
    journal(f"Unterlage gelöscht: {x['name']} (Ordner {x.get('ordner')})")
    r = akt_unterlagen(d, erlaubt)
    r["log"] = [f"✔ „{x['name']}“ gelöscht."]
    return r


__all__ = [_n for _n in dict(globals()) if not _n.startswith("__")]  # alle Namen an die folgenden Module weitergeben
