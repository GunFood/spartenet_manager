"""SparteNet Manager – Zwei-Faktor-Anmeldung (TOTP nach RFC 6238, z. B. Google/Microsoft Authenticator, Aegis, 2FAS)

Je Konto: Geheimnis (Base32), aktiv ja/nein, zuletzt benutzter Zeitschritt (gegen Wiederverwendung) und 8 Notfall-Codes
(nur als Prüfsumme). Das Konto „admin“ speichert seine Angaben unter „admin_totp“. Optional Pflicht für Administratoren.
"""
from .sicherung import *  # noqa: F401,F403 – alle Namen der vorherigen Module

TOTP_SCHRITT = 30
TOTP_STELLEN = 6
ZWEIFAKTOR_FREI = {"/api/benutzer-ich", "/api/2fa-start", "/api/2fa-bestaetigen", "/api/2fa-aus", "/api/einstellungen", "/api/ansicht", "/api/plan", "/api/pw-regel"}


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


def akt_sicherheit_einstellungen(d, b, ich):
    s = d.get("sicherheit") if isinstance(d.get("sicherheit"), dict) else {}
    if "2fa_admin" in b:
        s["2fa_admin"] = bool(b["2fa_admin"])
        if s["2fa_admin"] and not zweifaktor_aktiv(d, ich):
            raise Fehler("Bitte zuerst für Ihr eigenes Konto die Zwei-Faktor-Anmeldung einrichten (Mein Konto).")
    d["sicherheit"] = s
    speichere(d)
    journal(f"Sicherheit: Zwei-Faktor-Pflicht für Administratoren {'an' if s.get('2fa_admin') else 'aus'} durch {ich}")
    r = akt_benutzer(d, ich)
    r["log"] = ["✔ Gespeichert."]
    return r


__all__ = [_n for _n in dict(globals()) if not _n.startswith("__")]  # alle Namen an die folgenden Module weitergeben
