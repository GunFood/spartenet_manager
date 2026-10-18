"""SparteNet Manager – Benutzerkonten und Zugriffsrechte je Bereich (Arbeitsblatt/Funktion: kein Zugriff, lesen, schreiben)"""
from .umzug import *  # noqa: F401,F403 – alle Namen der vorherigen Module

# Das Konto „admin“ meldet sich mit dem Manager-Passwort an (SPARTENET_PASSWORD bzw. SPARTENET_PASSWORD_FILE)
# und kann weitere Konten anlegen. Weitere Konten liegen im Datenspeicher (Datei oder MariaDB) unter „benutzer“,
# Passwörter nur als PBKDF2-Prüfsumme.
#
# Ein Konto ist entweder Administrator (alles), gesperrt (keine Anmeldung) oder hat Rechte je Bereich:
#   kein = Bereich ausgeblendet · lesen = ansehen, Vorschau · schreiben = ändern und ans Gateway übertragen
ADMIN_NAME = "admin"
HANDY_NAME = "Handy (PIN)"
_BN_RUNDEN = 300_000
_BN_NAME_RE = re.compile(r"^[a-z0-9][a-z0-9._-]{2,31}$")

STUFEN = {"kein": "kein Zugriff", "lesen": "lesen", "schreiben": "lesen und schreiben"}
STUFE_RANG = {"kein": 0, "lesen": 1, "schreiben": 2}
ARTEN = {"admin": "Administrator", "bereiche": "Rechte je Bereich", "gesperrt": "Gesperrt"}
# Bereich, Bezeichnung, mögliche Stufen, Reiter in der Oberfläche
BEREICHE = [
    ("start", "Start / Überblick", ("kein", "lesen"), ["start"]),
    ("auslesen", "Auslesen, Abgleich, Systeminfo, Alle Daten, Änderungsprotokoll", ("kein", "lesen"), ["lesen", "abgleich", "system", "daten"]),
    ("planung", "Planung: Sparten, IP-Plan, Excel-Import", ("kein", "lesen", "schreiben"), ["planung"]),
    ("netze", "Netze und WLANs am Gateway anlegen", ("kein", "lesen", "schreiben"), ["einrichten"]),
    ("wlan_pw", "WLAN-Passwörter je Parzelle: erzeugen, ändern, ans Gateway übertragen, Rückgängig", ("kein", "lesen", "schreiben"), ["einrichten", "uebertragen"]),
    ("tarife", "Tarife festlegen und ans Gateway übertragen (Bandbreite, Netzgröße)", ("kein", "lesen", "schreiben"), ["tarife"]),
    ("buchungen", "Tarif buchen: Parzelle einem Tarif zuordnen, Buchungen erfassen", ("kein", "lesen", "schreiben"), ["tarife", "kalkulation"]),
    ("kalkulation", "Kalkulation: Annahmen, Investition, Excel", ("kein", "lesen", "schreiben"), ["kalkulation"]),
    ("netzplanung", "Netzplanung & Einnahmen", ("kein", "lesen", "schreiben"), ["netzplanung"]),
    ("karten", "Zugangskarten drucken (lesen; braucht WLAN-Passwörter lesen) und Kartendesign ändern (schreiben)", ("kein", "lesen", "schreiben"), ["einrichten", "kartendesign"]),
    ("voucher", "Gast-Voucher erstellen", ("kein", "lesen", "schreiben"), ["voucher", "start"]),
    ("unterlagen", "Unterlagen: Dateien ansehen (lesen), hochladen und löschen (schreiben)", ("kein", "lesen", "schreiben"), ["unterlagen"]),
    ("automationen", "Automationen: Regeln ansehen (lesen), anlegen und ändern (schreiben); E-Mail-Versand und API-Schlüssel nur Administratoren", ("kein", "lesen", "schreiben"), ["automationen"]),
    ("mitglieder", "Mitglieder: Liste ansehen (lesen), anlegen, ändern, importieren (schreiben)", ("kein", "lesen", "schreiben"), ["mitglieder"]),
    ("rechnungen", "Rechnungen und Zahlungsabgleich: ansehen (lesen), erstellen, senden, Zahlungen buchen (schreiben)", ("kein", "lesen", "schreiben"), ["rechnungen"]),
    ("tickets", "Anfragen (Tickets): ansehen (lesen), bearbeiten, beantworten, zuweisen (schreiben)", ("kein", "lesen", "schreiben"), ["tickets"]),
    ("verbindung", "Verbindung, Cloud-Key, Handy & Tablet, Protokoll, Diagnose", ("kein", "lesen", "schreiben"), ["verbindung"]),
    ("gestaltung", "Oberfläche gestalten: Anmeldeseite, Pächter-Seite, Menü und Ansichtsprofile der Konten", ("kein", "lesen", "schreiben"), ["gestaltung"]),
]
BEREICH_TEXT = {k: t for k, t, _, _ in BEREICHE}
BEREICH_STUFEN = {k: s for k, _, s, _ in BEREICHE}


