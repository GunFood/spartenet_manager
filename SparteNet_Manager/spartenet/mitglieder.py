"""SparteNet Manager – Mitglieder: Pächter mit Vorname, Nachname, E-Mail, Telefon, Sparte und Parzelle

Anlegen von Hand, per Excel/CSV-Import (mit Vorschau) oder über die API. Gebucht wird weiter über „Tarife“/„Kalkulation“ –
die Mitgliederliste zeigt den gebuchten Tarif der Parzelle dazu. In E-Mails stehen {vorname}, {nachname}, {telefon} und
„an den Kunden“ geht an die E-Mail des Mitglieds der Parzelle. Personenbezogene Daten: nicht ins Protokoll.
"""
import csv

from .automation import *  # noqa: F401,F403 – alle Namen der vorherigen Module

M_FELDER = ("vorname", "nachname", "email", "telefon", "sparte", "parzelle", "notiz")
_KOEPFE = {
    "vorname": ("vorname", "first name", "firstname"),
    "nachname": ("nachname", "name", "familienname", "last name", "lastname", "pächter", "paechter"),
    "email": ("e-mail", "email", "mail", "e-mail-adresse", "emailadresse"),
    "telefon": ("telefon", "tel", "tel.", "handy", "mobil", "telefonnummer", "phone"),
    "sparte": ("sparte", "kürzel", "kuerzel", "verein", "anlage"),
    "parzelle": ("parzelle", "parzellennr", "parzellen-nr", "parzellen-nr.", "nr", "nr.", "garten"),
    "notiz": ("notiz", "bemerkung", "hinweis"),
}
_TEL_RE = re.compile(r"^[0-9 +()/\-]{3,30}$")


def mitglieder(d):
    m = d.get("mitglieder")
    if not isinstance(m, dict):
        m = {}
        d["mitglieder"] = m
    return m


def _sparten_kz(d):
    try:
        return {kz: s.get("name", kz) for kz, s in kalk_sparten(d).items()}
    except Fehler:
        return {}


def mitglied_pruefen(d, roh, alt=None):
    """prüft und vereinheitlicht ein Mitglied; wirft Fehler mit verständlichem Text"""
    x = dict(alt or {})
    for k in M_FELDER:
        if k in roh:
            x[k] = text_einzeilig(roh.get(k) if roh.get(k) is not None else "", 300 if k == "notiz" else 120).strip()
    x["sparte"] = str(x.get("sparte") or "").upper()
    if not (x.get("vorname") or x.get("nachname")):
        raise Fehler("Vorname oder Nachname angeben.")
    if x.get("email") and not re.fullmatch(r"[^@\s,;<>]{1,64}@[A-Za-z0-9.-]{1,190}\.[A-Za-z]{2,}", x["email"]):
        raise Fehler(f"E-Mail-Adresse „{x['email']}“ ist ungültig.")
    x["email"] = (x.get("email") or "").lower()
    if x.get("telefon") and not _TEL_RE.match(x["telefon"]):
        raise Fehler(f"Telefonnummer „{x['telefon']}“: nur Ziffern, Leerzeichen und + ( ) / -.")
    sp = _sparten_kz(d)
    if x["sparte"] and x["sparte"] not in sp:
        raise Fehler(f"Sparte „{x['sparte']}“ gibt es nicht.")
    p = str(x.get("parzelle") or "").strip()
    if p:
        if not p.isdigit() or not 1 <= int(p) <= 999:
            raise Fehler(f"Parzelle „{p}“ muss eine Nummer sein.")
        if not x["sparte"]:
            raise Fehler("Zur Parzelle bitte die Sparte angeben.")
        n = (kalk_sparten(d).get(x["sparte"]) or {}).get("n")
        if n and int(p) > int(n):
            raise Fehler(f"{x['sparte']} hat die Parzellen 1–{n}.")
        x["parzelle"] = int(p)
    else:
        x["parzelle"] = ""
    return x


