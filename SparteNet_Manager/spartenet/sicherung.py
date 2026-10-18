"""SparteNet Manager – Datensicherung: alles in eine Datei (optional mit Passwort verschlüsselt), einspielen, täglich automatisch

Inhalt einer Sicherung (ZIP): meta.json, daten.json (alle Einstellungen, Planung, Buchungen, Benutzer mit Prüfsummen …),
journal.txt, register.txt und dateien/ (Passwörter je Parzelle, WLAN-/Tarif-Sicherungen, Kartenlogo, Unterlagen).
Verschlüsselt: AES-256-GCM, Schlüssel per PBKDF2-SHA256 (600 000 Runden) aus dem Passwort – Paket „cryptography“.
"""
from .logoerzeuger import *  # noqa: F401,F403 – alle Namen der vorherigen Module

SICHERUNG_KOPF = b"SPARTENET-SICHERUNG-1\n"
SICHERUNG_DIR = os.path.join(HIER, "datensicherungen")
SICHERUNG_PRAEFIXE = ("PPSK_", "SparteNet_Sicherung_", os.path.basename(LOGO_BASIS) + ".", "Unterlage_")
SICHERUNG_STANDARD = {"automatisch": True, "anzahl": 14, "uhrzeit": 3}
_SICHERUNG_PW_DATEI = os.environ.get("SPARTENET_SICHERUNG_PASSWORT_FILE", "").strip()
_SICHERUNG_LOCK = threading.Lock()


def _krypto():
    try:
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM
        from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
        from cryptography.hazmat.primitives import hashes
        return AESGCM, PBKDF2HMAC, hashes
    except ImportError:
        return None


def _schluessel(pw, salz):
    _, PBKDF2HMAC, hashes = _krypto()
    return PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salz, iterations=600_000).derive(pw.encode("utf-8"))


def verschluesseln(roh, pw):
    k = _krypto()
    if not k:
        raise Fehler("Verschlüsseln braucht das Paket „cryptography“ (im Docker-Image enthalten) – oder ohne Passwort sichern.")
    if len(pw) < 10:
        raise Fehler("Das Passwort für die Sicherung muss mindestens 10 Zeichen haben.")
    salz, nonce = secrets.token_bytes(16), secrets.token_bytes(12)
    return SICHERUNG_KOPF + salz + nonce + k[0](_schluessel(pw, salz)).encrypt(nonce, roh, SICHERUNG_KOPF)


def entschluesseln(roh, pw):
    if not roh.startswith(SICHERUNG_KOPF):
        return roh
    k = _krypto()
    if not k:
        raise Fehler("Diese Sicherung ist verschlüsselt – zum Einspielen wird das Paket „cryptography“ gebraucht.")
    if not pw:
        raise Fehler("Diese Sicherung ist verschlüsselt – bitte das Passwort eingeben.")
    n = len(SICHERUNG_KOPF)
    salz, nonce, inhalt = roh[n:n + 16], roh[n + 16:n + 28], roh[n + 28:]
    try:
        return k[0](_schluessel(pw, salz)).decrypt(nonce, inhalt, SICHERUNG_KOPF)
    except Exception:
        raise Fehler("Passwort falsch oder Sicherung beschädigt.")


def _journal_alle():
    if DB:
        return [f"{a:%Y-%m-%d %H:%M:%S} | {t}" for a, t in DB.sql("SELECT zeit, text FROM sn_journal ORDER BY id", alle=True)]
    try:
        with open(JOURNAL, encoding="utf-8", errors="replace") as f:
            return f.read().splitlines()
    except OSError:
        return []