def _alle(stufe, **ausnahmen):
    return {k: (ausnahmen.get(k) or (stufe if stufe in s else s[-1])) for k, _, s, _ in BEREICHE}


VORLAGEN = {
    "lesen": ("Nur lesen", _alle("lesen", verbindung="kein", gestaltung="kein")),
    "schreiben": ("Lesen und schreiben", _alle("schreiben", verbindung="lesen", gestaltung="lesen")),
    "vorstand": ("Vorstand Sparte: lesen + WLAN-Passwörter, Tarif buchen, Karten, Voucher",
                 _alle("lesen", verbindung="kein", wlan_pw="schreiben", buchungen="schreiben", karten="lesen", voucher="schreiben")),
    "kasse": ("Kasse: Tarif buchen und Kalkulation, sonst lesen", _alle("lesen", verbindung="kein", buchungen="schreiben", kalkulation="schreiben")),
}

# Was eine Anfrage braucht: ("immer",) · ("admin",) · (Bereich, Stufe)
_IMMER = {"/api/aktiv", "/api/2fa-vergessen", "/api/app-uebersicht", "/api/app-geraete", "/api/app-geraet-entfernen", "/api/einstellungen", "/api/ansicht", "/api/benutzer-ich", "/api/plan", "/api/pw-regel", "/api/2fa-start", "/api/2fa-bestaetigen", "/api/2fa-aus"}  # nur lesend (GET) bzw. eigene Ansicht
_NUR_ADMIN = {"/api/benutzer", "/api/benutzer-speichern", "/api/benutzer-loeschen", "/api/beenden"}
_LESEN = {
    "/api/start": "start", "/api/parzelle": "start",
    "/api/test": "auslesen", "/api/lesen": "auslesen", "/api/abgleich": "auslesen", "/api/vergleich": "auslesen", "/api/journal": "auslesen",
    "/api/system": "auslesen", "/api/daten-liste": "auslesen", "/api/daten-pruefen": "auslesen",
    "/api/tarif-vergleich": "tarife", "/api/tarif-erkennen": "buchungen", "/api/kalkulation": "kalkulation", "/api/gwplan": "netzplanung", "/api/gwplan-vlan": "netzplanung", "/api/zuteilung": "netzplanung", "/api/zuteilung-parzellen": "netzplanung",
    "/api/karten-vorschau": "karten", "/api/karten": "karten", "/api/log": "verbindung",
    "/api/wlans": "wlan_pw", "/api/unterlagen": "unterlagen", "/api/unterlage-datei": "unterlagen", "/api/voucher-liste": "voucher", "/api/voucher-druck": "voucher",
    "/api/automation": "automationen", "/api/email-layout": "automationen", "/api/email-vorschau": "automationen",
    "/api/mitglieder": "mitglieder", "/api/mitglieder-export": "mitglieder",
    "/api/tickets": "tickets", "/api/ticket": "tickets",
    "/api/rechnungen": "rechnungen", "/api/rechnung-pdf": "rechnungen",
    "/api/vertraege": "mitglieder", "/api/rundschreiben": "mitglieder", "/api/rundschreiben-empfaenger": "mitglieder", "/api/mitglied-auskunft": "mitglieder",
    "/api/ueberwachung": "auslesen", "/api/laufzeiten": "buchungen", "/api/gestaltung": "gestaltung", "/api/logos": "karten", "/api/logo-bild": "karten",
}
_GET_LESEN_SONST_SCHREIBEN = {"/api/voucher-vorlagen": "voucher", "/api/tarife": "tarife", "/api/buchungen": "buchungen", "/api/design": "karten", "/api/fern": "verbindung"}
_VORSCHAU = {"/api/zugang": "wlan_pw", "/api/netze": "netze", "/api/uebertragen": "wlan_pw", "/api/ppsk-hochladen": "wlan_pw", "/api/tarif-uebertragen": "tarife", "/api/voucher": "voucher", "/api/voucher-loeschen": "voucher", "/api/zuteilung-gateway": "netze", "/api/umzug": "netze"}
_SCHREIBEN = {
    "/api/laufzeit-verlaengern": "buchungen", "/api/laufzeit-starten": "buchungen",
    "/api/seiten-design": "gestaltung", "/api/seiten-vorschau": "gestaltung", "/api/ansicht-profile": "gestaltung",
    "/api/excel": "planung", "/api/schreibtest": "netze", "/api/umzug-rueckgaengig": "netze",
    "/api/ppsk-speichern": "wlan_pw", "/api/rueckgaengig": "wlan_pw", "/api/wlan-zuordnung": "wlan_pw", "/api/passwort": "wlan_pw",
    "/api/tarif-rueckgaengig": "tarife", "/api/tarif-zuordnung": "buchungen",
    "/api/kalk-annahmen": "kalkulation", "/api/kalk-sparte": "kalkulation", "/api/kalk-import": "kalkulation",
    "/api/gwplan-vlan-uebernehmen": "planung", "/api/gwplan-sparte": "netzplanung", "/api/gwplan-annahmen": "netzplanung", "/api/gwplan-zuruecksetzen": "netzplanung", "/api/gwplan-import": "netzplanung", "/api/zuteilung-einstellen": "netzplanung", "/api/zuteilung-setzen": "netzplanung", "/api/zuteilung-verdichten": "netzplanung",
    "/api/logo": "karten", "/api/logo-loeschen": "karten", "/api/logo-waehlen": "karten",
    "/api/unterlage-hochladen": "unterlagen", "/api/unterlage-aendern": "unterlagen", "/api/unterlage-loeschen": "unterlagen", "/api/unterlage-ordner": "unterlagen",
    "/api/email-vorlage-speichern": "automationen", "/api/email-vorlage-loeschen": "automationen",
    "/api/mitglied-speichern": "mitglieder", "/api/mitglied-loeschen": "mitglieder", "/api/mitglieder-import": "mitglieder",
    "/api/ticket-speichern": "tickets", "/api/ticket-kommentar": "tickets",
    "/api/rechnungslauf": "rechnungen", "/api/rechnung-senden": "rechnungen", "/api/rechnung-status": "rechnungen",
    "/api/zahlungen-import": "rechnungen", "/api/zahlungen-uebernehmen": "rechnungen",
    "/api/vertrag-speichern": "mitglieder", "/api/vertrag-kuendigen": "mitglieder", "/api/rundschreiben-senden": "mitglieder", "/api/mitglied-dsgvo-loeschen": "mitglieder",
    "/api/automation-speichern": "automationen", "/api/automation-loeschen": "automationen", "/api/automation-probe": "automationen",
    "/api/konsolen": "verbindung", "/api/log-loeschen": "verbindung", "/api/tailscale": "verbindung", "/api/diagnose": "verbindung",
}


