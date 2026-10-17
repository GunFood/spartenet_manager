"""SparteNet Manager – Anmeldung: Manager-Passwort, Handy-PIN, Sitzungen, Sperre bei Fehlversuchen"""
from .tarife import *  # noqa: F401,F403 – alle Namen der vorherigen Module


# =============================================================== Handy & Tablet (Web-App, Passwort und optionale PIN)
SITZUNG_TAGE = 30
_SPERRE = {"fehl": 0, "bis": 0.0}
_SPERRE_LOCK = threading.Lock()
_AUTH_SESSIONS = {}
_AUTH_SESSIONS_LOCK = threading.Lock()
_AUTH_LOCKS = {}
_AUTH_SPERRE_LOCK = threading.Lock()
LAUFZEIT = {"host": "127.0.0.1"}  # Adresse, an die der Webserver gebunden ist (setzt main)


def fern_daten(d):
    f = d.get("fern") if isinstance(d.get("fern"), dict) else {}
    f.setdefault("lan", False); f.setdefault("pin", {}); f.setdefault("sitzungen", {})
    d["fern"] = f
    return f


def _pin_hash(pin, salz):
    return hashlib.pbkdf2_hmac("sha256", pin.encode("utf-8"), bytes.fromhex(salz), 200_000).hex()


def pin_setzen(d, pin):
    pin = str(pin or "")
    if not 6 <= len(pin) <= 32:
        raise Fehler("Die PIN muss 6 bis 32 Zeichen lang sein (Ziffern oder Buchstaben).")
    if len(set(pin)) < 3 or pin in "0123456789012345678909876543210":
        raise Fehler("Die PIN ist zu einfach (z. B. 111111 oder 123456) – bitte eine andere wählen.")
    f = fern_daten(d)
    salz = secrets.token_hex(16)
    f["pin"] = {"salz": salz, "hash": _pin_hash(pin, salz)}
    f["sitzungen"] = {}  # neue PIN → alle Geräte neu anmelden


def pin_pruefen(d, pin):
    with _SPERRE_LOCK:
        jetzt = time.time()
        if _SPERRE["bis"] > jetzt:
            raise Fehler(f"Zu viele Fehlversuche – bitte {int(_SPERRE['bis'] - jetzt) // 60 + 1} Minute(n) warten.")
        p = fern_daten(d)["pin"]
        if not p.get("hash"):
            raise Fehler("Am PC ist noch keine PIN festgelegt (Verbindung → Handy & Tablet).")
        ok = hmac.compare_digest(_pin_hash(str(pin or ""), p["salz"]), p["hash"])
        if ok:
            _SPERRE["fehl"] = 0
            return True
        _SPERRE["fehl"] += 1
        LOG.warning("Falsche PIN bei der Anmeldung vom Handy (%d. Fehlversuch)", _SPERRE["fehl"])
        if _SPERRE["fehl"] >= 5:
            _SPERRE["bis"], _SPERRE["fehl"] = jetzt + 300, 0
            raise Fehler("Falsche PIN. Zu viele Fehlversuche – Anmeldung 5 Minuten gesperrt.")
        raise Fehler(f"Falsche PIN ({5 - _SPERRE['fehl']} Versuch(e) bis zur Sperre).")


def _sitzung_hash(t):
    return hashlib.sha256(("SparteNet-Sitzung|" + t).encode()).hexdigest()


def sitzung_neu(d, geraet):
    f = fern_daten(d)
    jetzt = time.time()
    f["sitzungen"] = {k: v for k, v in f["sitzungen"].items() if isinstance(v, dict) and v.get("bis", 0) > jetzt}
    while len(f["sitzungen"]) >= 20:
        f["sitzungen"].pop(min(f["sitzungen"], key=lambda k: f["sitzungen"][k]["bis"]))
    t = secrets.token_urlsafe(32)
    f["sitzungen"][_sitzung_hash(t)] = {"bis": jetzt + SITZUNG_TAGE * 86400, "geraet": str(geraet or "")[:80], "seit": time.strftime("%Y-%m-%d %H:%M")}
    speichere(d)
    return t


def sitzung_ok(d, t):
    if not t:
        return False
    s = fern_daten(d)["sitzungen"].get(_sitzung_hash(t))
    return bool(s) and s.get("bis", 0) > time.time()