def sicherung_bauen():
    d = lade()
    puffer = io.BytesIO()
    dateien = [n for p in SICHERUNG_PRAEFIXE for n in ablage_liste(p)]
    with zipfile.ZipFile(puffer, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("meta.json", json.dumps({"programm": "SparteNet Manager", "version": VERSION, "zeit": time.strftime("%Y-%m-%d %H:%M:%S"),
                                            "speicher": "mariadb" if DB else "dateien", "dateien": len(dateien)}, ensure_ascii=False))
        z.writestr("daten.json", json.dumps(dict(d), ensure_ascii=False))
        z.writestr("journal.txt", "\n".join(_journal_alle()))
        z.writestr("register.txt", "\n".join(sorted(_register_lesen())))
        for n in dateien:
            roh = ablage_lesen(n)
            if roh is not None:
                z.writestr("dateien/" + n, roh)
    return puffer.getvalue(), len(dateien)


def _sicherung_pruefen(roh):
    try:
        z = zipfile.ZipFile(io.BytesIO(roh))
        meta = json.loads(z.read("meta.json"))
        daten = json.loads(z.read("daten.json"))
    except (zipfile.BadZipFile, KeyError, ValueError):
        raise Fehler("Das ist keine SparteNet-Sicherung.")
    if meta.get("programm") != "SparteNet Manager" or not isinstance(daten, dict):
        raise Fehler("Das ist keine SparteNet-Sicherung.")
    if sum(i.file_size for i in z.infolist()) > 4_000_000_000:
        raise Fehler("Sicherung entpackt zu groß.")
    return z, meta, daten


def sicherung_server_schreiben(grund="automatisch"):
    """Sicherung im Datenordner unter datensicherungen/ (verschlüsselt, wenn SPARTENET_SICHERUNG_PASSWORT_FILE gesetzt)"""
    with _SICHERUNG_LOCK:
        roh, n = sicherung_bauen()
        pw = ""
        if _SICHERUNG_PW_DATEI:
            try:
                with open(_SICHERUNG_PW_DATEI, encoding="utf-8") as f:
                    pw = f.read().strip()
            except OSError:
                LOG.warning("SPARTENET_SICHERUNG_PASSWORT_FILE nicht lesbar – Sicherung unverschlüsselt")
        if pw and _krypto():
            roh = verschluesseln(roh, pw)
        os.makedirs(SICHERUNG_DIR, exist_ok=True)
        name = f"Datensicherung_{time.strftime('%Y%m%d_%H%M%S')}_{grund}.{'sns' if roh.startswith(SICHERUNG_KOPF) else 'zip'}"
        datei_atomar(os.path.join(SICHERUNG_DIR, name), roh)
        e = sicherung_einstellungen(lade())
        alle = sorted(x for x in os.listdir(SICHERUNG_DIR) if x.startswith("Datensicherung_") and "_automatisch." in x)
        for x in alle[:-e["anzahl"]]:
            try:
                os.remove(os.path.join(SICHERUNG_DIR, x))
            except OSError:
                pass
        LOG.info("Datensicherung geschrieben: %s (%d KB, %d Dateien)", name, len(roh) // 1024, n)
        return name


def sicherung_einstellungen(d):
    e = dict(SICHERUNG_STANDARD)
    roh = d.get("sicherung") if isinstance(d.get("sicherung"), dict) else {}
    e["automatisch"] = bool(roh.get("automatisch", True))
    try:
        e["anzahl"] = max(1, min(90, int(roh.get("anzahl", 14))))
        e["uhrzeit"] = max(0, min(23, int(roh.get("uhrzeit", 3))))
    except (TypeError, ValueError):
        pass
    return e


def _server_liste():
    if not os.path.isdir(SICHERUNG_DIR):
        return []
    aus = []
    for x in sorted(os.listdir(SICHERUNG_DIR), reverse=True):
        if re.fullmatch(r"Datensicherung_\d{8}_\d{6}_[a-z_]+\.(zip|sns)", x):
            p = os.path.join(SICHERUNG_DIR, x)
            aus.append({"name": x, "groesse": os.path.getsize(p), "zeit": time.strftime("%Y-%m-%d %H:%M", time.localtime(os.path.getmtime(p))),
                        "verschluesselt": x.endswith(".sns")})
    return aus


def akt_sicherung(d):
    return {"einstellungen": sicherung_einstellungen(d), "liste": _server_liste(), "krypto": bool(_krypto()), "ordner": SICHERUNG_DIR,
            "server_verschluesselt": bool(_SICHERUNG_PW_DATEI), "log": []}


def akt_sicherung_erstellen(d, b, wer):
    roh, n = sicherung_bauen()
    pw = str((b or {}).get("passwort") or "")
    if pw:
        roh = verschluesseln(roh, pw)
    name = f"SparteNet_Datensicherung_{time.strftime('%Y%m%d_%H%M')}.{'sns' if pw else 'zip'}"
    journal(f"Datensicherung heruntergeladen ({'verschlüsselt' if pw else 'unverschlüsselt'}, {n} Dateien) durch {wer}")
    return {"_datei": roh, "typ": "application/octet-stream", "name": name}


def akt_sicherung_datei(d, q):
    name = q.get("name", [""])[0]
    if not re.fullmatch(r"Datensicherung_\d{8}_\d{6}_[a-z_]+\.(zip|sns)", name or ""):
        raise Fehler("Ungültiger Name.")
    try:
        with open(os.path.join(SICHERUNG_DIR, name), "rb") as f:
            return {"_datei": f.read(), "typ": "application/octet-stream", "name": name}
    except OSError:
        raise Fehler("Sicherung nicht gefunden.")


def akt_sicherung_jetzt(d, wer):
    name = sicherung_server_schreiben("manuell")
    journal(f"Datensicherung auf dem Server erstellt: {name} durch {wer}")
    r = akt_sicherung(lade())
    r["log"] = [f"✔ {name} erstellt."]
    return r


def akt_sicherung_einstellungen(d, b):
    e = sicherung_einstellungen(d)
    if "automatisch" in b:
        e["automatisch"] = bool(b["automatisch"])
    for k, lo, hi in (("anzahl", 1, 90), ("uhrzeit", 0, 23)):
        if k in b:
            try:
                e[k] = max(lo, min(hi, int(b[k])))
            except (TypeError, ValueError):
                raise Fehler(f"{k}: bitte eine Zahl.")
    d["sicherung"] = e
    speichere(d)
    r = akt_sicherung(d)
    r["log"] = ["✔ Einstellungen gespeichert."]
    return r


def akt_sicherung_einspielen(d, roh, pw, wer):
    """ersetzt alle Daten durch die Sicherung – vorher wird der jetzige Stand gesichert"""
    roh = entschluesseln(roh, pw)
    z, meta, daten = _sicherung_pruefen(roh)
    vorher = sicherung_server_schreiben("vor_einspielen")
    # Einstellungen
    d.clear()          # d behält den geladenen Stand – speichere() schreibt Geändertes und entfernt Wegfallendes
    d.update(daten)
    speichere(d)
    # Dateien
    for p in SICHERUNG_PRAEFIXE:
        for n in ablage_liste(p):
            ablage_loeschen(n)
    n_dat = 0
    for info in z.infolist():
        if info.filename.startswith("dateien/") and not info.is_dir():
            name = info.filename[len("dateien/"):]
            if name.startswith(SICHERUNG_PRAEFIXE):
                ablage_schreiben(name, z.read(info))
                n_dat += 1
    # Änderungsprotokoll und Register
    zeilen = [x for x in z.read("journal.txt").decode("utf-8", "replace").splitlines() if " | " in x]
    if DB:
        DB.sql("DELETE FROM sn_journal")
        werte = []
        for x in zeilen:
            m = re.match(r"^(\d{4}-\d\d-\d\d \d\d:\d\d:\d\d) \| (.*)$", x)
            if m:
                werte.append((m.group(1), m.group(2)))
        if werte:
            DB.sql("INSERT INTO sn_journal (zeit, text) VALUES (%s, %s)", werte, viele=True)
    else:
        datei_atomar(JOURNAL, ("\n".join(zeilen) + "\n").encode("utf-8") if zeilen else b"")
    reg = [x.strip() for x in z.read("register.txt").decode("ascii", "ignore").splitlines() if re.fullmatch(r"[0-9a-f]{64}", x.strip())]
    if reg:
        if DB:
            DB.sql("INSERT IGNORE INTO sn_passwort_register (pruefsumme) VALUES (%s)", [(x,) for x in reg], viele=True)
        else:
            vorhanden = _register_lesen()
            fehlt = [x for x in reg if x not in vorhanden]
            if fehlt:
                with open(REGISTER, "a", encoding="utf-8") as f:
                    f.write("\n".join(fehlt) + "\n")
    journal(f"Datensicherung eingespielt: Stand vom {meta.get('zeit')} (Version {meta.get('version')}, {n_dat} Dateien) durch {wer} – vorheriger Stand: {vorher}")
    return {"log": [f"✔ Sicherung vom {meta.get('zeit')} eingespielt ({n_dat} Dateien).", f"Der vorherige Stand liegt auf dem Server: {vorher}",
                    "Bitte die Seite neu laden."], "neu_laden": True}


def sicherung_hintergrund():
    """täglich zur eingestellten Stunde eine Sicherung im Datenordner"""
    def schleife():
        time.sleep(120)
        letzte_tag = None
        while True:
            try:
                e = sicherung_einstellungen(lade())
                t = time.localtime()
                if e["automatisch"] and t.tm_hour == e["uhrzeit"] and letzte_tag != t.tm_yday:
                    sicherung_server_schreiben("automatisch")
                    letzte_tag = t.tm_yday
            except Exception as ex:
                LOG.warning("Automatische Datensicherung fehlgeschlagen: %s", ex)
            time.sleep(300)
    threading.Thread(target=schleife, daemon=True, name="sicherung").start()


__all__ = [_n for _n in dict(globals()) if not _n.startswith("__")]  # alle Namen an die folgenden Module weitergeben