def recht_fuer(pfad, q, b):
    """was eine Anfrage braucht – unbekannte Pfade nur für Administratoren"""
    if pfad in _NUR_ADMIN:
        return ("admin",)
    if pfad == "/api/einstellungen" and b is not None:
        return ("verbindung", "schreiben")
    if pfad in ("/api/plan", "/api/pw-regel") and b is not None:
        return ("planung" if pfad == "/api/plan" else "wlan_pw", "schreiben")
    if pfad in _IMMER:
        return ("immer",)
    if pfad == "/api/daten":
        return ("verbindung", "schreiben") if q.get("geheim", ["0"])[0] == "1" else ("auslesen", "lesen")
    if pfad in _LESEN:
        return (_LESEN[pfad], "lesen")
    if pfad in _GET_LESEN_SONST_SCHREIBEN:
        return (_GET_LESEN_SONST_SCHREIBEN[pfad], "lesen" if b is None else "schreiben")
    if pfad in _VORSCHAU:
        return (_VORSCHAU[pfad], "schreiben" if isinstance(b, dict) and b.get("ausfuehren") else "lesen")
    if pfad == "/api/ppsk":
        return ("wlan_pw", "lesen" if isinstance(b, dict) and b.get("art", "anzeigen") == "anzeigen" else "schreiben")
    if pfad in _SCHREIBEN:
        return (_SCHREIBEN[pfad], "schreiben")
    return ("admin",)


def benutzer_liste(d):
    u = d.get("benutzer")
    if not isinstance(u, dict):
        u = {}
        d["benutzer"] = u
    return u


def _bereiche_pruefen(roh, basis=None):
    aus = dict(basis or _alle("kein"))
    for k, v in (roh or {}).items():
        if k in BEREICH_STUFEN:
            aus[k] = v if v in BEREICH_STUFEN[k] else ("lesen" if v == "schreiben" and "lesen" in BEREICH_STUFEN[k] else "kein")
    return aus


def konto_rechte(d, name):
    """{"art": admin|bereiche|gesperrt, "bereiche": {...}} live aus dem Datenspeicher, oder None (Konto gibt es nicht)"""
    if name == ADMIN_NAME:
        return {"art": "admin", "bereiche": _alle("schreiben")}
    if name == HANDY_NAME:
        return {"art": "bereiche", "bereiche": _alle("schreiben")}
    u = benutzer_liste(d).get(name)
    if not isinstance(u, dict):
        return None
    r = u.get("recht")
    sp = [str(x) for x in u.get("sparten") or []] or None
    if r in VORLAGEN:  # Konten aus 4.4: „lesen“ / „schreiben“
        return {"art": "bereiche", "bereiche": dict(VORLAGEN[r][1]), "sparten": sp}
    if r in ("admin", "gesperrt"):
        return {"art": r, "bereiche": _alle("schreiben" if r == "admin" else "kein"), "sparten": None}
    return {"art": "bereiche", "bereiche": _bereiche_pruefen(u.get("bereiche")), "sparten": sp}