def _suchen(d, x):
    """vorhandenes Mitglied für einen Import/API-Eintrag: gleiche E-Mail, sonst gleiche Parzelle und gleicher Nachname"""
    for i, m in mitglieder(d).items():
        if x.get("email") and m.get("email") == x["email"]:
            return i
    for i, m in mitglieder(d).items():
        if x.get("parzelle") and m.get("sparte") == x.get("sparte") and str(m.get("parzelle")) == str(x["parzelle"]) \
                and (m.get("nachname") or "").lower() == (x.get("nachname") or "").lower():
            return i
    return None


def mitglied_eintragen(d, roh, quelle, mid=None, zusammenfuehren=True):
    """legt an oder ändert; gibt (id, neu) zurück. Löst bei neuen Mitgliedern das Ereignis „mitglied_neu“ aus."""
    alle = mitglieder(d)
    if mid and mid not in alle:
        raise Fehler("Mitglied nicht gefunden.")
    if not mid and zusammenfuehren:     # vorhandenes Mitglied? (gleiche E-Mail bzw. Parzelle + Nachname) – dann nur ergänzen
        probe = {"email": str(roh.get("email") or "").strip().lower(), "sparte": str(roh.get("sparte") or "").strip().upper(),
                 "parzelle": str(roh.get("parzelle") or "").strip(), "nachname": str(roh.get("nachname") or "").strip()}
        mid = _suchen(d, probe)
    if mid:
        x = mitglied_pruefen(d, {k: v for k, v in roh.items() if v not in (None, "")} if zusammenfuehren else roh, alle[mid])
    else:
        x = mitglied_pruefen(d, roh)
    neu = not mid
    if neu:
        if len(alle) >= 20000:
            raise Fehler("Höchstens 20000 Mitglieder.")
        mid = secrets.token_hex(6)
        x.update(angelegt=time.strftime("%Y-%m-%d %H:%M"), quelle=quelle)
    x["geaendert"] = time.strftime("%Y-%m-%d %H:%M")
    alle[mid] = x
    return mid, neu


def _zeile(d, i, m):
    tarif = ((d.get("buchungen") or {}).get(m.get("sparte")) or {}).get(str(m.get("parzelle")), "") if m.get("parzelle") else ""
    return {"id": i, **{k: m.get(k, "") for k in M_FELDER}, "tarif": tarif, "angelegt": m.get("angelegt", ""), "quelle": m.get("quelle", ""),
            "geaendert": m.get("geaendert", "")}


def akt_mitglieder(d, erlaubt=None):
    zeilen = [_zeile(d, i, m) for i, m in mitglieder(d).items() if erlaubt is None or m.get("sparte") in erlaubt]
    zeilen.sort(key=lambda z: (z["sparte"], int(z["parzelle"] or 0), z["nachname"].lower(), z["vorname"].lower()))
    gebucht = sum(1 for z in zeilen if z["tarif"])
    # gebuchte Parzellen ohne Mitglied
    mit = {(z["sparte"], str(z["parzelle"])) for z in zeilen}
    ohne = sorted(((kz, int(p)) for kz, b in (d.get("buchungen") or {}).items() for p, t in b.items()
                   if t and (erlaubt is None or kz in erlaubt) and (kz, str(p)) not in mit), key=lambda x: x)
    return {"zeilen": zeilen, "sparten": _sparten_kz(d), "ohne_mitglied": [{"sparte": kz, "parzelle": p} for kz, p in ohne[:500]],
            "log": [f"{len(zeilen)} Mitglied(er), davon {gebucht} mit gebuchtem Tarif" + (f" · {len(ohne)} gebuchte Parzelle(n) ohne Mitglied" if ohne else "")]}


def _sparte_erlaubt(x, erlaubt):
    if erlaubt is not None and x.get("sparte") not in erlaubt:
        raise Fehler("Ihr Konto darf nur Mitglieder der eigenen Sparten bearbeiten.")


