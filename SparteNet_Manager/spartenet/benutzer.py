"""SparteNet Manager – Benutzerkonten und Zugriffsrechte je Bereich (Arbeitsblatt/Funktion: kein Zugriff, lesen, schreiben)"""
from .netzplanung import *  # noqa: F401,F403 – alle Namen der vorherigen Module

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
    ("verbindung", "Verbindung, Cloud-Key, Handy & Tablet, Protokoll, Diagnose", ("kein", "lesen", "schreiben"), ["verbindung"]),
]
BEREICH_TEXT = {k: t for k, t, _, _ in BEREICHE}
BEREICH_STUFEN = {k: s for k, _, s, _ in BEREICHE}


def _alle(stufe, **ausnahmen):
    return {k: (ausnahmen.get(k) or (stufe if stufe in s else s[-1])) for k, _, s, _ in BEREICHE}


VORLAGEN = {
    "lesen": ("Nur lesen", _alle("lesen", verbindung="kein")),
    "schreiben": ("Lesen und schreiben", _alle("schreiben", verbindung="lesen")),
    "vorstand": ("Vorstand Sparte: lesen + WLAN-Passwörter, Tarif buchen, Karten, Voucher",
                 _alle("lesen", verbindung="kein", wlan_pw="schreiben", buchungen="schreiben", karten="lesen", voucher="schreiben")),
    "kasse": ("Kasse: Tarif buchen und Kalkulation, sonst lesen", _alle("lesen", verbindung="kein", buchungen="schreiben", kalkulation="schreiben")),
}

# Was eine Anfrage braucht: ("immer",) · ("admin",) · (Bereich, Stufe)
_IMMER = {"/api/einstellungen", "/api/ansicht", "/api/benutzer-ich", "/api/plan", "/api/pw-regel"}  # nur lesend (GET) bzw. eigene Ansicht
_NUR_ADMIN = {"/api/benutzer", "/api/benutzer-speichern", "/api/benutzer-loeschen", "/api/beenden"}
_LESEN = {
    "/api/start": "start", "/api/parzelle": "start",
    "/api/test": "auslesen", "/api/lesen": "auslesen", "/api/abgleich": "auslesen", "/api/vergleich": "auslesen", "/api/journal": "auslesen",
    "/api/system": "auslesen", "/api/daten-liste": "auslesen", "/api/daten-pruefen": "auslesen",
    "/api/tarif-vergleich": "tarife", "/api/tarif-erkennen": "buchungen", "/api/kalkulation": "kalkulation", "/api/gwplan": "netzplanung",
    "/api/karten-vorschau": "karten", "/api/karten": "karten", "/api/log": "verbindung",
}
_GET_LESEN_SONST_SCHREIBEN = {"/api/tarife": "tarife", "/api/buchungen": "buchungen", "/api/design": "karten", "/api/fern": "verbindung"}
_VORSCHAU = {"/api/netze": "netze", "/api/uebertragen": "wlan_pw", "/api/ppsk-hochladen": "wlan_pw", "/api/tarif-uebertragen": "tarife", "/api/voucher": "voucher"}
_SCHREIBEN = {
    "/api/excel": "planung", "/api/schreibtest": "netze",
    "/api/ppsk-speichern": "wlan_pw", "/api/rueckgaengig": "wlan_pw", "/api/passwort": "wlan_pw",
    "/api/tarif-rueckgaengig": "tarife", "/api/tarif-zuordnung": "buchungen",
    "/api/kalk-annahmen": "kalkulation", "/api/kalk-sparte": "kalkulation", "/api/kalk-import": "kalkulation",
    "/api/gwplan-sparte": "netzplanung", "/api/gwplan-annahmen": "netzplanung", "/api/gwplan-zuruecksetzen": "netzplanung", "/api/gwplan-import": "netzplanung",
    "/api/logo": "karten", "/api/logo-loeschen": "karten",
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
    if r in VORLAGEN:  # Konten aus 4.4: „lesen“ / „schreiben“
        return {"art": "bereiche", "bereiche": dict(VORLAGEN[r][1])}
    if r in ("admin", "gesperrt"):
        return {"art": r, "bereiche": _alle("schreiben" if r == "admin" else "kein")}
    return {"art": "bereiche", "bereiche": _bereiche_pruefen(u.get("bereiche"))}


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
            "bereiche": rechte["bereiche"], "reiter": reiter}


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


def benutzer_anmelden(d, name, passwort, quelle):
    """prüft Benutzername + Passwort und gibt den Kontonamen zurück; leerer Name oder „admin“ = Manager-Passwort"""
    name = str(name or "").strip().lower()
    if name in ("", ADMIN_NAME):
        passwort_pruefen(passwort, quelle)
        return ADMIN_NAME
    _anmeldesperre(quelle, None)
    u = benutzer_liste(d).get(name)
    pw = passwort if isinstance(passwort, str) else ""
    if isinstance(u, dict) and u.get("hash"):
        ok = hmac.compare_digest(_bn_hash(pw, u["salz"], u.get("runden", _BN_RUNDEN)), u["hash"])
    else:
        _bn_hash(pw, "00" * 16)  # gleiche Rechenzeit, damit nicht erkennbar ist, ob es das Konto gibt
        ok = False
    _anmeldesperre(quelle, ok)
    if konto_rechte(d, name)["art"] == "gesperrt":
        LOG.warning("Anmeldung mit gesperrtem Konto „%s“ abgelehnt", name)
        raise Fehler("Dieses Benutzerkonto ist gesperrt. Bitte an den Administrator wenden.")
    u["zuletzt"] = time.strftime("%Y-%m-%d %H:%M")
    speichere(d)
    return name


def akt_benutzer(d, ich):
    u = benutzer_liste(d)
    sitz = sitzungen_je_benutzer()
    adm = konto_rechte(d, ADMIN_NAME)
    zeilen = [{"name": ADMIN_NAME, "anzeige": "Administrator (Manager-Passwort)", "art": "admin", "bereiche": adm["bereiche"], "recht_text": "Administrator",
               "fest": True, "angelegt": "", "zuletzt": "", "von": "", "sitzungen": sitz.get(ADMIN_NAME, 0)}]
    for n in sorted(u):
        x, r = u[n], konto_rechte(d, n)
        zeilen.append({"name": n, "anzeige": x.get("anzeige", ""), "art": r["art"], "bereiche": r["bereiche"], "recht_text": rechte_text(r), "fest": False,
                       "angelegt": x.get("angelegt", ""), "zuletzt": x.get("zuletzt", ""), "von": x.get("von", ""), "sitzungen": sitz.get(n, 0)})
    return {"zeilen": zeilen, "arten": ARTEN, "stufen": STUFEN, "bereiche": [{"k": k, "text": t, "stufen": list(s)} for k, t, s, _ in BEREICHE],
            "vorlagen": {k: {"text": t, "bereiche": b} for k, (t, b) in VORLAGEN.items()}, "ich": ich,
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
        return {**ich_daten(ich, rechte), "anzeige": x.get("anzeige", ""), "eigenes_passwort": ich in benutzer_liste(d),
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