# ---- Rechte je Sparte: Konten mit Sparten-Liste sehen und ändern nur diese Sparten ------------------
# gateway- oder spartenübergreifende Änderungen bleiben Konten ohne Beschränkung vorbehalten
SPARTE_PFLICHT = {"/api/ppsk", "/api/ppsk-speichern", "/api/wlans", "/api/wlan-zuordnung", "/api/netze", "/api/uebertragen", "/api/rueckgaengig", "/api/vergleich", "/api/abgleich",
                  "/api/ppsk-hochladen", "/api/karten", "/api/buchungen", "/api/parzelle", "/api/kalk-sparte"}
NUR_OHNE_BESCHRAENKUNG = {"/api/seiten-design", "/api/ansicht-profile", "/api/excel", "/api/tarif-zuordnung", "/api/tarif-uebertragen", "/api/tarif-rueckgaengig", "/api/kalk-annahmen",
                          "/api/kalk-import", "/api/gwplan-annahmen", "/api/gwplan-zuruecksetzen", "/api/gwplan-import", "/api/gwplan-vlan-uebernehmen",
                          "/api/logo", "/api/logo-loeschen", "/api/logo-waehlen", "/api/schreibtest", "/api/konsolen", "/api/log-loeschen", "/api/tailscale", "/api/diagnose",
                          "/api/zuteilung-einstellen", "/api/zuteilung-gateway", "/api/zuteilung-setzen", "/api/zuteilung-verdichten", "/api/umzug", "/api/umzug-rueckgaengig",
                          "/api/email-vorlage-speichern", "/api/email-vorlage-loeschen", "/api/rechnungslauf", "/api/zahlungen-import", "/api/zahlungen-uebernehmen",
                          "/api/automation", "/api/automation-speichern", "/api/automation-loeschen", "/api/automation-probe"}
NUR_OHNE_BESCHRAENKUNG_SCHREIBEND = {"/api/plan", "/api/tarife", "/api/design", "/api/einstellungen", "/api/fern", "/api/pw-regel"}


def sparten_von(rechte):
    """None = alle Sparten, sonst Menge der erlaubten Kürzel"""
    if not rechte or rechte.get("art") == "admin" or not rechte.get("sparten"):
        return None
    return set(rechte["sparten"])


def sparte_pruefen(pfad, q, b, erlaubt, d):
    """wirft Fehler, wenn die Anfrage eine fremde Sparte betrifft oder spartenübergreifend schreibt"""
    if erlaubt is None:
        return
    if pfad in NUR_OHNE_BESCHRAENKUNG or (pfad in NUR_OHNE_BESCHRAENKUNG_SCHREIBEND and b is not None):
        raise Fehler("Diese Funktion betrifft alle Sparten bzw. das ganze Gateway – nur für Konten ohne Sparten-Beschränkung.")
    kz = None
    if isinstance(b, dict) and b.get("sparte") not in (None, ""):
        kz = str(b["sparte"])
    elif q.get("sparte", [""])[0]:
        kz = q["sparte"][0]
    elif pfad == "/api/gwplan-sparte":
        try:
            nr = int((b or {}).get("nr"))
        except (TypeError, ValueError):
            nr = None
        z = next((x for x in gwp_anlagen(d) if x["nr"] == nr), None)
        kz = (((d.get("gwplan") or {}).get("wahl") or {}).get(str(nr)) or {}).get("kz") or (z or {}).get("kz") or GWP_KUERZEL.get(nr)
        if isinstance(b, dict) and "kz" in b:
            raise Fehler("Kürzel ändern nur für Konten ohne Sparten-Beschränkung.")
    if pfad in SPARTE_PFLICHT or pfad == "/api/gwplan-sparte":
        if not kz:
            raise Fehler("Bitte eine Sparte auswählen – Ihr Konto ist auf bestimmte Sparten beschränkt.")
        if kz not in erlaubt:
            raise Fehler(f"Keine Berechtigung für die Sparte {kz} – Ihr Konto ist auf {', '.join(sorted(erlaubt))} beschränkt.")