def akt_mitglied_speichern(d, b, ich, erlaubt=None):
    roh = b.get("mitglied") or {}
    mid = str(roh.get("id") or "") or None
    if mid and mid in mitglieder(d):
        _sparte_erlaubt(mitglieder(d)[mid], erlaubt)
    _sparte_erlaubt({"sparte": str(roh.get("sparte") or (mitglieder(d).get(mid) or {}).get("sparte") or "").upper()}, erlaubt)
    mid, neu = mitglied_eintragen(d, roh, ich, mid, zusammenfuehren=False)
    speichere(d)
    m = mitglieder(d)[mid]
    journal(f"Mitglied {'angelegt' if neu else 'geändert'}: {m.get('sparte') or '–'} Parzelle {m.get('parzelle') or '–'} durch {ich}")
    if neu:
        ereignis("mitglied_neu", {**{k: m.get(k, "") for k in M_FELDER}, "name": f"{m.get('vorname', '')} {m.get('nachname', '')}".strip()}, d)
    r = akt_mitglieder(d, erlaubt)
    r["log"] = [f"✔ {m.get('vorname', '')} {m.get('nachname', '')} {'angelegt' if neu else 'gespeichert'}."] + r["log"]
    r["id"] = mid
    return r


def akt_mitglied_loeschen(d, b, ich, erlaubt=None):
    mid = str(b.get("id") or "")
    m = mitglieder(d).get(mid)
    if not m:
        raise Fehler("Mitglied nicht gefunden.")
    _sparte_erlaubt(m, erlaubt)
    del mitglieder(d)[mid]
    speichere(d)
    journal(f"Mitglied gelöscht: {m.get('sparte') or '–'} Parzelle {m.get('parzelle') or '–'} durch {ich}")
    r = akt_mitglieder(d, erlaubt)
    r["log"] = ["✔ Mitglied gelöscht."] + r["log"]
    return r


def _tabelle_lesen(roh, name):
    """Zeilen (Liste von Listen) aus .xlsx oder .csv"""
    if roh[:2] == b"PK":
        namen, lies = xlsx_lesen(roh)
        if not namen:
            raise Fehler("Die Excel-Datei hat kein Blatt.")
        zellen = lies(namen[0]) or {}
        zeilen = {}
        for ref, v in zellen.items():
            m = re.match(r"([A-Z]+)(\d+)$", ref)
            if not m:
                continue
            sp = 0
            for ch in m.group(1):
                sp = sp * 26 + ord(ch) - 64
            zeilen.setdefault(int(m.group(2)), {})[sp - 1] = v
        if not zeilen:
            return []
        breite = max(max(z) for z in zeilen.values()) + 1
        return [[("" if zeilen[r].get(c) is None else str(zeilen[r].get(c))).strip() for c in range(breite)] for r in sorted(zeilen)]
    try:
        text = roh.decode("utf-8-sig")
    except UnicodeDecodeError:
        text = roh.decode("cp1252", errors="replace")
    trenner = ";" if text.count(";") >= text.count(",") else ","
    return [[c.strip() for c in z] for z in csv.reader(io.StringIO(text), delimiter=trenner)]


