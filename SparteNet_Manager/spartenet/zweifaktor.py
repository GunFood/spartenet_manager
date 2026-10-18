"""SparteNet Manager – Zwei-Faktor-Anmeldung (TOTP nach RFC 6238, z. B. Google/Microsoft Authenticator, Aegis, 2FAS)

Je Konto: Geheimnis (Base32), aktiv ja/nein, zuletzt benutzter Zeitschritt (gegen Wiederverwendung) und 8 Notfall-Codes
(nur als Prüfsumme). Das Konto „admin“ speichert seine Angaben unter „admin_totp“. Optional Pflicht für Administratoren.
"""
from .sicherung import *  # noqa: F401,F403 – alle Namen der vorherigen Module

TOTP_SCHRITT = 30
TOTP_STELLEN = 6
ZWEIFAKTOR_FREI = {"/api/aktiv", "/api/benutzer-ich", "/api/2fa-start", "/api/2fa-bestaetigen", "/api/2fa-aus", "/api/einstellungen", "/api/ansicht", "/api/plan", "/api/pw-regel"}


def totp_code(geheim_b32, zaehler):
    schluessel = base64.b32decode(geheim_b32 + "=" * (-len(geheim_b32) % 8), casefold=True)
    h = hmac.new(schluessel, zaehler.to_bytes(8, "big"), hashlib.sha1).digest()
    o = h[-1] & 0x0F
    zahl = (int.from_bytes(h[o:o + 4], "big") & 0x7FFFFFFF) % (10 ** TOTP_STELLEN)
    return str(zahl).zfill(TOTP_STELLEN)


def _totp(d, name, anlegen=False):
    if name == ADMIN_NAME:
        t = d.get("admin_totp")
        if not isinstance(t, dict):
            t = {}
            if anlegen:
                d["admin_totp"] = t
        return t
    u = benutzer_liste(d).get(name)
    if not isinstance(u, dict):
        return {}
    if not isinstance(u.get("totp"), dict):
        if not anlegen:
            return {}
        u["totp"] = {}
    return u["totp"]


def zweifaktor_aktiv(d, name):
    return bool(_totp(d, name).get("aktiv"))


def _notfall_hash(code):
    return hashlib.sha256(("SparteNet-Notfall|" + re.sub(r"[^A-Z0-9]", "", code.upper())).encode()).hexdigest()