def antwort_filtern(pfad, a, erlaubt):
    """Listen auf die erlaubten Sparten kürzen"""
    if erlaubt is None or not isinstance(a, dict):
        return a
    if pfad == "/api/plan" and "sparten" in a:
        a = dict(a)
        a["sparten"] = [x for x in a["sparten"] if x.get("kz") in erlaubt]
        a["netze"] = [x for x in a.get("netze", []) if x.get("sparte") in erlaubt]
        if isinstance(a.get("roh"), dict):
            a["roh"] = {**a["roh"], "sparten": [x for x in a["roh"].get("sparten", []) if x.get("kz") in erlaubt]}
    elif pfad == "/api/kalkulation" and "zeilen" in a:
        a = dict(a)
        a["zeilen"] = [x for x in a["zeilen"] if x.get("kz") in erlaubt]
        z = a["zeilen"]
        a["gesamt"] = {**a["gesamt"], "sparten": len(z), "parzellen_alle": sum(x["n"] for x in z), "gebucht": sum(x["gebucht"] for x in z),
                       "umsatz_brutto": round(sum(x["umsatz_brutto"] for x in z), 2), "umsatz": round(sum(x["umsatz"] for x in z), 2),
                       "db": round(sum(x["db"] for x in z), 2), "beschraenkt": True}
    elif pfad.startswith("/api/gwplan") and "zeilen" in a and "standorte" in a:
        a = dict(a)
        a["zeilen"] = [x for x in a["zeilen"] if x.get("kz") in erlaubt]
        nrs = {x["standort"] for x in a["zeilen"]}
        a["standorte"] = [x for x in a["standorte"] if x["nr"] in nrs]
        z = a["zeilen"]
        g = dict(a["gesamt"])
        g.update(sparten=len(z), parzellen=sum(x["parz"] for x in z), kunden=round(sum(x["kunden"] for x in z), 1),
                 einnahme=round(sum(x["einnahme"] for x in z), 2), einnahme_monat=round(sum(x["einnahme_monat"] for x in z), 2),
                 investition=round(sum(x["investition"] for x in z), 2), db=round(sum(x["db"] for x in z), 2), beschraenkt=True)
        g["quote"] = g["kunden"] / g["parzellen"] if g["parzellen"] else 0
        a["gesamt"] = g
        a["log"] = [x for x in a.get("log", []) if x.startswith("✔")] + [f"{len(z)} Sparte(n) – nur Ihre Sparten ({', '.join(sorted(erlaubt))})"]
    return a


def rechte_text(rechte):
    if not rechte:
        return ""
    if rechte["art"] != "bereiche":
        return ARTEN[rechte["art"]]
    b = rechte["bereiche"]
    for k, (t, vorl) in VORLAGEN.items():
        if b == vorl:
            return t.split(":")[0]
    s = sum(1 for v in b.values() if v == "schreiben")
    l = sum(1 for v in b.values() if v == "lesen")
    if not s:
        return "Nur lesen" if l else "kein Zugriff"
    return f"Individuell ({s} Bereich{'e' if s != 1 else ''} schreiben, {l} lesen)"


def erlaubt(rechte, bedarf):
    if not rechte or rechte["art"] == "gesperrt":
        return False
    if rechte["art"] == "admin" or bedarf[0] == "immer":
        return True
    if bedarf[0] == "admin":
        return False
    return STUFE_RANG[rechte["bereiche"].get(bedarf[0], "kein")] >= STUFE_RANG[bedarf[1]]


def fehlt_text(name, rechte, bedarf):
    if bedarf[0] == "admin":
        return f"Keine Berechtigung – dafür sind Administrator-Rechte nötig (Ihr Konto: „{name}“)."
    hat = rechte["bereiche"].get(bedarf[0], "kein")
    return (f"Keine Berechtigung – Bereich „{BEREICH_TEXT[bedarf[0]]}“: Ihr Konto „{name}“ hat „{STUFEN[hat]}“, "
            f"dafür ist „{STUFEN[bedarf[1]]}“ nötig.")


def ich_daten(name, rechte):
    """für die Oberfläche: was das Konto sieht und darf"""
    reiter = {}
    for k, _, _, tabs in BEREICHE:
        for t in tabs:
            reiter[t] = max(reiter.get(t, "kein"), rechte["bereiche"].get(k, "kein"), key=STUFE_RANG.get)
    if rechte["art"] == "admin":
        reiter = {t: "schreiben" for t in reiter}
    return {"name": name, "art": rechte["art"], "admin": rechte["art"] == "admin", "recht_text": rechte_text(rechte),
            "bereiche": rechte["bereiche"], "reiter": reiter, "sparten": rechte.get("sparten")}


def _bn_hash(pw, salz, runden=_BN_RUNDEN):
    return hashlib.pbkdf2_hmac("sha256", pw.encode("utf-8"), bytes.fromhex(salz), runden).hex()


def _bn_name(name):
    n = str(name or "").strip().lower()
    if not _BN_NAME_RE.match(n):
        raise Fehler("Benutzername: 3–32 Zeichen, nur a–z, 0–9, Punkt, Bindestrich und Unterstrich, am Anfang ein Buchstabe oder eine Ziffer.")
    return n


