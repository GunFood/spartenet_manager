"""SparteNet Manager – Benutzerkonten und Zugriffsrechte (Administrator, Lesen und schreiben, Nur lesen, Gesperrt)"""
from .netzplanung import *  # noqa: F401,F403 – alle Namen der vorherigen Module

# Das Konto „admin“ meldet sich mit dem Manager-Passwort an (SPARTENET_PASSWORD bzw. SPARTENET_PASSWORD_FILE)
# und kann weitere Konten anlegen. Weitere Konten liegen im Datenspeicher (Datei oder MariaDB) unter „benutzer“,
# Passwörter nur als PBKDF2-Prüfsumme.
ADMIN_NAME = "admin"
RECHTE = {"admin": "Administrator", "schreiben": "Lesen und schreiben", "lesen": "Nur lesen", "gesperrt": "Gesperrt"}
RANG = {"gesperrt": 0, "lesen": 1, "schreiben": 2, "admin": 3}
HANDY_NAME = "Handy (PIN)"
_BN_RUNDEN = 300_000
_BN_NAME_RE = re.compile(r"^[a-z0-9][a-z0-9._-]{2,31}$")

# Welches Recht eine Anfrage braucht. Alles, was hier nicht als „lesen“ oder „admin“ steht, braucht „schreiben“.
LESEN_IMMER = {
    "/api/test", "/api/lesen", "/api/abgleich", "/api/vergleich", "/api/journal", "/api/system", "/api/daten-liste",
    "/api/daten-pruefen", "/api/tarif-vergleich", "/api/tarif-erkennen", "/api/kalkulation", "/api/gwplan", "/api/start",
    "/api/parzelle", "/api/karten-vorschau", "/api/karten", "/api/ansicht", "/api/benutzer-ich",
}
LESEN_OHNE_INHALT = {"/api/einstellungen", "/api/plan", "/api/design", "/api/tarife", "/api/buchungen", "/api/pw-regel"}  # GET = lesen
LESEN_VORSCHAU = {"/api/netze", "/api/uebertragen", "/api/tarif-uebertragen", "/api/ppsk-hochladen", "/api/voucher"}  # ohne „ausführen“ = lesen
NUR_ADMIN = {"/api/benutzer", "/api/benutzer-speichern", "/api/benutzer-loeschen", "/api/beenden", "/api/log-loeschen", "/api/tailscale"}


def recht_fuer(pfad, q, b):
    """nötiges Recht für eine Anfrage: lesen, schreiben oder admin"""
    if pfad in NUR_ADMIN or (pfad in ("/api/fern", "/api/einstellungen") and b is not None):
        return "admin"
    if pfad == "/api/daten":
        return "admin" if q.get("geheim", ["0"])[0] == "1" else "lesen"
    if pfad in LESEN_IMMER:
        return "lesen"
    if pfad in LESEN_OHNE_INHALT and b is None:
        return "lesen"
    if pfad in LESEN_VORSCHAU and isinstance(b, dict) and not b.get("ausfuehren"):
        return "lesen"
    if pfad == "/api/ppsk" and isinstance(b, dict) and b.get("art", "anzeigen") == "anzeigen":
        return "lesen"
    return "schreiben"


def benutzer_liste(d):
    u = d.get("benutzer")
    if not isinstance(u, dict):
        u = {}
        d["benutzer"] = u
    return u


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


def recht_von(d, name):
    """aktuelles Recht eines Kontos (live aus dem Datenspeicher, damit Sperren sofort wirkt) oder None"""
    if name == ADMIN_NAME:
        return "admin"
    if name == HANDY_NAME:
        return "schreiben"
    u = benutzer_liste(d).get(name)
    return u.get("recht") if isinstance(u, dict) and u.get("recht") in RECHTE else None


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
    if u.get("recht") == "gesperrt":
        LOG.warning("Anmeldung mit gesperrtem Konto „%s“ abgelehnt", name)
        raise Fehler("Dieses Benutzerkonto ist gesperrt. Bitte an den Administrator wenden.")
    u["zuletzt"] = time.strftime("%Y-%m-%d %H:%M")
    speichere(d)
    return name


def akt_benutzer(d, ich):
    u = benutzer_liste(d)
    sitz = sitzungen_je_benutzer()
    zeilen = [{"name": ADMIN_NAME, "anzeige": "Administrator (Manager-Passwort)", "recht": "admin", "fest": True,
               "angelegt": "", "zuletzt": "", "von": "", "sitzungen": sitz.get(ADMIN_NAME, 0)}]
    for n in sorted(u):
        x = u[n]
        zeilen.append({"name": n, "anzeige": x.get("anzeige", ""), "recht": x.get("recht", "lesen"), "fest": False, "angelegt": x.get("angelegt", ""),
                       "zuletzt": x.get("zuletzt", ""), "von": x.get("von", ""), "sitzungen": sitz.get(n, 0)})
    return {"zeilen": zeilen, "rechte": RECHTE, "ich": ich, "log": [f"{len(zeilen)} Benutzerkonten (davon {sum(1 for z in zeilen if z['recht'] == 'gesperrt')} gesperrt)."]}


def akt_benutzer_speichern(d, b, ich):
    """neues Konto anlegen oder Recht, Anzeigename, Passwort eines Kontos ändern"""
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
    log = []
    if "recht" in b or neu:
        recht = b.get("recht", "lesen")
        if recht not in RECHTE:
            raise Fehler("Unbekanntes Recht.")
        if x.get("recht") != recht:
            log.append(f"Recht: {RECHTE[recht]}")
        x["recht"] = recht
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
    if x["recht"] == "gesperrt" or b.get("passwort"):
        n = auth_sitzungen_beenden(name)
        if n:
            log.append(f"{n} Sitzung(en) abgemeldet")
    journal(f"Benutzerkonto {'angelegt' if neu else 'geändert'}: {name} ({RECHTE[x['recht']]}) durch {ich}" + (" · " + ", ".join(log) if log else ""))
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
    """eigenes Konto: anzeigen oder eigenes Passwort ändern"""
    recht = recht_von(d, ich)
    if b is None or not b.get("passwort"):
        x = benutzer_liste(d).get(ich) or {}
        return {"name": ich, "anzeige": x.get("anzeige", ""), "recht": recht, "recht_text": RECHTE.get(recht, ""), "eigenes_passwort": ich in benutzer_liste(d)}
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
    return {"log": ["✔ Passwort geändert."], "name": ich, "recht": recht, "recht_text": RECHTE.get(recht, "")}

__all__ = [_n for _n in dict(globals()) if not _n.startswith("__")]  # alle Namen an die folgenden Module weitergeben