def passwort_pruefen(passwort, quelle):
    with _AUTH_SPERRE_LOCK:
        jetzt = time.time()
        for ip, zustand in list(_AUTH_LOCKS.items()):
            if zustand["zuletzt"] < jetzt - 3600:
                del _AUTH_LOCKS[ip]
        quelle = str(quelle or "unbekannt")[:64]
        if quelle not in _AUTH_LOCKS and len(_AUTH_LOCKS) >= 4096:
            del _AUTH_LOCKS[min(_AUTH_LOCKS, key=lambda ip: _AUTH_LOCKS[ip]["zuletzt"])]
        sperre = _AUTH_LOCKS.setdefault(quelle, {"fehl": 0, "bis": 0.0, "zuletzt": jetzt})
        sperre["zuletzt"] = jetzt
        if sperre["bis"] > jetzt:
            raise Fehler(f"Zu viele Fehlversuche – bitte {int(sperre['bis'] - jetzt) // 60 + 1} Minute(n) warten.")
        ok = bool(AUTH_PASSWORD) and isinstance(passwort, str) and hmac.compare_digest(passwort, AUTH_PASSWORD)
        if ok:
            sperre["fehl"] = 0
            return True
        sperre["fehl"] += 1
        LOG.warning("Falsches Manager-Passwort bei der Anmeldung (%d. Fehlversuch)", sperre["fehl"])
        if sperre["fehl"] >= 5:
            sperre["bis"], sperre["fehl"] = jetzt + 300, 0
            raise Fehler("Falsches Passwort. Zu viele Fehlversuche – Anmeldung 5 Minuten gesperrt.")
        raise Fehler(f"Passwort falsch ({5 - sperre['fehl']} Versuch(e) bis zur Sperre).")


SITZUNG_KURZ_STUNDEN = 12      # ohne „Angemeldet bleiben“


def auth_sitzung_neu(geraet, benutzer="admin", bleiben=True):
    jetzt = time.time()
    with _AUTH_SESSIONS_LOCK:
        for k, sitzung in list(_AUTH_SESSIONS.items()):
            if sitzung["bis"] <= jetzt:
                del _AUTH_SESSIONS[k]
        while len(_AUTH_SESSIONS) >= 200:
            del _AUTH_SESSIONS[min(_AUTH_SESSIONS, key=lambda k: _AUTH_SESSIONS[k]["bis"])]
        t = secrets.token_urlsafe(32)
        _AUTH_SESSIONS[_sitzung_hash(t)] = {
            "bis": jetzt + (SITZUNG_TAGE * 86400 if bleiben else SITZUNG_KURZ_STUNDEN * 3600),
            "zuletzt": jetzt,
            "geraet": str(geraet or "Browser")[:80],
            "seit": time.strftime("%Y-%m-%d %H:%M"),
            "benutzer": str(benutzer or "admin"),
        }
    return t


def auth_sitzung_ok(t):
    if not t:
        return False
    h = _sitzung_hash(t)
    with _AUTH_SESSIONS_LOCK:
        sitzung = _AUTH_SESSIONS.get(h)
        if not sitzung or sitzung["bis"] <= time.time():
            _AUTH_SESSIONS.pop(h, None)
            return False
        return True


def auth_sitzung_info(t, leerlauf=0, aktiv=False):
    """Sitzung zum Cookie (mit Benutzername) oder None.
    leerlauf: Sekunden ohne Aktivität, nach denen die Sitzung endet (0 = nie); aktiv: Aktivität jetzt vermerken"""
    if not t:
        return None
    h = _sitzung_hash(t)
    jetzt = time.time()
    with _AUTH_SESSIONS_LOCK:
        sitzung = _AUTH_SESSIONS.get(h)
        # 90 s Spielraum: die Oberfläche meldet Aktivität höchstens jede Minute und zeigt vorher einen Countdown
        if not sitzung or sitzung["bis"] <= jetzt or (leerlauf and jetzt - float(sitzung.get("zuletzt") or jetzt) > leerlauf + 90):
            _AUTH_SESSIONS.pop(h, None)
            return None
        if aktiv:
            sitzung["zuletzt"] = jetzt
        return dict(sitzung)


def auth_sitzungen_beenden(benutzer):
    """alle Sitzungen eines Kontos abmelden (z. B. nach Sperren, Löschen oder neuem Passwort); gibt die Anzahl zurück"""
    with _AUTH_SESSIONS_LOCK:
        weg = [k for k, v in _AUTH_SESSIONS.items() if v.get("benutzer", "admin") == benutzer]
        for k in weg:
            del _AUTH_SESSIONS[k]
    return len(weg)


def sitzungen_je_benutzer():
    jetzt = time.time()
    zahl = {}
    with _AUTH_SESSIONS_LOCK:
        for v in _AUTH_SESSIONS.values():
            if v["bis"] > jetzt:
                zahl[v.get("benutzer", "admin")] = zahl.get(v.get("benutzer", "admin"), 0) + 1
    return zahl


def auth_sitzung_entfernen(t):
    if t:
        with _AUTH_SESSIONS_LOCK:
            _AUTH_SESSIONS.pop(_sitzung_hash(t), None)

__all__ = [_n for _n in dict(globals()) if not _n.startswith("__")]  # alle Namen an die folgenden Module weitergeben