def _bn_passwort(pw):
    pw = str(pw or "")
    if len(pw) < 12:
        raise Fehler("Das Passwort muss mindestens 12 Zeichen lang sein.")
    if len(pw) > 200:
        raise Fehler("Das Passwort ist zu lang (höchstens 200 Zeichen).")
    if len(set(pw)) < 5:
        raise Fehler("Das Passwort ist zu einfach – bitte mehr verschiedene Zeichen verwenden.")
    return pw


def _anmeldesperre(quelle, ok):
    """gleiche Sperre wie beim Manager-Passwort: 5 Fehlversuche je Adresse → 5 Minuten warten"""
    with _AUTH_SPERRE_LOCK:
        jetzt = time.time()
        quelle = str(quelle or "unbekannt")[:64]
        if quelle not in _AUTH_LOCKS and len(_AUTH_LOCKS) >= 4096:
            del _AUTH_LOCKS[min(_AUTH_LOCKS, key=lambda ip: _AUTH_LOCKS[ip]["zuletzt"])]
        sperre = _AUTH_LOCKS.setdefault(quelle, {"fehl": 0, "bis": 0.0, "zuletzt": jetzt})
        sperre["zuletzt"] = jetzt
        if sperre["bis"] > jetzt:
            raise Fehler(f"Zu viele Fehlversuche – bitte {int(sperre['bis'] - jetzt) // 60 + 1} Minute(n) warten.")
        if ok is None:
            return
        if ok:
            sperre["fehl"] = 0
            return
        sperre["fehl"] += 1
        LOG.warning("Falsche Anmeldung (%d. Fehlversuch)", sperre["fehl"])
        if sperre["fehl"] >= 5:
            sperre["bis"], sperre["fehl"] = jetzt + 300, 0
            raise Fehler("Benutzername oder Passwort falsch. Zu viele Fehlversuche – Anmeldung 5 Minuten gesperrt.")
        raise Fehler(f"Benutzername oder Passwort falsch ({5 - sperre['fehl']} Versuch(e) bis zur Sperre).")


_KONTO_SPERRE = {}
_KONTO_SPERRE_LOCK = threading.Lock()


def _konto_sperre(name, ok):
    """zusätzlich je Konto: 10 Fehlversuche (egal von wo) → 15 Minuten gesperrt (S3)"""
    with _KONTO_SPERRE_LOCK:
        jetzt = time.time()
        z = _KONTO_SPERRE.setdefault(name, {"fehl": 0, "bis": 0.0})
        if z["bis"] > jetzt:
            raise Fehler(f"Dieses Konto ist nach vielen Fehlversuchen für {int(z['bis'] - jetzt) // 60 + 1} Minute(n) gesperrt.")
        if ok is None:
            return
        if ok:
            z["fehl"] = 0
            return
        z["fehl"] += 1
        if z["fehl"] >= 10:
            z["bis"], z["fehl"] = jetzt + 900, 0
            LOG.warning("Konto „%s“ nach 10 Fehlversuchen 15 Minuten gesperrt", text_einzeilig(name, 40))


def benutzer_anmelden(d, name, passwort, quelle):
    """prüft Benutzername + Passwort und gibt den Kontonamen zurück; leerer Name oder „admin“ = Manager-Passwort"""
    name = str(name or "").strip().lower()[:40]
    if name in ("", ADMIN_NAME):
        _konto_sperre(ADMIN_NAME, None)
        try:
            passwort_pruefen(passwort, quelle)
        except Fehler:
            _konto_sperre(ADMIN_NAME, False)
            raise
        _konto_sperre(ADMIN_NAME, True)
        return ADMIN_NAME
    _konto_sperre(name, None)
    _anmeldesperre(quelle, None)
    u = benutzer_liste(d).get(name)
    pw = passwort if isinstance(passwort, str) else ""
    if isinstance(u, dict) and u.get("hash"):
        ok = hmac.compare_digest(_bn_hash(pw, u["salz"], u.get("runden", _BN_RUNDEN)), u["hash"])
    else:
        _bn_hash(pw, "00" * 16)  # gleiche Rechenzeit, damit nicht erkennbar ist, ob es das Konto gibt
        ok = False
    if not ok:
        _konto_sperre(name, False)
    _anmeldesperre(quelle, ok)
    _konto_sperre(name, True)
    if konto_rechte(d, name)["art"] == "gesperrt":
        LOG.warning("Anmeldung mit gesperrtem Konto „%s“ abgelehnt", name)
        raise Fehler("Dieses Benutzerkonto ist gesperrt. Bitte an den Administrator wenden.")
    u["zuletzt"] = time.strftime("%Y-%m-%d %H:%M")
    speichere(d)
    return name


SICHERHEIT_STANDARD = {"2fa_admin": False, "abmelden_minuten": 30, "app_abmelden_minuten": 0, "2fa_merken_stunden": 0}