def akt_mitglieder_import(d, q, roh, ich, erlaubt=None):
    """Vorschau (ohne ?uebernehmen=1) bzw. Übernahme einer Excel-/CSV-Liste"""
    if not roh:
        raise Fehler("Leere Datei.")
    zeilen = [z for z in _tabelle_lesen(roh, q.get("name", [""])[0]) if any(z)]
    if len(zeilen) < 2:
        raise Fehler("Die Datei braucht eine Kopfzeile und mindestens eine Zeile mit Daten.")
    kopf = [c.lower().strip().rstrip(":") for c in zeilen[0]]
    spalten = {}
    for feld, namen in _KOEPFE.items():
        for i, k in enumerate(kopf):
            if k in namen and i not in spalten.values():
                spalten.setdefault(feld, i)
    if "nachname" not in spalten and "vorname" not in spalten:
        raise Fehler("Keine Spalte „Nachname“ oder „Vorname“ gefunden. Erkannt werden: Vorname, Nachname, E-Mail, Telefon, Sparte, Parzelle, Notiz.")
    standard_sparte = str(q.get("sparte", [""])[0] or "").upper()
    uebernehmen = q.get("uebernehmen", ["0"])[0] == "1"
    ergebnis, neu, geaendert, fehler = [], 0, 0, 0
    if len(zeilen) > 5001:
        raise Fehler("Höchstens 5000 Zeilen je Import.")
    for nr, z in enumerate(zeilen[1:], start=2):
        roh_m = {f: (z[i] if i < len(z) else "") for f, i in spalten.items()}
        if not roh_m.get("sparte") and standard_sparte:
            roh_m["sparte"] = standard_sparte
        try:
            x = mitglied_pruefen(d, roh_m)
            _sparte_erlaubt(x, erlaubt)
            vorhanden = _suchen(d, x)
            if uebernehmen:
                mid, ist_neu = mitglied_eintragen(d, roh_m, f"Import {ich}")
                if ist_neu:
                    m = mitglieder(d)[mid]
                    ereignis("mitglied_neu", {**{k: m.get(k, "") for k in M_FELDER}, "name": f"{m.get('vorname', '')} {m.get('nachname', '')}".strip()}, d)
            neu += not vorhanden
            geaendert += bool(vorhanden)
            ergebnis.append({"zeile": nr, "status": "aktualisieren" if vorhanden else "neu", "name": f"{x['vorname']} {x['nachname']}".strip(),
                             "sparte": x["sparte"], "parzelle": x["parzelle"], "email": x["email"], "telefon": x.get("telefon", "")})
        except Fehler as e:
            fehler += 1
            ergebnis.append({"zeile": nr, "status": "Fehler", "name": " ".join(str(roh_m.get(k, "")) for k in ("vorname", "nachname")).strip(), "fehler": str(e)})
    if uebernehmen:
        speichere(d)
        journal(f"Mitglieder-Import durch {ich}: {neu} neu, {geaendert} aktualisiert, {fehler} Fehler")
    erkannt = ", ".join(f"{f} = Spalte {zeilen[0][i] or i + 1}" for f, i in spalten.items())
    return {"zeilen": ergebnis[:2000], "neu": neu, "geaendert": geaendert, "fehler": fehler, "uebernommen": uebernehmen,
            "log": [("✔ Übernommen: " if uebernehmen else "Vorschau: ") + f"{neu} neu, {geaendert} aktualisieren, {fehler} mit Fehler (nicht übernommen).",
                    f"Erkannte Spalten: {erkannt}."]}


def akt_mitglieder_export(d, erlaubt=None):
    f = io.StringIO()
    w = csv.writer(f, delimiter=";")
    w.writerow(["Vorname", "Nachname", "E-Mail", "Telefon", "Sparte", "Parzelle", "Tarif", "Notiz", "angelegt"])
    for z in akt_mitglieder(d, erlaubt)["zeilen"]:
        w.writerow([csv_sicher(z[k]) for k in ("vorname", "nachname", "email", "telefon", "sparte", "parzelle", "tarif", "notiz", "angelegt")])
    journal("Mitgliederliste exportiert")
    return {"_datei": ("﻿" + f.getvalue()).encode("utf-8"), "typ": "text/csv", "name": f"SparteNet_Mitglieder_{time.strftime('%Y%m%d')}.csv"}


def csv_sicher(v):
    """Schutz vor Formeln beim Öffnen in Excel (=, +, -, @ am Anfang)"""
    v = "" if v is None else str(v)
    return "'" + v if v[:1] in ("=", "+", "-", "@") and not re.fullmatch(r"[+\-]?[0-9 ()/]+", v) else v


__all__ = [_n for _n in dict(globals()) if not _n.startswith("__")]  # alle Namen an die folgenden Module weitergeben