def zweifaktor_pruefen(d, name, code):
    """True, wenn der Code stimmt (App-Code ±30 s oder unbenutzter Notfall-Code); speichert die Nutzung"""
    t = _totp(d, name)
    if not t.get("aktiv"):
        return True
    code = str(code or "").strip().replace(" ", "")
    if re.fullmatch(r"\d{6}", code):
        jetzt = int(time.time() // TOTP_SCHRITT)
        for z in (jetzt, jetzt - 1, jetzt + 1):
            if z > int(t.get("zuletzt", 0)) and hmac.compare_digest(totp_code(t["geheim"], z), code):
                t["zuletzt"] = z
                speichere(d)
                return True
        return False
    h = _notfall_hash(code)
    if len(code) >= 8 and h in (t.get("notfall") or []):
        t["notfall"].remove(h)
        speichere(d)
        journal(f"Notfall-Code benutzt: {name} (noch {len(t['notfall'])} übrig)")
        return True
    return False


def zweifaktor_pflicht_offen(d, name, rechte):
    """Administrator ohne Zwei-Faktor, obwohl Pflicht eingeschaltet ist"""
    s = d.get("sicherheit") if isinstance(d.get("sicherheit"), dict) else {}
    return bool(s.get("2fa_admin")) and rechte.get("art") == "admin" and name != HANDY_NAME and not zweifaktor_aktiv(d, name)


def akt_2fa_start(d, ich):
    if ich == HANDY_NAME:
        raise Fehler("Für die Handy-PIN gibt es keine Zwei-Faktor-Anmeldung.")
    t = _totp(d, ich, anlegen=True)
    geheim = base64.b32encode(secrets.token_bytes(20)).decode().rstrip("=")
    t["neu"] = geheim
    speichere(d)
    uri = f"otpauth://totp/SparteNet:{urllib.parse.quote(ich)}?secret={geheim}&issuer=SparteNet%20Manager&digits={TOTP_STELLEN}&period={TOTP_SCHRITT}"
    return {"svg": qr_svg(uri), "geheim": " ".join(geheim[i:i + 4] for i in range(0, len(geheim), 4)), "uri": uri,
            "log": ["Code mit der Authenticator-App scannen und den angezeigten 6-stelligen Code eingeben."]}


def akt_2fa_bestaetigen(d, ich, code):
    t = _totp(d, ich, anlegen=True)
    if not t.get("neu"):
        raise Fehler("Bitte zuerst „Einrichten“ wählen.")
    jetzt = int(time.time() // TOTP_SCHRITT)
    code = str(code or "").strip().replace(" ", "")
    if not any(hmac.compare_digest(totp_code(t["neu"], z), code) for z in (jetzt - 1, jetzt, jetzt + 1)):
        raise Fehler("Der Code stimmt nicht – Uhrzeit am Handy prüfen und den aktuellen Code eingeben.")
    notfall = ["-".join(secrets.token_hex(2).upper() for _ in range(3)) for _ in range(8)]
    t.update(aktiv=True, geheim=t.pop("neu"), zuletzt=jetzt, notfall=[_notfall_hash(c) for c in notfall], seit=time.strftime("%Y-%m-%d %H:%M"))
    speichere(d)
    journal(f"Zwei-Faktor-Anmeldung eingeschaltet: {ich}")
    return {"notfall": notfall, "log": ["✔ Zwei-Faktor-Anmeldung ist eingeschaltet. Die Notfall-Codes jetzt notieren – sie werden nur einmal angezeigt."]}


def akt_2fa_aus(d, ich, code):
    if not zweifaktor_aktiv(d, ich):
        raise Fehler("Zwei-Faktor-Anmeldung ist nicht eingeschaltet.")
    s = d.get("sicherheit") if isinstance(d.get("sicherheit"), dict) else {}
    if s.get("2fa_admin") and konto_rechte(d, ich)["art"] == "admin":
        raise Fehler("Für Administratoren ist die Zwei-Faktor-Anmeldung Pflicht – ausschalten geht erst, wenn die Pflicht aufgehoben ist.")
    if not zweifaktor_pruefen(d, ich, code):
        raise Fehler("Der Code stimmt nicht.")
    t = _totp(d, ich)
    t.clear()
    speichere(d)
    journal(f"Zwei-Faktor-Anmeldung ausgeschaltet: {ich}")
    return {"log": ["✔ Zwei-Faktor-Anmeldung ausgeschaltet."]}


def akt_2fa_zuruecksetzen(d, name, ich):
    """Administrator setzt die Zwei-Faktor-Anmeldung eines Kontos zurück (z. B. Handy verloren)"""
    name = str(name or "").strip().lower()
    if name != ADMIN_NAME and name not in benutzer_liste(d):
        raise Fehler("Konto nicht gefunden.")
    t = _totp(d, name)
    t.clear()
    speichere(d)
    auth_sitzungen_beenden(name)
    journal(f"Zwei-Faktor-Anmeldung zurückgesetzt: {name} durch {ich}")
    r = akt_benutzer(d, ich)
    r["log"] = [f"✔ Zwei-Faktor-Anmeldung von „{name}“ zurückgesetzt – das Konto muss sie neu einrichten."]
    return r


# ---- Anmeldung: automatisch abmelden, Zwei-Faktor-Code merken -------------------------------------------------------
SICHERHEIT_GRENZEN = {"abmelden_minuten": (0, 24 * 60), "app_abmelden_minuten": (0, 7 * 24 * 60), "2fa_merken_stunden": (0, 90 * 24)}
MERKEN_COOKIE = "sn_2fa"


def dauer_text_kurz(stunden):
    if stunden % 24 == 0:
        t = stunden // 24
        return "1 Tag" if t == 1 else f"{t} Tage"
    return "1 Stunde" if stunden == 1 else f"{stunden} Stunden"


def _merken_fp(d, name):
    """Fingerabdruck des aktuellen 2FA-Geheimnisses – nach Zurücksetzen/Neu-Einrichten gelten gemerkte Geräte nicht mehr"""
    g = _totp(d, name).get("geheim") or ""
    return hashlib.sha256(("SparteNet-2FA-FP|" + g).encode()).hexdigest()[:24] if g else ""


def _merken_liste(d):
    m = d.get("zweifaktor_merken")
    if not isinstance(m, dict):
        m = {}
        d["zweifaktor_merken"] = m
    return m


def zweifaktor_gemerkt(d, name, token):
    """True, wenn dieses Gerät/dieser Browser den Code für das Konto noch nicht erneut eingeben muss"""
    stunden = sicherheit(d)["2fa_merken_stunden"]
    if not stunden or not token or not re.fullmatch(r"[A-Za-z0-9_-]{30,80}", str(token)):
        return False
    x = _merken_liste(d).get(hashlib.sha256(("SparteNet-2FA-Merken|" + token).encode()).hexdigest())
    if not x or x.get("konto") != name or time.time() > float(x.get("bis") or 0):
        return False
    fp = _merken_fp(d, name)
    # zusätzlich die aktuelle Höchstdauer beachten (falls sie inzwischen verkürzt wurde)
    return bool(fp) and hmac.compare_digest(x.get("fp", ""), fp) and time.time() < float(x.get("seit") or 0) + stunden * 3600


def zweifaktor_merken(d, name, geraet=""):
    """neues Merk-Token nach erfolgreicher Code-Eingabe; gibt (token, sekunden) oder (None, 0) zurück"""
    stunden = sicherheit(d)["2fa_merken_stunden"]
    fp = _merken_fp(d, name)
    if not stunden or not fp:
        return None, 0
    m = _merken_liste(d)
    jetzt = time.time()
    for k in [k for k, v in m.items() if not isinstance(v, dict) or float(v.get("bis") or 0) < jetzt]:
        del m[k]
    eigene = sorted((k for k, v in m.items() if v.get("konto") == name), key=lambda k: m[k].get("seit", 0))
    for k in eigene[:-19]:      # höchstens 20 gemerkte Geräte je Konto
        del m[k]
    t = secrets.token_urlsafe(32)
    m[hashlib.sha256(("SparteNet-2FA-Merken|" + t).encode()).hexdigest()] = {
        "konto": name, "fp": fp, "seit": jetzt, "bis": jetzt + stunden * 3600, "geraet": text_einzeilig(geraet or "", 80)}
    return t, stunden * 3600


def akt_2fa_vergessen(d, ich):
    m = _merken_liste(d)
    weg = [k for k, v in m.items() if v.get("konto") == ich]
    for k in weg:
        del m[k]
    speichere(d)
    journal(f"Gemerkte Geräte für die Zwei-Faktor-Anmeldung vergessen: {ich} ({len(weg)})")
    return {"log": [f"✔ {len(weg)} gemerkte(s) Gerät(e) vergessen – beim nächsten Anmelden wird der Code wieder abgefragt."]}


def akt_sicherheit_einstellungen(d, b, ich):
    s = sicherheit(d)
    if "2fa_admin" in b:
        s["2fa_admin"] = bool(b["2fa_admin"])
        if s["2fa_admin"] and not zweifaktor_aktiv(d, ich):
            raise Fehler("Bitte zuerst für Ihr eigenes Konto die Zwei-Faktor-Anmeldung einrichten (Mein Konto).")
    for k, (lo, hi) in SICHERHEIT_GRENZEN.items():
        if k in b:
            try:
                v = int(b[k] or 0)
            except (TypeError, ValueError):
                raise Fehler("Bitte ganze Zahlen angeben.")
            if not lo <= v <= hi:
                raise Fehler(f"Wert außerhalb des erlaubten Bereichs ({lo}–{hi}).")
            if k == "abmelden_minuten" and 0 < v < 5:
                raise Fehler("Automatisch abmelden: mindestens 5 Minuten (oder aus).")
            s[k] = v
    d["sicherheit"] = s
    speichere(d)
    journal(f"Sicherheit geändert durch {ich}: 2FA-Pflicht Admins {'an' if s['2fa_admin'] else 'aus'}, Browser abmelden nach "
            f"{s['abmelden_minuten'] or 'nie'} Min., App nach {s['app_abmelden_minuten'] or 'nie'} Min., 2FA merken "
            f"{dauer_text_kurz(s['2fa_merken_stunden']) if s['2fa_merken_stunden'] else 'nein'}")
    r = akt_benutzer(d, ich)
    r["log"] = ["✔ Gespeichert."]
    return r


__all__ = [_n for _n in dict(globals()) if not _n.startswith("__")]  # alle Namen an die folgenden Module weitergeben