def sicherheit(d):
    """Sicherheits-Einstellungen mit Standardwerten (Browser nach 30 Min. ohne Aktivität abmelden, App aus, 2FA-Code nicht merken)"""
    roh = d.get("sicherheit") if isinstance(d.get("sicherheit"), dict) else {}
    s = dict(SICHERHEIT_STANDARD)
    for k, std in SICHERHEIT_STANDARD.items():
        if k in roh:
            try:
                s[k] = bool(roh[k]) if isinstance(std, bool) else int(roh[k])
            except (TypeError, ValueError):
                pass
    return s


def akt_benutzer(d, ich):
    u = benutzer_liste(d)
    sitz = sitzungen_je_benutzer()
    adm = konto_rechte(d, ADMIN_NAME)
    zeilen = [{"name": ADMIN_NAME, "anzeige": "Administrator (Manager-Passwort)", "email": d.get("admin_email", ""), "art": "admin", "bereiche": adm["bereiche"], "recht_text": "Administrator",
               "fest": True, "angelegt": "", "zuletzt": "", "von": "", "sitzungen": sitz.get(ADMIN_NAME, 0),
               "zwei_faktor": bool((d.get("admin_totp") or {}).get("aktiv"))}]
    for n in sorted(u):
        x, r = u[n], konto_rechte(d, n)
        zeilen.append({"name": n, "anzeige": x.get("anzeige", ""), "email": x.get("email", ""), "art": r["art"], "bereiche": r["bereiche"], "recht_text": rechte_text(r), "fest": False,
                       "sparten": x.get("sparten") or [], "zwei_faktor": bool((x.get("totp") or {}).get("aktiv")),
                       "angelegt": x.get("angelegt", ""), "zuletzt": x.get("zuletzt", ""), "von": x.get("von", ""), "sitzungen": sitz.get(n, 0)})
    return {"zeilen": zeilen, "arten": ARTEN, "stufen": STUFEN, "bereiche": [{"k": k, "text": t, "stufen": list(s)} for k, t, s, _ in BEREICHE],
            "vorlagen": {k: {"text": t, "bereiche": b} for k, (t, b) in VORLAGEN.items()}, "ich": ich,
            "zwei_faktor_pflicht": bool((d.get("sicherheit") or {}).get("2fa_admin")), "sicherheit": sicherheit(d),
            "log": [f"{len(zeilen)} Benutzerkonten (davon {sum(1 for z in zeilen if z['art'] == 'gesperrt')} gesperrt)."]}


def akt_benutzer_speichern(d, b, ich):
    """neues Konto anlegen oder Art (Administrator/Bereiche/Gesperrt), Bereichsrechte, Anzeigename, Passwort ändern"""
    u = benutzer_liste(d)
    neu = bool(b.get("neu"))
    name = _bn_name(b.get("name"))
    if name == ADMIN_NAME or name == HANDY_NAME.lower():
        raise Fehler("Das Konto „admin“ ist fest eingebaut – es meldet sich mit dem Manager-Passwort an.")
    if neu and name in u:
        raise Fehler(f"Das Konto „{name}“ gibt es schon.")
    if not neu and name not in u:
        raise Fehler(f"Das Konto „{name}“ gibt es nicht.")
    x = u.get(name) or {"angelegt": time.strftime("%Y-%m-%d %H:%M"), "von": ich}
    alt = konto_rechte(d, name) if name in u else None
    log = []
    vorlage = b.get("vorlage")
    if vorlage is not None and vorlage not in VORLAGEN:
        raise Fehler("Unbekannte Vorlage.")
    art = b.get("art") or (x.get("recht") if x.get("recht") in ARTEN else ("bereiche" if not neu or vorlage else None))
    if art is None:
        art = "bereiche"
        vorlage = vorlage or "lesen"
    if art not in ARTEN:
        raise Fehler("Unbekannte Kontoart.")
    # gespeicherte Bereichsrechte bleiben erhalten, auch während das Konto gesperrt oder Administrator ist
    if isinstance(x.get("bereiche"), dict):
        bereiche = _bereiche_pruefen(x["bereiche"])
    elif x.get("recht") in VORLAGEN:
        bereiche = dict(VORLAGEN[x["recht"]][1])
    else:
        bereiche = _alle("kein")
    if vorlage:
        bereiche = dict(VORLAGEN[vorlage][1])
    if isinstance(b.get("bereiche"), dict):
        bereiche = _bereiche_pruefen(b["bereiche"], bereiche)
    x["recht"], x["bereiche"] = art, bereiche
    neu_r = konto_rechte({"benutzer": {name: x}}, name)
    if not alt or alt != neu_r:
        log.append("Rechte: " + rechte_text(neu_r))
    if "anzeige" in b:
        x["anzeige"] = str(b.get("anzeige") or "").strip()[:60]
    if "email" in b:
        em = str(b.get("email") or "").strip().lower()[:200]
        if em and not re.fullmatch(r"[^@\s,;<>]{1,64}@[A-Za-z0-9.-]{1,190}\.[A-Za-z]{2,}", em):
            raise Fehler(f"E-Mail-Adresse „{em}“ ist ungültig.")
        x["email"] = em
    if "sparten" in b:
        roh = b["sparten"] if isinstance(b["sparten"], list) else re.split(r"[,;\s]+", str(b["sparten"] or ""))
        liste = sorted({str(k).strip().upper() for k in roh if str(k).strip()})
        bekannt = {z["kz"] for z in gwp_anlagen(d)} | {str(w.get("kz")) for w in ((d.get("gwplan") or {}).get("wahl") or {}).values() if w.get("kz")} \
            | {s_.get("kz", "").upper() for s_ in (d.get("plan") or {}).get("sparten", [])}
        unbekannt = [k for k in liste if k not in bekannt]
        if unbekannt:
            raise Fehler("Unbekannte Kürzel: " + ", ".join(unbekannt))
        if x.get("sparten", []) != liste:
            log.append("Sparten: " + (", ".join(liste) if liste else "alle"))
        x["sparten"] = liste
    if b.get("passwort") or neu:
        if b.get("passwort") != b.get("passwort2"):
            raise Fehler("Die beiden Passwörter stimmen nicht überein.")
        pw = _bn_passwort(b.get("passwort"))
        x["salz"] = secrets.token_hex(16)
        x["runden"] = _BN_RUNDEN
        x["hash"] = _bn_hash(pw, x["salz"])
        log.append("Passwort gesetzt")
    u[name] = x
    speichere(d)
    if art == "gesperrt" or b.get("passwort"):
        n = auth_sitzungen_beenden(name)
        if n:
            log.append(f"{n} Sitzung(en) abgemeldet")
    journal(f"Benutzerkonto {'angelegt' if neu else 'geändert'}: {name} ({rechte_text(neu_r)}) durch {ich}" + (" · " + ", ".join(log) if log else ""))
    r = akt_benutzer(d, ich)
    r["log"] = [f"✔ Konto „{name}“ {'angelegt' if neu else 'gespeichert'}" + (": " + ", ".join(log) if log else ".")]
    return r


def akt_benutzer_loeschen(d, b, ich):
    u = benutzer_liste(d)
    name = str(b.get("name") or "").strip().lower()
    if name not in u:
        raise Fehler("Konto nicht gefunden (das Konto „admin“ lässt sich nicht löschen).")
    del u[name]
    speichere(d)
    auth_sitzungen_beenden(name)
    journal(f"Benutzerkonto gelöscht: {name} durch {ich}")
    r = akt_benutzer(d, ich)
    r["log"] = [f"✔ Konto „{name}“ gelöscht und abgemeldet."]
    return r


def akt_benutzer_ich(d, ich, b):
    """eigenes Konto: Rechte anzeigen oder eigenes Passwort ändern"""
    rechte = konto_rechte(d, ich)
    if b is None or not b.get("passwort"):
        x = benutzer_liste(d).get(ich) or {}
        t = (d.get("admin_totp") if ich == ADMIN_NAME else x.get("totp")) or {}
        return {**ich_daten(ich, rechte), "anzeige": x.get("anzeige", ""), "eigenes_passwort": ich in benutzer_liste(d),
                "zwei_faktor": bool(t.get("aktiv")), "zwei_faktor_seit": t.get("seit", ""), "notfall_rest": len(t.get("notfall") or []),
                "zwei_faktor_pflicht": bool((d.get("sicherheit") or {}).get("2fa_admin")) and rechte["art"] == "admin",
                "liste": [{"text": t, "stufe": STUFEN[rechte["bereiche"].get(k, "kein")]} for k, t, _, _ in BEREICHE]}
    if ich not in benutzer_liste(d):
        raise Fehler("Das Passwort des Kontos „admin“ ist das Manager-Passwort – es wird in der Docker-Konfiguration geändert.")
    x = benutzer_liste(d)[ich]
    if not hmac.compare_digest(_bn_hash(str(b.get("alt") or ""), x["salz"], x.get("runden", _BN_RUNDEN)), x["hash"]):
        raise Fehler("Das bisherige Passwort stimmt nicht.")
    if b.get("passwort") != b.get("passwort2"):
        raise Fehler("Die beiden neuen Passwörter stimmen nicht überein.")
    pw = _bn_passwort(b.get("passwort"))
    x["salz"] = secrets.token_hex(16)
    x["runden"] = _BN_RUNDEN
    x["hash"] = _bn_hash(pw, x["salz"])
    speichere(d)
    journal(f"Benutzerkonto {ich}: eigenes Passwort geändert")
    return {"log": ["✔ Passwort geändert."], **ich_daten(ich, rechte)}


__all__ = [_n for _n in dict(globals()) if not _n.startswith("__")]  # alle Namen an die folgenden Module weitergeben
