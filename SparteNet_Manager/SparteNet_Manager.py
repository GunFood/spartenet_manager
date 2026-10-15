#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SparteNet Manager 3.3 (Cloud) – Bedienoberfläche für UniFi Cloud Gateways in Kleingartensparten

Funktioniert vollständig über die UniFi-Cloud (api.ui.com) – kein lokaler Zugriff, kein VPN.
Benötigt nur Python 3 (keine Zusatzpakete).

Start:  ./SparteNet_starten.sh  ·  oder  python3 SparteNet_Manager.py
Der Browser öffnet sich unter http://127.0.0.1:8765

API-Key: unifi.ui.com → Einstellungen → API Keys (Site-Manager-Key, vom Besitzer der Konsole erstellt)

Schema:
  Parzelle p auf Steckplatz n:  VLAN 1000 + n·100 + p  (Steckplatz 10: 3000 + p)   Netz 10.<Sparten-ID>.p.0/24
  Vorstand 2000 + n·10 + 1 (10.S.200.0/24) · Gäste +2 (10.S.201.0/24) · Technik +9 (10.S.250.0/24)
  Namen: BW-Paz.001, BW-Vorstand, BW-Gäste, BW-Technik · WLANs: <Präfix>-BW-Pächter, -Gäste, -Vorstand
"""
import base64, concurrent.futures, copy, csv, hashlib, hmac, io, ipaddress, json, shutil, socket, subprocess, os, re, secrets, ssl, sys, threading, time, urllib.error, urllib.parse, urllib.request, webbrowser, zipfile
import xml.etree.ElementTree as ET
import logging, logging.handlers, traceback
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from http.cookies import SimpleCookie, CookieError

VERSION = "4.3"
HIER = os.path.abspath(os.environ.get("SPARTENET_DATA_DIR") or os.path.dirname(os.path.abspath(sys.argv[0])))
os.makedirs(HIER, exist_ok=True)
DATEI = os.path.join(HIER, "SparteNet_Manager.json")
PORT = int(os.environ.get("SPARTENET_PORT", "8765"))
HOST_OVERRIDE = os.environ.get("SPARTENET_HOST") or None
CLOUD = os.environ.get("SPARTENET_CLOUD_URL", "https://api.ui.com")
AUTH_PASSWORD_FILE = os.environ.get("SPARTENET_PASSWORD_FILE", "")
if AUTH_PASSWORD_FILE:
    try:
        with open(AUTH_PASSWORD_FILE, encoding="utf-8") as f:
            AUTH_PASSWORD = f.read().rstrip("\r\n")
    except OSError as e:
        raise SystemExit(f"SPARTENET_PASSWORD_FILE kann nicht gelesen werden: {e}")
else:
    AUTH_PASSWORD = os.environ.get("SPARTENET_PASSWORD", "")
TOKEN = secrets.token_urlsafe(24)
LOGDATEI = os.path.join(HIER, "SparteNet_Manager.log")
LOG = logging.getLogger("spartenet")
LOG.setLevel(logging.DEBUG)
LOG.propagate = False


def log_einrichten(aktiv):
    for h in list(LOG.handlers):
        LOG.removeHandler(h); h.close()
    if aktiv:
        h = logging.handlers.RotatingFileHandler(LOGDATEI, maxBytes=2_000_000, backupCount=3, encoding="utf-8")
        h.setFormatter(logging.Formatter("%(asctime)s %(levelname)-7s %(message)s"))
        LOG.addHandler(h)
        LOG.info("==== Protokoll eingeschaltet – SparteNet Manager %s, Python %s, %s", VERSION, sys.version.split()[0], sys.platform)
    else:
        LOG.addHandler(logging.NullHandler())


def _maskiere(obj):
    if isinstance(obj, dict):
        return {k: ("***" if k.lower() in ("password", "x_passphrase", "passphrase", "x_password", "cloud_key", "api_key") else _maskiere(v)) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_maskiere(x) for x in obj]
    return obj

# ---- Namensschema -------------------------------------------------------------------------
NETZ_PARZELLE = "{kz}-Paz.{p:03d}"
NETZ_VORSTAND = "{kz}-Vorstand"
NETZ_GAESTE = "{kz}-Gäste"
NETZ_TECHNIK = "{kz}-Technik"
WLAN_PAECHTER = "{pre}-{kz}-Pächter"
WLAN_GAESTE = "{pre}-{kz}-Gäste"
WLAN_VORSTAND = "{pre}-{kz}-Vorstand"

STANDARD_PLAN = {"gateway": 1, "gatewayname": "KGS Buchenweg e.V.", "praefix": "SparteNet.de",
                 "sparten": [{"name": "KGS Buchenweg e.V.", "kz": "BW", "sid": 1, "n": 85}]}


# ---- Zugangskarten-Design ------------------------------------------------------------------
LOGO_BASIS = os.path.join(HIER, "SparteNet_Kartenlogo")
LOGO_TYPEN = {"png": "image/png", "jpg": "image/jpeg", "gif": "image/gif", "webp": "image/webp", "svg": "image/svg+xml"}
PAPIER = {"A4": (210, 297), "A5": (148, 210), "A6": (105, 148)}
SCHRIFTEN = {"Arial": "Arial,Helvetica,sans-serif", "Verdana": "Verdana,Geneva,sans-serif",
             "Trebuchet": "'Trebuchet MS',Tahoma,sans-serif", "Georgia": "Georgia,'Times New Roman',serif",
             "Times": "'Times New Roman',Times,serif", "Courier": "'Courier New',Courier,monospace"}
DESIGN_STANDARD = {
    "format": "A5", "quer": False, "rand_mm": 12, "schrift": "Arial", "ausrichtung": "center",
    "farbe_akzent": "#3a9a1f", "farbe_text": "#1d2f3e", "farbe_hell": "#5d6b75", "farbe_seite": "#ffffff",
    "farbe_pw_hinter": "#f0f4ee", "farbe_qr": "#000000", "farbe_qr_hinter": "#ffffff",
    "gr_kopf": 13, "gr_titel": 28, "gr_text": 12, "gr_pw": 17, "gr_klein": 9,
    "qr_cm": 9.0,
    "t_kopf": "SparteNet.de · {sparte}", "t_titel": "Parzelle {parzelle}", "t_unter": "Ihr persönlicher WLAN-Zugang",
    "t_scan": "Handy-Kamera auf den Code richten – verbindet automatisch",
    "t_fuss": "Bitte vertraulich behandeln und nicht weitergeben. Bei Fragen: SparteNet.de",
    "zeige_kopf": True, "zeige_unter": True, "zeige_scan": True, "zeige_zugang": True, "zeige_fuss": True, "fuss_unten": True,
    "rahmen": False, "farbe_rahmen": "#3a9a1f", "rahmen_mm": 0.8, "rahmen_radius": 4,
    "logo": "", "logo_ort": "oben", "logo_pos": "center", "logo_mm": 40,
}


def design_pruefen(roh):
    """Übernimmt nur bekannte Felder mit gültigen Werten, alles andere = Standard."""
    d = copy.deepcopy(DESIGN_STANDARD)
    roh = roh if isinstance(roh, dict) else {}
    zahl = {"rand_mm": (3, 30), "gr_kopf": (6, 40), "gr_titel": (8, 80), "gr_text": (6, 30), "gr_pw": (8, 40),
            "gr_klein": (5, 20), "qr_cm": (2, 25), "rahmen_mm": (0.2, 5), "rahmen_radius": (0, 20), "logo_mm": (5, 180)}
    for k, v in roh.items():
        if k not in d:
            continue
        std = d[k]
        if k in zahl:
            try:
                d[k] = round(min(zahl[k][1], max(zahl[k][0], float(v))), 1)
            except (TypeError, ValueError):
                pass
        elif isinstance(std, bool):
            d[k] = bool(v)
        elif k.startswith("farbe_"):
            if isinstance(v, str) and re.fullmatch(r"#[0-9a-fA-F]{6}", v):
                d[k] = v.lower()
        elif k.startswith("t_"):
            d[k] = str(v)[:400]
        elif k == "format" and v in PAPIER:
            d[k] = v
        elif k == "schrift" and v in SCHRIFTEN:
            d[k] = v
        elif k == "ausrichtung" and v in ("left", "center", "right"):
            d[k] = v
        elif k == "logo_ort" and v in ("oben", "unten"):
            d[k] = v
        elif k == "logo_pos" and v in ("left", "center", "right"):
            d[k] = v
        elif k == "logo" and v in ("",) + tuple(os.path.basename(LOGO_BASIS) + "." + e for e in LOGO_TYPEN):
            d[k] = v
    return d


def logo_daten_uri(design):
    if not design.get("logo"):
        return ""
    roh = ablage_lesen(design["logo"])
    if not roh:
        return ""
    return f"data:{LOGO_TYPEN[design['logo'].rsplit('.', 1)[1]]};base64," + base64.b64encode(roh).decode()


def logo_speichern(roh):
    if not roh:
        raise Fehler("Keine Datei empfangen.")
    if len(roh) > 2_000_000:
        raise Fehler("Logo zu groß (max. 2 MB). Bitte verkleinern.")
    kopf = roh[:1024].lstrip()
    if roh.startswith(b"\x89PNG"):
        ext = "png"
    elif roh.startswith(b"\xff\xd8"):
        ext = "jpg"
    elif roh[:6] in (b"GIF87a", b"GIF89a"):
        ext = "gif"
    elif roh[:4] == b"RIFF" and roh[8:12] == b"WEBP":
        ext = "webp"
    elif b"<svg" in kopf.lower():
        ext = "svg"
    else:
        raise Fehler("Unbekanntes Bildformat – bitte PNG, JPG, GIF, WEBP oder SVG verwenden.")
    logo_entfernen()
    name = os.path.basename(LOGO_BASIS) + "." + ext
    ablage_schreiben(name, roh)
    return name


def logo_entfernen():
    for e in LOGO_TYPEN:
        ablage_loeschen(os.path.basename(LOGO_BASIS) + "." + e)


def vlan_parzelle(slot, p):
    m, q = (slot, p) if p <= 99 else (slot + 1, p - 100)
    return (1000 + m * 100 if m <= 9 else 3000) + q


class Fehler(Exception):
    pass


# =============================================================== Datenspeicher: Dateien im Datenordner oder MariaDB/MySQL
# Mit SPARTENET_DB_HOST speichert der Manager alles in der Datenbank (Einstellungen, Planung, Buchungen, Passwörter je Parzelle,
# Sicherungen, Änderungsprotokoll, Passwort-Register, Kartenlogo). Ohne: wie bisher Dateien im Datenordner.
DB_HOST = os.environ.get("SPARTENET_DB_HOST", "").strip()
DB_PORT = int(os.environ.get("SPARTENET_DB_PORT", "3306") or 3306)
DB_NAME = os.environ.get("SPARTENET_DB_NAME", "spartenet").strip() or "spartenet"
DB_USER = os.environ.get("SPARTENET_DB_USER", "spartenet").strip() or "spartenet"
DB_SSL = os.environ.get("SPARTENET_DB_SSL", "0").strip().lower() in ("1", "ja", "true", "yes")
DB_SSL_CA = os.environ.get("SPARTENET_DB_SSL_CA", "").strip()
DB_PASSWORD_FILE = os.environ.get("SPARTENET_DB_PASSWORD_FILE", "").strip()
if DB_PASSWORD_FILE:
    try:
        with open(DB_PASSWORD_FILE, encoding="utf-8") as f:
            DB_PASSWORD = f.read().rstrip("\r\n")
    except OSError as e:
        raise SystemExit(f"SPARTENET_DB_PASSWORD_FILE kann nicht gelesen werden: {e}")
else:
    DB_PASSWORD = os.environ.get("SPARTENET_DB_PASSWORD", "")
DB_TABELLEN = [
    """CREATE TABLE IF NOT EXISTS sn_daten (
        schluessel VARCHAR(100) NOT NULL PRIMARY KEY,
        wert LONGTEXT NOT NULL,
        geaendert TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci""",
    """CREATE TABLE IF NOT EXISTS sn_dateien (
        name VARCHAR(190) NOT NULL PRIMARY KEY,
        inhalt LONGBLOB NOT NULL,
        geaendert TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci""",
    """CREATE TABLE IF NOT EXISTS sn_journal (
        id BIGINT NOT NULL AUTO_INCREMENT PRIMARY KEY,
        zeit DATETIME NOT NULL,
        text TEXT NOT NULL,
        KEY zeit (zeit)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci""",
    """CREATE TABLE IF NOT EXISTS sn_passwort_register (
        pruefsumme CHAR(64) NOT NULL PRIMARY KEY,
        angelegt TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
    ) ENGINE=InnoDB DEFAULT CHARSET=ascii""",
    """CREATE TABLE IF NOT EXISTS sn_meta (
        schluessel VARCHAR(100) NOT NULL PRIMARY KEY,
        wert TEXT NOT NULL
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci""",
]
DB_SCHEMA = "1"


class Datenbank:
    """eine Verbindung je Thread, bei Abbruch einmal neu verbinden"""

    def __init__(self):
        self._lokal = threading.local()
        try:
            import pymysql
        except ImportError:
            raise SystemExit("SPARTENET_DB_HOST ist gesetzt, aber das Paket PyMySQL fehlt: pip install PyMySQL (im Docker-Image enthalten).")
        self.pymysql = pymysql

    def _verbinden(self):
        ssl_opt = None
        if DB_SSL:
            ctx = ssl.create_default_context(cafile=DB_SSL_CA or None)
            ssl_opt = ctx
        return self.pymysql.connect(host=DB_HOST, port=DB_PORT, user=DB_USER, password=DB_PASSWORD, database=DB_NAME, charset="utf8mb4",
                                    autocommit=True, connect_timeout=10, read_timeout=60, write_timeout=60, ssl=ssl_opt)

    def _verbindung(self):
        c = getattr(self._lokal, "c", None)
        if c is None:
            c = self._lokal.c = self._verbinden()
        return c

    def sql(self, befehl, werte=None, viele=False, alle=False):
        for versuch in (1, 2):
            try:
                with self._verbindung().cursor() as k:
                    if viele:
                        k.executemany(befehl, werte)
                    else:
                        k.execute(befehl, werte)
                    return k.fetchall() if alle else k.rowcount
            except (self.pymysql.err.OperationalError, self.pymysql.err.InterfaceError) as e:
                try:
                    self._lokal.c.close()
                except Exception:
                    pass
                self._lokal.c = None
                if versuch == 2:
                    LOG.error("Datenbank nicht erreichbar: %s", e)
                    raise Fehler(f"Datenbank {DB_HOST}:{DB_PORT}/{DB_NAME} nicht erreichbar ({e.args[0] if e.args else e}).")

    def einrichten(self):
        for t in DB_TABELLEN:
            self.sql(t)
        self.sql("INSERT INTO sn_meta (schluessel, wert) VALUES ('schema', %s) ON DUPLICATE KEY UPDATE wert = VALUES(wert)", (DB_SCHEMA,))


DB = Datenbank() if DB_HOST else None


class Daten(dict):
    """Einstellungen; merkt sich den geladenen Stand je Schlüssel, damit nur Geändertes in die Datenbank geht"""
    _stand = None


def speicher_text():
    return f"MariaDB/MySQL {DB_USER}@{DB_HOST}:{DB_PORT}/{DB_NAME}" if DB else f"Dateien im Ordner {HIER}"


def ablage_lesen(name):
    """Datei aus dem Datenspeicher (bytes) oder None"""
    if DB:
        r = DB.sql("SELECT inhalt FROM sn_dateien WHERE name = %s", (name,), alle=True)
        return bytes(r[0][0]) if r else None
    try:
        with open(os.path.join(HIER, name), "rb") as f:
            return f.read()
    except OSError:
        return None


def ablage_schreiben(name, roh):
    if isinstance(roh, str):
        roh = roh.encode("utf-8")
    if DB:
        DB.sql("INSERT INTO sn_dateien (name, inhalt) VALUES (%s, %s) ON DUPLICATE KEY UPDATE inhalt = VALUES(inhalt)", (name, roh))
        return
    pfad = os.path.join(HIER, name)
    with open(pfad, "wb") as f:
        f.write(roh)
    try:
        os.chmod(pfad, 0o600)
    except OSError:
        pass


def ablage_liste(praefix, endung=""):
    if DB:
        namen = [r[0] for r in DB.sql("SELECT name FROM sn_dateien WHERE LEFT(name, %s) = %s", (len(praefix), praefix), alle=True)]
    else:
        namen = [x for x in os.listdir(HIER) if x.startswith(praefix) and os.path.isfile(os.path.join(HIER, x))]
    return sorted(x for x in namen if x.startswith(praefix) and x.endswith(endung))


def ablage_loeschen(name):
    if DB:
        DB.sql("DELETE FROM sn_dateien WHERE name = %s", (name,))
        return
    try:
        os.remove(os.path.join(HIER, name))
    except OSError:
        pass


def ablage_umbenennen(alt, neu):
    if DB:
        DB.sql("DELETE FROM sn_dateien WHERE name = %s", (neu,))
        DB.sql("UPDATE sn_dateien SET name = %s WHERE name = %s", (neu, alt))
        return
    os.replace(os.path.join(HIER, alt), os.path.join(HIER, neu))


def datenbank_starten():
    """Tabellen anlegen; beim ersten Start vorhandene Dateien aus dem Datenordner übernehmen"""
    if not DB:
        return
    try:
        DB.einrichten()
    except Fehler as e:
        raise SystemExit(str(e))
    except Exception as e:
        raise SystemExit(f"Datenbank {DB_HOST}:{DB_PORT}/{DB_NAME}: {e}")
    leer = not DB.sql("SELECT COUNT(*) FROM sn_daten", alle=True)[0][0]
    dateien = sorted(x for x in os.listdir(HIER) if os.path.isfile(os.path.join(HIER, x)) and (
        x == os.path.basename(DATEI) or x in (os.path.basename(JOURNAL), os.path.basename(REGISTER))
        or x.startswith(("PPSK_", "SparteNet_Sicherung_", os.path.basename(LOGO_BASIS) + "."))))
    if not dateien:
        return
    if not leer:
        LOG.warning("Datenbank enthält schon Daten – Dateien im Datenordner werden nicht übernommen: %s", ", ".join(dateien))
        print("Hinweis: Datenbank enthält schon Daten – alte Dateien im Datenordner werden ignoriert.")
        return
    n = {"daten": 0, "journal": 0, "register": 0, "dateien": 0}
    for x in dateien:
        pfad = os.path.join(HIER, x)
        if x == os.path.basename(DATEI):
            with open(pfad, encoding="utf-8") as f:
                alt = json.load(f)
            DB.sql("INSERT INTO sn_daten (schluessel, wert) VALUES (%s, %s) ON DUPLICATE KEY UPDATE wert = VALUES(wert)",
                   [(k, json.dumps(v, ensure_ascii=False)) for k, v in alt.items()], viele=True)
            n["daten"] = len(alt)
        elif x == os.path.basename(JOURNAL):
            zeilen = []
            with open(pfad, encoding="utf-8", errors="replace") as f:
                for z in f:
                    m = re.match(r"^(\d{4}-\d\d-\d\d \d\d:\d\d:\d\d) \| (.*)$", z.rstrip("\n"))
                    if m:
                        zeilen.append((m.group(1), m.group(2)))
            if zeilen:
                DB.sql("INSERT INTO sn_journal (zeit, text) VALUES (%s, %s)", zeilen, viele=True)
            n["journal"] = len(zeilen)
        elif x == os.path.basename(REGISTER):
            with open(pfad, encoding="utf-8") as f:
                h = sorted({z.strip() for z in f if re.fullmatch(r"[0-9a-f]{64}", z.strip())})
            if h:
                DB.sql("INSERT IGNORE INTO sn_passwort_register (pruefsumme) VALUES (%s)", [(x,) for x in h], viele=True)
            n["register"] = len(h)
        else:
            with open(pfad, "rb") as f:
                ablage_schreiben(x, f.read())
            n["dateien"] += 1
    ziel = os.path.join(HIER, "in_Datenbank_uebernommen_" + time.strftime("%Y%m%d_%H%M%S"))
    os.makedirs(ziel, exist_ok=True)
    for x in dateien:
        try:
            os.replace(os.path.join(HIER, x), os.path.join(ziel, x))
        except OSError:
            pass
    text = (f"In die Datenbank übernommen: {n['daten']} Einstellungsbereiche, {n['journal']} Protokollzeilen, {n['register']} Register-Einträge, "
            f"{n['dateien']} Dateien (Passwörter je Parzelle, Sicherungen, Logo). Die alten Dateien liegen in {ziel}.")
    print(text)
    LOG.info(text)
    journal(text)


# =============================================================== Einstellungen (JSON)
def lade():
    if DB:
        stand = {k: v for k, v in DB.sql("SELECT schluessel, wert FROM sn_daten", alle=True)}
        d = Daten()
        for k, v in stand.items():
            try:
                d[k] = json.loads(v)
            except ValueError:
                LOG.error("Datenbank: Wert „%s“ ist kein gültiges JSON – übersprungen", k)
        d._stand = stand
    else:
        try:
            with open(DATEI, encoding="utf-8") as f:
                d = Daten(json.load(f))
        except (OSError, ValueError):
            d = Daten()
    d.setdefault("cloud_key", ""); d.setdefault("konsole_id", ""); d.setdefault("konsole_name", "")
    d.setdefault("plan", copy.deepcopy(STANDARD_PLAN))
    d.setdefault("log_aktiv", False)
    d.setdefault("tarife", copy.deepcopy(TARIFE_STANDARD)); d.setdefault("tarif_modus", "tarif"); d.setdefault("tarif_zuordnung", {})
    d["design"] = design_pruefen(d.get("design"))
    return d


def speichere(d):
    if DB:
        neu = {k: json.dumps(v, ensure_ascii=False) for k, v in d.items()}
        alt = getattr(d, "_stand", None) or {}
        geaendert = [(k, v) for k, v in neu.items() if alt.get(k) != v]
        if geaendert:
            DB.sql("INSERT INTO sn_daten (schluessel, wert) VALUES (%s, %s) ON DUPLICATE KEY UPDATE wert = VALUES(wert)", geaendert, viele=True)
        for k in alt:
            if k not in neu:
                DB.sql("DELETE FROM sn_daten WHERE schluessel = %s", (k,))
        if isinstance(d, Daten):
            d._stand = neu
        return
    with open(DATEI, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=2)
    try:
        os.chmod(DATEI, 0o600)
    except OSError:
        pass


# =============================================================== Cloud-Zugriff (nur Standardbibliothek)
ERKLAERUNG = {
    401: "API-Key wird abgelehnt (401). Es muss ein Site-Manager-Key von unifi.ui.com sein, erstellt vom Besitzer der Konsole.",
    403: "Keine Berechtigung (403) für diese Konsole oder Funktion.",
    404: "Nicht gefunden (404).",
    429: "Zu viele Anfragen (429) – kurz warten und erneut versuchen.",
    502: "Konsole antwortet nicht über die Cloud (502) – ist sie online?",
    503: "Dienst vorübergehend nicht erreichbar (503).",
}


def http(methode, url, key, body=None, timeout=45):
    t0 = time.time()
    try:
        code, d = _http(methode, url, key, body, timeout)
    except Fehler as e:
        LOG.error("%s %s → FEHLER %s (%d ms)", methode, url, e, (time.time() - t0) * 1000)
        raise
    ms = (time.time() - t0) * 1000
    if body is not None:
        LOG.debug("   Anfrage: %s", json.dumps(_maskiere(body), ensure_ascii=False)[:3000])
    antwort = json.dumps(_maskiere(d), ensure_ascii=False) if not isinstance(d, str) else d
    (LOG.warning if code >= 400 else LOG.info)("%s %s → %s (%d ms)", methode, url, code, ms)
    LOG.debug("   Antwort: %s", antwort[:3000])
    return code, d


def _http(methode, url, key, body=None, timeout=45):
    daten = json.dumps(body).encode("utf-8") if body is not None else None
    req = urllib.request.Request(url, data=daten, method=methode,
                                 headers={"X-API-KEY": key, "Accept": "application/json", "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=timeout, context=ssl.create_default_context()) as r:
            roh = r.read().decode("utf-8", "replace")
            return r.status, (json.loads(roh) if roh.strip() else {})
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", "replace")[:400]
    except urllib.error.URLError as e:
        raise Fehler(f"UniFi-Cloud nicht erreichbar: {e.reason}. Internetverbindung prüfen.")
    except TimeoutError:
        raise Fehler("Zeitüberschreitung – die Konsole antwortet zu langsam. Erneut versuchen.")
    except ValueError:
        raise Fehler("Antwort ist kein JSON.")


def konsolen(key):
    if not key:
        raise Fehler("Bitte den Site-Manager-API-Key eintragen (unifi.ui.com → Einstellungen → API Keys).")
    code, d = http("GET", f"{CLOUD}/v1/hosts", key)
    if code != 200:
        raise Fehler(ERKLAERUNG.get(code, f"Fehler {code}: {d}"))
    aus = []
    for h in d.get("data", []):
        rs = h.get("reportedState") or {}
        hw = rs.get("hardware") if isinstance(rs.get("hardware"), dict) else {}
        aus.append({"id": h.get("id", ""), "name": rs.get("name") or rs.get("hostname") or h.get("hardwareId", "")[:12],
                    "modell": hw.get("shortname", ""), "firmware": rs.get("version", ""), "ip": h.get("ipAddress", "")})
    return aus


def schreibfehler(code, methode):
    if methode == "GET":
        return ""
    return {401: "Schreiben abgelehnt (401): Der API-Key ist ungültig.",
            403: "Schreiben abgelehnt (403): Der API-Key darf nur lesen. Er muss vom Besitzer bzw. einem Super-Admin mit Vollzugriff erstellt sein.",
            404: "Schreiben nicht möglich (404): Diese Funktion gibt es auf der Konsole nicht (Firmware/Network-Version?).",
            405: "Schreiben nicht möglich (405): Die UniFi-Cloud lässt diese Art von Änderung nicht durch.",
            400: "Das Gateway hat die Änderung abgelehnt (400) – Angaben ungültig.",
            409: "Konflikt (409): Eintrag existiert bereits oder überschneidet sich.",
            502: "Konsole antwortet nicht über die Cloud (502) – ist sie online?"}.get(code, "")


JOURNAL = os.path.join(HIER, "SparteNet_Aenderungen.log")


def journal(text):
    """Änderungsprotokoll – immer an, ohne Passwörter"""
    try:
        if DB:
            DB.sql("INSERT INTO sn_journal (zeit, text) VALUES (%s, %s)", (time.strftime("%Y-%m-%d %H:%M:%S"), text))
        else:
            with open(JOURNAL, "a", encoding="utf-8") as f:
                f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} | {text}\n")
    except (OSError, Fehler):
        pass
    LOG.info("ÄNDERUNG: %s", text)


class Gateway:
    def __init__(self, d):
        if not d["cloud_key"] or not d["konsole_id"]:
            raise Fehler("Verbindung unvollständig: unter „Verbindung“ Key eintragen, „Konsolen laden“, Konsole wählen und speichern.")
        self.key = d["cloud_key"]
        stamm = f"{CLOUD}/v1/connector/consoles/{urllib.parse.quote(d['konsole_id'], safe='')}/proxy/network"
        self.int_base, self.leg_base = stamm + "/integration", stamm + "/api/s/default"
        self.v2_base = stamm + "/v2/api/site/default"
        self._site = None

    def req(self, methode, pfad, body=None):
        if "{site}" in pfad:
            pfad = pfad.replace("{site}", self.site_id())
        code, d = http(methode, self.int_base + pfad, self.key, body)
        if code >= 400:
            raise Fehler((schreibfehler(code, methode) or ERKLAERUNG.get(code, f"Fehler {code}")) + f" ({methode} {pfad}) " + (d if isinstance(d, str) else "")[:300])
        return d

    def alle(self, pfad, maximal=None):
        daten, offset = [], 0
        while True:
            if maximal and len(daten) >= maximal:
                return daten[:maximal]
            sep = "&" if "?" in pfad else "?"
            a = self.req("GET", f"{pfad}{sep}offset={offset}&limit=200")
            teil = a.get("data", []) if isinstance(a, dict) else a
            daten += teil
            gesamt = a.get("totalCount", len(daten)) if isinstance(a, dict) else len(daten)
            offset += len(teil)
            if not teil or offset >= gesamt:
                return daten

    def site_id(self):
        if not self._site:
            code, d = http("GET", self.int_base + "/v1/sites", self.key)
            if code >= 400:
                raise Fehler(ERKLAERUNG.get(code, f"Fehler {code}"))
            sites = d.get("data", [])
            if not sites:
                raise Fehler("Keine Site gefunden.")
            self._site = sites[0]["id"]
        return self._site

    def cloud(self, pfad):
        """Site-Manager-API direkt auf api.ui.com (nicht über die Konsole)"""
        code, d = http("GET", CLOUD + pfad, self.key)
        if code >= 400:
            raise Fehler(ERKLAERUNG.get(code, f"Fehler {code}") + f" (GET {pfad})")
        return d

    def legacy_roh(self, pfad):
        code, d = http("GET", f"{self.leg_base}/{pfad.lstrip('/')}", self.key)
        if code >= 400 or not isinstance(d, dict):
            raise Fehler(f"Klassische Schnittstelle über die Cloud nicht verfügbar ({code}).")
        return d.get("data", [])

    def legacy_post(self, pfad, body):
        code, d = http("POST", f"{self.leg_base}/{pfad.lstrip('/')}", self.key, body)
        if code >= 400 or not isinstance(d, dict):
            raise Fehler(f"Verlaufsdaten über die Cloud nicht verfügbar ({code}).")
        return d.get("data", [])

    def v2(self, methode, pfad, body=None):
        """v2-Schnittstelle der Network-App (QoS-Regeln)"""
        code, d = http(methode, f"{self.v2_base}/{pfad.lstrip('/')}", self.key, body)
        if code >= 400:
            msg = (d.get("message") or d.get("errorCode") or "") if isinstance(d, dict) else str(d)[:300]
            if methode == "GET" and code == 404:
                raise Fehler("QoS-Regeln über die Cloud nicht erreichbar (404). QoS-Regeln gibt es ab UniFi Network 9.1 – Version unter „Systeminfo“ prüfen.")
            raise Fehler(((schreibfehler(code, methode) or f"Gateway lehnt ab ({code})") + f" ({methode} {pfad}) {msg}")[:500])
        return d

    def legacy(self, methode, pfad, body=None):
        """klassische Schnittstelle (für PPSK) – über die Cloud nur, wenn UniFi sie freigibt"""
        code, d = http(methode, f"{self.leg_base}/{pfad.lstrip('/')}", self.key, body)
        if methode != "GET" and (code >= 400 or not isinstance(d, dict)):
            raise Fehler((schreibfehler(code, methode) or f"Schreiben abgelehnt ({code})") + f" ({methode} {pfad}) " + (d if isinstance(d, str) else "")[:300])
        if isinstance(d, dict) and (d.get("meta") or {}).get("rc") == "error":
            raise Fehler(f"Gateway meldet Fehler: {(d.get('meta') or {}).get('msg', '?')} ({methode} {pfad})")
        if code >= 400 or not isinstance(d, dict):
            raise Fehler(f"PPSK-Schnittstelle über die Cloud nicht verfügbar ({code}). Passwörter dann in der UniFi-Oberfläche "
                         f"(unifi.ui.com → Konsole → WLAN „Pächter“ → Private Pre-Shared Keys) eintragen – Liste und Zugangskarten erzeugt der Manager.")
        return d.get("data", [])


# =============================================================== Plan
def plan_berechnen(roh):
    sparten, slot = [], 1
    g, pre = int(roh.get("gateway") or 1), str(roh.get("praefix") or "SparteNet.de")
    for s in roh.get("sparten", []):
        if not s.get("name") or not s.get("n"):
            continue
        try:
            n, sid = int(s["n"]), int(s.get("sid") or 0)
        except (TypeError, ValueError):
            raise Fehler(f"Sparte „{s.get('name')}“: Sparten-ID und Parzellen müssen Zahlen sein.")
        kz = str(s.get("kz") or "").strip()
        if not kz or not 1 <= sid <= 254 or not 1 <= n <= 199:
            raise Fehler(f"Sparte „{s.get('name')}“: Kürzel, Sparten-ID (1–254) und Parzellen (1–199) prüfen.")
        sparten.append({"name": str(s["name"]), "kz": kz, "sid": sid, "n": n, "slot": slot})
        slot += 2 if n > 99 else 1
    if slot - 1 > 10:
        raise Fehler("Mehr als 10 Steckplätze belegt.")
    if len({s["sid"] for s in sparten}) != len(sparten) or len({s["kz"] for s in sparten}) != len(sparten):
        raise Fehler("Sparten-ID und Kürzel müssen je Sparte einmalig sein.")
    netze = []
    for s in sparten:
        f = {"kz": s["kz"], "pre": pre}
        def e(art, name, vlan, x, ssid, parz="", zugang=""):
            return {"sparte": s["kz"], "name": name, "vlan": vlan, "x": x, "sid": s["sid"], "netz": f"10.{s['sid']}.{x}.0/24",
                    "maske": "255.255.255.0", "router": f"10.{s['sid']}.{x}.1", "dhcp_start": f"10.{s['sid']}.{x}.10",
                    "dhcp_ende": f"10.{s['sid']}.{x}.250", "art": art, "ssid": ssid, "parzelle": parz, "zugang": zugang}
        for p in range(1, s["n"] + 1):
            netze.append(e("parzelle", NETZ_PARZELLE.format(p=p, **f), vlan_parzelle(s["slot"], p), p, WLAN_PAECHTER.format(**f), p, f"Passwort Parzelle {p}"))
        netze.append(e("vorstand", NETZ_VORSTAND.format(**f), 2000 + s["slot"] * 10 + 1, 200, WLAN_VORSTAND.format(**f), "", "eigenes WLAN"))
        netze.append(e("gaeste", NETZ_GAESTE.format(**f), 2000 + s["slot"] * 10 + 2, 201, WLAN_GAESTE.format(**f), "", "Voucher"))
        netze.append(e("technik", NETZ_TECHNIK.format(**f), 2000 + s["slot"] * 10 + 9, 250, "", "", "Switches, Access Points"))
    return {"gateway": g, "gatewayname": str(roh.get("gatewayname") or f"Gateway {g}"), "praefix": pre, "sparten": sparten, "netze": netze,
            "gateway_netz": {"name": "Gateway", "vlan": 1, "netz": f"10.0.{g}.0/24", "router": f"10.0.{g}.1"}}


def excel_import(roh_bytes):
    """liest Blatt „Eingabe“ des VLAN-Planers ohne Zusatzpakete"""
    M = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
    R = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}"
    try:
        z = zipfile.ZipFile(io.BytesIO(roh_bytes))
    except zipfile.BadZipFile:
        raise Fehler("Das ist keine Excel-Datei (.xlsx).")
    wb = ET.fromstring(z.read("xl/workbook.xml"))
    rid = next((s.get(R + "id") for s in wb.iter(M + "sheet") if s.get("name") == "Eingabe"), None)
    if not rid:
        raise Fehler("Blatt „Eingabe“ nicht gefunden – ist das der VLAN-Planer?")
    rels = ET.fromstring(z.read("xl/_rels/workbook.xml.rels"))
    ziel = next(r.get("Target") for r in rels if r.get("Id") == rid).lstrip("/")
    ziel = ziel if ziel.startswith("xl/") else "xl/" + ziel
    strings = []
    if "xl/sharedStrings.xml" in z.namelist():
        for si in ET.fromstring(z.read("xl/sharedStrings.xml")).iter(M + "si"):
            strings.append("".join(t.text or "" for t in si.iter(M + "t")))
    zellen = {}
    for c in ET.fromstring(z.read(ziel)).iter(M + "c"):
        v, t = c.find(M + "v"), c.get("t")
        if t == "inlineStr":
            wert = "".join(x.text or "" for x in c.iter(M + "t"))
        elif v is None or t == "e":
            continue  # leer oder Formel ohne gespeichertes Ergebnis bzw. mit Fehler
        elif t == "s":
            wert = strings[int(v.text)]
        else:
            wert = v.text
        zellen[c.get("r")] = wert
    def zahl(x):
        try:
            return int(float(x))
        except (TypeError, ValueError):
            return 0
    sparten = [{"name": zellen[f"B{r}"], "kz": zellen.get(f"C{r}", ""), "sid": zahl(zellen.get(f"D{r}")), "n": zahl(zellen.get(f"E{r}"))}
               for r in range(9, 19) if zellen.get(f"B{r}") and zellen.get(f"E{r}")]
    if not sparten and any(zellen.get(f"B{r}") is None for r in range(9, 19)) and "Sparten" in [s.get("name") for s in wb.iter(M + "sheet")]:
        raise Fehler("Im VLAN-Planer sind für das gewählte Gateway keine Sparten eingetragen – oder die Datei wurde ohne berechnete Werte gespeichert. "
                     "In Excel/LibreOffice öffnen, unter „Eingabe“ B4 das Gateway wählen, speichern und erneut übernehmen.")
    plan = {"gateway": zahl(zellen.get("B4")) or 1, "gatewayname": zellen.get("B5", ""), "praefix": zellen.get("B6", "SparteNet.de"), "sparten": sparten}
    plan_berechnen(plan)
    return plan


PW_REGEL_STANDARD = {"praefix": "SN", "ziffern": 10}
REGISTER = os.path.join(HIER, "SparteNet_Passwort_Register.txt")
_PW_SPERRE = threading.Lock()


def pw_regel(d=None):
    r = dict(PW_REGEL_STANDARD)
    roh = (d or lade()).get("pw_regel") or {}
    pre = str(roh.get("praefix", r["praefix"]))
    if re.fullmatch(r"[A-Za-z0-9\-_.]{0,10}", pre):
        r["praefix"] = pre
    try:
        r["ziffern"] = min(30, max(6, int(roh.get("ziffern", r["ziffern"]))))
    except (TypeError, ValueError):
        pass
    if len(r["praefix"]) + r["ziffern"] < 8:          # WPA2 verlangt mindestens 8 Zeichen
        r["ziffern"] = 8 - len(r["praefix"])
    return r


def _hash(pw):
    import hashlib
    return hashlib.sha256(("SparteNet|" + pw).encode("utf-8")).hexdigest()


def _register_lesen():
    if DB:
        return {r[0] for r in DB.sql("SELECT pruefsumme FROM sn_passwort_register", alle=True)}
    try:
        with open(REGISTER, encoding="utf-8") as f:
            return {z.strip() for z in f if z.strip()}
    except OSError:
        return set()


def register_eintragen(passwoerter):
    """Merkt sich jedes jemals vergebene Passwort (nur als Prüfsumme, nicht im Klartext)."""
    vorhanden = _register_lesen()
    neu = [_hash(p) for p in passwoerter if p and _hash(p) not in vorhanden]
    if neu and DB:
        DB.sql("INSERT IGNORE INTO sn_passwort_register (pruefsumme) VALUES (%s)", [(h,) for h in neu], viele=True)
    elif neu:
        with open(REGISTER, "a", encoding="utf-8") as f:
            f.write("\n".join(neu) + "\n")
        try:
            os.chmod(REGISTER, 0o600)
        except OSError:
            pass


def alle_belegten():
    """Klartext aller aktuell vergebenen Passwörter aller Sparten (PPSK_*.csv)"""
    belegt = set()
    for f in ablage_liste("PPSK_", ".csv"):
        try:
            belegt |= {z.get("Passwort", "") for z in lese_ppsk(f[5:-4])}
        except Exception:
            pass
    belegt.discard("")
    return belegt


def passwoerter_erzeugen(anzahl, d=None, zusaetzlich=()):
    """Neue Passwörter nach Regel Präfix + Ziffern, nie doppelt: weder in einer Sparte noch je zuvor vergeben."""
    r = pw_regel(d)
    with _PW_SPERRE:
        belegt, reg = alle_belegten() | set(zusaetzlich), _register_lesen()
        aus = []
        while len(aus) < anzahl:
            pw = r["praefix"] + "".join(secrets.choice("0123456789") for _ in range(r["ziffern"]))
            if pw in belegt or _hash(pw) in reg:
                continue
            belegt.add(pw); aus.append(pw)
        register_eintragen(aus)
    return aus


def passwort(d=None):
    return passwoerter_erzeugen(1, d)[0]


def passwort_fehler(pw):
    """WPA2-Passphrase: 8–63 druckbare ASCII-Zeichen. Leer = Parzelle ohne Zugang."""
    if pw == "":
        return ""
    if not 8 <= len(pw) <= 63:
        return "muss 8 bis 63 Zeichen lang sein"
    if any(not 32 <= ord(c) <= 126 for c in pw):
        return "nur Buchstaben A–Z, Ziffern und einfache Sonderzeichen (keine Umlaute)"
    if pw != pw.strip():
        return "darf nicht mit einem Leerzeichen beginnen oder enden"
    return ""


def ppsk_datei(kz):
    return f"PPSK_{kz}.csv"


def lese_ppsk(kz):
    roh = ablage_lesen(ppsk_datei(kz))
    if roh is None:
        return []
    return list(csv.DictReader(io.StringIO(roh.decode("utf-8-sig")), delimiter=";"))


def schreibe_ppsk(kz, zeilen):
    f = io.StringIO(newline="")
    w = csv.DictWriter(f, fieldnames=["Parzelle", "Netz", "VLAN", "WLAN", "Passwort"], delimiter=";", extrasaction="ignore")
    w.writeheader(); w.writerows(zeilen)
    ablage_schreiben(ppsk_datei(kz), f.getvalue().encode("utf-8-sig"))


def wo_ist(ip, plan):
    try:
        a = ipaddress.ip_address(ip)
    except ValueError:
        return ("unbekannt", "")
    if a in ipaddress.ip_network(plan["gateway_netz"]["netz"]):
        return ("gateway", "Gateway-/Technik-Netz")
    for n in plan["netze"]:
        if a in ipaddress.ip_network(n["netz"]):
            return (n["art"], n["name"])
    return ("ausserhalb", "außerhalb des Plans")


# =============================================================== QR-Code (ohne Zusatzpakete, nach ISO/IEC 18004)
_ECC_PRO_BLOCK = {  # Fehlerkorrektur-Codewörter je Block, Stufe M, Version 1–20
    "M": (-1, 10, 16, 26, 18, 24, 16, 18, 22, 22, 26, 30, 22, 22, 24, 24, 28, 28, 26, 26, 26)}
_BLOECKE = {"M": (-1, 1, 1, 1, 2, 2, 4, 4, 4, 5, 5, 5, 8, 9, 9, 10, 10, 11, 13, 14, 16)}


def _gf_mul(x, y):
    z = 0
    for i in reversed(range(8)):
        z = (z << 1) ^ ((z >> 7) * 0x11D)
        z ^= ((y >> i) & 1) * x
    return z


def _rs_divisor(grad):
    erg = [0] * (grad - 1) + [1]
    wurzel = 1
    for _ in range(grad):
        for j in range(grad):
            erg[j] = _gf_mul(erg[j], wurzel)
            if j + 1 < grad:
                erg[j] ^= erg[j + 1]
        wurzel = _gf_mul(wurzel, 0x02)
    return erg


def _rs_rest(daten, divisor):
    erg = [0] * len(divisor)
    for b in daten:
        f = b ^ erg.pop(0)
        erg.append(0)
        for i, c in enumerate(divisor):
            erg[i] ^= _gf_mul(c, f)
    return erg


def _roh_module(v):
    r = (16 * v + 128) * v + 64
    if v >= 2:
        n = v // 7 + 2
        r -= (25 * n - 10) * n - 55
        if v >= 7:
            r -= 36
    return r


def qr_matrix(text, ecl="M"):
    daten = text.encode("utf-8")
    for v in range(1, 21):
        nutz = _roh_module(v) // 8 - _ECC_PRO_BLOCK[ecl][v] * _BLOECKE[ecl][v]
        zbits = 8 if v <= 9 else 16
        if 4 + zbits + len(daten) * 8 <= nutz * 8:
            break
    else:
        raise ValueError("Text zu lang für QR-Code")
    bits = [0, 1, 0, 0] + [(len(daten) >> i) & 1 for i in reversed(range(zbits))]
    for b in daten:
        bits += [(b >> i) & 1 for i in reversed(range(8))]
    bits += [0] * min(4, nutz * 8 - len(bits))
    bits += [0] * (-len(bits) % 8)
    cw = [int("".join(map(str, bits[i:i + 8])), 2) for i in range(0, len(bits), 8)]
    pad = 0xEC
    while len(cw) < nutz:
        cw.append(pad); pad ^= 0xEC ^ 0x11
    # Fehlerkorrektur und Verschachtelung
    nb, eccl = _BLOECKE[ecl][v], _ECC_PRO_BLOCK[ecl][v]
    roh = _roh_module(v) // 8
    kurz = nb - roh % nb
    kurzlen = roh // nb
    div = _rs_divisor(eccl)
    bloecke, k = [], 0
    for i in range(nb):
        dl = kurzlen - eccl + (0 if i < kurz else 1)
        dat = cw[k:k + dl]; k += dl
        ecc = _rs_rest(dat, div)
        if i < kurz:
            dat = dat + [0]
        bloecke.append(dat + ecc)
    folge = []
    for i in range(len(bloecke[0])):
        for j, blk in enumerate(bloecke):
            if i != kurzlen - eccl or j >= kurz:
                folge.append(blk[i])
    n = v * 4 + 17
    mod = [[False] * n for _ in range(n)]
    fkt = [[False] * n for _ in range(n)]

    def setze(x, y, w):
        mod[y][x] = w; fkt[y][x] = True
    for i in range(n):
        setze(6, i, i % 2 == 0); setze(i, 6, i % 2 == 0)
    for cx, cy in ((3, 3), (n - 4, 3), (3, n - 4)):
        for dy in range(-4, 5):
            for dx in range(-4, 5):
                x, y = cx + dx, cy + dy
                if 0 <= x < n and 0 <= y < n:
                    setze(x, y, max(abs(dx), abs(dy)) not in (2, 4))
    if v > 1:
        na = v // 7 + 2
        schritt = (v * 8 + na * 3 + 5) // (na * 4 - 4) * 2
        pos = [6] + sorted(n - 7 - i * schritt for i in range(na - 1))
        for i, a in enumerate(pos):
            for j, b in enumerate(pos):
                if (i == 0 and j == 0) or (i == 0 and j == na - 1) or (i == na - 1 and j == 0):
                    continue
                for dy in range(-2, 3):
                    for dx in range(-2, 3):
                        setze(a + dx, b + dy, max(abs(dx), abs(dy)) != 1)

    def format_bits(maske):
        d = (0 << 3) | maske          # Stufe M = 00
        r = d
        for _ in range(10):
            r = (r << 1) ^ ((r >> 9) * 0x537)
        b = ((d << 10) | r) ^ 0x5412
        for i in range(6):
            setze(8, i, (b >> i) & 1)
        setze(8, 7, (b >> 6) & 1); setze(8, 8, (b >> 7) & 1); setze(7, 8, (b >> 8) & 1)
        for i in range(9, 15):
            setze(14 - i, 8, (b >> i) & 1)
        for i in range(8):
            setze(n - 1 - i, 8, (b >> i) & 1)
        for i in range(8, 15):
            setze(8, n - 15 + i, (b >> i) & 1)
        setze(8, n - 8, True)
    format_bits(0)
    if v >= 7:
        r = v
        for _ in range(12):
            r = (r << 1) ^ ((r >> 11) * 0x1F25)
        b = (v << 12) | r
        for i in range(18):
            w = (b >> i) & 1
            a, c = n - 11 + i % 3, i // 3
            setze(a, c, w); setze(c, a, w)
    i = 0
    rechts = n - 1
    while rechts >= 1:
        if rechts == 6:
            rechts = 5
        for vert in range(n):
            for j in range(2):
                x = rechts - j
                hoch = ((rechts + 1) & 2) == 0
                y = n - 1 - vert if hoch else vert
                if not fkt[y][x] and i < len(folge) * 8:
                    mod[y][x] = bool((folge[i >> 3] >> (7 - (i & 7))) & 1)
                    i += 1
        rechts -= 2
    masken = [lambda x, y: (x + y) % 2 == 0, lambda x, y: y % 2 == 0, lambda x, y: x % 3 == 0, lambda x, y: (x + y) % 3 == 0,
              lambda x, y: (x // 3 + y // 2) % 2 == 0, lambda x, y: x * y % 2 + x * y % 3 == 0,
              lambda x, y: (x * y % 2 + x * y % 3) % 2 == 0, lambda x, y: ((x + y) % 2 + x * y % 3) % 2 == 0]

    def anwenden(m):
        for y in range(n):
            for x in range(n):
                if not fkt[y][x] and masken[m](x, y):
                    mod[y][x] = not mod[y][x]

    def strafe():
        s = 0
        for zeilen in (mod, list(map(list, zip(*mod)))):
            for z in zeilen:
                lauf, farbe = 0, None
                for w in z:
                    if w == farbe:
                        lauf += 1
                    else:
                        if lauf >= 5:
                            s += 3 + lauf - 5
                        farbe, lauf = w, 1
                if lauf >= 5:
                    s += 3 + lauf - 5
        for y in range(n - 1):
            for x in range(n - 1):
                if mod[y][x] == mod[y][x + 1] == mod[y + 1][x] == mod[y + 1][x + 1]:
                    s += 3
        dunkel = sum(sum(z) for z in mod)
        s += abs(dunkel * 20 - n * n * 10) // (n * n) * 10
        return s
    beste, best_s = 0, None
    for m in range(8):
        anwenden(m); format_bits(m)
        p = strafe()
        if best_s is None or p < best_s:
            beste, best_s = m, p
        anwenden(m)
    anwenden(beste); format_bits(beste)
    return mod


def qr_svg(text, rand=4, farbe="#000000", hintergrund="#ffffff"):
    m = qr_matrix(text)
    n = len(m) + 2 * rand
    pfad = "".join(f"M{x + rand},{y + rand}h1v1h-1z" for y, z in enumerate(m) for x, w in enumerate(z) if w)
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {n} {n}" shape-rendering="crispEdges">'
            f'<rect width="{n}" height="{n}" fill="{hintergrund}"/><path d="{pfad}" fill="{farbe}"/></svg>')


def qr_kontrast_ok(farbe, hintergrund):
    hell = lambda c: (0.2126 * int(c[1:3], 16) + 0.7152 * int(c[3:5], 16) + 0.0722 * int(c[5:7], 16)) / 255
    return hell(hintergrund) - hell(farbe) >= 0.45


def wlan_qr_text(ssid, pw):
    esc = lambda s: re.sub(r'([\\;,:"])', r"\\\1", s)
    return f"WIFI:T:WPA;S:{esc(ssid)};P:{esc(pw)};;"


# =============================================================== Aktionen
def akt_test(d):
    log, g = [], Gateway(d)
    info = g.req("GET", "/v1/info")
    log.append(f"✔ Konsole „{d['konsole_name']}“ über die Cloud erreichbar – Network-App {info.get('applicationVersion', '?')}")
    sites = g.req("GET", "/v1/sites").get("data", [])
    log.append(f"✔ {len(sites)} Site(s): " + ", ".join(s.get("name", "") for s in sites))
    netze, geraete = g.alle("/v1/sites/{site}/networks"), g.alle("/v1/sites/{site}/devices")
    log.append(f"✔ {len(netze)} Netze, {len(geraete)} Geräte – Auslesen, Abgleich, Netze anlegen und Voucher nutzbar")
    try:
        w = g.legacy("GET", "rest/wlanconf")
        log.append(f"✔ PPSK-Schnittstelle über die Cloud erreichbar ({len(w)} WLANs) – Passwörter können hochgeladen werden")
    except Fehler as e:
        log.append(f"ℹ {e}")
    return {"log": log}


LESEN = {
    "geraete": ("/v1/sites/{site}/devices", [("name", "Name"), ("model", "Modell"), ("ipAddress", "IP-Adresse"), ("macAddress", "MAC"), ("state", "Status"), ("firmwareVersion", "Firmware")]),
    "clients": ("/v1/sites/{site}/clients", [("name", "Name"), ("type", "Art"), ("ipAddress", "IP-Adresse"), ("macAddress", "MAC"), ("connectedAt", "verbunden seit")]),
    "netze": ("/v1/sites/{site}/networks", [("name", "Name"), ("vlanId", "VLAN"), ("enabled", "aktiv")]),
    "wlans": ("/v1/sites/{site}/wifi/broadcasts", [("name", "Name"), ("type", "Art"), ("enabled", "aktiv")]),
    "voucher": ("/v1/sites/{site}/hotspot/vouchers", [("code", "Code"), ("name", "Bezeichnung"), ("timeLimitMinutes", "Minuten"), ("expired", "abgelaufen"), ("createdAt", "erstellt")]),
}


def akt_lesen(d, was):
    if was not in LESEN:
        raise Fehler("Unbekannte Auswahl.")
    pfad, sp = LESEN[was]
    daten = Gateway(d).alle(pfad)
    return {"spalten": [list(t) for t in sp], "zeilen": [{k: x.get(k, "") for k, _ in sp} for x in daten]}


def akt_abgleich(d, kz):
    plan, g = plan_berechnen(d["plan"]), Gateway(d)
    soll = [n for n in plan["netze"] if not kz or n["sparte"] == kz]
    ist = g.alle("/v1/sites/{site}/networks")
    nach_vlan, nach_name = {n.get("vlanId"): n for n in ist}, {n.get("name"): n for n in ist}
    fehlen, abweichend, ok = [], [], 0
    for n in soll:
        v, m = nach_vlan.get(n["vlan"]), nach_name.get(n["name"])
        if v and v.get("name") == n["name"]:
            ok += 1
        elif v:
            abweichend.append({"netz": n["name"], "soll": f"VLAN {n['vlan']}", "ist": f"VLAN {n['vlan']} heißt „{v.get('name')}“"})
        elif m:
            abweichend.append({"netz": n["name"], "soll": f"VLAN {n['vlan']}", "ist": f"hat VLAN {m.get('vlanId')}"})
        else:
            fehlen.append({"netz": n["name"], "vlan": n["vlan"], "subnetz": n["netz"]})
    soll_vlans = {n["vlan"] for n in plan["netze"]} | {1}
    extra = [{"netz": n.get("name"), "vlan": n.get("vlanId")} for n in ist if n.get("vlanId") not in soll_vlans]
    hinweise, clients = [], []
    for x in g.alle("/v1/sites/{site}/devices"):
        art, wo = wo_ist(x.get("ipAddress", ""), plan)
        if art in ("parzelle", "vorstand", "gaeste"):
            hinweise.append({"art": "Gerät", "name": x.get("name"), "ip": x.get("ipAddress"), "hinweis": f"Technik im Netz {wo} – Verwaltung gehört ins Gateway-/Technik-Netz"})
        elif art == "ausserhalb":
            hinweise.append({"art": "Gerät", "name": x.get("name"), "ip": x.get("ipAddress"), "hinweis": "außerhalb des Plans (beim Gateway selbst normal)"})
    for x in g.alle("/v1/sites/{site}/clients"):
        art, wo = wo_ist(x.get("ipAddress", ""), plan)
        if art in ("gateway", "technik"):
            hinweise.append({"art": "Client", "name": x.get("name"), "ip": x.get("ipAddress"), "hinweis": "Endgerät im Technik-Netz – WLAN/PPSK prüfen"})
        clients.append({"name": x.get("name"), "ip": x.get("ipAddress"), "netz": wo})
    return {"log": [f"Soll {len(soll)} Netze · korrekt {ok} · fehlen {len(fehlen)} · abweichend {len(abweichend)} · zusätzlich {len(extra)} · Hinweise {len(hinweise)}"],
            "fehlen": fehlen, "abweichend": abweichend, "extra": extra, "hinweise": hinweise, "clients": clients}


def _ersetze(obj, alt, neu):
    if isinstance(obj, str):
        return obj.replace(alt, neu)
    if isinstance(obj, list):
        return [_ersetze(x, alt, neu) for x in obj]
    if isinstance(obj, dict):
        return {k: _ersetze(v, alt, neu) for k, v in obj.items()}
    return obj


def akt_netze(d, kz, ausfuehren, nur_eins, namen=None):
    plan, g = plan_berechnen(d["plan"]), Gateway(d)
    soll = [n for n in plan["netze"] if n["sparte"] == kz]
    if not soll:
        raise Fehler("Sparte nicht im Plan.")
    ist = g.alle("/v1/sites/{site}/networks")
    auswahl_namen = set(namen) if namen else None
    vlans = {n.get("vlanId") for n in ist}
    namen_am_gw = {n.get("name") for n in ist}
    neu = [n for n in soll if n["name"] not in namen_am_gw and n["vlan"] not in vlans]
    if auswahl_namen is not None:
        neu = [n for n in neu if n["name"] in auswahl_namen]
    log = [f"{len(neu)} ausgewählte(s) Netz(e) für {kz}."] if auswahl_namen is not None else [f"{len(soll)} Netze im Plan, {len(soll) - len(neu)} vorhanden, {len(neu)} fehlen."]
    if not neu:
        return {"log": log + ["Nichts zu tun – alle Netze vorhanden."]}
    muster = re.compile(r"-Paz\.\d{3}$")
    kand = [n for n in ist if str(n.get("name", "")).startswith(kz + "-") and muster.search(str(n.get("name", "")))] or \
           [n for n in ist if muster.search(str(n.get("name", "")))]
    if not kand:
        raise Fehler("Keine Vorlage gefunden. Bitte ein Parzellennetz (z. B. BW-Paz.001) einmal in der UniFi-Oberfläche anlegen – der Manager kopiert dann dessen Einstellungen.")
    vorlage = g.req("GET", f"/v1/sites/{{site}}/networks/{kand[0]['id']}")
    host = (vorlage.get("ipv4Configuration") or {}).get("hostIpAddress") or ""
    if host.count(".") != 3:
        raise Fehler(f"Vorlage „{vorlage.get('name')}“ hat keine IPv4-Gateway-Adresse.")
    alt = host.rsplit(".", 1)[0] + "."
    for k in ("id", "default", "metadata", "_id"):
        vorlage.pop(k, None)
    log.append(f"Vorlage: {kand[0].get('name')} ({alt}0/24) – DHCP, Isolation, Firewall-Zone werden übernommen.")
    def body(n):
        b = _ersetze(copy.deepcopy(vorlage), alt, f"10.{n['sid']}.{n['x']}.")
        b.update({"name": n["name"], "vlanId": n["vlan"], "enabled": True})
        return b
    if nur_eins:
        neu = neu[:1]
    if not ausfuehren:
        log += [f"Vorschau: {n['name']:<16} VLAN {n['vlan']:<5} {n['netz']}" for n in neu]
        log.append("Anfrage für das erste Netz:\n" + json.dumps(body(neu[0]), indent=2, ensure_ascii=False))
        return {"log": log}
    ok = 0
    for n in neu:
        try:
            g.req("POST", "/v1/sites/{site}/networks", body(n)); ok += 1
            log.append(f"✔ angelegt: {n['name']} VLAN {n['vlan']} {n['netz']}")
        except Fehler as e:
            log.append(f"✖ {n['name']}: {e}")
            if ok == 0:
                log.append("Abbruch nach dem ersten Fehler."); break
    journal(f"Netze {kz}: {ok} von {len(neu)} angelegt ({', '.join(n['name'] for n in neu[:ok][:20])}{' …' if ok > 20 else ''})")
    log.append(f"Fertig: {ok} von {len(neu)} angelegt." + (" Bitte in der UniFi-Oberfläche prüfen, dann den Rest anlegen." if nur_eins and ok else ""))
    return {"log": log}


def akt_ppsk(d, kz, art):
    plan = plan_berechnen(d["plan"])
    s = next((x for x in plan["sparten"] if x["kz"] == kz), None)
    if not s:
        raise Fehler("Sparte nicht im Plan.")
    soll = [n for n in plan["netze"] if n["sparte"] == kz and n["art"] == "parzelle"]
    bisher = lese_ppsk(kz)
    register_eintragen([z.get("Passwort", "") for z in bisher])   # auch ältere Passwörter nie wieder vergeben
    vorhanden = {} if art == "neu" else {z["Netz"]: z["Passwort"] for z in bisher}
    log = []
    if art == "gateway":
        g = Gateway(d)
        nid = {n["_id"]: n["name"] for n in g.legacy("GET", "rest/networkconf")}
        ssid = WLAN_PAECHTER.format(kz=kz, pre=plan["praefix"])
        wlan = next((w for w in g.legacy("GET", "rest/wlanconf") if w.get("name") == ssid), None)
        if not wlan:
            raise Fehler(f"WLAN „{ssid}“ nicht gefunden.")
        u = 0
        for k in wlan.get("private_preshared_keys") or []:
            name = nid.get(k.get("networkconf_id"))
            if name and k.get("password"):
                vorhanden[name] = k["password"]; u += 1
        log.append(f"✔ {u} vorhandene Passwörter vom Gateway übernommen.")
    zeilen, neu = [], 0
    fehlend = sum(1 for n in soll if not vorhanden.get(n["name"])) if art != "anzeigen" else 0
    andere = alle_belegten() - set(z["Passwort"] for z in lese_ppsk(kz)) if art == "neu" else set()
    vorrat = iter(passwoerter_erzeugen(fehlend, d, zusaetzlich=set(vorhanden.values()) | andere)) if fehlend else iter(())
    for n in soll:
        pw = vorhanden.get(n["name"], "")
        if not pw and art != "anzeigen":
            pw = next(vorrat); neu += 1
        zeilen.append({"Parzelle": n["parzelle"], "Netz": n["name"], "VLAN": n["vlan"], "WLAN": n["ssid"], "Passwort": pw})
    if art != "anzeigen":
        schreibe_ppsk(kz, zeilen)
        register_eintragen([z["Passwort"] for z in zeilen])
        r = pw_regel(d)
        log.append(f"✔ {neu} neue Passwörter ({r['praefix']} + {r['ziffern']} Ziffern, geprüft auf doppelte), {len(zeilen) - neu} beibehalten – gespeichert in PPSK_{kz}.csv")
    else:
        log.append(f"{sum(1 for z in zeilen if z['Passwort'])} von {len(zeilen)} Parzellen haben ein Passwort.")
    return {"log": log, "zeilen": zeilen, "sparte": s}


def akt_ppsk_speichern(d, kz, aenderungen):
    """aenderungen: {"Parzelle": "neues Passwort" | ""} – wird in PPSK_<kz>.csv geschrieben"""
    if not isinstance(aenderungen, dict) or not aenderungen:
        raise Fehler("Keine Änderungen.")
    basis = akt_ppsk(d, kz, "anzeigen")["zeilen"]
    alt = {str(z["Parzelle"]): z["Passwort"] for z in basis}
    fehler, log = [], []
    for p, pw in aenderungen.items():
        if str(p) not in alt:
            fehler.append(f"Parzelle {p}: nicht im Plan")
            continue
        f = passwort_fehler(str(pw))
        if f:
            fehler.append(f"Parzelle {p}: Passwort {f}")
    for z in basis:
        p = str(z["Parzelle"])
        if p in aenderungen:
            z["Passwort"] = str(aenderungen[p])
    gesehen = {}
    for z in basis:
        if z["Passwort"]:
            if z["Passwort"] in gesehen:
                fehler.append(f"Parzelle {z['Parzelle']}: gleiches Passwort wie Parzelle {gesehen[z['Passwort']]} – jedes Passwort darf im WLAN nur einmal vorkommen")
            gesehen.setdefault(z["Passwort"], z["Parzelle"])
    andere = set()
    for f in ablage_liste("PPSK_", ".csv"):
        if f != f"PPSK_{kz}.csv":
            andere |= {(z.get("Passwort"), f[5:-4], z.get("Parzelle")) for z in lese_ppsk(f[5:-4]) if z.get("Passwort")}
    for p, pw in aenderungen.items():
        for apw, akz, ap in andere:
            if pw and pw == apw:
                fehler.append(f"Parzelle {p}: Passwort ist schon in Sparte {akz} (Parzelle {ap}) vergeben")
    reg = _register_lesen()
    for p, pw in aenderungen.items():
        if pw and pw != alt.get(str(p)) and _hash(pw) in reg and pw not in alt.values():
            fehler.append(f"Parzelle {p}: dieses Passwort wurde früher schon einmal vergeben – bitte ein anderes nehmen")
    if fehler:
        raise Fehler("Nicht gespeichert:\n" + "\n".join(fehler[:15]))
    schreibe_ppsk(kz, basis)
    register_eintragen([pw for pw in aenderungen.values() if pw])
    geaendert = [p for p, pw in aenderungen.items() if alt[str(p)] != pw]
    gesperrt = [p for p in geaendert if aenderungen[p] == ""]
    LOG.info("PPSK geändert: Sparte %s, Parzellen %s (Passwörter nicht protokolliert)", kz, ",".join(map(str, geaendert)))
    log.append(f"✔ {len(geaendert)} Parzelle(n) geändert und in PPSK_{kz}.csv gespeichert: " + ", ".join(map(str, geaendert)))
    if gesperrt:
        log.append(f"ℹ Ohne Passwort (Zugang wird beim Hochladen entfernt): Parzelle " + ", ".join(map(str, gesperrt)))
    log.append("➜ Damit die Änderung im WLAN gilt: Schritt 4 „Ausführen“. Danach die Karten der geänderten Parzellen neu drucken.")
    return {"log": log, "zeilen": basis, "geaendert": geaendert}


def akt_schreibtest(d):
    """Prüft, ob über die Cloud geschrieben werden darf – ohne etwas dauerhaft zu ändern."""
    g, log, ok = Gateway(d), [], {"network": False, "klassisch": False}
    # 1) Network-API: 1 Test-Voucher (1 Minute) anlegen und sofort wieder löschen
    try:
        a = g.req("POST", "/v1/sites/{site}/hotspot/vouchers", {"count": 1, "name": "SparteNet-Schreibtest", "timeLimitMinutes": 1})
        v = ((a or {}).get("vouchers") or [{}])[0] if isinstance(a, dict) else {}
        if v.get("id"):
            g.req("DELETE", f"/v1/sites/{{site}}/hotspot/vouchers/{v['id']}")
            log.append("✔ Network-API: Schreiben erlaubt (Test-Voucher angelegt und wieder gelöscht) – Netze anlegen und Voucher funktionieren.")
        else:
            log.append("✔ Network-API: Schreiben erlaubt. ℹ Test-Voucher „SparteNet-Schreibtest“ (1 Minute) bitte unter Hotspot löschen.")
        ok["network"] = True
    except Fehler as e:
        log.append(f"✖ Network-API: {e}")
    # 2) Klassische Schnittstelle (für Passwörter/PPSK): Notiz eines bekannten Clients unverändert zurückschreiben
    try:
        nutzer = [u for u in g.legacy_roh("rest/user") if u.get("_id")]
        if not nutzer:
            log.append("ℹ Klassische Schnittstelle: kein bekannter Client für den Test vorhanden – Test übersprungen.")
        else:
            u = nutzer[0]
            g.legacy("PUT", f"rest/user/{u['_id']}", {"note": u.get("note", ""), "noted": bool(u.get("noted", False))})
            log.append("✔ Klassische Schnittstelle: Schreiben erlaubt (ohne Änderung getestet) – Passwörter je Parzelle können übertragen werden.")
            ok["klassisch"] = True
    except Fehler as e:
        log.append(f"✖ Klassische Schnittstelle: {e}")
    if not ok["network"] and not ok["klassisch"]:
        log.append("➜ Über die Cloud ist kein Schreiben möglich. Lösung: API-Key als Besitzer/Super-Admin neu erstellen – oder lokal über VPN/Teleport arbeiten.")
    journal(f"Schreibtest: Network-API {'ok' if ok['network'] else 'abgelehnt'}, klassisch {'ok' if ok['klassisch'] else 'abgelehnt/übersprungen'}")
    return {"log": log, "ok": ok}


def _ppsk_lage(d, kz):
    """Soll (PPSK_<kz>.csv) gegen Ist (WLAN am Gateway) – gemeinsame Grundlage für Vergleich und Übertragung"""
    plan = plan_berechnen(d["plan"])
    ssid = WLAN_PAECHTER.format(kz=kz, pre=plan["praefix"])
    g = Gateway(d)
    nid = {n["name"]: n["_id"] for n in g.legacy("GET", "rest/networkconf")}
    wlan = next((w for w in g.legacy("GET", "rest/wlanconf") if w.get("name") == ssid), None)
    if not wlan:
        raise Fehler(f"WLAN „{ssid}“ nicht am Gateway gefunden – erst in der UniFi-Oberfläche anlegen (WPA2, Private Pre-Shared Keys).")
    soll = {z["Netz"]: z for z in lese_ppsk(kz)}
    if not soll:
        raise Fehler(f"Noch keine Passwörter für {kz} – erst „Einrichten“ Schritt 3.")
    ist = {}
    for k in wlan.get("private_preshared_keys") or []:
        ist.setdefault(k.get("networkconf_id"), []).append(k.get("password", ""))
    zeilen = []
    for n in [x for x in plan["netze"] if x["sparte"] == kz and x["art"] == "parzelle"]:
        z = soll.get(n["name"], {})
        pw_soll, nid_ = z.get("Passwort", ""), nid.get(n["name"])
        pw_ist = ist.get(nid_, []) if nid_ else []
        if not nid_:
            status = "netz_fehlt" if pw_soll else "gleich"
        elif pw_soll and not pw_ist:
            status = "neu"
        elif pw_soll and pw_ist != [pw_soll]:
            status = "geaendert"
        elif not pw_soll and pw_ist:
            status = "entfernen"
        else:
            status = "gleich"
        zeilen.append({"Parzelle": n["parzelle"], "Netz": n["name"], "VLAN": n["vlan"], "status": status, "soll": pw_soll, "ist": pw_ist, "nid": nid_})
    return g, wlan, ssid, zeilen


STATUS_TEXT = {"neu": "neu – noch nicht am Gateway", "geaendert": "geändert", "entfernen": "Zugang wird entfernt",
               "netz_fehlt": "Netz fehlt – wird übertragen, sobald das Netz angelegt ist (oben mit auswählen)", "gleich": "aktuell"}


def akt_vergleich(d, kz):
    plan = plan_berechnen(d["plan"])
    soll_netze = [n for n in plan["netze"] if n["sparte"] == kz]
    if not soll_netze:
        raise Fehler("Sparte nicht im Plan.")
    g = Gateway(d)
    ist = g.alle("/v1/sites/{site}/networks")
    namen, vlans = {n.get("name") for n in ist}, {n.get("vlanId") for n in ist}
    netze = [{"Netz": n["name"], "VLAN": n["vlan"], "Subnetz": n["netz"]} for n in soll_netze if n["name"] not in namen and n["vlan"] not in vlans]
    ppsk, ppsk_fehler = [], ""
    try:
        _, _, ssid, zeilen = _ppsk_lage(d, kz)
        for z in zeilen:
            if z["status"] != "gleich":
                ppsk.append({"Parzelle": z["Parzelle"], "Netz": z["Netz"], "status": z["status"], "Status": STATUS_TEXT[z["status"]]})
        gleich = sum(1 for z in zeilen if z["status"] == "gleich")
    except Fehler as e:
        ppsk_fehler, gleich = str(e), 0
    reihe = {"geaendert": 0, "entfernen": 1, "neu": 2, "netz_fehlt": 3}
    ppsk.sort(key=lambda p: (reihe.get(p["status"], 9), p["Parzelle"]))
    zahl = lambda st: sum(1 for p in ppsk if p["status"] == st)
    log = [f"Sparte {kz}: {len(netze)} Netze fehlen · Passwörter: {zahl('neu')} neu, {zahl('geaendert')} geändert, {zahl('entfernen')} zu entfernen, {gleich} aktuell"]
    if ppsk_fehler:
        log.append("ℹ Passwörter: " + ppsk_fehler)
    return {"log": log, "netze": netze, "ppsk": ppsk, "gleich": gleich, "ppsk_fehler": ppsk_fehler}


def _sicherung_schreiben(kz, wlan, ssid):
    pfad = f"SparteNet_Sicherung_{kz}_{time.strftime('%Y%m%d_%H%M%S')}.json"
    ablage_schreiben(pfad, json.dumps({"zeit": time.strftime("%Y-%m-%d %H:%M:%S"), "ssid": ssid, "wlan_id": wlan.get("_id"),
                                       "private_preshared_keys_enabled": wlan.get("private_preshared_keys_enabled"),
                                       "private_preshared_keys": wlan.get("private_preshared_keys") or []}, ensure_ascii=False, indent=1))
    for x in ablage_liste(f"SparteNet_Sicherung_{kz}_")[:-10]:
        ablage_loeschen(x)
    return pfad


def _ppsk_schreiben_und_pruefen(g, wlan, ssid, liste):
    g.legacy("PUT", f"rest/wlanconf/{wlan['_id']}", {"private_preshared_keys_enabled": True, "private_preshared_keys": liste})
    time.sleep(1)
    neu = next((w for w in g.legacy("GET", "rest/wlanconf") if w.get("_id") == wlan["_id"]), {})
    erwartet = sorted((k["networkconf_id"], k["password"]) for k in liste)
    ist = sorted((k.get("networkconf_id"), k.get("password")) for k in neu.get("private_preshared_keys") or [])
    return erwartet == ist


def akt_uebertragen(d, kz, parzellen, netze, ausfuehren):
    """Überträgt ausgewählte Änderungen: fehlende Netze anlegen, Passwörter je Parzelle setzen/ändern/entfernen."""
    log = []
    if netze:
        r = akt_netze(d, kz, ausfuehren, False, namen=netze)
        log += r["log"]
    if parzellen:
        g, wlan, ssid, zeilen = _ppsk_lage(d, kz)
        wahl = {str(p) for p in parzellen}
        betroffen = [z for z in zeilen if str(z["Parzelle"]) in wahl and z["status"] in ("neu", "geaendert", "entfernen")]
        uebersprungen = [z for z in zeilen if str(z["Parzelle"]) in wahl and z["status"] == "netz_fehlt"]
        if uebersprungen:
            log.append("ℹ Übersprungen, Netz fehlt noch am Gateway: Parzelle " + ", ".join(str(z["Parzelle"]) for z in uebersprungen))
        if not betroffen:
            log.append("Passwörter: nichts zu übertragen.")
        else:
            nids = {z["nid"] for z in betroffen}
            liste = [k for k in (wlan.get("private_preshared_keys") or []) if k.get("networkconf_id") not in nids]
            liste += [{"password": z["soll"], "networkconf_id": z["nid"]} for z in betroffen if z["soll"]]
            pws = [k["password"] for k in liste]
            doppelt = {p for p in pws if pws.count(p) > 1}
            if doppelt:
                raise Fehler("Ein Passwort käme im WLAN doppelt vor (auch Einträge anderer Sparten zählen) – bitte in Schritt 3 ändern.")
            text = ", ".join(f"{z['Parzelle']} ({ {'neu': 'neu', 'geaendert': 'geändert', 'entfernen': 'entfernt'}[z['status']] })" for z in betroffen)
            if not ausfuehren:
                log.append(f"Vorschau WLAN „{ssid}“: {len(betroffen)} Parzelle(n) – {text}. Alle anderen Einträge bleiben unverändert.")
            else:
                sich = _sicherung_schreiben(kz, wlan, ssid)
                bestaetigt = _ppsk_schreiben_und_pruefen(g, wlan, ssid, liste)
                journal(f"Passwörter {kz} → „{ssid}“: {text} · {'am Gateway bestätigt' if bestaetigt else 'NICHT bestätigt'} · Sicherung {os.path.basename(sich)}")
                log.append(f"✔ {len(betroffen)} Parzelle(n) an das Gateway übertragen: {text}")
                log.append("✔ Am Gateway nachgelesen und bestätigt." if bestaetigt else "⚠ Übertragen, aber beim Nachlesen nicht identisch – bitte in der UniFi-Oberfläche prüfen.")
                log.append(f"Sicherung des vorherigen Stands: {os.path.basename(sich)} (für „Rückgängig“). Mit einem Handy testen!")
    if not netze and not parzellen:
        raise Fehler("Nichts ausgewählt.")
    return {"log": log}


def akt_rueckgaengig(d, kz):
    dateien = ablage_liste(f"SparteNet_Sicherung_{kz}_", ".json")
    if not dateien:
        raise Fehler("Keine Sicherung vorhanden.")
    sich = json.loads(ablage_lesen(dateien[-1]).decode("utf-8"))
    g = Gateway(d)
    wlan = next((w for w in g.legacy("GET", "rest/wlanconf") if w.get("_id") == sich["wlan_id"]), None)
    if not wlan:
        raise Fehler("Das WLAN aus der Sicherung gibt es am Gateway nicht mehr.")
    bestaetigt = _ppsk_schreiben_und_pruefen(g, wlan, sich["ssid"], sich["private_preshared_keys"])
    ablage_umbenennen(dateien[-1], dateien[-1][:-5] + ".zurueckgespielt")
    journal(f"Rückgängig {kz} → „{sich['ssid']}“: Stand vom {sich['zeit']} wiederhergestellt · {'bestätigt' if bestaetigt else 'NICHT bestätigt'}")
    return {"log": [f"✔ Passwörter im WLAN „{sich['ssid']}“ auf den Stand vom {sich['zeit']} zurückgesetzt ({len(sich['private_preshared_keys'])} Einträge)."
                    + (" Am Gateway bestätigt." if bestaetigt else " ⚠ Nicht bestätigt – bitte prüfen."),
                    "ℹ PPSK_" + kz + ".csv wurde nicht verändert – dort stehen weiter die neuen Passwörter."]}


def akt_journal():
    if DB:
        z = DB.sql("SELECT zeit, text FROM sn_journal ORDER BY id DESC LIMIT 300", alle=True)
        return {"log": [f"{a:%Y-%m-%d %H:%M:%S} | {t}" for a, t in z] or ["(noch keine Änderungen übertragen)"]}
    if not os.path.exists(JOURNAL):
        return {"log": ["(noch keine Änderungen übertragen)"]}
    with open(JOURNAL, encoding="utf-8") as f:
        return {"log": f.read().splitlines()[-300:][::-1]}


def akt_ppsk_hochladen(d, kz, ausfuehren):
    """Schritt 4: alle Unterschiede der Sparte übertragen"""
    _, _, _, zeilen = _ppsk_lage(d, kz)
    return akt_uebertragen(d, kz, [z["Parzelle"] for z in zeilen if z["status"] in ("neu", "geaendert", "entfernen", "netz_fehlt")], [], ausfuehren)


def akt_ppsk_hochladen_alt(d, kz, ausfuehren):
    plan = plan_berechnen(d["plan"])
    keys = [k for k in lese_ppsk(kz) if k.get("Passwort")]
    if not keys:
        raise Fehler("Keine Passwörter vorhanden – erst Schritt 3.")
    ssid = WLAN_PAECHTER.format(kz=kz, pre=plan["praefix"])
    if not ausfuehren:
        return {"log": [f"Vorschau: WLAN „{ssid}“ bekommt bzw. behält {len(keys)} Parzellen-Passwörter. Andere Passwörter bleiben erhalten."]}
    if len({k["Passwort"] for k in keys}) != len(keys):
        raise Fehler("Ein Passwort kommt doppelt vor – bitte korrigieren.")
    g = Gateway(d)
    nid = {n["name"]: n["_id"] for n in g.legacy("GET", "rest/networkconf")}
    wlan = next((w for w in g.legacy("GET", "rest/wlanconf") if w.get("name") == ssid), None)
    if not wlan:
        raise Fehler(f"WLAN „{ssid}“ nicht gefunden.")
    fehlt = [k["Netz"] for k in keys if k["Netz"] not in nid]
    if fehlt:
        raise Fehler(f"Netze fehlen noch: {', '.join(fehlt[:6])} … – erst Schritt 1.")
    alle_parz = [n["name"] for n in plan["netze"] if n["sparte"] == kz and n["art"] == "parzelle"]
    unsere = {nid[n] for n in alle_parz if n in nid}
    behalten = [k for k in (wlan.get("private_preshared_keys") or []) if k.get("networkconf_id") not in unsere]
    wlan["private_preshared_keys_enabled"] = True
    wlan["private_preshared_keys"] = behalten + [{"password": k["Passwort"], "networkconf_id": nid[k["Netz"]]} for k in keys]
    g.legacy("PUT", f"rest/wlanconf/{wlan['_id']}", wlan)
    ohne = len([n for n in alle_parz if n in nid]) - len(keys)
    return {"log": [f"✔ {len(keys)} Passwörter im WLAN „{ssid}“ gespeichert ({len(behalten)} weitere unverändert"
                    + (f", {ohne} Parzellen ohne Zugang" if ohne > 0 else "") + "). Mit einem Handy testen!"]}


def _parallel(funktionen, anzahl=6):
    """führt {schluessel: funktion} parallel aus → {schluessel: (ergebnis, fehlertext)}"""
    aus = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=anzahl) as ex:
        zuk = {ex.submit(f): k for k, f in funktionen.items()}
        for z in concurrent.futures.as_completed(zuk):
            try:
                aus[zuk[z]] = (z.result(), "")
            except Exception as e:  # einzelne Quelle darf fehlen
                aus[zuk[z]] = (None, str(e)[:200])
    return aus


def _isp_metrics(g, konsole):
    """ISP-Messwerte (5 Minuten, 24 h) der Konsole aus der Site-Manager-API"""
    letzter = ""
    for pfad in ("/v1/isp-metrics/5m?duration=24h", "/ea/isp-metrics/5m?duration=24h"):
        try:
            a = g.cloud(pfad)
        except Fehler as e:
            letzter = str(e); continue
        for m in (a.get("data") or []):
            if m.get("hostId") == konsole:
                punkte, roh = [], {}
                def wert(w, *namen):
                    for n in namen:
                        if isinstance(w.get(n), (int, float)):
                            return float(w[n])
                    return None
                for p in m.get("periods") or []:
                    w = ((p.get("data") or {}).get("wan") or {})
                    if w:
                        roh = {"metricTime": p.get("metricTime"), **w}
                    punkte.append({"t": p.get("metricTime"), "down": wert(w, "download_kbps", "downloadKbps", "download"),
                                   "up": wert(w, "upload_kbps", "uploadKbps", "upload"),
                                   "lat": wert(w, "avgLatency"), "maxlat": wert(w, "maxLatency"), "verlust": wert(w, "packetLoss"),
                                   "uptime": wert(w, "uptime"), "isp": w.get("ispName")})
                punkte.sort(key=lambda x: x["t"] or "")
                return {"punkte": punkte, "roh": roh, "hinweise": _isp_bereinigen(punkte)}
        return {"punkte": [], "roh": {}, "hinweise": []}
    raise Fehler(letzter)


def _wan_verlauf(g):
    """Datenverkehr am Internet-Anschluss je 5 Minuten (letzte 24 h) aus den Berichten des Gateways"""
    jetzt = int(time.time() * 1000)
    body = {"attrs": ["wan-rx_bytes", "wan-tx_bytes", "wan2-rx_bytes", "wan2-tx_bytes", "num_sta", "time"], "start": jetzt - 86_400_000, "end": jetzt}
    roh = g.legacy_post("stat/report/5minutes.site", body)
    aus = []
    for r in roh:
        if not r.get("time"):
            continue
        rx = (r.get("wan-rx_bytes") or 0) + (r.get("wan2-rx_bytes") or 0)
        tx = (r.get("wan-tx_bytes") or 0) + (r.get("wan2-tx_bytes") or 0)
        aus.append({"t": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(r["time"] / 1000)),
                    "down": rx * 8 / 300 / 1000, "up": tx * 8 / 300 / 1000, "clients": r.get("num_sta")})
    aus.sort(key=lambda x: x["t"])
    return aus


def _isp_bereinigen(punkte):
    """Einheiten prüfen und einzelne Ausreißer markieren. Werte in kbit/s."""
    hinweise = []
    for k, name in (("down", "Download"), ("up", "Upload")):
        werte = sorted(p[k] for p in punkte if p[k])
        if not werte:
            hinweise.append(f"{name}: die UniFi-Cloud liefert für diesen Zeitraum keine Werte (0 oder leer).")
            continue
        if len(werte) > 3 and werte[0] == werte[-1]:   # immer derselbe Wert = keine Messung (z. B. eingestellte Leitungsgeschwindigkeit)
            mbit = werte[0] / 1e6 if werte[0] > 2_000_000 else werte[0] / 1e3
            for p in punkte:
                p[k] = None
            hinweise.append(f"{name}: die UniFi-Cloud meldet immer denselben Wert ({mbit:g} Mbit/s) – das ist keine Messung und wird nicht gezeichnet.")
            continue
        median = werte[len(werte) // 2]
        if median > 2_000_000:   # > 2 Gbit/s als „kbps“ ist unrealistisch → Feld enthält bit/s
            for p in punkte:
                if p[k] is not None:
                    p[k] = p[k] / 1000
            hinweise.append(f"{name}: Werte kamen offenbar in bit/s statt kbit/s und wurden umgerechnet.")
            werte = [w / 1000 for w in werte]; median /= 1000
        grenze = max(median * 20, 1000)
        spitzen = [p for p in punkte if p[k] and p[k] > grenze]
        if spitzen and len(spitzen) <= max(3, len(punkte) // 50):
            for p in spitzen:
                p[k + "_roh"] = p[k]; p[k] = None
            hinweise.append(f"{name}: {len(spitzen)} unplausible Spitze(n) ausgeblendet (z. B. {spitzen[0][k + '_roh'] / 1000:,.0f} Mbit/s).".replace(",", "."))
    return hinweise


def akt_system(d):
    g, plan = Gateway(d), plan_berechnen(d["plan"])
    g.site_id()
    quellen = _parallel({
        "geraete": lambda: g.alle("/v1/sites/{site}/devices"),
        "clients": lambda: g.alle("/v1/sites/{site}/clients"),
        "sites": lambda: g.cloud("/v1/sites"),
        "isp": lambda: _isp_metrics(g, d["konsole_id"]),
        "verlauf": lambda: _wan_verlauf(g),
        "health": lambda: g.legacy_roh("stat/health"),
        "sta": lambda: g.legacy_roh("stat/sta"),
        "legdev": lambda: g.legacy_roh("stat/device"),
    })
    hinweise = []
    geraete = quellen["geraete"][0] or []
    if quellen["geraete"][1]:
        raise Fehler(quellen["geraete"][1])
    stats = _parallel({x["id"]: (lambda i=x["id"]: g.req("GET", f"/v1/sites/{{site}}/devices/{i}/statistics/latest")) for x in geraete if x.get("id")})
    details = _parallel({x["id"]: (lambda i=x["id"]: g.req("GET", f"/v1/sites/{{site}}/devices/{i}")) for x in geraete if x.get("id")})
    legdev = {str(x.get("mac", "")).lower(): x for x in (quellen["legdev"][0] or [])}
    zeilen = []
    for x in geraete:
        st = (stats.get(x.get("id")) or (None,))[0] or {}
        de = (details.get(x.get("id")) or (None,))[0] or {}
        ports = ((de.get("interfaces") or {}).get("ports") or [])
        radios = ((de.get("interfaces") or {}).get("radios") or [])
        st_rad = ((st.get("interfaces") or {}).get("radios") or [])
        up = st.get("uplink") or {}
        lg = legdev.get(str(x.get("macAddress", "")).lower(), {})
        zeilen.append({
            "gw": bool(re.match(r"(UDM|UDR|UCG|UXG|UDW|EFG|UX\b|Dream|Cloud Gateway|Gateway)", str(x.get("model") or ""), re.I)) or x.get("name") == d["konsole_name"],
            "name": x.get("name"), "modell": x.get("model"), "ip": x.get("ipAddress"), "status": x.get("state"),
            "firmware": x.get("firmwareVersion"), "update": bool(de.get("firmwareUpdatable")),
            "cpu": st.get("cpuUtilizationPct"), "ram": st.get("memoryUtilizationPct"),
            "load": st.get("loadAverage1Min"), "uptime": st.get("uptimeSec"),
            "rx_bps": up.get("rxRateBps"), "tx_bps": up.get("txRateBps"),
            "ports_auf": sum(1 for p in ports if p.get("state") == "UP"), "ports": len(ports),
            "poe": sum(1 for p in ports if (p.get("poe") or {}).get("enabled")),
            "funk": " · ".join(f"{r.get('frequencyGHz')} GHz K{r.get('channel', '?')}/{r.get('channelWidthMHz', '?')} MHz" for r in radios),
            "retries": " · ".join(f"{r.get('frequencyGHz')} GHz {r.get('txRetriesPct')} %" for r in st_rad if r.get("txRetriesPct") is not None),
            "clients": lg.get("num_sta"), "temp": next((t.get("value") for t in (lg.get("temperatures") or []) if isinstance(t, dict)), lg.get("general_temperature")),
        })
    fehlende_stats = sum(1 for k, v in stats.items() if v[1])
    if fehlende_stats:
        hinweise.append(f"Für {fehlende_stats} Gerät(e) liefert die Konsole keine Auslastung (offline oder nicht unterstützt).")

    # Clients je Netz
    clients = quellen["clients"][0] or []
    arten, je_netz = {}, {}
    for c in clients:
        arten[c.get("type") or "?"] = arten.get(c.get("type") or "?", 0) + 1
        _, wo = wo_ist(c.get("ipAddress", ""), plan)
        e = je_netz.setdefault(wo or "unbekannt", {"netz": wo or "unbekannt", "clients": 0, "rx": 0, "tx": 0})
        e["clients"] += 1

    # Datenverkehr je Client (nur klassische Schnittstelle)
    sta = quellen["sta"][0]
    top = []
    if sta:
        for c in sta:
            _, wo = wo_ist(c.get("ip", ""), plan)
            e = je_netz.setdefault(wo or "unbekannt", {"netz": wo or "unbekannt", "clients": 0, "rx": 0, "tx": 0})
            e["rx"] += int(c.get("rx_bytes") or 0); e["tx"] += int(c.get("tx_bytes") or 0)
            top.append({"name": c.get("name") or c.get("hostname") or c.get("mac"), "ip": c.get("ip"), "netz": wo,
                        "wlan": c.get("essid") or ("Kabel" if c.get("is_wired") else ""), "signal": c.get("signal"),
                        "rx": int(c.get("rx_bytes") or 0), "tx": int(c.get("tx_bytes") or 0), "seit": c.get("uptime")})
        top.sort(key=lambda c: c["rx"] + c["tx"], reverse=True)
    else:
        hinweise.append("Datenverkehr je Gerät/Parzelle braucht die klassische Schnittstelle – über die Cloud nicht verfügbar. Angezeigt werden Anzahl Clients je Netz.")

    # WAN / Internet
    wan = {}
    for h in quellen["health"][0] or []:
        if h.get("subsystem") == "wan":
            wan.update({"wan_ip": h.get("wan_ip"), "isp": h.get("isp_name"), "rx_bps": (h.get("rx_bytes-r") or 0) * 8,
                        "tx_bps": (h.get("tx_bytes-r") or 0) * 8, "status": h.get("status"), "gw_cpu": (h.get("gw_system-stats") or {}).get("cpu")})
        if h.get("subsystem") == "www":
            wan.update({"latenz": h.get("latency"), "speed_down": h.get("xput_down"), "speed_up": h.get("xput_up"), "speedtest": h.get("speedtest_lastrun")})
    site = {}
    for sx in ((quellen["sites"][0] or {}).get("data") or []):
        if sx.get("hostId") == d["konsole_id"]:
            stt = sx.get("statistics") or {}
            site = {"zaehler": stt.get("counts") or {}, "prozent": stt.get("percentages") or {},
                    "isp": (stt.get("ispInfo") or {}).get("name") or (stt.get("ispInfo") or {}).get("organization"),
                    "wans": stt.get("wans") or {}, "gateway": stt.get("gateway") or {}}
            break
    isp_erg = quellen["isp"][0] or {"punkte": [], "roh": {}, "hinweise": []}
    isp = isp_erg["punkte"]
    if quellen["isp"][1]:
        hinweise.append("Internet-Verlauf (ISP-Messwerte) nicht verfügbar: " + quellen["isp"][1])
    netze = sorted(je_netz.values(), key=lambda e: (-(e["rx"] + e["tx"]), -e["clients"], e["netz"]))
    return {"geraete": zeilen, "clients_arten": arten, "clients_gesamt": len(clients), "je_netz": netze, "top": top[:15],
            "wan": wan, "site": site, "isp": isp, "isp_roh": isp_erg["roh"], "verlauf": quellen["verlauf"][0] or [], "verlauf_fehler": quellen["verlauf"][1], "isp_hinweise": isp_erg["hinweise"], "hinweise": hinweise, "zeit": time.strftime("%H:%M:%S"),
            "log": [f"✔ Aktualisiert {time.strftime('%H:%M:%S')} – {len(zeilen)} Geräte, {len(clients)} Clients"] + [f"ℹ {h}" for h in hinweise]}


# ---------------------------------------------------------------- Alle Daten (nur lesen)
DATEN = {
    # Schlüssel: (Gruppe, Titel, Art, Pfad)   Art: int = Network-API (Liste), int1 = Einzelobjekt, cloud = Site Manager, leg = klassisch
    "info": ("Network-API", "Version / Info", "int1", "/v1/info"),
    "sites": ("Network-API", "Sites", "int", "/v1/sites"),
    "devices": ("Network-API", "Geräte", "int", "/v1/sites/{site}/devices"),
    "pending": ("Network-API", "Geräte zur Übernahme", "int", "/v1/pending-devices"),
    "clients": ("Network-API", "Clients", "int", "/v1/sites/{site}/clients"),
    "networks": ("Network-API", "Netze / VLANs", "int", "/v1/sites/{site}/networks"),
    "wifi": ("Network-API", "WLANs", "int", "/v1/sites/{site}/wifi/broadcasts"),
    "vouchers": ("Network-API", "Hotspot-Voucher", "int", "/v1/sites/{site}/hotspot/vouchers"),
    "wans": ("Network-API", "WAN-Anschlüsse", "int", "/v1/sites/{site}/wans"),
    "zones": ("Network-API", "Firewall-Zonen", "int", "/v1/sites/{site}/firewall/zones"),
    "policies": ("Network-API", "Firewall-Regeln", "int", "/v1/sites/{site}/firewall/policies"),
    "acl": ("Network-API", "ACL-Regeln", "int", "/v1/sites/{site}/acl-rules"),
    "tml": ("Network-API", "Traffic-Listen", "int", "/v1/sites/{site}/traffic-matching-lists"),
    "vpnserver": ("Network-API", "VPN-Server", "int", "/v1/sites/{site}/vpn/servers"),
    "vpntunnel": ("Network-API", "VPN-Tunnel (Site-to-Site)", "int", "/v1/sites/{site}/vpn/site-to-site-tunnels"),
    "radius": ("Network-API", "RADIUS-Profile", "int", "/v1/sites/{site}/radius/profiles"),
    "tags": ("Network-API", "Geräte-Tags", "int", "/v1/sites/{site}/device-tags"),
    "dpicat": ("Network-API", "DPI-Kategorien", "int", "/v1/dpi/categories"),
    "dpiapp": ("Network-API", "DPI-Anwendungen", "int", "/v1/dpi/applications"),
    "countries": ("Network-API", "Länder", "int", "/v1/countries"),
    "c_hosts": ("UniFi-Cloud (Site Manager)", "Konsolen im Konto", "cloud", "/v1/hosts"),
    "c_sites": ("UniFi-Cloud (Site Manager)", "Sites mit Statistik", "cloud", "/v1/sites"),
    "c_devices": ("UniFi-Cloud (Site Manager)", "Geräte aller Konsolen", "cloud", "/v1/devices"),
    "c_isp5": ("UniFi-Cloud (Site Manager)", "Internet-Messwerte 24 h (5 min)", "cloud", "/v1/isp-metrics/5m?duration=24h"),
    "c_isp1": ("UniFi-Cloud (Site Manager)", "Internet-Messwerte 7 Tage (1 h)", "cloud", "/v1/isp-metrics/1h?duration=7d"),
    "c_sdwan": ("UniFi-Cloud (Site Manager)", "SD-WAN-Konfigurationen", "cloud", "/ea/sd-wan-configs"),
    "l_health": ("Klassische Schnittstelle", "Zustand (Health)", "leg", "stat/health"),
    "l_sysinfo": ("Klassische Schnittstelle", "Systeminfo", "leg", "stat/sysinfo"),
    "l_device": ("Klassische Schnittstelle", "Geräte (ausführlich)", "leg", "stat/device"),
    "l_sta": ("Klassische Schnittstelle", "Aktive Clients mit Datenverkehr", "leg", "stat/sta"),
    "l_user": ("Klassische Schnittstelle", "Bekannte Clients", "leg", "rest/user"),
    "l_net": ("Klassische Schnittstelle", "Netzkonfiguration", "leg", "rest/networkconf"),
    "l_wlan": ("Klassische Schnittstelle", "WLAN-Konfiguration", "leg", "rest/wlanconf"),
    "l_pf": ("Klassische Schnittstelle", "Portweiterleitungen", "leg", "rest/portforward"),
    "l_fw": ("Klassische Schnittstelle", "Firewall-Regeln (alt)", "leg", "rest/firewallrule"),
    "l_fwg": ("Klassische Schnittstelle", "Firewall-Gruppen", "leg", "rest/firewallgroup"),
    "l_route": ("Klassische Schnittstelle", "Statische Routen", "leg", "rest/routing"),
    "l_portconf": ("Klassische Schnittstelle", "Port-Profile", "leg", "rest/portconf"),
    "l_setting": ("Klassische Schnittstelle", "Einstellungen", "leg", "rest/setting"),
    "l_alarm": ("Klassische Schnittstelle", "Alarme", "leg", "list/alarm"),
    "l_rogue": ("Klassische Schnittstelle", "Fremde WLANs in der Nähe", "leg", "stat/rogueap"),
    "l_ddns": ("Klassische Schnittstelle", "Dynamisches DNS", "leg", "rest/dynamicdns"),
    "v2_qos": ("Klassische Schnittstelle", "QoS-Regeln (Bandbreite)", "v2", "qos-rules"),
}
GEHEIM = re.compile(r"(pass|secret|psk|preshared|token|private_?key|^x_|cloud_key|api_?key)", re.I)


def _verdecke(obj):
    if isinstance(obj, dict):
        return {k: ("••••••" if GEHEIM.search(k) and v not in (None, "", [], {}, False, True) else _verdecke(v)) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_verdecke(x) for x in obj]
    return obj


def _daten_holen(g, schluessel, maximal=1000):
    gruppe, titel, art, pfad = DATEN[schluessel]
    if art == "int":
        return g.alle(pfad, maximal)
    if art == "int1":
        return g.req("GET", pfad)
    if art == "cloud":
        a = g.cloud(pfad)
        return a.get("data", a) if isinstance(a, dict) else a
    if art == "v2":
        a = g.v2("GET", pfad)
        return a.get("data", a) if isinstance(a, dict) else a
    return g.legacy_roh(pfad)


def akt_daten(d, schluessel, geheim):
    if schluessel not in DATEN:
        raise Fehler("Unbekannte Datenquelle.")
    g = Gateway(d)
    roh = _daten_holen(g, schluessel)
    if not geheim:
        roh = _verdecke(roh)
    gruppe, titel, art, pfad = DATEN[schluessel]
    anzahl = len(roh) if isinstance(roh, list) else 1
    return {"titel": titel, "gruppe": gruppe, "pfad": pfad, "anzahl": anzahl, "roh": roh,
            "log": [f"✔ {titel}: {anzahl} {'Eintrag' if anzahl == 1 else 'Einträge'}" + (" (max. 1000 angezeigt)" if anzahl >= 1000 else "")
                    + ("" if geheim else " · Passwörter/Schlüssel verdeckt")]}


def akt_daten_pruefen(d):
    g = Gateway(d)
    g.site_id()
    def zaehle(k):
        art = DATEN[k][2]
        if art == "int":
            pfad = DATEN[k][3]
            a = g.req("GET", pfad + ("&" if "?" in pfad else "?") + "limit=1")
            return a.get("totalCount", len(a.get("data", []))) if isinstance(a, dict) else len(a)
        r = _daten_holen(g, k, 1)
        return len(r) if isinstance(r, list) else 1
    erg = _parallel({k: (lambda k=k: zaehle(k)) for k in DATEN}, anzahl=6)
    aus = {k: {"ok": not erg[k][1], "anzahl": erg[k][0], "fehler": erg[k][1]} for k in DATEN}
    ok = sum(1 for v in aus.values() if v["ok"])
    return {"quellen": aus, "log": [f"✔ {ok} von {len(DATEN)} Datenquellen über die Cloud lesbar."]}


PERSOENLICH = re.compile(r"^(email|fullName|firstName|lastName|phone|username|owner|ownerEmail)$", re.I)


def akt_diagnose(d, anonym=True):
    """Liest alle relevanten Antworten roh aus (nur GET), verdeckt Geheimnisse, optional anonymisiert – zum Weitergeben an den Support."""
    g = Gateway(d)
    stamm = g.int_base[len(CLOUD):]
    eintraege = []

    def hole(art, pfad):
        url = CLOUD + pfad if art == "cloud" else (g.int_base + pfad if art == "int" else (f"{g.v2_base}/{pfad}" if art == "v2" else f"{g.leg_base}/{pfad}"))
        t0 = time.time()
        try:
            code, a = http("GET", url, g.key)
        except Fehler as e:
            code, a = 0, str(e)
        eintraege.append({"art": art, "pfad": pfad, "code": code, "ms": int((time.time() - t0) * 1000), "antwort": a})
        return a if code == 200 else None

    for p in ("/v1/hosts", "/v1/sites", "/v1/devices", "/v1/isp-metrics/5m?duration=24h", "/v1/isp-metrics/1h?duration=7d", "/ea/isp-metrics/5m?duration=24h"):
        hole("cloud", p)
    hole("int", "/v1/info")
    sites = hole("int", "/v1/sites")
    site = ((sites or {}).get("data") or [{}])[0].get("id") if isinstance(sites, dict) else None
    hole("int", "/v1/pending-devices?limit=200")
    if site:
        b = f"/v1/sites/{site}"
        geraete = hole("int", b + "/devices?limit=200")
        for x in ((geraete or {}).get("data") or []) if isinstance(geraete, dict) else []:
            hole("int", f"{b}/devices/{x.get('id')}")
            hole("int", f"{b}/devices/{x.get('id')}/statistics/latest")
        for t in ("clients", "networks", "wifi/broadcasts", "hotspot/vouchers", "wans", "firewall/zones", "firewall/policies", "acl-rules",
                  "traffic-matching-lists", "vpn/servers", "vpn/site-to-site-tunnels", "radius/profiles", "device-tags"):
            hole("int", f"{b}/{t}?limit=200")
    for p in ("stat/health", "stat/sysinfo", "stat/device", "stat/sta", "rest/networkconf", "rest/wlanconf"):
        hole("leg", p)
    hole("v2", "qos-rules")
    jetzt = int(time.time() * 1000)
    for p in ("stat/report/5minutes.site", "stat/report/5minutes.gw"):
        t0 = time.time()
        body = {"attrs": ["wan-rx_bytes", "wan-tx_bytes", "wan2-rx_bytes", "wan2-tx_bytes", "num_sta", "time"], "start": jetzt - 86_400_000, "end": jetzt}
        try:
            code, a = http("POST", f"{g.leg_base}/{p}", g.key, body)
        except Fehler as e:
            code, a = 0, str(e)
        eintraege.append({"art": "legpost", "pfad": p, "code": code, "ms": int((time.time() - t0) * 1000), "antwort": a})

    # Geheimnisse und persönliche Daten entfernen
    namen, macs = {}, {}
    def anon(obj, client=False):
        if isinstance(obj, dict):
            aus = {}
            for k, v in obj.items():
                if GEHEIM.search(k) and v not in (None, "", [], {}, False, True):
                    aus[k] = "••••••"
                elif PERSOENLICH.match(k) and v:
                    aus[k] = "•"
                elif anonym and client and k in ("name", "hostname", "displayName") and isinstance(v, str) and v:
                    aus[k] = namen.setdefault(v, f"Client-{len(namen) + 1:02d}")
                elif anonym and client and k in ("macAddress", "mac") and isinstance(v, str) and v:
                    aus[k] = macs.setdefault(v.lower(), f"02:00:00:00:{(len(macs) + 1) // 256:02x}:{(len(macs) + 1) % 256:02x}")
                else:
                    aus[k] = anon(v, client)
            return aus
        if isinstance(obj, list):
            return [anon(x, client) for x in obj]
        return obj
    for e in eintraege:
        e["antwort"] = anon(e["antwort"], client=e["pfad"].split("?")[0].endswith(("/clients", "stat/sta")))
    paket = {"programm": f"SparteNet Manager {VERSION}", "erstellt": time.strftime("%Y-%m-%d %H:%M:%S"), "anonymisiert": anonym,
             "cloud_stamm": stamm, "eintraege": eintraege}
    datei = os.path.join(HIER, f"SparteNet_Diagnose_{time.strftime('%Y%m%d_%H%M')}.json")
    with open(datei, "w", encoding="utf-8") as f:
        json.dump(paket, f, ensure_ascii=False, indent=1)
    ok = sum(1 for e in eintraege if e["code"] == 200)
    return {"log": [f"✔ Diagnose-Datei erstellt: {datei}", f"{ok} von {len(eintraege)} Abfragen erfolgreich · Passwörter, Schlüssel und E-Mail-Adressen entfernt"
                    + (" · Clientnamen und MAC-Adressen anonymisiert" if anonym else ""), "Die Datei wird zusätzlich heruntergeladen – im Chat anhängen."],
            "name": os.path.basename(datei), "inhalt": json.dumps(paket, ensure_ascii=False, indent=1)}


ANSICHT_STANDARD = {"breite": 1200, "zoom": 0, "tabh": 520, "spalten": False, "kd": 430, "dl": 270}


def ansicht_pruefen(roh):
    """Bildschirm-Einstellungen der Oberfläche. 0 bei breite/zoom/tabh = automatisch."""
    a = dict(ANSICHT_STANDARD)
    roh = roh if isinstance(roh, dict) else {}
    grenzen = {"breite": (800, 8000, True), "zoom": (0.6, 3, True), "tabh": (200, 4000, True), "kd": (280, 1600, False), "dl": (200, 1000, False)}
    for k, (lo, hi, null_erlaubt) in grenzen.items():
        try:
            v = float(roh.get(k, a[k]))
        except (TypeError, ValueError):
            continue
        a[k] = 0 if (null_erlaubt and v == 0) else round(min(hi, max(lo, v)), 2)
    a["spalten"] = bool(roh.get("spalten", a["spalten"]))
    return a


def daten_liste():
    return [{"schluessel": k, "gruppe": v[0], "titel": v[1], "pfad": v[3]} for k, v in DATEN.items()]


def karten_html(design, sparte_name, kz, zeilen, drucken=True, vorschau=False):
    """Eine Seite je Eintrag. zeilen: [{"Parzelle", "WLAN", "Passwort"}]"""
    g = design_pruefen(design)
    esc = lambda t: str(t).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")
    breite, hoehe = PAPIER[g["format"]]
    if g["quer"]:
        breite, hoehe = hoehe, breite
    innen_b, innen_h = breite - 2 * g["rand_mm"], hoehe - 2 * g["rand_mm"]
    qr_mm = min(g["qr_cm"] * 10, (innen_b * 0.45) if g["quer"] else (innen_b - 6), innen_h * 0.75)
    logo = logo_daten_uri(g)
    logo_html = (f'<div class="logo" style="text-align:{g["logo_pos"]}"><img src="{logo}" alt=""></div>' if logo else "")

    def txt(vorlage, z):
        t = vorlage
        for k, v in (("{sparte}", sparte_name), ("{kz}", kz), ("{parzelle}", z["Parzelle"]), ("{wlan}", z["WLAN"])):
            t = t.replace(k, str(v))
        return esc(t).replace("\n", "<br>")

    seiten = []
    for z in zeilen:
        svg = qr_svg(wlan_qr_text(z["WLAN"], z["Passwort"]), farbe=g["farbe_qr"], hintergrund=g["farbe_qr_hinter"])
        teile, qr_teil = [], []
        if g["logo_ort"] == "oben":
            teile.append(logo_html)
        if g["zeige_kopf"] and g["t_kopf"].strip():
            teile.append(f'<div class="kopf">{txt(g["t_kopf"], z)}</div>')
        if g["t_titel"].strip():
            teile.append(f'<h1>{txt(g["t_titel"], z)}</h1>')
        if g["zeige_unter"] and g["t_unter"].strip():
            teile.append(f'<p class="info">{txt(g["t_unter"], z)}</p>')
        qr_teil.append(f'<div class="qr">{svg}</div>')
        if g["zeige_scan"] and g["t_scan"].strip():
            qr_teil.append(f'<p class="scan">{txt(g["t_scan"], z)}</p>')
        zugang = []
        if g["zeige_zugang"]:
            zugang.append(f'<div class="zugang"><div class="lbl">WLAN</div><div class="ssid">{esc(z["WLAN"])}</div>'
                          f'<div class="lbl">Passwort</div><div class="pw">{esc(z["Passwort"])}</div></div>')
        unten = [logo_html] if g["logo_ort"] == "unten" else []
        fuss = f'<p class="fuss">{txt(g["t_fuss"], z)}</p>' if g["zeige_fuss"] and g["t_fuss"].strip() else ""
        if g["quer"]:   # Querformat: Texte links, QR-Code rechts
            inhalt = (f'<div class="zwei"><div class="sp-text">{"".join(teile + zugang + unten)}</div>'
                      f'<div class="sp-qr">{"".join(qr_teil)}</div></div>{fuss}')
        else:
            inhalt = "".join(teile + qr_teil + zugang + unten) + fuss
        seiten.append(f'<section class="seite"><div class="innen">{inhalt}</div></section>')

    rahmen = (f'border:{g["rahmen_mm"]}mm solid {g["farbe_rahmen"]};border-radius:{g["rahmen_radius"]}mm;padding:5mm;'
              if g["rahmen"] else "padding:1mm;")
    css = f"""@page{{size:{breite}mm {hoehe}mm;margin:0}}
*{{box-sizing:border-box;-webkit-print-color-adjust:exact;print-color-adjust:exact}}
html,body{{margin:0;padding:0}}body{{font-family:{SCHRIFTEN[g["schrift"]]};color:{g["farbe_text"]};font-size:{g["gr_text"]}pt}}
.seite{{width:{breite}mm;height:{hoehe}mm;padding:{g["rand_mm"]}mm;background:{g["farbe_seite"]};overflow:hidden;page-break-after:always;break-after:page}}
.seite:last-child{{page-break-after:auto;break-after:auto}}
.innen{{height:100%;display:flex;flex-direction:column;text-align:{g["ausrichtung"]};{rahmen}}}
.kopf{{color:{g["farbe_akzent"]};font-weight:bold;font-size:{g["gr_kopf"]}pt;margin-top:2mm}}
h1{{font-size:{g["gr_titel"]}pt;margin:3mm 0 0;line-height:1.1}}
.info{{margin:1mm 0 3mm;color:{g["farbe_hell"]}}}
.qr{{margin:2mm 0}}.qr svg{{width:{qr_mm:.1f}mm;max-width:100%;height:auto;display:inline-block;vertical-align:top}}
.scan{{font-size:{g["gr_klein"] + 1}pt;color:{g["farbe_hell"]};margin:1mm 0 4mm}}
.zugang{{margin:1mm 0 2mm}}.lbl{{font-size:{g["gr_klein"]}pt;color:{g["farbe_hell"]};text-transform:uppercase;letter-spacing:.5px;margin-top:2mm}}
.ssid{{font-weight:bold;font-size:{g["gr_text"] + 1}pt;white-space:nowrap}}
.pw{{display:inline-block;white-space:nowrap;font-family:Consolas,'DejaVu Sans Mono','Courier New',monospace;font-size:{g["gr_pw"]}pt;letter-spacing:1px;background:{g["farbe_pw_hinter"]};padding:1mm 3mm;border-radius:1.5mm;margin-top:.5mm;font-variant-ligatures:none}}
.zwei{{display:flex;gap:6mm;align-items:center;flex:1 0 auto}}.sp-text{{flex:1 1 55%;min-width:0}}.sp-qr{{flex:0 1 45%;text-align:center}}
.logo{{margin:1mm 0 2mm}}.logo img{{width:{g["logo_mm"]}mm;max-width:100%;max-height:{innen_h * 0.3:.0f}mm;object-fit:contain}}
.fuss{{font-size:{g["gr_klein"]}pt;color:{g["farbe_hell"]};margin:{"auto 0 0" if g["fuss_unten"] and not g["quer"] else "4mm 0 0"};padding-top:3mm}}
@media screen{{body{{background:#8a949b;padding:8mm 0}}.seite{{margin:0 auto 8mm;box-shadow:0 2px 12px rgba(0,0,0,.35)}}}}"""
    # Passt der Inhalt nicht auf die Seite, wird der QR-Code schrittweise verkleinert (min. 2,5 cm).
    anpassen = ("function anpassen(){let klein=0,voll=0,cm=0;document.querySelectorAll('.innen').forEach(i=>{const s=i.querySelector('.qr svg');"
                "i.querySelectorAll('.ssid,.pw').forEach(e=>{let f=parseFloat(getComputedStyle(e).fontSize);const b=e.parentElement.clientWidth;while(e.scrollWidth>b&&f>6){f*=0.95;e.style.fontSize=f+'px'}});"
                "const im=i.querySelector('.logo img');if(im){let lw=im.getBoundingClientRect().width/(parseFloat(document.body.style.zoom)||1);while(i.scrollHeight>i.clientHeight+1&&lw>57){lw*=0.94;im.style.width=lw+'px'}}"
                "let w=parseFloat(getComputedStyle(s).width);const w0=w,min=Math.min(w0,94.5);"
                "while(i.scrollHeight>i.clientHeight+1&&w>min){w=Math.max(min,w*0.96);s.style.width=w+'px'}"
                "if(w<w0-0.5){klein++;cm=w/37.795}if(i.scrollHeight>i.clientHeight+1)voll++});"
                "const t=[];if(klein)t.push('ℹ QR-Code automatisch auf '+cm.toFixed(1).replace('.',',')+' cm verkleinert, damit alles auf die Seite passt.');"
                "if(voll)t.push('⚠ Inhalt passt nicht auf die Seite – Schrift oder Logo verkleinern, Texte kürzen oder größeres Format wählen.');"
                "try{if(parent!==window&&parent.kdHinweis)parent.kdHinweis(t.join('\\n'))}catch(e){}return t}")
    if vorschau:
        skript = ("<script>" + anpassen + "function f(){document.body.style.zoom=1;const s=document.querySelector('.seite');const w=s.offsetWidth+40,h=s.offsetHeight+40;"
                  "document.body.style.zoom=Math.min(1,innerWidth/w,innerHeight/h)}addEventListener('resize',f);"
                  "addEventListener('load',()=>{anpassen();f()})</script>")
        css += "\n@media screen{body{padding:20px 0;min-height:100vh;display:flex;align-items:center;justify-content:center}.seite{margin:0}}"
    else:
        skript = "<script>" + anpassen + "addEventListener('load',()=>{const t=anpassen();" + ("setTimeout(()=>print(),300)" if drucken else "") + "})</script>"
    return (f'<!doctype html><html lang="de"><head><meta charset="utf-8"><title>Zugangskarten {esc(sparte_name)}</title>'
            f'<style>{css}</style></head><body>{"".join(seiten)}{skript}</body></html>')


def beispiel_zeile(d):
    plan = plan_berechnen(d["plan"])
    s = plan["sparten"][0] if plan["sparten"] else {"name": "Musterverein e.V.", "kz": "MV"}
    pre = plan.get("praefix") or "SparteNet.de"
    return s["name"], s["kz"], {"Parzelle": 1, "WLAN": WLAN_PAECHTER.format(pre=pre, kz=s["kz"]), "Passwort": "Gartenzwerg-4711"}


def akt_karten_vorschau(d, design, drucken=False):
    g = design_pruefen(design)
    name, kz, z = beispiel_zeile(d)
    log = []
    if not qr_kontrast_ok(g["farbe_qr"], g["farbe_qr_hinter"]):
        log.append("⚠ QR-Code: zu wenig Kontrast – dunkle Punkte auf hellem Grund verwenden, sonst scannen viele Handys nicht.")
    if g["qr_cm"] < 3:
        log.append("⚠ QR-Code kleiner als 3 cm – aus der Hand schlecht lesbar.")
    return {"html": karten_html(g, name, kz, [z], drucken=drucken, vorschau=not drucken), "log": log or ["✔ Vorschau aktuell."]}


def akt_karten(d, kz, auswahl):
    plan = plan_berechnen(d["plan"])
    s = next((x for x in plan["sparten"] if x["kz"] == kz), None)
    if not s:
        raise Fehler("Sparte nicht im Plan.")
    zeilen = [z for z in lese_ppsk(kz) if z.get("Passwort")]
    if auswahl != "alle":
        wahl = {str(x) for x in auswahl}
        zeilen = [z for z in zeilen if str(z["Parzelle"]) in wahl]
    if not zeilen:
        raise Fehler("Keine Einträge ausgewählt bzw. keine Passwörter vorhanden.")
    g = d["design"]
    html = karten_html(g, s["name"], kz, zeilen)
    LOG.info("Zugangskarten erzeugt: Sparte %s, %d Seiten, Format %s", kz, len(zeilen), g["format"])
    return {"html": html, "log": [f"✔ {len(zeilen)} Zugangskarten ({g['format']}{' quer' if g['quer'] else ''}, je Parzelle eine Seite, Design aus „Kartendesign“) zum Drucken geöffnet."]}


def akt_voucher(d, anzahl, minuten, name, ausfuehren):
    body = {"count": int(anzahl), "name": name or "Gast", "timeLimitMinutes": int(minuten)}
    if not ausfuehren:
        return {"log": [f"Vorschau: {anzahl} Voucher „{body['name']}“ für je {minuten} Minuten.", json.dumps(body)]}
    a = Gateway(d).req("POST", "/v1/sites/{site}/hotspot/vouchers", body)
    liste = (a.get("vouchers") or a.get("data") or []) if isinstance(a, dict) else (a or [])
    codes = [v["code"] for v in liste if isinstance(v, dict) and v.get("code")]
    return {"log": [f"✔ {len(codes) or anzahl} Voucher erstellt." + ("" if codes else " Codes unter „Auslesen → Voucher“.")], "codes": codes, "minuten": int(minuten)}


# =============================================================== Tarife (Bandbreite per QoS-Regel, Netzgröße per Subnetz/DHCP)
TARIFE_STANDARD = [
    {"name": "Basic", "down": 30, "up": 10, "praefix": 29, "geraete": 5, "preis": 120},
    {"name": "Plus", "down": 60, "up": 20, "praefix": 28, "geraete": 10, "preis": 180},
    {"name": "Max", "down": 100, "up": 40, "praefix": 24, "geraete": 0, "preis": 240},
]
QOS_TARIF, QOS_NETZ = "SparteNet-Tarif-", "SparteNet-Netz-"
NETZ_ZWECK_AUS = {"wan", "remote-user-vpn", "site-vpn", "vpn-client", "vlan-only"}
TARIF_SICHERUNG = "SparteNet_Sicherung_Tarife_"


def _zahl(x):
    return int(x) if float(x) == int(float(x)) else round(float(x), 1)


def dhcp_bereich(router, praefix, geraete=0):
    """Neues Subnetz und DHCP-Bereich. Router-IP bleibt gleich. Wie am Gateway üblich:
    /24 und größer → DHCP ab .6, kleinere Netze → direkt nach dem Router. geraete = Größe des DHCP-Bereichs (0 = alles)."""
    r = ipaddress.ip_address(router)
    netz = ipaddress.ip_network(f"{router}/{praefix}", strict=False)
    erste, letzte = netz.network_address + 1, netz.broadcast_address - 1
    if not erste <= r <= letzte:
        raise Fehler(f"Router-IP {router} ist in einem /{praefix} nicht möglich.")
    start = max(r + 1, netz.network_address + 6) if praefix <= 24 else r + 1
    if start > letzte:
        raise Fehler(f"Router-IP {router}: in einem /{praefix} bleibt kein Platz für Endgeräte.")
    platz = int(letzte) - int(start) + 1
    stop = letzte
    if geraete:
        if geraete > platz:
            raise Fehler(f"/{praefix} mit Router {router}: Platz für {platz} Endgeräte, der Tarif verlangt {geraete}.")
        stop = start + geraete - 1
    return str(netz), f"{r}/{praefix}", str(start), str(stop), platz


def tarife_pruefen(roh):
    if not isinstance(roh, list) or not roh:
        raise Fehler("Mindestens ein Tarif ist nötig.")
    if len(roh) > 12:
        raise Fehler("Höchstens 12 Tarife.")
    aus, namen = [], set()
    for t in roh:
        name = str((t or {}).get("name") or "").strip()
        if not re.fullmatch(r"[A-Za-z0-9ÄÖÜäöüß .\-_+]{1,24}", name):
            raise Fehler(f"Tarifname „{name}“: 1–24 Zeichen (Buchstaben, Ziffern, Leerzeichen, . - _ +).")
        if name.lower() in namen:
            raise Fehler(f"Tarif „{name}“ gibt es doppelt.")
        namen.add(name.lower())
        try:
            down, up, praefix, geraete = float(t.get("down")), float(t.get("up")), int(t.get("praefix")), int(t.get("geraete") or 0)
        except (TypeError, ValueError):
            raise Fehler(f"Tarif „{name}“: Bandbreite, Netzmaske und Endgeräte müssen Zahlen sein.")
        if not (0.1 <= down <= 10000 and 0.1 <= up <= 10000):
            raise Fehler(f"Tarif „{name}“: Bandbreite zwischen 0,1 und 10000 Mbit/s.")
        if not 24 <= praefix <= 30:
            raise Fehler(f"Tarif „{name}“: Netzmaske /24 bis /30.")
        if geraete < 0:
            raise Fehler(f"Tarif „{name}“: Endgeräte nicht negativ.")
        dhcp_bereich("10.0.0.1", praefix, geraete)  # passt die Anzahl ins Netz?
        roh_preis = t.get("preis")
        if roh_preis in (None, ""):
            roh_preis = next((x["preis"] for x in TARIFE_STANDARD if x["name"].lower() == name.lower()), 0)
        try:
            preis = float(str(roh_preis).replace(",", "."))
        except ValueError:
            raise Fehler(f"Tarif „{name}“: Preis muss eine Zahl sein.")
        if not 0 <= preis <= 100000:
            raise Fehler(f"Tarif „{name}“: Preis 0 bis 100000 € pro Jahr.")
        aus.append({"name": name, "down": _zahl(down), "up": _zahl(up), "praefix": praefix, "geraete": geraete, "preis": _zahl(preis)})
    return aus


def _tarif_netze(g):
    return [n for n in g.legacy("GET", "rest/networkconf") if n.get("ip_subnet") and n.get("purpose") not in NETZ_ZWECK_AUS]


def _qos_regeln(g):
    r = g.v2("GET", "qos-rules")
    return r.get("data", []) if isinstance(r, dict) else (r or [])


def _ist_eigene(r):
    return str(r.get("name", "")).startswith((QOS_TARIF, QOS_NETZ))


def _qos_vorlage(r):
    b = copy.deepcopy(r) if r else {}
    for k in ("_id", "site_id", "index", "wan_or_vpn_network", "attr_hidden", "attr_hidden_id", "attr_no_delete", "attr_no_edit"):
        b.pop(k, None)
    return b


def _qos_soll(name, t, ids, basis=None):
    b = copy.deepcopy(basis) if basis else {}
    b.update({"name": name, "enabled": True, "objective": "LIMIT",
              "download_limit_kbps": int(round(t["down"] * 1000)), "upload_limit_kbps": int(round(t["up"] * 1000)),
              "download_burst": b.get("download_burst") or "OFF", "upload_burst": b.get("upload_burst") or "OFF"})
    b["source"] = {"matching_target": "NETWORK", "network_ids": sorted(ids), "port_matching_type": "ANY"}
    b["destination"] = {"matching_target": "ANY", "port_matching_type": "ANY"}
    b["schedule"] = {"mode": "ALWAYS", "time_all_day": False}
    return b


def _qos_passt(r, soll):
    s, z, sch = r.get("source") or {}, r.get("destination") or {}, r.get("schedule") or {}
    try:
        down, up = int(r.get("download_limit_kbps") or 0), int(r.get("upload_limit_kbps") or 0)
    except (TypeError, ValueError):
        return False
    return (r.get("enabled") is True and r.get("objective") == "LIMIT"
            and down == soll["download_limit_kbps"] and up == soll["upload_limit_kbps"]
            and s.get("matching_target") == "NETWORK" and sorted(s.get("network_ids") or []) == soll["source"]["network_ids"]
            and (z.get("matching_target") or "ANY") == "ANY" and (sch.get("mode") or "ALWAYS") == "ALWAYS")


def _mbit(kbps):
    try:
        return _zahl(int(kbps) / 1000)
    except (TypeError, ValueError):
        return "?"


def _kurz(ip):
    return "." + ip.rsplit(".", 1)[-1] if ip else "?"


def tarif_lage(d):
    tarife = {t["name"]: t for t in tarife_pruefen(d["tarife"])}
    zuord = d.get("tarif_zuordnung") or {}
    modus = d.get("tarif_modus", "tarif")
    g = Gateway(d)
    netze = _tarif_netze(g)
    # Netznamen merken; Parzellen-Zuordnungen in die Buchungen übernehmen (eine gemeinsame Quelle mit der Kalkulation)
    netznamen = {n["_id"]: n.get("name") or "" for n in netze}
    geaendert = netznamen != (d.get("tarif_netznamen") or {})
    for nid, t in list(zuord.items()):
        zp = netz_parzelle(netznamen.get(nid))
        if zp:
            b = d.setdefault("buchungen", {}).setdefault(zp[0], {})
            b.setdefault(str(zp[1]), t)
            zuord.pop(nid); geaendert = True
    if geaendert:
        d["tarif_netznamen"], d["tarif_zuordnung"] = netznamen, zuord
        speichere(d)
    regeln = _qos_regeln(g)
    eigene = [r for r in regeln if _ist_eigene(r)]
    fremde = [r for r in regeln if not _ist_eigene(r)]
    ips = {}
    for quelle, feld in (("stat/sta", "ip"), ("rest/user", "fixed_ip")):
        try:
            for c in g.legacy_roh(quelle):
                if quelle == "rest/user" and not c.get("use_fixedip"):
                    continue
                if c.get(feld) and c.get("network_id"):
                    ips.setdefault(c["network_id"], set()).add(c[feld])
        except Fehler:
            pass
    nach_id = {n["_id"]: n for n in netze}
    in_regel = {}
    for r in regeln:
        for nid in (r.get("source") or {}).get("network_ids") or []:
            in_regel.setdefault(nid, []).append(r)

    zeilen, ops = [], []
    for n in sorted(netze, key=lambda n: (n.get("name") or "").lower()):
        tname = tarif_von_netz(d, n["_id"], n.get("name"))
        t = tarife.get(tname)
        z = {"id": n["_id"], "name": n.get("name") or "?", "vlan": n.get("vlan") or "", "subnetz": n["ip_subnet"],
             "dhcp": f"{n.get('dhcpd_start', '')} – {_kurz(n.get('dhcpd_stop'))}" if n.get("dhcpd_enabled") else "aus",
             "tarif": tname if t else "", "tarif_weg": tname if tname and not t else "",
             "qos": " · ".join(f"{'' if _ist_eigene(r) else '(fremd) '}{r.get('name')}: {_mbit(r.get('download_limit_kbps'))}/{_mbit(r.get('upload_limit_kbps'))}"
                               for r in in_regel.get(n["_id"], [])),
             "status": "ohne", "aenderung": "", "warnung": ""}
        if t:
            router = n["ip_subnet"].split("/")[0]
            try:
                netz, ip_subnet, start, stop, platz = dhcp_bereich(router, t["praefix"], t["geraete"])
                neu_netz = ipaddress.ip_network(netz)
                for m in netze:
                    if m is not n and ipaddress.ip_network(m["ip_subnet"], strict=False).overlaps(neu_netz):
                        raise Fehler(f"{netz} überschneidet sich mit „{m.get('name')}“ ({m['ip_subnet']}).")
                felder, text, warn = {}, [], []
                if n["ip_subnet"] != ip_subnet:
                    felder["ip_subnet"] = ip_subnet
                    text.append(f"Subnetz /{n['ip_subnet'].split('/')[-1]} → /{t['praefix']}")
                if n.get("dhcpd_enabled"):
                    if n.get("dhcpd_start") != start or n.get("dhcpd_stop") != stop:
                        felder.update({"dhcpd_start": start, "dhcpd_stop": stop})
                        text.append(f"DHCP {_kurz(n.get('dhcpd_start'))}–{_kurz(n.get('dhcpd_stop'))} → {_kurz(start)}–{_kurz(stop)}")
                elif t["geraete"]:
                    warn.append("DHCP ist aus – die Geräte-Begrenzung wirkt nur mit DHCP")
                aussen = sorted(ip for ip in ips.get(n["_id"], ()) if ipaddress.ip_address(ip) not in neu_netz)
                if aussen and "ip_subnet" in felder:
                    warn.append(f"{len(aussen)} Gerät(e) mit IP außerhalb des neuen Netzes ({', '.join(aussen[:3])}{' …' if len(aussen) > 3 else ''}) – verlieren die Verbindung bis zur neuen IP")
                if felder:
                    ops.append({"art": "netz", "id": n["_id"], "name": z["name"], "felder": felder,
                                "alt": {k: n.get(k) for k in felder}, "text": " · ".join(text)})
                z.update(status="aendern" if felder else "gleich", aenderung=" · ".join(text) or "passt",
                         warnung=" · ".join(warn), ziel=f"{ip_subnet} · DHCP {_kurz(start)}–{_kurz(stop)} ({int(ipaddress.ip_address(stop)) - int(ipaddress.ip_address(start)) + 1} Geräte)")
            except Fehler as e:
                z.update(status="fehler", aenderung="nicht möglich", warnung=str(e))
        elif tname:
            z["warnung"] = f"Tarif „{tname}“ gibt es nicht mehr – bitte neu zuordnen"
        zeilen.append(z)

    # QoS-Sollzustand
    soll = {}
    for z in zeilen:
        if z["tarif"] and z["status"] != "fehler":
            t = tarife[z["tarif"]]
            if modus == "netz":
                soll[QOS_NETZ + z["name"]] = (t, [z["id"]])
            else:
                soll.setdefault(QOS_TARIF + t["name"], (t, []))[1].append(z["id"])
    vorh = {}
    for r in eigene:
        vorh.setdefault(r["name"], []).append(r)
    vorlage = _qos_vorlage(next(iter(fremde or eigene), None))
    for name, (t, ids) in sorted(soll.items()):
        liste = vorh.pop(name, [])
        limit = f"{t['down']}/{t['up']} Mbit/s"
        anz = f"{len(ids)} Netz{'e' if len(ids) != 1 else ''}"
        if liste:
            b = _qos_soll(name, t, ids, liste[0])
            if not _qos_passt(liste[0], b):
                alt_ids = set((liste[0].get("source") or {}).get("network_ids") or [])
                dazu, weg = len(set(ids) - alt_ids), len(alt_ids - set(ids))
                was = [f"Limit {_mbit(liste[0].get('download_limit_kbps'))}/{_mbit(liste[0].get('upload_limit_kbps'))} → {limit}"] \
                    if _mbit(liste[0].get('download_limit_kbps')) != t["down"] or _mbit(liste[0].get('upload_limit_kbps')) != t["up"] else []
                was += [f"+{dazu} Netz(e)"] * bool(dazu) + [f"−{weg} Netz(e)"] * bool(weg)
                if liste[0].get("enabled") is not True:
                    was.append("wieder einschalten")
                ops.append({"art": "qos_aendern", "id": liste[0]["_id"], "name": name, "body": b,
                            "text": f"{limit} · {anz} · " + (", ".join(was) or "Einstellungen angleichen")})
            for dup in liste[1:]:
                ops.append({"art": "qos_loeschen", "id": dup["_id"], "name": name, "text": "doppelte Regel"})
        else:
            ops.append({"art": "qos_neu", "name": name, "body": _qos_soll(name, t, ids, vorlage), "text": f"{limit} · {anz}"})
    for name, liste in sorted(vorh.items()):
        for r in liste:
            ops.append({"art": "qos_loeschen", "id": r["_id"], "name": name,
                        "text": "kein Netz mehr in diesem Tarif" if name.startswith(QOS_TARIF if modus == "tarif" else QOS_NETZ) else "andere Regel-Art (Modus gewechselt)"})

    zahl = lambda a: sum(1 for o in ops if o["art"] == a)
    mit = sum(1 for z in zeilen if z["tarif"])
    log = [f"{len(netze)} Netze am Gateway · {mit} mit Tarif · {zahl('netz')} Netz(e) zu ändern · QoS: {zahl('qos_neu')} neu, "
           f"{zahl('qos_aendern')} ändern, {zahl('qos_loeschen')} löschen · {len(fremde)} weitere QoS-Regel(n) bleiben unberührt"]
    if any(z["status"] == "fehler" for z in zeilen):
        log.append("⚠ Bei einigen Netzen passt der Tarif nicht – siehe Spalte Hinweis.")
    return {"g": g, "netze": nach_id, "eigene": eigene, "zeilen": zeilen, "ops": ops, "fremde": [r.get("name") for r in fremde], "log": log, "modus": modus}


def akt_tarif_vergleich(d):
    lage = tarif_lage(d)
    return {k: lage[k] for k in ("zeilen", "ops", "fremde", "log", "modus")}


def _tarif_sicherung(netze, eigene):
    pfad = f"{TARIF_SICHERUNG}{time.strftime('%Y%m%d_%H%M%S')}.json"
    ablage_schreiben(pfad, json.dumps({"zeit": time.strftime("%Y-%m-%d %H:%M:%S"),
                                       "netze": [{k: n.get(k) for k in ("_id", "name", "ip_subnet", "dhcpd_start", "dhcpd_stop")} for n in netze],
                                       "regeln": eigene}, ensure_ascii=False, indent=1))
    for x in ablage_liste(TARIF_SICHERUNG, ".json")[:-10]:
        ablage_loeschen(x)
    return pfad


def _qos_ausfuehren(g, op):
    if op["art"] == "qos_neu":
        g.v2("POST", "qos-rules", op["body"])
    elif op["art"] == "qos_aendern":
        g.v2("PUT", f"qos-rules/{op['id']}", op["body"])
    elif op["art"] == "qos_loeschen":
        g.v2("DELETE", f"qos-rules/{op['id']}")


def akt_tarif_uebertragen(d, netze_ids, regeln, ausfuehren):
    lage = tarif_lage(d)
    g, wahl_n, wahl_r = lage["g"], set(netze_ids or []), set(regeln or [])
    ops_q = [o for o in lage["ops"] if o["art"] != "netz" and o["name"] in wahl_r]
    ops_n = [o for o in lage["ops"] if o["art"] == "netz" and o["id"] in wahl_n]
    if not ops_q and not ops_n:
        raise Fehler("Nichts zu übertragen – ausgewählte Einträge sind schon aktuell. Erst „Unterschiede ermitteln“.")
    wort = {"qos_neu": "anlegen", "qos_aendern": "ändern", "qos_loeschen": "löschen"}
    zeilen = [f"QoS-Regel „{o['name']}“ {wort[o['art']]}: {o['text']}" for o in ops_q] + [f"Netz „{o['name']}“: {o['text']}" for o in ops_n]
    if not ausfuehren:
        return {"log": [f"Vorschau – {len(ops_q)} QoS-Regel(n), {len(ops_n)} Netz(e). Am Gateway ändert sich noch nichts:"] + ["  • " + z for z in zeilen]
                + (["", "ℹ Bei verkleinerten Netzen bekommen Geräte mit IP außerhalb des neuen Bereichs kurz keine Verbindung, bis sie eine neue IP haben (WLAN aus/an)."] if ops_n else [])}
    sich = _tarif_sicherung([lage["netze"][o["id"]] for o in ops_n], lage["eigene"])
    erledigt, log = [], []
    try:
        for o in ops_q:
            _qos_ausfuehren(g, o)
            erledigt.append(o)
        for o in ops_n:
            g.legacy("PUT", f"rest/networkconf/{o['id']}", {**lage["netze"][o["id"]], **o["felder"]})
            erledigt.append(o)
    except Fehler as e:
        journal(f"Tarife: abgebrochen nach {len(erledigt)} von {len(ops_q) + len(ops_n)} Schritten – {e} · Sicherung {os.path.basename(sich)}")
        return {"log": [f"✖ Abgebrochen nach {len(erledigt)} von {len(ops_q) + len(ops_n)} Schritten: {e}"]
                + ["  ✔ " + (f"QoS „{o['name']}“" if o["art"] != "netz" else f"Netz „{o['name']}“") for o in erledigt]
                + [f"Sicherung: {os.path.basename(sich)} – mit „Letzte Tarif-Übertragung rückgängig“ zurücksetzen."]}
    time.sleep(1)
    neu = tarif_lage(d)
    offen = {(o["art"] == "netz", o.get("id") if o["art"] == "netz" else o["name"]) for o in neu["ops"]}
    nicht = [o for o in erledigt if (o["art"] == "netz", o["id"] if o["art"] == "netz" else o["name"]) in offen]
    for o in erledigt:
        journal(f"Tarife: {'Netz' if o['art'] == 'netz' else 'QoS'} „{o['name']}“ {'' if o['art'] == 'netz' else wort[o['art']] + ' '}– {o['text']}")
    journal(f"Tarife: {len(erledigt)} Änderung(en) · {'am Gateway bestätigt' if not nicht else str(len(nicht)) + ' NICHT bestätigt'} · Sicherung {os.path.basename(sich)}")
    log.append(f"✔ {len(erledigt)} Änderung(en) übertragen:")
    log += ["  • " + z for z in zeilen]
    log.append("✔ Am Gateway nachgelesen und bestätigt." if not nicht else
               "⚠ Beim Nachlesen weichen ab: " + ", ".join(o["name"] for o in nicht) + " – bitte in der UniFi-Oberfläche prüfen (Einstellungen → Netzwerke bzw. QoS).")
    log.append(f"Sicherung des vorherigen Stands: {os.path.basename(sich)} (für „Rückgängig“). Tipp: in einer Parzelle einen Geschwindigkeitstest machen.")
    return {"log": log}


def akt_tarif_rueckgaengig(d):
    dateien = ablage_liste(TARIF_SICHERUNG, ".json")
    if not dateien:
        raise Fehler("Keine Tarif-Sicherung vorhanden.")
    sich = json.loads(ablage_lesen(dateien[-1]).decode("utf-8"))
    g = Gateway(d)
    netze = {n["_id"]: n for n in _tarif_netze(g)}
    jetzt = {r["_id"]: r for r in _qos_regeln(g) if _ist_eigene(r)}
    alt = {r["_id"]: r for r in sich["regeln"]}
    log, n_netz, n_qos = [], 0, 0
    for r in jetzt.values():
        if r["_id"] not in alt:
            g.v2("DELETE", f"qos-rules/{r['_id']}"); n_qos += 1
    for rid, r in alt.items():
        if rid in jetzt:
            if jetzt[rid] != r:
                g.v2("PUT", f"qos-rules/{rid}", r); n_qos += 1
        else:
            g.v2("POST", "qos-rules", _qos_vorlage(r)); n_qos += 1
    for a in sich["netze"]:
        n = netze.get(a["_id"])
        if not n:
            log.append(f"⚠ Netz „{a['name']}“ gibt es nicht mehr – übersprungen."); continue
        felder = {k: a[k] for k in ("ip_subnet", "dhcpd_start", "dhcpd_stop") if a.get(k) is not None and n.get(k) != a[k]}
        if felder:
            g.legacy("PUT", f"rest/networkconf/{a['_id']}", {**n, **felder}); n_netz += 1
    ablage_umbenennen(dateien[-1], dateien[-1][:-5] + ".zurueckgespielt")
    journal(f"Tarife rückgängig: Stand vom {sich['zeit']} · {n_qos} QoS-Regel(n), {n_netz} Netz(e) zurückgesetzt")
    return {"log": [f"✔ Stand vom {sich['zeit']} wiederhergestellt: {n_qos} QoS-Regel(n), {n_netz} Netz(e)."] + log
            + ["ℹ Die Tarif-Zuordnung im Manager bleibt wie sie ist – „Unterschiede ermitteln“ zeigt die Abweichung."]}


def akt_tarife_speichern(d, b):
    tarife = tarife_pruefen(b.get("tarife"))
    modus = b.get("modus", d.get("tarif_modus", "tarif"))
    if modus not in ("tarif", "netz"):
        raise Fehler("Unbekannter Modus.")
    umben = {}
    for roh_t, t in zip(b["tarife"], tarife):
        alt = str((roh_t or {}).get("alt") or "")
        if alt and alt != t["name"]:
            umben[alt] = t["name"]
    zuord = d.get("tarif_zuordnung") or {}
    d["tarif_zuordnung"] = {k: umben.get(v, v) for k, v in zuord.items()}
    d["buchungen"] = {kz: {pz: umben.get(t, t) for pz, t in b.items()} for kz, b in (d.get("buchungen") or {}).items()}
    d["tarife"], d["tarif_modus"] = tarife, modus
    speichere(d)
    return {"tarife": tarife, "modus": modus, "log": [f"✔ {len(tarife)} Tarife gespeichert"
            + (f" · umbenannt: {', '.join(f'{a} → {n}' for a, n in umben.items())}" if umben else "")
            + f" · Modus: {'eine QoS-Regel je Tarif' if modus == 'tarif' else 'eine QoS-Regel je Netz'}"]}


def akt_tarif_zuordnen(d, aenderungen):
    if not isinstance(aenderungen, dict):
        raise Fehler("Ungültige Zuordnung.")
    namen = {t["name"] for t in tarife_pruefen(d["tarife"])}
    zuord = dict(d.get("tarif_zuordnung") or {})
    netznamen = d.get("tarif_netznamen") or {}
    buch = d.setdefault("buchungen", {})
    for nid, t in aenderungen.items():
        if not re.fullmatch(r"[A-Za-z0-9\-]{1,64}", str(nid)):
            raise Fehler("Ungültige Netz-ID.")
        if t and t not in namen:
            raise Fehler(f"Tarif „{t}“ gibt es nicht.")
        zp = netz_parzelle(netznamen.get(nid))
        if zp:  # Parzelle → Buchung (gilt auch für die Kalkulation)
            zuord.pop(nid, None)
            b = buch.setdefault(zp[0], {})
            if t:
                b[str(zp[1])] = t
            else:
                b.pop(str(zp[1]), None)
        elif not t:
            zuord.pop(nid, None)
        else:
            zuord[nid] = t
    d["buchungen"] = {kz: b for kz, b in buch.items() if b}
    d["tarif_zuordnung"] = zuord
    speichere(d)
    n_buch = sum(len(b) for b in d["buchungen"].values())
    return {"log": [f"✔ Zuordnung gespeichert ({len(aenderungen)} Änderung(en)) – {n_buch} Parzellen gebucht, {len(zuord)} weitere Netze mit Tarif. Die Parzellen-Tarife gelten auch in der Kalkulation."]}


def akt_tarif_erkennen(d):
    """Vorschlag aus dem Ist-Zustand: Netze in SparteNet-QoS-Regeln → deren Tarif; Parzellen-Netze sonst nach Netzmaske (wenn eindeutig)."""
    tarife = tarife_pruefen(d["tarife"])
    nach_name = {t["name"]: t for t in tarife}
    g = Gateway(d)
    netze, regeln = _tarif_netze(g), _qos_regeln(g)
    zuord, vorschlag = d.get("tarif_zuordnung") or {}, {}
    for r in regeln:
        if r.get("name", "").startswith(QOS_TARIF) and r["name"][len(QOS_TARIF):] in nach_name:
            for nid in (r.get("source") or {}).get("network_ids") or []:
                vorschlag[nid] = r["name"][len(QOS_TARIF):]
        elif r.get("name", "").startswith(QOS_NETZ):
            passend = [t["name"] for t in tarife if int(round(t["down"] * 1000)) == r.get("download_limit_kbps") and int(round(t["up"] * 1000)) == r.get("upload_limit_kbps")]
            if len(passend) == 1:
                for nid in (r.get("source") or {}).get("network_ids") or []:
                    vorschlag[nid] = passend[0]
    for n in netze:
        if n["_id"] in vorschlag or "Paz." not in (n.get("name") or ""):
            continue
        p = int(n["ip_subnet"].split("/")[-1])
        passend = [t["name"] for t in tarife if t["praefix"] == p]
        if len(passend) == 1:
            vorschlag[n["_id"]] = passend[0]
    neu = {k: v for k, v in vorschlag.items() if not tarif_von_netz(d, k, next((n.get("name") for n in netze if n["_id"] == k), ""))}
    return {"vorschlag": neu, "log": [f"Vorschlag für {len(neu)} Netz(e) ohne Tarif (bestehende Zuordnungen bleiben). Übernehmen = in der Tabelle eingetragen, dann „Speichern“."]}


# =============================================================== Handy & Tablet (Web-App, Passwort und optionale PIN)
SITZUNG_TAGE = 30
_SPERRE = {"fehl": 0, "bis": 0.0}
_SPERRE_LOCK = threading.Lock()
_AUTH_SESSIONS = {}
_AUTH_SESSIONS_LOCK = threading.Lock()
_AUTH_LOCKS = {}
_AUTH_SPERRE_LOCK = threading.Lock()
SERVER_HOST = "127.0.0.1"


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


def auth_sitzung_neu(geraet):
    jetzt = time.time()
    with _AUTH_SESSIONS_LOCK:
        for k, sitzung in list(_AUTH_SESSIONS.items()):
            if sitzung["bis"] <= jetzt:
                del _AUTH_SESSIONS[k]
        while len(_AUTH_SESSIONS) >= 200:
            del _AUTH_SESSIONS[min(_AUTH_SESSIONS, key=lambda k: _AUTH_SESSIONS[k]["bis"])]
        t = secrets.token_urlsafe(32)
        _AUTH_SESSIONS[_sitzung_hash(t)] = {
            "bis": jetzt + SITZUNG_TAGE * 86400,
            "geraet": str(geraet or "Browser")[:80],
            "seit": time.strftime("%Y-%m-%d %H:%M"),
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


def auth_sitzung_entfernen(t):
    if t:
        with _AUTH_SESSIONS_LOCK:
            _AUTH_SESSIONS.pop(_sitzung_hash(t), None)


def lan_adressen():
    ips = set()
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("192.0.2.1", 9))  # sendet nichts, ermittelt nur die eigene Adresse
        ips.add(s.getsockname()[0]); s.close()
    except OSError:
        pass
    try:
        ips.update(a[4][0] for a in socket.getaddrinfo(socket.gethostname(), None, socket.AF_INET))
    except OSError:
        pass
    return sorted(i for i in ips if not i.startswith(("127.", "169.254.")))


def _tailscale_exe():
    exe = shutil.which("tailscale")
    if not exe and os.name == "nt":
        for p in (r"C:\Program Files\Tailscale\tailscale.exe", r"C:\Program Files (x86)\Tailscale\tailscale.exe"):
            if os.path.exists(p):
                return p
    if not exe and sys.platform == "darwin" and os.path.exists("/Applications/Tailscale.app/Contents/MacOS/Tailscale"):
        return "/Applications/Tailscale.app/Contents/MacOS/Tailscale"
    return exe


def tailscale_lage():
    exe = _tailscale_exe()
    if not exe:
        return {"installiert": False}
    try:
        r = subprocess.run([exe, "status", "--json"], capture_output=True, text=True, timeout=8)
        st = json.loads(r.stdout or "{}")
    except (OSError, ValueError, subprocess.TimeoutExpired) as e:
        return {"installiert": True, "aktiv": False, "fehler": str(e)[:200]}
    dns = ((st.get("Self") or {}).get("DNSName") or "").rstrip(".")
    freigabe = False
    try:
        s = subprocess.run([exe, "serve", "status", "--json"], capture_output=True, text=True, timeout=8)
        freigabe = f"127.0.0.1:{PORT}" in s.stdout or f"localhost:{PORT}" in s.stdout
    except (OSError, subprocess.TimeoutExpired):
        pass
    return {"installiert": True, "aktiv": st.get("BackendState") == "Running", "name": dns,
            "url": f"https://{dns}/" if dns else "", "freigabe": freigabe}


def akt_tailscale(an):
    exe = _tailscale_exe()
    if not exe:
        raise Fehler("Tailscale ist auf diesem PC nicht installiert (tailscale.com/download).")
    befehl = [exe, "serve", "--bg", f"http://127.0.0.1:{PORT}"] if an else [exe, "serve", "--https=443", "off"]
    try:
        r = subprocess.run(befehl, capture_output=True, text=True, timeout=25)
    except subprocess.TimeoutExpired:
        raise Fehler("Tailscale antwortet nicht. Evtl. muss HTTPS im Tailscale-Konto erst erlaubt werden: login.tailscale.com → DNS → „HTTPS Certificates“ aktivieren, dann erneut.")
    except OSError as e:
        raise Fehler(f"Tailscale konnte nicht gestartet werden: {e}")
    text = (r.stdout + "\n" + r.stderr).strip()
    journal(f"Tailscale-Freigabe {'eingeschaltet' if an else 'ausgeschaltet'} (Rückgabe {r.returncode})")
    if r.returncode != 0:
        hilfe = ""
        if "denied" in text.lower() or "operator" in text.lower() or "permission" in text.lower():
            hilfe = "\nLinux: einmal im Terminal „sudo tailscale set --operator=$USER“ ausführen, dann erneut."
        raise Fehler(f"Tailscale meldet einen Fehler:\n{text[:600]}{hilfe}")
    lage = tailscale_lage()
    return {"log": [f"✔ Tailscale-Freigabe {'eingeschaltet' if an else 'ausgeschaltet'}."] + ([text[:600]] if text else [])
            + ([f"App-Adresse: {lage['url']}"] if an and lage.get("url") else []), "tailscale": lage}


def akt_fern(d):
    f = fern_daten(d)
    adressen = [f"http://{ip}:{PORT}/" for ip in lan_adressen()] if SERVER_HOST == "0.0.0.0" else []
    ts = tailscale_lage()
    urls = ([ts["url"]] if ts.get("freigabe") and ts.get("url") else []) + adressen
    jetzt = time.time()
    geraete = [{"geraet": v.get("geraet") or "?", "seit": v.get("seit", "")} for v in f["sitzungen"].values() if isinstance(v, dict) and v.get("bis", 0) > jetzt]
    with _AUTH_SESSIONS_LOCK:
        geraete.extend({"geraet": v["geraet"], "seit": v["seit"]} for v in _AUTH_SESSIONS.values() if v["bis"] > jetzt)
    return {"lan": SERVER_HOST == "0.0.0.0", "lan_aktiv": SERVER_HOST == "0.0.0.0", "lan_env": HOST_OVERRIDE is not None, "pin_gesetzt": bool(f["pin"].get("hash")), "geraete": geraete,
            "adressen": adressen, "tailscale": ts, "qr": {u: qr_svg(u, rand=2) for u in urls}}


def akt_fern_speichern(d, b):
    f, log = fern_daten(d), []
    if b.get("pin"):
        pin_setzen(d, b["pin"]); log.append("✔ PIN gespeichert. Bereits angemeldete Handys müssen sich neu anmelden.")
    if b.get("abmelden"):
        f["sitzungen"] = {}
        with _AUTH_SESSIONS_LOCK:
            _AUTH_SESSIONS.clear()
        log.append("✔ Alle Handys, Tablets und Browser abgemeldet.")
    if "lan" in b:
        if HOST_OVERRIDE is not None:
            raise Fehler("Die Server-Bindung wird durch SPARTENET_HOST gesteuert; Heimnetz hier nicht umschaltbar.")
        f["lan"] = bool(b["lan"])
        if f["lan"] != (SERVER_HOST == "0.0.0.0"):
            log.append(f"✔ Zugriff aus dem Heimnetz {'ein' if f['lan'] else 'aus'}geschaltet – wirkt nach einem Neustart des Managers (Beenden und wieder starten)."
                       + (" Windows fragt dann evtl. nach der Firewall: „Private Netzwerke“ erlauben." if f["lan"] and os.name == "nt" else ""))
        else:
            log.append(f"✔ Zugriff aus dem Heimnetz bleibt {'ein' if f['lan'] else 'aus'}.")
    speichere(d)
    journal("Handy-Zugriff geändert: " + ", ".join(k for k in ("pin", "abmelden", "lan") if k in b))
    return {"log": log or ["Nichts geändert."]}


def akt_start(d):
    g = Gateway(d)
    erg = _parallel({"geraete": lambda: g.alle("/v1/sites/{site}/devices"), "clients": lambda: g.alle("/v1/sites/{site}/clients"),
                     "health": lambda: g.legacy_roh("stat/health")}, anzahl=3)
    geraete, fehler = erg["geraete"]
    if fehler:
        raise Fehler(fehler)
    clients = erg["clients"][0] or []
    health = {h.get("subsystem"): h for h in (erg["health"][0] or [])}
    online = [x for x in geraete if str(x.get("state", "")).upper() == "ONLINE"]
    offline = [x.get("name") or x.get("model") or "?" for x in geraete if x not in online]
    wan, www = health.get("wan") or {}, health.get("www") or {}
    kacheln = [
        {"t": "Geräte online", "v": f"{len(online)}/{len(geraete)}", "a": "gut" if not offline else "schlecht", "k": ("offline: " + ", ".join(offline)) if offline else "alle erreichbar"},
        {"t": "Endgeräte im WLAN/LAN", "v": len(clients), "a": "gut", "k": f"{sum(1 for c in clients if c.get('type') == 'WIRELESS')} per WLAN"},
    ]
    if wan or www:
        kacheln.append({"t": "Internet", "v": "online" if (wan.get("status") or www.get("status", "ok")) == "ok" else "gestört",
                        "a": "gut" if (wan.get("status") or "ok") == "ok" else "schlecht",
                        "k": " · ".join(x for x in (wan.get("isp_name") or "", f"{www.get('latency')} ms" if www.get("latency") is not None else "") if x)})
    try:
        kg = akt_kalkulation(d)["gesamt"]
        if kg["parzellen_konf"]:
            kacheln.append({"t": "Auslastung", "v": f"{kg['auslastung_konf']:.0%}", "a": "gut" if kg["auslastung_konf"] >= 0.6 else "", "k": f"{kg['gebucht']} von {kg['parzellen_konf']} Parzellen gebucht"})
    except Fehler:
        pass
    return {"kacheln": kacheln, "konsole": d.get("konsole_name", ""), "zeit": time.strftime("%H:%M"), "log": []}


def akt_parzelle(d, kz, p):
    try:
        p = int(p)
    except (TypeError, ValueError):
        raise Fehler("Bitte eine Parzellen-Nummer eingeben.")
    plan = plan_berechnen(d["plan"])
    sp = next((s for s in plan["sparten"] if s["kz"] == kz), None)
    if not sp:
        raise Fehler("Sparte nicht im Plan.")
    if not 1 <= p <= sp["n"]:
        raise Fehler(f"Sparte {kz} hat die Parzellen 1 bis {sp['n']}.")
    netz = next((n for n in plan["netze"] if n["sparte"] == kz and str(n.get("parzelle", "")) == str(p)), None) \
        or next((n for n in plan["netze"] if n["sparte"] == kz and n["name"] == NETZ_PARZELLE.format(kz=kz, p=p)), None)
    zeile = next((z for z in lese_ppsk(kz) if str(z.get("Parzelle")) == str(p)), None)
    if not zeile or not zeile.get("Passwort"):
        raise Fehler(f"Für Parzelle {p} ist noch kein WLAN-Passwort vergeben (Einrichten → Schritt 3) oder der Zugang ist gesperrt.")
    ssid = zeile.get("WLAN") or ""
    return {"parzelle": p, "sparte": sp["name"], "netz": zeile.get("Netz") or (netz or {}).get("name", ""), "vlan": zeile.get("VLAN") or (netz or {}).get("vlan", ""),
            "subnetz": (netz or {}).get("netz", ""), "wlan": ssid, "passwort": zeile["Passwort"],
            "qr": qr_svg(wlan_qr_text(ssid, zeile["Passwort"]), rand=2), "log": []}


def _b64(s):
    return base64.b64decode(s)


PWA_ICONS = {
    '/icon-192.png': (_b64('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'), "image/png"),
    '/icon-512.png': (_b64('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'), "image/png"),
    '/icon-maskable.png': (_b64('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'), "image/png"),
    '/apple-touch-icon.png': (_b64('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'), "image/png"),
    '/favicon.png': (_b64('iVBORw0KGgoAAAANSUhEUgAAACAAAAAgCAMAAABEpIrGAAABgFBMVEX///////7+//7+//3+/v7+/v39/v39/vz9/f38/vv8/f38/fv7/fr8/P37/Pz7/Pv4/vX6/Pr5/Pj5+/n4+fn2+vX09/Tw+O3r9+Ts9ejr8ujm8uHk8OHi793Y6dHV4tTN5cXK473F4rXG37zB3bfB27283K653Kq32Ke12aWx2ZrD1MCy1qmv1J6n04yl0JGxy6ajzJqxvLqhz4qf0X2dzIyayYiWw4iSzmuGx1yMxmqNxHJ4xEWVvoqHvXmCvmaBuXJ8vGB2uVtzv0CwtL6ksqumq7SiqrCepqufoq+Wpp6WnKV8tm13tmBytlRntUlusFaDp4FqrVRkr0RdsDtgsDVbqzhaqDxQqSJLphpHphpKpRpVoTtOnDNLoiBHnxpCoBlDnBs/mhiQl6CJlZeKkJ2BjJR/iJJ5g4x0f4hweodDmCA+lxk4mBgzlxg/kyg2kxlSglNjbnpfanlcaHVVX3JNWmhMWGlFVWBAUFw8SF4tP08kOEkjNkYiNUUfL0OavpwhAAAB1ElEQVR42mNgGHaAhYFL3T8uOjrURAKbLAsbk2JohLW6opJxaKS+EBuaPDsDAyeDn5WUmn2Qk760ZqgkAxOKPBODID9QkXhYrLWuaXCiMtA6FMDDoBkaqsbALqkpp+9jLqcmx8CKZr50ZHRkvCzQILNw84AgBjQDmBiUHKPj4+MjNJiEeGX8FUBiHCj61aLiExOTkhJiBTkYxMNt3Uu8GRj4EIZwM9gnZCcl5OTkZAswGKWX19dmlJTJI5nAzWCelBMbkJ2bG6JdWltTl+FWlOpdkSYGcwgLg3BsQUGQhqmPb3JVsWuqS1ZdTW2Fe1GZGAtUBRN7TG5ejE+Cr7iLl4VBsXdtdWZRWZ2RvAjMCjZBGTsfH7uCggDpsAiv+uTaShePtBoPBi6oPB9DqneqZ7JaXmx+QIFjUR1UgTsHH1xBRkVlRVWqQ76tjqFRaalbVWVWSVmNBxNCQWZGkbe3m6yGrpaWnp6JiYl5YFpWqQuDIDS4hRmSPV3Nff3D/f3srU1MLCydgcDGSlcClATAKkQNA4J89ZWlReEhIyarpGfpZ60AiUhVBzMFqI8YWZnZ2ZkZIRwhBX1dKSAtrwrSyc7NzgZPISxMrOycwBTEIC4zTDITAIRdYFZa9jZpAAAAAElFTkSuQmCC'), "image/png"),
}

MANIFEST = {
    "name": "SparteNet Manager", "short_name": "SparteNet", "description": "WLAN der Gartensparten verwalten",
    "id": "/", "start_url": "/#start", "scope": "/", "display": "standalone", "orientation": "any", "lang": "de",
    "background_color": "#f5f7f4", "theme_color": "#1d2f3e",
    "icons": [{"src": "/icon-192.png", "sizes": "192x192", "type": "image/png", "purpose": "any"},
              {"src": "/icon-512.png", "sizes": "512x512", "type": "image/png", "purpose": "any"},
              {"src": "/icon-maskable.png", "sizes": "512x512", "type": "image/png", "purpose": "maskable"}],
    "shortcuts": [{"name": "Parzelle nachschlagen", "url": "/#start", "icons": [{"src": "/icon-192.png", "sizes": "192x192"}]},
                  {"name": "Gast-Voucher", "url": "/#voucher", "icons": [{"src": "/icon-192.png", "sizes": "192x192"}]},
                  {"name": "Tarife", "url": "/#tarife", "icons": [{"src": "/icon-192.png", "sizes": "192x192"}]},
                  {"name": "Systeminfo", "url": "/#system", "icons": [{"src": "/icon-192.png", "sizes": "192x192"}]}],
}

SW_JS = r"""const V="spartenet-__VERSION__";
self.addEventListener("install",e=>{e.waitUntil(caches.open(V).then(c=>c.addAll(["/offline.html","/icon-192.png","/icon-512.png","/favicon.png"])));self.skipWaiting()});
self.addEventListener("activate",e=>{e.waitUntil(caches.keys().then(k=>Promise.all(k.filter(x=>x!==V).map(x=>caches.delete(x)))).then(()=>self.clients.claim()))});
self.addEventListener("fetch",e=>{const r=e.request,u=new URL(r.url);if(r.method!=="GET"||u.origin!==location.origin)return;
 if(r.mode==="navigate"){e.respondWith(fetch(r).catch(()=>caches.match("/offline.html")));return}
 if(/\.png$/.test(u.pathname)){e.respondWith(caches.match(r).then(a=>a||fetch(r)))}});
"""

OFFLINE_HTML = """<!doctype html><html lang="de"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<meta name="theme-color" content="#1d2f3e"><title>SparteNet – keine Verbindung</title><style>
body{margin:0;font-family:system-ui,Roboto,Arial,sans-serif;background:#f5f7f4;color:#1d2f3e;display:grid;place-items:center;min-height:100vh;padding:20px;box-sizing:border-box}
.k{background:#fff;border:1px solid #d9e0d6;border-radius:14px;padding:26px;max-width:420px;text-align:center}img{width:96px}h1{font-size:20px}p{color:#5d6b75;font-size:15px;line-height:1.45;text-align:left}
button{background:#3a9a1f;color:#fff;border:0;border-radius:8px;padding:13px 22px;font-size:16px;margin-top:8px}</style></head><body><div class="k">
<img src="/icon-192.png" alt=""><h1>PC mit dem SparteNet Manager nicht erreichbar</h1>
<p>• Läuft der Manager auf dem PC? (Fenster offen lassen)<br>• Im Heimnetz: Ist das Handy im selben WLAN wie der PC?<br>• Unterwegs: Ist Tailscale auf Handy und PC eingeschaltet?</p>
<button onclick="location.reload()">Erneut versuchen</button></div></body></html>"""

LOGIN_HTML = """<!doctype html><html lang="de"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>SparteNet Manager – Anmelden</title><meta name="theme-color" content="#1d2f3e"><link rel="manifest" href="/manifest.webmanifest">
<link rel="icon" href="/favicon.png"><link rel="apple-touch-icon" href="/apple-touch-icon.png"><meta name="apple-mobile-web-app-capable" content="yes"><meta name="mobile-web-app-capable" content="yes"><meta name="apple-mobile-web-app-title" content="SparteNet">
<style>body{margin:0;font-family:system-ui,Roboto,Arial,sans-serif;background:#1d2f3e;color:#1d2f3e;display:grid;place-items:center;min-height:100vh;padding:20px;box-sizing:border-box}
.k{background:#fff;border-radius:16px;padding:28px 24px;width:100%;max-width:380px;text-align:center;box-shadow:0 12px 40px rgba(0,0,0,.3)}img{width:110px}h1{font-size:21px;margin:8px 0 4px}h1 span{color:#3a9a1f}
p{color:#5d6b75;font-size:14px;margin:4px 0 18px}input{width:100%;box-sizing:border-box;font-size:22px;letter-spacing:4px;text-align:center;padding:13px;border:1px solid #d9e0d6;border-radius:10px}
button{width:100%;background:#3a9a1f;color:#fff;border:0;border-radius:10px;padding:14px;font-size:17px;margin-top:12px;font-weight:600}button:disabled{opacity:.6}
.f{color:#b42318;font-size:14px;min-height:20px;margin-top:10px}</style></head><body><div class="k">
<img src="/icon-192.png" alt=""><h1>Sparte<span>Net</span> Manager</h1>
__INHALT__
</div><script>
if("serviceWorker" in navigator&&isSecureContext)navigator.serviceWorker.register("/sw.js").catch(()=>{});
async function an(e){e.preventDefault();const b=document.getElementById("b"),f=document.getElementById("f");b.disabled=true;f.textContent="";
 try{const r=await fetch("/login",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({passwort:document.getElementById("passwort").value,geraet:navigator.userAgent})});
  const d=await r.json();if(!r.ok)throw new Error(d.fehler||r.status);location.reload()}catch(x){f.textContent=x.message;b.disabled=false;document.getElementById("passwort").select()}}
</script></body></html>"""

LOGIN_FORM = """<p>Bitte das Manager-Passwort eingeben. Auf entfernten Handys funktioniert auch die eingerichtete Handy-PIN.</p>
<form onsubmit="an(event)"><input id="passwort" type="password" autocomplete="current-password" placeholder="Passwort" autofocus required>
<button id="b">Anmelden</button><div class="f" id="f"></div></form>"""


# =============================================================== Kalkulation (Buchungen, Umsatz, Auslastung, Wirtschaftlichkeit)
KALK_STANDARD = {
    "kleinunternehmer": True, "ust": 19.0, "preise_inkl_ust": True,
    "uplink_monat": 75.0, "strom_mast": 50.0, "strom_hv": 80.0, "zahlung_pct": 3.0, "wartung_pct": 3.0,
    "zentral_start_technik": 1200.0, "zentral_start_personal": 0.0, "zentral_start_sonstiges": 1500.0,
    "zentral_voll_technik": 36000.0, "zentral_voll_personal": 60000.0, "zentral_voll_sonstiges": 15000.0,
    "phase": "auto", "abschreibung_jahre": 5.0, "ueberbuchung": 8.0,
    "ku_grenze_vorjahr": 25000.0, "ku_grenze_lfd": 100000.0, "quote_prognose": 60.0,
}
KALK_TEXTE = {
    "kleinunternehmer": "Kleinunternehmer (§ 19 UStG)", "ust": "Umsatzsteuersatz (%)", "preise_inkl_ust": "Regelbesteuerung: Tarifpreise enthalten MwSt.",
    "uplink_monat": "Uplink je Sparte und Monat (€, netto)", "strom_mast": "Strom je Mast mit Technik und Jahr (€)", "strom_hv": "Strom Hauptverteiler je Sparte und Jahr (€)",
    "zahlung_pct": "Zahlungsabwicklung (% vom Umsatz)", "wartung_pct": "Wartung/Ersatzteile (% der Investition je Jahr)",
    "zentral_start_technik": "Startphase: zentrale Technik (€/Jahr)", "zentral_start_personal": "Startphase: Personal (€/Jahr)", "zentral_start_sonstiges": "Startphase: Versicherung, Steuerberatung (€/Jahr)",
    "zentral_voll_technik": "Ausbau: zentrale Technik (€/Jahr)", "zentral_voll_personal": "Ausbau: Personal (€/Jahr)", "zentral_voll_sonstiges": "Ausbau: Versicherung, Steuerberatung, Recht (€/Jahr)",
    "phase": "Zentrale Kosten", "abschreibung_jahre": "Abschreibungsdauer Hardware (Jahre)", "ueberbuchung": "Überbuchungsfaktor (1:x) für den Uplink",
    "ku_grenze_vorjahr": "Umsatzgrenze Kleinunternehmer Vorjahr (€)", "ku_grenze_lfd": "Umsatzgrenze laufendes Jahr (€)", "quote_prognose": "Buchungsquote für Prognose (%)",
}
PAZ_RE = re.compile(r"^(.+)-Paz\.(\d{1,3})$")


def netz_parzelle(name):
    m = PAZ_RE.match(str(name or ""))
    return (m.group(1), int(m.group(2))) if m else None


def tarif_von_netz(d, nid, name):
    """Tarif eines Netzes: bei Parzellen-Netzen aus den Buchungen, sonst aus der Netz-Zuordnung"""
    zp = netz_parzelle(name)
    if zp:
        t = ((d.get("buchungen") or {}).get(zp[0]) or {}).get(str(zp[1]))
        if t:
            return t
    return (d.get("tarif_zuordnung") or {}).get(nid, "")


def kalk_annahmen(d):
    roh = ((d.get("kalk") or {}).get("annahmen")) or {}
    a = dict(KALK_STANDARD)
    for k, std in KALK_STANDARD.items():
        if k not in roh:
            continue
        v = roh[k]
        if isinstance(std, bool):
            a[k] = bool(v)
        elif k == "phase":
            a[k] = v if v in ("auto", "start", "voll") else "auto"
        else:
            try:
                a[k] = max(0.0, float(v))
            except (TypeError, ValueError):
                raise Fehler(f"„{KALK_TEXTE.get(k, k)}“ muss eine Zahl sein.")
    if a["abschreibung_jahre"] < 1 or a["ueberbuchung"] < 1:
        raise Fehler("Abschreibungsdauer und Überbuchungsfaktor müssen mindestens 1 sein.")
    if a["quote_prognose"] > 100:
        raise Fehler("Buchungsquote höchstens 100 %.")
    return a


def kalk_sparten(d):
    """Alle eingetragenen Sparten: aus der Planung (aktives Gateway) und aus dem VLAN-Planer übernommene"""
    k = d.get("kalk") or {}
    extra = k.get("sparten") or {}
    aus = {}
    try:
        plan = plan_berechnen(d["plan"])
        for s in plan["sparten"]:
            aus[s["kz"]] = {"kz": s["kz"], "name": s["name"], "n": s["n"], "gateway": plan["gateway"], "quelle": "Planung"}
    except Fehler:
        pass
    for kz, s in extra.items():
        if kz in aus:
            continue
        try:
            n = int(s.get("n") or 0)
        except (TypeError, ValueError):
            n = 0
        if s.get("name") and n > 0:
            aus[kz] = {"kz": kz, "name": s["name"], "n": n, "gateway": s.get("gateway") or "", "quelle": s.get("quelle", "VLAN-Planer")}
    for kz, s in aus.items():
        w = extra.get(kz) or {}
        s["investition"] = w.get("investition")
        s["masten"] = w.get("masten")
        s["uplink"] = w.get("uplink")
    return aus


def _zahl_oder_none(v, text):
    if v in (None, ""):
        return None
    try:
        x = float(str(v).replace(",", "."))
    except ValueError:
        raise Fehler(f"{text}: bitte eine Zahl eintragen.")
    if x < 0:
        raise Fehler(f"{text}: nicht negativ.")
    return x


def akt_kalkulation(d, prognose=False):
    a = kalk_annahmen(d)
    tarife = tarife_pruefen(d["tarife"])
    preis = {t["name"]: float(t.get("preis") or 0) for t in tarife}
    down = {t["name"]: float(t.get("down") or 0) for t in tarife}
    ku = a["kleinunternehmer"]
    ek = 1 + a["ust"] / 100 if ku else 1.0  # Einkauf ohne Vorsteuerabzug = brutto
    netto = (lambda p: p) if ku else ((lambda p: p / (1 + a["ust"] / 100)) if a["preise_inkl_ust"] else (lambda p: p))
    oe = sum(preis.values()) / len(preis) if preis else 0
    buch = d.get("buchungen") or {}
    zeilen, unbekannt = [], 0
    for kz, s in sorted(kalk_sparten(d).items(), key=lambda x: (str(x[1]["gateway"]), x[1]["name"].lower())):
        b = buch.get(kz) or {}
        je = {t["name"]: 0 for t in tarife}
        for p, t in b.items():
            if p.isdigit() and 1 <= int(p) <= s["n"]:
                if t in je:
                    je[t] += 1
                else:
                    unbekannt += 1
        gebucht = sum(je.values())
        umsatz_b = sum(je[t] * preis[t] for t in je)
        umsatz = sum(je[t] * netto(preis[t]) for t in je)
        uplink_bedarf = sum(je[t] * down[t] for t in je) / a["ueberbuchung"]
        status = "konfiguriert" if gebucht else "eingetragen"
        prog = False
        if not gebucht and prognose and a["quote_prognose"] > 0:
            # Prognose: Buchungsquote × Parzellen, Tarifmix wie im Durchschnitt der Tarifpreise
            gebucht_p = round(s["n"] * a["quote_prognose"] / 100)
            umsatz_b = gebucht_p * oe
            umsatz = gebucht_p * netto(oe)
            uplink_bedarf = gebucht_p * (sum(down.values()) / len(down) if down else 0) / a["ueberbuchung"]
            prog, status = gebucht_p, "Prognose"
        inv = float(s["investition"] or 0)
        masten = float(s["masten"] or 0)
        uplink = s["uplink"] if s["uplink"] is not None else a["uplink_monat"]
        in_betrieb = bool(gebucht or prog or inv)
        kosten = ((uplink * 12 + masten * a["strom_mast"] + a["strom_hv"]) * ek + umsatz * a["zahlung_pct"] / 100 + inv * a["wartung_pct"] / 100) if in_betrieb else 0.0
        db = umsatz - kosten
        zeilen.append({
            "kz": kz, "name": s["name"], "gateway": s["gateway"], "quelle": s["quelle"], "n": s["n"], "gebucht": gebucht, "prognose": prog or 0,
            "rate": gebucht / s["n"] if s["n"] else 0, "je": je, "umsatz_brutto": round(umsatz_b, 2), "umsatz": round(umsatz, 2),
            "erloes_monat": round(umsatz_b / gebucht / 12, 2) if gebucht else (round(oe / 12, 2) if prog else 0),
            "investition": s["investition"], "masten": s["masten"], "uplink": s["uplink"], "kosten": round(kosten, 2), "db": round(db, 2),
            "amortisation": round(inv / db, 1) if inv and db > 0 else ("nie" if inv and db <= 0 else None),
            "uplink_bedarf": round(uplink_bedarf), "uplink_warnung": uplink_bedarf > 900, "status": status})
    konf = [z for z in zeilen if z["status"] == "konfiguriert"]
    summe = lambda liste, k: round(sum(float(z[k] or 0) for z in liste), 2)
    parz_konf, geb = sum(z["n"] for z in konf), sum(z["gebucht"] for z in konf)
    parz_alle = sum(z["n"] for z in zeilen)
    phase = a["phase"] if a["phase"] != "auto" else ("start" if ku else "voll")
    zentral = sum(a[f"zentral_{phase}_{x}"] for x in ("technik", "personal", "sonstiges"))
    zentral_ek = (a[f"zentral_{phase}_technik"] + a[f"zentral_{phase}_sonstiges"]) * ek + a[f"zentral_{phase}_personal"]
    umsatz_ges, db_ges, inv_ges = summe(zeilen, "umsatz"), summe(zeilen, "db"), summe(zeilen, "investition")
    afa = inv_ges / a["abschreibung_jahre"]
    ergebnis_vor = db_ges - zentral_ek
    umsatz_brutto_ges = summe(zeilen, "umsatz_brutto")
    oe_buchung = umsatz_brutto_ges / max(1, geb + sum(z["prognose"] for z in zeilen)) if umsatz_brutto_ges else oe
    gesamt = {
        "sparten": len(zeilen), "sparten_konf": len(konf), "parzellen_alle": parz_alle, "parzellen_konf": parz_konf, "gebucht": geb,
        "auslastung_konf": geb / parz_konf if parz_konf else 0, "auslastung_alle": geb / parz_alle if parz_alle else 0,
        "je": {t["name"]: sum(z["je"][t["name"]] for z in zeilen) for t in tarife},
        "umsatz_brutto": umsatz_brutto_ges, "umsatz": umsatz_ges, "kosten": summe(zeilen, "kosten"), "db": db_ges, "investition": inv_ges,
        "zentral": round(zentral_ek, 2), "phase": phase, "ergebnis_vor_afa": round(ergebnis_vor, 2), "afa": round(afa, 2), "ergebnis": round(ergebnis_vor - afa, 2),
        "amortisation": round(inv_ges / ergebnis_vor, 1) if inv_ges and ergebnis_vor > 0 else ("nicht erreicht" if inv_ges else None),
        "ku": ku, "ku_grenze": a["ku_grenze_vorjahr"], "ku_status": ("unter der Grenze" if umsatz_brutto_ges <= a["ku_grenze_vorjahr"] else "Grenze überschritten → ab Folgejahr Regelbesteuerung") if ku else "Regelbesteuerung",
        "ku_rest_parzellen": int(max(0, a["ku_grenze_vorjahr"] - umsatz_brutto_ges) // oe_buchung) if ku and oe_buchung else None,
    }
    log = [f"{len(zeilen)} Sparten eingetragen, davon {len(konf)} mit Buchungen · {geb} von {parz_konf} Parzellen gebucht ({gesamt['auslastung_konf']:.1%})"]
    if unbekannt:
        log.append(f"⚠ {unbekannt} Buchung(en) mit einem Tarif, den es nicht mehr gibt – im Bereich „Buchungen erfassen“ neu zuordnen.")
    if any(z["uplink_warnung"] for z in zeilen):
        log.append("⚠ Bei mindestens einer Sparte reicht 1 Gbit/s Uplink rechnerisch nicht (Spalte Uplink-Bedarf).")
    return {"zeilen": zeilen, "gesamt": gesamt, "tarife": [{"name": t["name"], "preis": t.get("preis", 0), "down": t["down"]} for t in tarife],
            "annahmen": a, "texte": KALK_TEXTE, "log": log}


def akt_kalk_annahmen(d, b):
    k = d.setdefault("kalk", {})
    alt = k.get("annahmen") or {}
    k["annahmen"] = {**alt, **{x: b[x] for x in KALK_STANDARD if x in b}}
    try:
        kalk_annahmen(d)
    except Fehler:
        k["annahmen"] = alt
        raise
    speichere(d)
    return {"log": ["✔ Annahmen gespeichert."]}


def akt_kalk_sparte(d, b):
    """Investition, Masten mit Technik und Uplink je Sparte speichern"""
    kz = str(b.get("sparte") or "")
    if kz not in kalk_sparten(d):
        raise Fehler("Sparte unbekannt.")
    k = d.setdefault("kalk", {})
    s = k.setdefault("sparten", {}).setdefault(kz, {})
    for feld, text in (("investition", "Investition"), ("masten", "Masten mit Technik"), ("uplink", "Uplink €/Monat")):
        if feld in b:
            s[feld] = _zahl_oder_none(b[feld], text)
    speichere(d)
    return {"log": [f"✔ {kz} gespeichert."]}


def akt_buchungen(d, kz):
    sp = kalk_sparten(d).get(kz)
    if not sp:
        raise Fehler("Sparte unbekannt.")
    b = (d.get("buchungen") or {}).get(kz) or {}
    namen = {t["name"] for t in tarife_pruefen(d["tarife"])}
    return {"sparte": sp["name"], "kz": kz, "n": sp["n"],
            "zeilen": [{"p": p, "netz": NETZ_PARZELLE.format(kz=kz, p=p), "tarif": b.get(str(p), ""), "unbekannt": bool(b.get(str(p))) and b.get(str(p)) not in namen}
                       for p in range(1, sp["n"] + 1)], "log": []}


def akt_buchungen_speichern(d, kz, aenderungen):
    sp = kalk_sparten(d).get(kz)
    if not sp or not isinstance(aenderungen, dict):
        raise Fehler("Sparte unbekannt oder ungültige Angaben.")
    namen = {t["name"] for t in tarife_pruefen(d["tarife"])}
    b = d.setdefault("buchungen", {}).setdefault(kz, {})
    for p, t in aenderungen.items():
        if not str(p).isdigit() or not 1 <= int(p) <= sp["n"]:
            raise Fehler(f"Parzelle {p} gibt es in {kz} nicht (1–{sp['n']}).")
        if not t:
            b.pop(str(int(p)), None)
        elif t in namen:
            b[str(int(p))] = t
        else:
            raise Fehler(f"Tarif „{t}“ gibt es nicht.")
    if not b:
        d["buchungen"].pop(kz, None)
    speichere(d)
    journal(f"Buchungen {kz}: {len(aenderungen)} Änderung(en), jetzt {len(b)} gebucht")
    return {"log": [f"✔ {len(aenderungen)} Änderung(en) gespeichert – {len(b)} von {sp['n']} Parzellen gebucht. "
                    "Ans Gateway (Bandbreite/Netzgröße) geht das über den Reiter „Tarife“."]}


def _xlsx_blaetter(roh_bytes):
    """liest alle Blätter einer xlsx (gespeicherte Werte, auch Formelergebnisse) – ohne Zusatzpakete"""
    M = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
    R = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}"
    try:
        z = zipfile.ZipFile(io.BytesIO(roh_bytes))
    except zipfile.BadZipFile:
        raise Fehler("Das ist keine Excel-Datei (.xlsx).")
    wb = ET.fromstring(z.read("xl/workbook.xml"))
    rels = {r.get("Id"): r.get("Target") for r in ET.fromstring(z.read("xl/_rels/workbook.xml.rels"))}
    strings = []
    if "xl/sharedStrings.xml" in z.namelist():
        for si in ET.fromstring(z.read("xl/sharedStrings.xml")).iter(M + "si"):
            strings.append("".join(t.text or "" for t in si.iter(M + "t")))
    def lies(name):
        rid = next((s.get(R + "id") for s in wb.iter(M + "sheet") if s.get("name") == name), None)
        if not rid:
            return None
        ziel = rels[rid].lstrip("/")
        ziel = ziel if ziel.startswith("xl/") else "xl/" + ziel
        zellen = {}
        for c in ET.fromstring(z.read(ziel)).iter(M + "c"):
            v, t = c.find(M + "v"), c.get("t")
            if t == "inlineStr":
                zellen[c.get("r")] = "".join(x.text or "" for x in c.iter(M + "t"))
            elif v is None or t == "e":
                continue
            elif t == "s":
                zellen[c.get("r")] = strings[int(v.text)]
            elif t in ("str", "b"):
                zellen[c.get("r")] = v.text
            else:
                try:
                    f = float(v.text)
                    zellen[c.get("r")] = int(f) if f == int(f) else f
                except ValueError:
                    zellen[c.get("r")] = v.text
        return zellen
    return [s.get("name") for s in wb.iter(M + "sheet")], lies


def _norm(s):
    s = str(s or "").lower()
    for a, b in (("ä", "ae"), ("ö", "oe"), ("ü", "ue"), ("ß", "ss")):
        s = s.replace(a, b)
    s = re.sub(r"\b(kgv|kga|kgs|kleingartenverein|kleingartenanlage|e\.?\s?v\.?|sparte)\b", " ", s)
    return re.sub(r"[^a-z0-9]+", "", s)


def akt_kalk_import(d, roh):
    """Excel: entweder die Kalkulation (Annahmen, Sparten-Blätter) oder der VLAN-Planer (Blatt Sparten)"""
    namen, lies = _xlsx_blaetter(roh)
    log = []
    k = d.setdefault("kalk", {})
    if "Annahmen" in namen and "Zusammenfassung" in namen:
        an = lies("Annahmen") or {}
        def z(c, std=None):
            v = an.get(c)
            return v if isinstance(v, (int, float)) else std
        neu = {"kleinunternehmer": z("B12", 1) == 1, "ust": (z("B20", 0.19) or 0) * 100, "preise_inkl_ust": z("B19", 1) == 1,
               "uplink_monat": z("B24"), "strom_mast": z("B25"), "strom_hv": z("B26"),
               "zahlung_pct": (z("B27", 0.03) or 0) * 100, "wartung_pct": (z("B28", 0.03) or 0) * 100,
               "zentral_voll_technik": z("B31"), "zentral_voll_personal": z("B32"), "zentral_voll_sonstiges": z("B33"),
               "zentral_start_technik": z("B36"), "zentral_start_personal": z("B37"), "zentral_start_sonstiges": z("B38"),
               "abschreibung_jahre": z("B40"), "ueberbuchung": z("B41"), "ku_grenze_vorjahr": z("B14"), "ku_grenze_lfd": z("B15"),
               "quote_prognose": (z("B18", 0.6) or 0) * 100}
        k["annahmen"] = {**(k.get("annahmen") or {}), **{x: v for x, v in neu.items() if v is not None}}
        log.append("✔ Annahmen übernommen (Steuer, Uplink, Strom, Zahlung, Wartung, zentrale Kosten, Abschreibung, Quote).")
        # Tarifpreise der Reihe nach auf die Tarife des Managers
        tarife = tarife_pruefen(d["tarife"])
        preise = [(an.get(f"A{r}"), an.get(f"C{r}")) for r in range(4, 10) if isinstance(an.get(f"C{r}"), (int, float))]
        for t, (n, p) in zip(tarife, preise):
            t["preis"] = _zahl(p)
            log.append(f"✔ Preis {t['name']}: {t['preis']} €/Jahr (aus „{n}“)")
        d["tarife"] = tarife
        # Sparten-Blätter aus der Zusammenfassung
        zus = lies("Zusammenfassung") or {}
        sparten = kalk_sparten(d)
        for r in range(5, 155):
            blatt = zus.get(f"A{r}")
            if not blatt or blatt not in namen:
                continue
            w = lies(blatt) or {}
            name, var = w.get("B3") or blatt, str(w.get("B7") or "A").upper()
            inv = w.get("G49") if isinstance(w.get("G49"), (int, float)) else w.get("F49" if var == "B" else "D49")
            masten = w.get("G52") if isinstance(w.get("G52"), (int, float)) else None
            treffer = next((kz for kz, s in sparten.items() if _norm(s["name"]) and (_norm(s["name"]) in _norm(name) or _norm(name) in _norm(s["name"]))), None)
            if not treffer:
                log.append(f"ℹ Blatt „{blatt}“ ({name}): keine passende Sparte im Manager – erst Sparte eintragen bzw. VLAN-Planer übernehmen.")
                continue
            s = k.setdefault("sparten", {}).setdefault(treffer, {})
            if isinstance(inv, (int, float)):
                s["investition"] = round(float(inv), 2)
            if isinstance(masten, (int, float)):
                s["masten"] = float(masten)
            up = w.get("B6")
            if isinstance(up, (int, float)):
                s["uplink"] = float(up)
            log.append(f"✔ {treffer} ← Blatt „{blatt}“: Investition {s.get('investition', 0):,.2f} € (Variante {var}), {int(s.get('masten') or 0)} Masten mit Technik".replace(",", "X").replace(".", ",").replace("X", "."))
    elif "Sparten" in namen and "Gateways" in namen:
        sp = lies("Sparten") or {}
        n_neu = 0
        for r in range(5, 1000):
            name = sp.get(f"B{r}")
            if name is None and sp.get(f"A{r}") is None:
                break
            gw, kz, n = sp.get(f"F{r}"), sp.get(f"D{r}"), sp.get(f"C{r}")
            if not name or not kz or not isinstance(n, (int, float)) or gw in (None, ""):
                continue
            s = k.setdefault("sparten", {}).setdefault(str(kz), {})
            s.update({"name": str(name), "n": int(n), "gateway": gw, "quelle": "VLAN-Planer"})
            n_neu += 1
        # Sparten, die im VLAN-Planer kein Gateway mehr haben, verlieren den Planer-Eintrag (Werte bleiben)
        log.append(f"✔ {n_neu} Sparten mit Gateway aus dem VLAN-Planer übernommen (Name, Kürzel, Parzellen, Gateway).")
    else:
        raise Fehler("Unbekannte Datei: erwartet wird die Kalkulation (Blätter „Annahmen“ und „Zusammenfassung“) oder der VLAN-Planer (Blätter „Sparten“ und „Gateways“).")
    speichere(d)
    return {"log": log}


# =============================================================== Netzplanung (Gateway-Standorte, Glasfaser-Kette, Buchungsquote, theoretische Einnahmen)
# gleiche Rechnung wie Kleingarten_Gateway_Planung.xlsx – Daten: Kleingartenentwicklungskonzept 2040 Brandenburg a. d. H., Anlage 1 + 2
GWP_ANLAGEN = [  # Nr, Name, Adresse, Stufe, Eigentum, Parzellen, lt. Konzept, Leerstand, Fläche m², Alter bis30/30-50/50-70/70-90/ab90, x km, y km, Vorschlag Standort, Vorschlag Zuleitung
    (1, '1. März', 'Willibald-Alexis-Straße 38', 'B – Beobachtung', 'Stadt BRB', 30, 30, 2, 8547, (0.4, 24.3, 10.8, 4.1, 0.0), 9.22, 7.78, 33, 6),
    (2, 'Abendfrieden', 'Ziesarer Landstraße 24', 'C – Qualifizierung', 'Stadt / Kirche', 75, 75, 4, 34727, (0.0, 36.8, 33.3, 12.7, 0.0), 9.12, 2.09, 41, 20),
    (3, 'Abendrot', 'Am Gallberg 3', 'A – Stabil', 'Stadt / privat', 137, 137, 0, 64614, (1.6, 42.5, 105.7, 51.9, 0.0), 9.64, 6.32, 30, 30),
    (4, 'Abendruh', 'Mahlerstraße 21', 'A – Stabil', 'Stadt BRB', 142, 142, 0, 75974, (2.8, 46.9, 71.4, 52.9, 2.8), 8.01, 7.51, 30, 30),
    (5, 'Abendsonne', 'Bayernstraße 9a', 'A – Stabil', 'Privat', 67, 67, 13, 17033, (1.7, 21.5, 30.3, 8.1, 0.0), 8.03, 5.22, 23, 24),
    (6, 'Altstadt Forst', 'Rathenower Landstraße 3', 'A – Stabil', 'Stadt / privat', 88, 88, 0, 46549, (2.8, 46.9, 71.4, 52.9, 2.8), 8.52, 8.34, 33, 33),
    (7, 'Am Beetzseeufer', 'Beetzseeufer 8', 'A – Stabil', 'Stadt BRB', 77, 76, 0, 38607, (0.1, 44.9, 59.7, 11.7, 0.0), 11.55, 6.05, 49, 88),
    (8, 'Am Büttelhandfassgraben', 'Am Bittelhandfassgraben 14', 'B – Beobachtung', 'Privat', 5, 5, 0, 2345, (1.1, 0.0, 1.7, 0.0, 0.0), 10.02, 3.54, 49, 50),
    (9, 'Am Eichenweg', 'Ziesarer Landstraße 1', 'C – Qualifizierung', 'Stadt / Kirche', 54, 54, 2, 33743, (0.9, 33.0, 22.2, 8.9, 0.0), 9.1, 2.38, 17, 17),
    (10, 'Am Jakobsgraben', 'Otto-Gartz-Straße 10a', 'D – Planungskonflikt', 'Stadt BRB', 41, 41, 0, 21966, (0.4, 17.5, 22.6, 9.6, 0.0), 10.92, 3.53, 17, 27),
    (11, 'Am Schafdamm', 'Schafdamm 3', 'C – Qualifizierung', 'Stadt / privat', 10, 10, 0, 6123, (0.0, 1.6, 5.1, 5.0, 0.0), 8.11, 9.91, 33, 12),
    (12, 'Am Schlangenpfad', 'Schlangenpfad 21', 'C – Qualifizierung', 'Stadt BRB', 19, 19, 0, 11021, (0.0, 2.9, 8.6, 14.6, 0.0), 8.03, 9.59, 33, 13),
    (13, 'Am Waldesrand', 'Schafdamm 1', 'B – Beobachtung', 'Stadt BRB', 96, 96, 2, 48263, (5.7, 27.5, 44.1, 37.0, 0.9), 8.11, 9.33, 33, 33),
    (14, 'An der Plane I', 'Planeweg 1', 'C – Qualifizierung', 'Kirche', 16, 16, 0, 12898, (0.0, 2.8, 9.7, 6.2, 0.0), 9.37, 2.57, 73, 68),
    (15, 'Bergeshöh', 'Triglafweg 20', 'A – Stabil', 'Stadt BRB', 14, 14, 1, 7551, (0.0, 12.6, 3.3, 3.2, 0.0), 10.6, 5.33, 28, 83),
    (16, 'Bergfrieden', 'Wusterwitzer Str. 71', 'C – Qualifizierung', 'Stadt BRB', 130, 139, 17, 55513, (5.0, 38.9, 45.7, 47.0, 0.1), 0.27, 3.02, 16, None),
    (17, 'Birkenwäldchen', 'Wittstocker Gäßchen 36', 'B – Beobachtung', 'Stadt / privat', 56, 56, 3, 30065, (0.0, 16.8, 54.2, 3.3, 0.0), 9.78, 1.18, 17, None),
    (18, 'BKV Pfefferland', 'Pfefferlander Weg 11', 'B – Beobachtung', 'Privat', 64, 64, 0, 32712, (0.3, 28.5, 44.4, 14.5, 0.0), 7.78, 1.54, 73, 73),
    (19, 'Brielower Dreieck', 'Am Industriegelande 1', 'A – Stabil', 'Stadt BRB', 35, 35, 0, 15539, (1.3, 4.4, 30.4, 6.9, 0.0), 10.78, 6.72, 81, 81),
    (20, 'Buchenweg', 'Buchenweg 77', 'B – Beobachtung', 'Stadt BRB', 86, 86, 1, 49614, (5.4, 44.2, 38.1, 20.6, 0.0), 9.3, 1.65, 41, 41),
    (21, 'Butterlake', 'Brielower Aue 30', 'B – Beobachtung', 'Stadt / privat', 75, 75, 1, 34343, (0.0, 37.3, 42.3, 32.1, 0.3), 8.22, 9.04, 33, 33),
    (22, 'Eichhorstweg', 'Eichhorstweg 15', 'B – Beobachtung', 'Privat', 38, 38, 1, 20436, (1.2, 13.9, 21.9, 11.6, 0.0), 9.53, 0.95, 22, None),
    (23, 'Eigener Fleiß', 'Hannoversche Str. 38', 'A – Stabil', 'Stadt BRB', 123, 123, 0, 63177, (6.1, 44.7, 81.9, 49.7, 0.0), 7.81, 4.85, 23, None),
    (24, 'Einheit', 'Thuringer Str. 18', 'A – Stabil', 'Stadt BRB', 99, 99, 1, 49589, (4.8, 45.8, 49.2, 21.1, 0.0), 8.32, 4.92, 23, 23),
    (25, 'Einigkeit', 'Klingenbergstr. 2b', 'A – Stabil', 'Stadt BRB', 14, 14, 0, 4670, (0.5, 3.2, 8.8, 1.2, 0.0), 9.44, 4.39, 56, 56),
    (26, 'Eintracht I', 'Franz-Ziegler-Str. 29b', 'A – Stabil', 'Stadt / privat', 32, 32, 1, 9606, (0.2, 7.9, 18.3, 4.2, 0.0), 10.46, 3.81, 23, 55),
    (27, 'Eintracht II', 'Gottiner Landstr. 17', 'A – Stabil', 'k. A.', 42, 42, 2, 15820, (0.0, 24.0, 26.7, 8.7, 0.0), 10.2, 2.67, 17, 9),
    (28, 'Erdenglück', 'Johannisburger Anger 26', 'B – Beobachtung', 'Stadt / privat', 99, 96, 2, 40185, (0.8, 39.9, 46.1, 42.3, 0.0), 6.72, 7.19, 28, None),
    (29, 'Erntesegen', 'Brahmsstr. 12b', 'A – Stabil', 'Stadt / privat', 92, 91, 1, 43349, (4.4, 43.6, 42.2, 19.8, 0.4), 7.97, 6.74, 28, 28),
    (30, 'Feierabend', 'Beethovenstr. 31', 'A – Stabil', 'Stadt BRB', 190, 190, 5, 99039, (7.9, 61.8, 79.2, 81.3, 1.1), 8.64, 6.96, 30, None),
    (31, 'Feldstraße', 'Feldstraße 1c', 'C – Qualifizierung', 'Stadt BRB', 68, 68, 4, 35041, (1.1, 24.4, 32.2, 21.3, 0.0), 9.65, 2.54, 41, 60),
    (32, 'Finkenhain', 'Mendelssohnstr. 13', 'C – Qualifizierung', 'Stadt BRB', 8, 8, 0, 5992, (0.0, 0.0, 5.7, 1.5, 0.0), 7.35, 7.18, 28, 82),
    (33, 'Fohrder Landstraße', 'Brielower Aue 33', 'A – Stabil', 'Stadt / privat', 127, 127, 1, 71463, (1.5, 54.0, 51.7, 49.4, 1.6), 8.35, 8.76, 33, None),
    (34, 'Freiheit', 'Feldstr. 1b', 'C – Qualifizierung', 'Stadt BRB', 55, 55, 6, 28864, (0.0, 30.6, 18.3, 6.9, 0.0), 9.86, 2.55, 49, 64),
    (35, 'Freizeit', 'Ziesarer Landstr. 64', 'B – Beobachtung', 'Stadt / privat', 63, 63, 1, 32286, (1.7, 20.7, 28.8, 20.9, 0.0), 8.93, 1.91, 41, 2),
    (36, 'Friedland', 'Klingenbergstr. 19', 'A – Stabil', 'k. A.', 64, 64, 1, 29654, (0.0, 30.9, 24.3, 23.3, 0.0), 8.93, 4.49, 23, 24),
    (37, 'Frisch Auf', 'Klingenbergstr. 4', 'B – Beobachtung', 'Stadt BRB', 19, 19, 1, 9927, (0.0, 3.7, 12.4, 4.9, 0.0), 9.24, 4.36, 56, 56),
    (38, 'Frohsinn', 'Ziesarer Landstr. 3', 'C – Qualifizierung', 'Stadt / Kirche', 54, 54, 3, 29762, (0.4, 23.7, 33.5, 12.4, 0.0), 8.62, 1.78, 17, 9),
    (39, 'Gartenfreunde Brielower Aue', 'Brielower Aue 47', 'B – Beobachtung', 'Stadt / privat', 69, 69, 1, 39053, (2.4, 27.5, 27.7, 14.1, 0.0), 9.37, 9.04, 33, 33),
    (40, 'Glück Auf', 'Ziesarer Landstr. 117', 'B – Beobachtung', 'Stadt BRB', 34, 34, 2, 19944, (0.1, 12.7, 13.4, 7.1, 0.0), 8.31, 1.36, 73, 73),
    (41, 'Glück im Winkel', 'Eichhorstweg 3', 'B – Beobachtung', 'Stadt BRB', 139, 139, 3, 96483, (8.4, 51.3, 60.8, 40.7, 0.0), 9.85, 1.48, 41, None),
    (42, 'Grüne Ecke', 'Pfefferlander Weg 48', 'A – Stabil', 'Stadt / privat', 50, 50, 0, 30158, (0.0, 14.6, 38.7, 16.7, 0.0), 8.33, 1.88, 17, 38),
    (43, 'Grüner Kranz', 'GutsMuthsstr. 21a', 'A – Stabil', 'Stadt BRB', 70, 70, 2, 31984, (4.5, 27.8, 30.1, 12.1, 0.0), 11.18, 6.17, 49, 7),
    (44, 'Grünes Heim', 'Ferdinand-Lassalle-Str. 12', 'B – Beobachtung', 'Kirche', 23, 23, 1, 9696, (0.4, 10.4, 10.4, 0.1, 0.0), 9.78, 4.5, 56, 56),
    (45, 'Gut Wetter', 'Fohrder Landstr. 9', 'A – Stabil', 'Stadt BRB', 17, 17, 0, 8997, (0.0, 4.8, 6.7, 4.0, 0.0), 10.01, 6.78, 30, 3),
    (46, 'Handwerker', 'Planeweg 1b', 'C – Qualifizierung', 'Kirche', 36, 36, 1, 15873, (2.6, 15.3, 20.0, 12.0, 0.0), 9.22, 2.78, 23, 79),
    (47, 'Harmonie', 'August-Bebel-Str. 19', 'D – Planungskonflikt', 'Stadt BRB', 60, 62, 20, 22450, (2.0, 10.4, 17.5, 12.0, 0.0), 9.6, 5.81, 30, 3),
    (48, 'Heidekrug', 'Plauer Landstr. 42', 'B – Beobachtung', 'Stadt BRB', 34, 34, 0, 14955, (2.1, 6.7, 25.0, 12.0, 0.0), 5.88, 5.58, 48, None),
    (49, 'Helgoland', 'Grune Aue 31', 'A – Stabil', 'Stadt / Kirche', 110, 110, 6, 50704, (0.0, 51.1, 39.0, 15.3, 0.0), 10.37, 3.98, 49, None),
    (50, 'Hoffnung', 'Baebenrothufer 7', 'B – Beobachtung', 'Stadt BRB', 7, 7, 1, 4673, (0.0, 4.8, 1.8, 2.1, 0.0), 9.96, 3.51, 49, 65),
    (51, 'Holland', 'Klingenbergstr. 2', 'B – Beobachtung', 'Stadt BRB', 9, 9, 1, 3365, (0.0, 8.6, 4.6, 0.0, 0.0), 9.55, 4.66, 56, 44),
    (52, 'Im Mittelbruch I', 'Krakauer Str. 28', 'C – Qualifizierung', 'Stadt / privat', 33, 33, 0, 27542, (0.0, 11.3, 23.0, 11.0, 0.0), 12.71, 5.58, 85, 61),
    (53, 'Im Mittelbruch II', 'Krakauer Str. 29', 'C – Qualifizierung', 'Stadt / privat', 47, 47, 1, 23601, (0.0, 25.9, 20.0, 26.3, 1.4), 12.18, 5.37, 85, 61),
    (54, 'Immergrün', 'Gordenallee 169', 'A – Stabil', 'Stadt BRB', 57, 57, 0, 28680, (6.3, 21.9, 25.1, 14.7, 0.5), 8.94, 6.43, 28, 29),
    (55, 'Jakobswerder', 'Grune Aue 48', 'B – Beobachtung', 'Stadt / Kirche', 49, 49, 1, 22337, (3.0, 19.5, 24.1, 12.1, 0.0), 9.88, 3.99, 23, 36),
    (56, 'Kammgarn', 'Klingenbergstr. 2a', 'B – Beobachtung', 'Privat', 28, 28, 10, 9938, (1.8, 9.4, 15.0, 0.0, 0.0), 9.62, 4.34, 56, None),
    (57, 'Kirchmöser-Dorf', 'Bahnhofstr. 3', 'C – Qualifizierung', 'Stadt / privat', 48, 48, 2, 34296, (0.0, 10.8, 23.5, 16.3, 0.0), 1.57, 1.76, 57, None),
    (58, 'Kirchmöser-Lehmgarten', 'Uferstr. 71b', 'B – Beobachtung', 'Stadt BRB', 38, 38, 1, 13623, (1.0, 14.1, 23.6, 8.1, 0.0), 2.69, 2.18, 59, 59),
    (59, 'Kirchmöser-Ost', 'Kurze Str. 17', 'A – Stabil', 'Stadt BRB', 66, 71, 0, 24565, (0.0, 15.9, 39.1, 32.9, 0.0), 3.21, 2.06, 59, None),
    (60, 'Landheim', 'Wilhelmsdorfer Landstr. 65', 'A – Stabil', 'Stadt BRB', 109, 109, 11, 52025, (2.3, 42.6, 44.4, 28.0, 0.0), 9.6, 2.79, 41, 41),
    (61, 'Märkische Aue', 'Krakauer Str. 27', 'B – Beobachtung', 'Stadt / privat', 73, 73, 0, 36741, (0.0, 18.2, 54.1, 18.1, 0.0), 12.33, 5.83, 85, 85),
    (62, 'Mittelweg', 'Buchenweg 63a', 'C – Qualifizierung', 'Privat', 36, 36, 2, 15206, (0.0, 11.9, 19.5, 13.4, 0.0), 9.3, 1.15, 22, 22),
    (63, 'Morgenrot', 'Ziesarer Landstr. 66', 'B – Beobachtung', 'Stadt BRB', 25, 25, 1, 14070, (1.6, 21.7, 4.2, 0.0, 0.0), 9.02, 1.75, 73, 74),
    (64, 'Neues Leben', 'Koppehlstr. 7', 'C – Qualifizierung', 'Stadt BRB', 62, 76, 3, 34980, (0.4, 25.6, 32.3, 12.7, 0.0), 10.33, 3.32, 49, 65),
    (65, 'Neu-Sanssouci', 'Grune Aue 46', 'A – Stabil', 'Stadt / Kirche', 77, 62, 0, 30770, (0.0, 36.7, 34.9, 14.2, 0.0), 9.91, 3.76, 49, 49),
    (66, 'Oase', 'Brahmsstr. 14b', 'A – Stabil', 'Stadt BRB', 47, 47, 0, 25083, (3.8, 29.0, 25.0, 0.8, 0.0), 8.3, 7.37, 28, 29),
    (67, 'Pferdewiese', 'Seestr. 50', 'C – Qualifizierung', 'Stadt BRB', 55, 55, 1, 30105, (1.9, 15.4, 42.0, 18.1, 0.0), 0.83, 3.84, 16, 16),
    (68, 'Plane II', 'Planeweg 4&', 'C – Qualifizierung', 'Stadt / privat', 28, 28, 0, 14775, (0.7, 9.0, 19.7, 5.7, 0.0), 8.86, 2.58, 73, 40),
    (69, 'Platz der Einheit', 'Platz der Einheit 19', 'C – Qualifizierung', 'Stadt BRB', 48, 48, 1, 18906, (0.0, 26.4, 26.8, 7.6, 0.0), 1.21, 2.22, 57, 57),
    (70, 'Sandfurth-Oase', 'Sandfurthweg 27', 'B – Beobachtung', 'Privat', 15, 15, 0, 7765, (0.5, 4.8, 11.1, 3.3, 0.0), 7.72, 1.92, 73, 18),
    (71, 'Sanssouci', 'Wilhelmsdorfer Landstr. 55', 'A – Stabil', 'Stadt / privat', 39, 39, 5, 16848, (0.0, 21.5, 12.2, 5.0, 0.0), 9.88, 3.05, 23, 55),
    (72, 'Sommerfreude I', 'Eichhorstweg 9', 'B – Beobachtung', 'Stadt / privat', 49, 49, 1, 24945, (0.0, 15.2, 32.2, 17.2, 0.0), 9.61, 1.1, 17, 17),
    (73, 'Sommerfreude II', 'Pfefferlander Weg 9', 'A – Stabil', 'Stadt / privat', 130, 130, 1, 75448, (7.7, 41.2, 59.1, 50.9, 0.0), 7.94, 1.38, 73, None),
    (74, 'Sonnenrot', 'Ziesarer Landstr. 68', 'A – Stabil', 'Privat', 28, 28, 0, 12438, (2.1, 13.2, 13.9, 8.9, 0.0), 8.87, 1.75, 73, 40),
    (75, 'Sonnenschein', 'Mahlerstr. 22', 'A – Stabil', 'Stadt BRB', 40, 40, 1, 19604, (2.4, 23.6, 22.9, 6.8, 0.0), 7.79, 7.59, 28, 82),
    (76, 'Sonnenwinkel', 'Buchenweg 65a', 'A – Stabil', 'Stadt / privat', 48, 48, 0, 22186, (0.5, 25.6, 21.7, 14.8, 0.0), 9.45, 1.29, 17, 72),
    (77, 'Sorgenfrei I', 'Ziesarer Landstr. 76', 'B – Beobachtung', 'Stadt BRB', 45, 45, 2, 23588, (1.6, 20.0, 18.9, 7.1, 0.0), 8.91, 1.61, 17, 38),
    (78, 'Sorgenfrei II', 'Buchenweg 62', 'B – Beobachtung', 'Privat', 23, 23, 2, 16763, (0.0, 10.2, 16.0, 3.9, 0.0), 9.03, 1.43, 73, 63),
    (79, 'Sportpark', 'Wilhelmsdorfer Landstr. 90', 'C – Qualifizierung', 'Privat', 37, 37, 1, 19323, (0.7, 11.9, 17.0, 18.5, 0.6), 9.33, 2.94, 23, 71),
    (80, 'Stiller Winkel', 'Pfefferlander Weg 50', 'B – Beobachtung', 'Stadt / privat', 50, 50, 2, 27635, (0.3, 19.8, 24.7, 18.2, 0.0), 8.56, 2.02, 17, 38),
    (81, 'Traumland', 'Fritze-Bollmann-Weg 82', 'B – Beobachtung', 'Stadt BRB', 49, 49, 1, 21764, (0.0, 16.9, 26.4, 8.8, 0.0), 11.1, 7.69, 81, None),
    (82, 'Waldfrieden', 'Weberstr. 59', 'A – Stabil', 'Stadt / privat', 90, 90, 3, 51208, (2.3, 47.0, 42.1, 23.5, 0.0), 7.54, 7.41, 28, 29),
    (83, 'Weinmeisterweg', 'Weinmeisterweg 10', 'A – Stabil', 'Privat', 26, 26, 1, 8902, (0.0, 13.2, 7.4, 8.8, 0.0), 9.97, 5.72, 28, 54),
    (84, 'Wittstocker Gäßchen', 'Wittstocker Gäßchen 15', 'B – Beobachtung', 'Stadt / Kirche', 54, 54, 0, 36135, (0.9, 16.7, 22.5, 24.1, 0.0), 9.54, 1.72, 17, 17),
    (85, 'Zukunft', 'Hagelberger Str. 3', 'A – Stabil', 'Privat', 85, 85, 3, 47523, (2.9, 33.3, 65.8, 11.4, 0.0), 12.47, 6.53, 85, None),
    (86, 'Zum Burgweg', 'Burgweg 4a', 'A – Stabil', 'Stadt BRB', 9, 9, 0, 5216, (0.0, 1.9, 7.5, 2.4, 0.0), 11.66, 5.29, 85, 87),
    (87, 'Zum kühlen Grunde', 'Grillendamm 8', 'A – Stabil', 'Stadt BRB', 26, 26, 0, 14389, (2.6, 8.1, 15.7, 9.0, 0.0), 11.67, 5.46, 85, 53),
    (88, 'Zur Insel', 'Domkietz 8a', 'A – Stabil', 'Stadt / privat', 86, 86, 0, 54091, (0.0, 21.8, 53.6, 28.7, 0.0), 11.24, 5.17, 49, 49),
]

GWP_STANDARD = {
    "PG": 55, "Max_GW": 10, "Vorschlag_nutzen": 1, "Umweg": 1.3, "Uplink_Kap": 1000, "Ueberbuchung": 8, "Bandbreite": 30, "Jahre": 5,
    "P_UCG": 250, "P_Agg": 240, "P_DAC": 20, "P_KVz": 1500, "P_USV": 250, "P_SFP": 21.9, "P_Flex": 179, "P_NT": 70, "P_Halter": 8.5,
    "P_Luefter": 45, "P_Spleiss": 32.9, "P_Saeule": 300, "P_Ueber": 80, "P_Surge": 12, "P_AP": 250, "P_Mast": 392, "P_Fund": 120,
    "P_Faser": 1.5, "P_Kupfer": 1.2, "P_Tiefbau": 0, "P_MontStandort": 500, "P_MontMast": 150, "P_MontZul": 150,
    "KU": 1, "USt": 0.19,
    "Parz_je_AP": 3.6, "AP_je_Mast": 2.2, "Anteil_Technik": 0.5, "Leitung_k": 2.806, "Faser_f": 1.66, "Kupfer_f": 1.06, "Kabel_je_AP": 0.42, "Ports_Agg": 8,
    "Uplink_Monat": 75, "Strom_Standort": 80, "Strom_GW": 25, "Strom_Mast": 50, "Wartung": 0.03, "Zahlung": 0.03, "Preis_Jahr": 120,
    "Quote_Modus": 1, "Quote_fest": 0.6, "Szenario": 1,
    "Neig_1": 0.80, "Neig_2": 0.75, "Neig_3": 0.60, "Neig_4": 0.35, "Neig_5": 0.10,
    "Stufe_A": 1.0, "Stufe_B": 1.0, "Stufe_C": 0.9, "Stufe_D": 0.75,
    "Abg_1": 0.05, "Abg_2": 0.05, "Abg_3": 0.10, "Abg_4": 0.30, "Abg_5": 0.60, "Nachbes": 0.7, "Nachbes_Leer": 2,
}
# Gruppen, Texte und Einheit für das Formular („%“ = intern Anteil 0–1, im Formular Prozent)
GWP_FELDER = [
    ("Netz-Regeln", [("PG", "Parzellen je Gateway", ""), ("Max_GW", "Gateways je Standort (Warnung darüber)", ""),
                     ("Vorschlag_nutzen", "Standort-Vorschlag nutzen, wo nichts gewählt (1 = ja, 0 = eigenständig)", ""),
                     ("Umweg", "Umwegfaktor Glasfaser (Trasse statt Luftlinie)", ""), ("Uplink_Kap", "Kapazität Internet-Anschluss (Mbit/s)", ""),
                     ("Ueberbuchung", "Überbuchungsfaktor (1:x)", ""), ("Bandbreite", "Ø Bandbreite je Kunde (Mbit/s)", ""), ("Jahre", "Betrachtungszeitraum (Jahre)", "")]),
    ("Buchungsquote", [("Quote_Modus", "Modus (1 = aus Alter und Leerstand, 2 = feste Quote)", ""), ("Quote_fest", "Feste Quote (Modus 2)", "%"),
                       ("Szenario", "Modus 1 rechnet mit (1 = heute, 2 = in 5 Jahren)", ""),
                       ("Neig_1", "Buchungsneigung Pächter bis 30", "%"), ("Neig_2", "Buchungsneigung 30–50", "%"), ("Neig_3", "Buchungsneigung 50–70", "%"),
                       ("Neig_4", "Buchungsneigung 70–90", "%"), ("Neig_5", "Buchungsneigung ab 90", "%"),
                       ("Stufe_A", "Faktor Entwicklungsstufe A", "%"), ("Stufe_B", "Faktor Stufe B", "%"), ("Stufe_C", "Faktor Stufe C", "%"), ("Stufe_D", "Faktor Stufe D", "%"),
                       ("Abg_1", "Pachtaufgabe in 5 J., bis 30", "%"), ("Abg_2", "Pachtaufgabe 30–50", "%"), ("Abg_3", "Pachtaufgabe 50–70", "%"),
                       ("Abg_4", "Pachtaufgabe 70–90", "%"), ("Abg_5", "Pachtaufgabe ab 90", "%"),
                       ("Nachbes", "Nachbesetzung frei werdender Parzellen", "%"), ("Nachbes_Leer", "Abschlag je Prozentpunkt Leerstand", "")]),
    ("Laufende Kosten und Erlös", [("Preis_Jahr", "Fester Preis je Kunde und Jahr (€) – wenn nicht nach Tarifmix", ""),
                                   ("Uplink_Monat", "Internet-Anschluss je Monat (€ netto)", ""), ("Strom_Standort", "Strom Standort je Jahr (€)", ""),
                                   ("Strom_GW", "Strom je Gateway und Jahr (€)", ""), ("Strom_Mast", "Strom je Mast mit Technik und Jahr (€)", ""),
                                   ("Wartung", "Wartung (Anteil der Investition je Jahr)", "%"), ("Zahlung", "Zahlungsabwicklung (Anteil vom Umsatz)", "%"),
                                   ("KU", "Kleinunternehmer (1 = ja, 0 = nein)", ""), ("USt", "Umsatzsteuersatz", "%")]),
    ("Preise (netto, €)", [("P_UCG", "Gateway (Cloud Gateway Fiber)", ""), ("P_Agg", "Switch Aggregation (8× SFP+)", ""), ("P_DAC", "DAC-Kabel je Gateway", ""),
                           ("P_KVz", "Außenschrank Standort", ""), ("P_USV", "USV + Überspannungsschutz Standort", ""), ("P_SFP", "SFP 1G Singlemode", ""),
                           ("P_Flex", "Switch Flex 2.5G PoE", ""), ("P_NT", "Netzteil Flex", ""), ("P_Halter", "Hutschienen-Halter", ""), ("P_Luefter", "Lüfter mit Thermostat", ""),
                           ("P_Spleiss", "Mini-Spleißbox", ""), ("P_Saeule", "Strom-Säule", ""), ("P_Ueber", "Überspannungsschutz + LS/FI Säule", ""),
                           ("P_Surge", "Ethernet Surge Protection", ""), ("P_AP", "Access Point U7 Pro Outdoor", ""), ("P_Mast", "Mast 5 m", ""), ("P_Fund", "Mastfundament", ""),
                           ("P_Faser", "Glasfaser €/m", ""), ("P_Kupfer", "Erdkabel Cat 7 €/m", ""), ("P_Tiefbau", "Tiefbau €/m (0 = keine)", ""),
                           ("P_MontStandort", "Montage Standort", ""), ("P_MontMast", "Montage je Mast", ""), ("P_MontZul", "Montage je Glasfaser-Zuleitung", "")]),
    ("Mengen in der Sparte (Faustregeln)", [("Parz_je_AP", "Parzellen je Access Point", ""), ("AP_je_Mast", "Access Points je Mast", ""),
                                            ("Anteil_Technik", "Anteil Masten mit Technik", "%"), ("Leitung_k", "Leitungsweg-Faktor (m = k × √Fläche)", ""),
                                            ("Faser_f", "Glasfaser m je m Leitungsweg", ""), ("Kupfer_f", "Kupfer m je m Leitungsweg", ""),
                                            ("Kabel_je_AP", "Kupferkabel je AP", ""), ("Ports_Agg", "Anschlüsse je Aggregation-Switch", "")]),
]
GWP_WAHL = ("standort", "zuleitung", "reihenfolge", "entfernung", "quote", "aps", "masten", "leitung", "parz", "leer")


def _ceil(x):
    return int(-(-x // 1)) if x > 0 else 0


def _rund(x):
    return int(x + 0.5) if x >= 0 else -int(-x + 0.5)


def gwp_anlagen(d):
    g = d.get("gwplan") or {}
    if g.get("anlagen"):
        return g["anlagen"]
    return [{"nr": t[0], "name": t[1], "adresse": t[2], "stufe": t[3], "eigentum": t[4], "parz": t[5], "parz_konzept": t[6], "leer": t[7],
             "flaeche": t[8], "alter": list(t[9]), "x": t[10], "y": t[11], "vs_standort": t[12], "vs_zuleitung": t[13]} for t in GWP_ANLAGEN]


def gwp_annahmen(d):
    roh = ((d.get("gwplan") or {}).get("annahmen")) or {}
    a = dict(GWP_STANDARD)
    for k, v in roh.items():
        if k in a:
            try:
                a[k] = float(v)
            except (TypeError, ValueError):
                pass
    return a


def gwp_preis(d, a):
    """Ø Preis je Kunde und Jahr: nach Tarifmix aus den Tarifen des Managers oder fest"""
    g = d.get("gwplan") or {}
    tarife = [t for t in tarife_pruefen(d["tarife"])]
    mix = g.get("tarifmix") or ({tarife[0]["name"]: 100} if tarife else {})
    quelle = g.get("preis_quelle", "tarife")
    anteile = {t["name"]: max(0.0, float(mix.get(t["name"], 0) or 0)) for t in tarife}
    summe = sum(anteile.values())
    if quelle == "tarife" and summe > 0:
        preis = sum(anteile[t["name"]] * float(t.get("preis") or 0) for t in tarife) / summe
        anteile = {k: v / summe for k, v in anteile.items()}
    else:
        quelle, preis, anteile = "fest", a["Preis_Jahr"], {}
    return quelle, preis, anteile, [{"name": t["name"], "preis": float(t.get("preis") or 0), "down": t.get("down"), "anteil": anteile.get(t["name"], 0),
                                     "mix": float(mix.get(t["name"], 0) or 0)} for t in tarife]


def gwplan_berechnen(d):
    a = gwp_annahmen(d)
    A = [dict(x) for x in gwp_anlagen(d)]
    wahl = ((d.get("gwplan") or {}).get("wahl")) or {}
    EK = 1 + a["USt"] if a["KU"] == 1 else 1.0
    PG = max(1, int(a["PG"]))
    idx = {s["nr"]: s for s in A}
    for i, s in enumerate(A):
        w = wahl.get(str(s["nr"])) or {}
        s["w"] = w
        s["row"] = i + 5
        if w.get("parz") is not None:
            s["parz"] = int(w["parz"])
        if w.get("leer") is not None:
            s["leer"] = int(w["leer"])
    vn = a["Vorschlag_nutzen"] == 1
    # wirksamer Standort und Zuleitung
    for s in A:
        w, nr = s["w"], s["nr"]
        s["C"] = w["standort"] if w.get("standort") is not None else (s["vs_standort"] if vn else nr)
        if s["C"] == nr:
            s["D"] = None
        elif w.get("zuleitung") is not None:
            s["D"] = w["zuleitung"]
        elif w.get("standort") is None and vn and s.get("vs_zuleitung") is not None:
            s["D"] = s["vs_zuleitung"]
        else:
            s["D"] = s["C"]
    zahl_am = {}
    for s in A:
        zahl_am[s["C"]] = zahl_am.get(s["C"], 0) + 1
    uv = (a["P_Saeule"] + a["P_Flex"] + a["P_NT"] + a["P_Halter"] + a["P_Luefter"] + a["P_Spleiss"] + a["P_Ueber"]) * EK
    for s in A:
        w, nr = s["w"], s["nr"]
        eigen = s["C"] == nr
        q = idx.get(s["D"])
        s["rolle"] = ("Gateway-Standort" if zahl_am.get(nr, 0) > 1 else "eigenständig") if eigen else "über " + (q["name"] if q else "?")
        if eigen:
            km = 0.0
        elif w.get("entfernung") is not None:
            km = w["entfernung"] / 1000
        else:
            km = ((s["x"] - q["x"]) ** 2 + (s["y"] - q["y"]) ** 2) ** 0.5 if q else 0.0
        s["km"] = km
        s["faser_zul"] = 0.0 if eigen else (w["entfernung"] if w.get("entfernung") is not None else km * 1000 * a["Umweg"])
        s["zul_eur"] = 0.0 if eigen else (s["faser_zul"] * (a["P_Faser"] + a["P_Tiefbau"]) + 2 * a["P_SFP"] + a["P_MontZul"]) * EK
        s["uv_eur"] = 0.0 if eigen else uv
        s["sort"] = w["reihenfolge"] if w.get("reihenfolge") is not None else (500 if eigen else 1000) + s["row"]
    for s in A:
        vor = sum(t["parz"] for t in A if t["C"] == s["C"] and t["sort"] < s["sort"])
        s["davor"] = vor
        s["gw_von"] = vor // PG + 1
        s["gw_bis"] = max(s["gw_von"], _ceil((vor + s["parz"]) / PG))
        c = idx.get(s["C"])
        s["versorgt"] = f"{c['name'] if c else '?'}: GW {s['gw_von']}" + (f"–{s['gw_bis']}" if s["gw_bis"] > s["gw_von"] else "")
        nr = s["nr"]
        if not c:
            s["pruefung"] = "Fehler: Standort unbekannt"
        elif s["C"] == nr:
            s["pruefung"] = "OK"
        elif c["C"] != s["C"]:
            s["pruefung"] = "Fehler: Standort hängt selbst an anderem Standort"
        elif s["D"] == nr:
            s["pruefung"] = "Fehler: Zuleitung von sich selbst"
        elif s["D"] not in idx:
            s["pruefung"] = "Fehler: Zuleitung unbekannt"
        elif idx[s["D"]]["C"] != s["C"]:
            s["pruefung"] = "Fehler: Zuleitung hängt an anderem Standort"
        else:
            s["pruefung"] = "OK"
    # Ring in der Zuleitung (kommt nie am Standort an)
    for s in A:
        if s["pruefung"] != "OK" or s["C"] == s["nr"]:
            continue
        x, gesehen = s, set()
        while x and x["C"] != x["nr"] and x["nr"] not in gesehen:
            gesehen.add(x["nr"]); x = idx.get(x["D"])
        if not x or x["C"] != x["nr"]:
            s["pruefung"] = "Fehler: Zuleitung im Kreis – führt nicht zum Standort"
    # Buchungsquote
    for s in A:
        w, P, L = s["w"], max(1, s["parz"]), s["leer"]
        sm = max(0.0001, sum(s["alter"]))
        sh = [x / sm for x in s["alter"]]
        neig = sum(sh[i] * a[f"Neig_{i + 1}"] for i in range(5))
        sf = a.get("Stufe_" + str(s["stufe"])[:1].upper(), a["Stufe_D"])
        lq = L / P
        q_heute = neig * (1 - lq) * sf
        abg = sum(sh[i] * a[f"Abg_{i + 1}"] for i in range(5))
        nach = max(0.0, min(1.0, a["Nachbes"] - lq * a["Nachbes_Leer"]))
        leer5 = L + (P - L) * abg * (1 - nach)
        nb5 = sum(sh[i] * (1 - a[f"Abg_{i + 1}"]) * a[f"Neig_{i + 1}"] for i in range(5)) / max(0.0001, 1 - abg)
        q5 = (P - L) * ((1 - abg) * nb5 + abg * nach * a["Neig_2"]) * sf / P
        if w.get("quote") is not None:
            q, herk = w["quote"], "manuell"
        elif a["Quote_Modus"] == 2:
            q, herk = a["Quote_fest"], "fest"
        elif a["Szenario"] == 2:
            q, herk = q5, "Alter, in 5 J."
        else:
            q, herk = q_heute, "Alter, heute"
        s.update(leerq=lq, leer5=leer5, q_heute=q_heute, q5=q5, quote=q, herkunft=herk, kunden=s["parz"] * q)
    # Technik in der Sparte und Vergleich eigenständig
    for s in A:
        w = s["w"]
        aps = w["aps"] if w.get("aps") is not None else max(2, _ceil(s["parz"] / a["Parz_je_AP"]))
        masten = w["masten"] if w.get("masten") is not None else _ceil(aps / a["AP_je_Mast"])
        tech = max(1, _ceil(masten * a["Anteil_Technik"]))
        leitung = w["leitung"] if w.get("leitung") is not None else a["Leitung_k"] * (s["flaeche"] ** 0.5)
        faser, kupfer, kabel = leitung * a["Faser_f"], leitung * a["Kupfer_f"], _rund(aps * a["Kabel_je_AP"])
        J = tech * (2 * a["P_SFP"] + a["P_Flex"] + a["P_NT"] + a["P_Halter"] + a["P_Luefter"] + a["P_Spleiss"] + a["P_Saeule"] + a["P_Ueber"]) * EK
        K = (aps * a["P_AP"] + masten * (a["P_Mast"] + a["P_Fund"] + a["P_MontMast"]) + kabel * 2 * a["P_Surge"]) * EK
        Lt = (faser * a["P_Faser"] + kupfer * a["P_Kupfer"] + leitung * a["P_Tiefbau"]) * EK
        N = J + K + Lt + s["zul_eur"] + s["uv_eur"]
        P_gw = _ceil(s["parz"] / PG)
        Q = J + K + Lt + (a["P_KVz"] + a["P_USV"] + a["P_MontStandort"] + P_gw * (a["P_UCG"] + a["P_DAC"]) + a["P_Agg"] * _ceil((P_gw + tech) / a["Ports_Agg"])) * EK
        R = (a["Uplink_Monat"] * 12 * max(1, _ceil(s["kunden"] * a["Bandbreite"] / a["Ueberbuchung"] / a["Uplink_Kap"])) + a["Strom_Standort"]
             + P_gw * a["Strom_GW"] + tech * a["Strom_Mast"]) * EK + Q * a["Wartung"]
        s.update(aps=aps, masten=masten, tech=tech, leitung=leitung, inv_sparte=N, lfd_sparte=tech * a["Strom_Mast"] * EK + N * a["Wartung"],
                 gw_eigen=P_gw, inv_eigen=Q, lfd_eigen=R)
    # Standorte
    standorte = []
    for s in A:
        if s["C"] != s["nr"]:
            continue
        mit = [t for t in A if t["C"] == s["nr"]]
        parz = sum(t["parz"] for t in mit)
        gw = _ceil(parz / PG)
        straenge = s["tech"] + sum(1 for t in A if t["D"] == s["nr"])
        agg = _ceil((gw + straenge) / a["Ports_Agg"])
        kunden = sum(t["kunden"] for t in mit)
        bedarf = kunden * a["Bandbreite"] / a["Ueberbuchung"]
        ans = max(1, _ceil(bedarf / a["Uplink_Kap"]))
        inv = gw * (a["P_UCG"] + a["P_DAC"]) * EK + (a["P_KVz"] + a["P_USV"] + a["P_MontStandort"] + agg * a["P_Agg"]) * EK
        lfd = (ans * a["Uplink_Monat"] * 12 + a["Strom_Standort"] + gw * a["Strom_GW"]) * EK + inv * a["Wartung"]
        pr = f"Achtung: mehr als {int(a['Max_GW'])} Gateways" if gw > a["Max_GW"] else (f"OK – {ans} Internet-Anschlüsse nötig" if ans > 1 else "OK")
        standorte.append({"nr": s["nr"], "name": s["name"], "sparten": len(mit), "namen": [t["name"] for t in sorted(mit, key=lambda t: t["sort"])],
                          "parz": parz, "gw": gw, "belegung": parz / (gw * PG) if gw else 0, "straenge": straenge, "agg": agg, "kunden": round(kunden, 1),
                          "bedarf": round(bedarf), "anschluesse": ans, "inv": round(inv, 2), "lfd": round(lfd, 2), "pruefung": pr})
    st_idx = {x["nr"]: x for x in standorte}
    # Einnahmen und Ergebnis
    quelle, preis, anteile, tarife = gwp_preis(d, a)
    netto = (lambda v: v) if a["KU"] == 1 else (lambda v: v / (1 + a["USt"]))
    ist = {}
    try:
        for z in akt_kalkulation(d)["zeilen"]:
            if z["gebucht"]:
                ist[_norm(z["name"])] = z
    except Exception:
        pass
    zeilen = []
    for s in A:
        so = st_idx.get(s["C"])
        anteil = s["parz"] / so["parz"] if so and so["parz"] else 0
        einnahme = s["kunden"] * preis
        inv = s["inv_sparte"] + anteil * (so["inv"] if so else 0)
        lfd = s["lfd_sparte"] + anteil * (so["lfd"] if so else 0) + netto(einnahme) * a["Zahlung"]
        db = netto(einnahme) - lfd
        treffer = next((z for k, z in ist.items() if k and (k == _norm(s["name"]) or (len(k) > 4 and (k in _norm(s["name"]) or _norm(s["name"]) in k)))), None)
        zeilen.append({
            "nr": s["nr"], "name": s["name"], "adresse": s["adresse"], "stufe": s["stufe"], "parz": s["parz"], "leer": s["leer"], "parz_konzept": s["parz_konzept"],
            "standort": s["C"], "zuleitung": s["D"], "sort": s["sort"], "rolle": s["rolle"], "versorgt": s["versorgt"], "gw_von": s["gw_von"], "gw_bis": s["gw_bis"],
            "km": round(s["km"], 3), "faser_zul": round(s["faser_zul"]), "pruefung": s["pruefung"],
            "quote": s["quote"], "herkunft": s["herkunft"], "q_heute": s["q_heute"], "q5": s["q5"], "kunden": round(s["kunden"], 1),
            "einnahme": round(einnahme, 2), "einnahme_monat": round(einnahme / 12, 2), "je_tarif": {k: round(s["kunden"] * v, 1) for k, v in anteile.items()},
            "aps": s["aps"], "masten": s["masten"], "investition": round(inv, 2), "laufend": round(lfd, 2), "db": round(db, 2),
            "amortisation": round(inv / db, 1) if db > 0 else None, "inv_kunde": round(inv / s["kunden"]) if s["kunden"] else None,
            "ist_gebucht": treffer["gebucht"] if treffer else None, "ist_einnahme": treffer["umsatz_brutto"] if treffer else None,
            "w": {k: s["w"].get(k) for k in GWP_WAHL if s["w"].get(k) is not None},
            "vs_standort": s["vs_standort"], "vs_zuleitung": s["vs_zuleitung"]})
    S = lambda liste, k: sum(float(x[k] or 0) for x in liste)
    parz = S(A, "parz")
    kunden = S(A, "kunden")
    einnahme = S(zeilen, "einnahme")
    inv_plan = S(A, "inv_sparte") + S(standorte, "inv")
    lfd_plan = S(A, "lfd_sparte") + S(standorte, "lfd") + netto(einnahme) * a["Zahlung"]
    lfd_plan_ohne_zahlung = S(A, "lfd_sparte") + S(standorte, "lfd")
    db = netto(einnahme) - lfd_plan
    fehler = sum(1 for s in A if s["pruefung"].startswith("Fehler"))
    gesamt = {
        "sparten": len(A), "parzellen": int(parz), "leerq": S(A, "leer") / parz if parz else 0, "leerq5": S(A, "leer5") / parz if parz else 0,
        "quote": kunden / parz if parz else 0, "kunden": round(kunden, 1),
        "preis": round(preis, 2), "preis_quelle": quelle, "einnahme": round(einnahme, 2), "einnahme_monat": round(einnahme / 12, 2), "einnahme_netto": round(netto(einnahme), 2),
        "je_tarif": {k: {"kunden": round(kunden * v, 1), "einnahme": round(kunden * v * next(t["preis"] for t in tarife if t["name"] == k), 2)} for k, v in anteile.items()},
        "standorte": len(standorte), "gateways": int(S(standorte, "gw")), "anschluesse": int(S(standorte, "anschluesse")), "faser": round(S(A, "faser_zul")),
        "fehler": fehler, "investition": round(inv_plan, 2), "laufend": round(lfd_plan_ohne_zahlung, 2), "zahlung": round(netto(einnahme) * a["Zahlung"], 2), "db": round(db, 2),
        "amortisation": round(inv_plan / db, 1) if db > 0 else None, "inv_kunde": round(inv_plan / kunden) if kunden else None,
        "eigen": {"standorte": len(A), "gateways": int(S(A, "gw_eigen")), "anschluesse": len(A), "investition": round(S(A, "inv_eigen"), 2), "laufend": round(S(A, "lfd_eigen"), 2)},
        "plan_laufend_ohne_zahlung": round(lfd_plan_ohne_zahlung, 2), "jahre": a["Jahre"],
        "ist_gebucht": sum(z["ist_gebucht"] or 0 for z in zeilen), "ist_einnahme": round(sum(z["ist_einnahme"] or 0 for z in zeilen), 2),
        "modus": "manuell je Sparte / " + ("feste Quote " + f"{a['Quote_fest']:.0%}" if a["Quote_Modus"] == 2 else ("aus Alter und Leerstand, in 5 Jahren" if a["Szenario"] == 2 else "aus Alter und Leerstand, heute")),
    }
    gesamt["eigen"]["zeitraum"] = round(gesamt["eigen"]["investition"] + gesamt["eigen"]["laufend"] * a["Jahre"], 2)
    gesamt["zeitraum"] = round(inv_plan + lfd_plan_ohne_zahlung * a["Jahre"], 2)
    log = [f"{len(A)} Sparten · {len(standorte)} Gateway-Standorte · {gesamt['gateways']} Gateways · {gesamt['kunden']:.0f} Kunden (Quote {gesamt['quote']:.1%})"]
    if fehler:
        log.append(f"⚠ {fehler} Sparte(n) mit Fehler in der Zuordnung – Spalte „Prüfung“.")
    if any(x["pruefung"].startswith("Achtung") for x in standorte):
        log.append(f"⚠ Mindestens ein Standort hat mehr als {int(a['Max_GW'])} Gateways.")
    return {"zeilen": zeilen, "standorte": standorte, "gesamt": gesamt, "tarife": tarife, "annahmen": a, "felder": GWP_FELDER,
            "quelle_daten": "Excel-Import" if (d.get("gwplan") or {}).get("anlagen") else "Kleingartenentwicklungskonzept 2040 (eingebaut)", "log": log}


def _gwp_int(v, text, lo, hi):
    if v in (None, ""):
        return None
    try:
        x = float(str(v).replace(",", "."))
    except ValueError:
        raise Fehler(f"{text}: bitte eine Zahl eintragen.")
    if x != int(x) or not lo <= x <= hi:
        raise Fehler(f"{text}: ganze Zahl von {lo} bis {hi}.")
    return int(x)


def akt_gwplan_sparte(d, b):
    nrs = {s["nr"]: s for s in gwp_anlagen(d)}
    try:
        nr = int(b.get("nr"))
    except (TypeError, ValueError):
        nr = None
    if nr not in nrs:
        raise Fehler("Sparte unbekannt.")
    g = d.setdefault("gwplan", {})
    w = dict((g.setdefault("wahl", {})).get(str(nr)) or {})
    for feld, wert in b.items():
        if feld not in GWP_WAHL:
            continue
        if feld in ("standort", "zuleitung"):
            v = _gwp_int(wert, "Standort" if feld == "standort" else "Zuleitung von", 1, 9999)
            if v is not None and v not in nrs:
                raise Fehler(f"Sparte Nr. {v} gibt es nicht.")
        elif feld == "reihenfolge":
            v = _gwp_int(wert, "Reihenfolge", 1, 999)
        elif feld == "quote":
            v = _zahl_oder_none(wert, "Quote manuell")
            if v is not None:
                if v > 100:
                    raise Fehler("Quote manuell: höchstens 100 %.")
                v = v / 100
        elif feld == "parz":
            v = _gwp_int(wert, "Parzellen", 1, 2000)
        elif feld == "leer":
            v = _gwp_int(wert, "Leerstand", 0, 2000)
        else:
            v = _zahl_oder_none(wert, {"entfernung": "Entfernung (m)", "aps": "Access Points", "masten": "Masten", "leitung": "Leitungsweg (m)"}[feld])
        if v is None:
            w.pop(feld, None)
        else:
            w[feld] = v
    p = w.get("parz", nrs[nr]["parz"])
    if w.get("leer", nrs[nr]["leer"]) > p:
        raise Fehler("Leerstand kann nicht größer sein als die Parzellenzahl.")
    if w:
        g["wahl"][str(nr)] = w
    else:
        g["wahl"].pop(str(nr), None)
    speichere(d)
    return gwplan_berechnen(d)


def akt_gwplan_annahmen(d, b):
    g = d.setdefault("gwplan", {})
    neu = dict(g.get("annahmen") or {})
    prozent = {k for _, gr in GWP_FELDER for k, _, e in gr if e == "%"}
    texte = {k: t for _, gr in GWP_FELDER for k, t, _ in gr}
    for k, v in (b.get("annahmen") or {}).items():
        if k not in GWP_STANDARD:
            continue
        x = _zahl_oder_none(v, texte.get(k, k))
        if x is None:
            neu.pop(k, None)
            continue
        neu[k] = x / 100 if k in prozent else x
    probe = {**GWP_STANDARD, **neu}
    if probe["PG"] < 1 or probe["Ueberbuchung"] < 1 or probe["Uplink_Kap"] <= 0 or probe["Ports_Agg"] < 1 or probe["Parz_je_AP"] <= 0 or probe["AP_je_Mast"] <= 0:
        raise Fehler("Parzellen je Gateway, Überbuchung, Uplink-Kapazität, Ports und Faustregeln müssen größer als 0 sein.")
    if probe["Quote_Modus"] not in (1, 2) or probe["Szenario"] not in (1, 2) or probe["Vorschlag_nutzen"] not in (0, 1) or probe["KU"] not in (0, 1):
        raise Fehler("Modus und Szenario sind 1 oder 2, Vorschlag und Kleinunternehmer 0 oder 1.")
    g["annahmen"] = neu
    if "tarifmix" in b and isinstance(b["tarifmix"], dict):
        namen = {t["name"] for t in tarife_pruefen(d["tarife"])}
        g["tarifmix"] = {k: _zahl_oder_none(v, f"Anteil {k}") or 0 for k, v in b["tarifmix"].items() if k in namen}
    if b.get("preis_quelle") in ("tarife", "fest"):
        g["preis_quelle"] = b["preis_quelle"]
    speichere(d)
    r = gwplan_berechnen(d)
    r["log"] = ["✔ Einstellungen gespeichert."] + r["log"]
    return r


def akt_gwplan_zuruecksetzen(d, was):
    g = d.setdefault("gwplan", {})
    if was == "wahl":
        g["wahl"] = {}
        txt = "✔ Eigene Zuordnungen entfernt – es gilt wieder der Vorschlag."
    elif was == "annahmen":
        g.pop("annahmen", None); g.pop("tarifmix", None); g.pop("preis_quelle", None)
        txt = "✔ Einstellungen auf Standard zurückgesetzt."
    elif was == "daten":
        g.pop("anlagen", None)
        txt = "✔ Wieder mit den eingebauten Daten aus dem Kleingartenentwicklungskonzept."
    else:
        raise Fehler("Unbekannt.")
    speichere(d)
    r = gwplan_berechnen(d)
    r["log"] = [txt] + r["log"]
    return r


def _xlsx_namen(roh_bytes):
    """definierte Namen einer xlsx → {Name: (Blatt, Zelle)}"""
    M = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
    z = zipfile.ZipFile(io.BytesIO(roh_bytes))
    aus = {}
    for n in ET.fromstring(z.read("xl/workbook.xml")).iter(M + "definedName"):
        m = re.match(r"^'?(.+?)'?!\$?([A-Z]+)\$?(\d+)$", (n.text or "").strip())
        if m:
            aus[n.get("name")] = (m.group(1), m.group(2) + m.group(3))
    return aus


def akt_gwplan_import(d, roh):
    """Kleingarten_Gateway_Planung.xlsx: Anlagen (Daten + gelbe Spalten) und Annahmen übernehmen"""
    namen, lies = _xlsx_blaetter(roh)
    if not {"Anlagen", "Netz", "Annahmen"} <= set(namen):
        raise Fehler("Das ist nicht die Gateway-Planung (Kleingarten_Gateway_Planung.xlsx) – es fehlen die Blätter „Anlagen“, „Netz“ oder „Annahmen“.")
    an = lies("Anlagen") or {}
    zahl = lambda v: v if isinstance(v, (int, float)) else None
    anlagen, wahl = [], {}
    felder = {"S": "standort", "T": "zuleitung", "U": "reihenfolge", "V": "entfernung", "W": "quote", "X": "aps", "Y": "masten", "Z": "leitung"}
    for r in range(5, 1000):
        nr = zahl(an.get(f"A{r}"))
        if nr is None:
            if an.get(f"B{r}") is None:
                break
            continue
        nr = int(nr)
        parz = zahl(an.get(f"F{r}"))
        if not parz:
            raise Fehler(f"Anlagen Zeile {r}: Parzellenzahl fehlt.")
        vs, vz = zahl(an.get(f"Q{r}")), zahl(an.get(f"R{r}"))
        anlagen.append({"nr": nr, "name": str(an.get(f"B{r}") or f"Sparte {nr}"), "adresse": str(an.get(f"C{r}") or ""), "stufe": str(an.get(f"D{r}") or "D"),
                        "eigentum": str(an.get(f"E{r}") or ""), "parz": int(parz), "parz_konzept": int(zahl(an.get(f"P{r}")) or parz),
                        "leer": int(zahl(an.get(f"G{r}")) or 0), "flaeche": float(zahl(an.get(f"H{r}")) or 0),
                        "alter": [float(zahl(an.get(f"{c}{r}")) or 0) for c in "IJKLM"], "x": float(zahl(an.get(f"N{r}")) or 0), "y": float(zahl(an.get(f"O{r}")) or 0),
                        "vs_standort": int(vs) if vs else nr, "vs_zuleitung": int(vz) if vz else None})
        w = {}
        for c, f in felder.items():
            v = zahl(an.get(f"{c}{r}"))
            if v is not None:
                w[f] = int(v) if f in ("standort", "zuleitung", "reihenfolge") else float(v)
        if w:
            wahl[str(nr)] = w
    if not anlagen:
        raise Fehler("Im Blatt „Anlagen“ stehen keine Sparten.")
    nrs = {s["nr"] for s in anlagen}
    for k, w in wahl.items():
        for f in ("standort", "zuleitung"):
            if w.get(f) is not None and w[f] not in nrs:
                raise Fehler(f"Sparte {k}: {f} Nr. {w[f]} gibt es in der Liste nicht.")
    neu = {}
    try:
        dn = _xlsx_namen(roh)
        cache = {}
        for k in GWP_STANDARD:
            if k in dn:
                blatt, zelle = dn[k]
                if blatt not in cache:
                    cache[blatt] = lies(blatt) or {}
                v = cache[blatt].get(zelle)
                if isinstance(v, (int, float)):
                    neu[k] = float(v)
    except (KeyError, ET.ParseError):
        pass
    g = d.setdefault("gwplan", {})
    g["anlagen"], g["wahl"] = anlagen, wahl
    if neu:
        g["annahmen"] = {k: v for k, v in neu.items() if v != GWP_STANDARD[k]}
    speichere(d)
    r = gwplan_berechnen(d)
    r["log"] = [f"✔ Aus Excel übernommen: {len(anlagen)} Sparten, {len(wahl)} mit eigener Zuordnung, {len(neu)} Annahmen."] + r["log"]
    journal(f"Netzplanung aus Excel übernommen: {len(anlagen)} Sparten")
    return r


# =============================================================== Webserver
class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def _lade(self):
        """Einstellungen laden; ist die Datenbank weg, verständliche Antwort statt Verbindungsabbruch"""
        try:
            return lade()
        except Fehler as e:
            if self.path.split("?")[0] == "/":
                self._send(503, ("<!doctype html><meta charset='utf-8'><title>SparteNet Manager</title><body style='font-family:sans-serif;padding:24px'>"
                                 "<h2>Datenspeicher nicht erreichbar</h2><p>" + str(e).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;") + "</p>"
                                 "<p>Bitte die Datenbank prüfen und die Seite neu laden.</p>").encode("utf-8"), "text/html")
            else:
                self._send(503, {"fehler": str(e)})
            return None

    def _send(self, code, daten, typ="application/json", extra=None):
        roh = daten if isinstance(daten, bytes) else json.dumps(daten, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", typ + ("; charset=utf-8" if typ.startswith(("text/", "application/json", "application/javascript", "application/manifest")) else ""))
        self.send_header("Content-Length", str(len(roh)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff"); self.send_header("Referrer-Policy", "no-referrer"); self.send_header("X-Frame-Options", "SAMEORIGIN")
        for k, v in (extra or {}).items():
            for wert in v if isinstance(v, (list, tuple)) else (v,):
                self.send_header(k, wert)
        self.end_headers(); self.wfile.write(roh)

    def _fern(self):
        """True, wenn die Anfrage nicht direkt von diesem PC kommt (Heimnetz, Tailscale, Weiterleitung, fremder Hostname)."""
        weiter = any(self.headers.get(k) for k in ("X-Forwarded-For", "X-Forwarded-Host", "Forwarded", "X-Real-IP", "Tailscale-User-Login"))
        host = (self.headers.get("Host") or "").lower()
        return weiter or self.client_address[0] not in ("127.0.0.1", "::1", "::ffff:127.0.0.1") or host not in (f"127.0.0.1:{PORT}", f"localhost:{PORT}")

    def _sitzung(self):
        c = SimpleCookie()
        try:
            c.load(self.headers.get("Cookie") or "")
        except CookieError:
            return ""
        return c["sn_sitzung"].value if "sn_sitzung" in c else ""

    def _auth_sitzung(self):
        c = SimpleCookie()
        try:
            c.load(self.headers.get("Cookie") or "")
        except CookieError:
            return ""
        return c["sn_auth"].value if "sn_auth" in c else ""

    def _erlaubt(self, d):
        return auth_sitzung_ok(self._auth_sitzung()) or (self._fern() and sitzung_ok(d, self._sitzung()))

    def _statisch(self, pfad):
        if pfad in PWA_ICONS:
            return self._send(200, PWA_ICONS[pfad][0], "image/png")
        if pfad == "/manifest.webmanifest":
            return self._send(200, json.dumps(MANIFEST, ensure_ascii=False).encode("utf-8"), "application/manifest+json")
        if pfad == "/sw.js":
            return self._send(200, SW_JS.replace("__VERSION__", VERSION).encode("utf-8"), "application/javascript")
        if pfad == "/offline.html":
            return self._send(200, OFFLINE_HTML.encode("utf-8"), "text/html")
        return None

    def do_GET(self):
        u = urllib.parse.urlparse(self.path)
        if u.path in PWA_ICONS or u.path in ("/manifest.webmanifest", "/sw.js", "/offline.html"):
            return self._statisch(u.path)
        d = self._lade()
        if d is None:
            return
        if u.path == "/":
            if not self._erlaubt(d):
                return self._send(200, LOGIN_HTML.replace("__INHALT__", LOGIN_FORM).encode("utf-8"), "text/html")
            fern_nur = self._fern() and not auth_sitzung_ok(self._auth_sitzung())
            return self._send(200, HTML.replace("__TOKEN__", TOKEN).replace("__VERSION__", VERSION).replace("__FERN__", "1" if fern_nur else "0")
                              .replace("__SITZUNG_TAGE__", str(SITZUNG_TAGE)).encode("utf-8"), "text/html")
        if not self._erlaubt(d):
            return self._send(401, {"fehler": "anmelden"})
        if self.headers.get("X-Token") != TOKEN:
            return self._send(403, {"fehler": "nicht erlaubt"})
        self._antwort(u.path, urllib.parse.parse_qs(u.query), None, b"")

    def _anmelden(self):
        try:
            n = int(self.headers.get("Content-Length") or 0)
        except ValueError:
            return self._send(400, {"fehler": "Ungültige Anfrage."})
        if n < 0 or n > 4096:
            return self._send(413, {"fehler": "Anfrage zu groß."})
        try:
            b = json.loads(self.rfile.read(n) or b"{}")
        except (ValueError, UnicodeDecodeError):
            return self._send(400, {"fehler": "Ungültige Anfrage."})
        if not isinstance(b, dict):
            return self._send(400, {"fehler": "Ungültige Anfrage."})
        d = self._lade()
        if d is None:
            return
        geheim = b.get("passwort", b.get("pin"))
        try:
            passwort_pruefen(geheim, self.client_address[0])
            t = auth_sitzung_neu(b.get("geraet"))
            cookie = f"sn_auth={t}"
            LOG.info("Manager-Anmeldung erfolgreich")
        except Fehler as passwort_fehler:
            if not self._fern() or not fern_daten(d)["pin"].get("hash"):
                return self._send(400, {"fehler": str(passwort_fehler)})
            try:
                pin_pruefen(d, geheim)
            except Fehler as pin_fehler:
                return self._send(400, {"fehler": str(pin_fehler)})
            t = sitzung_neu(d, b.get("geraet"))
            cookie = f"sn_sitzung={t}"
            LOG.info("Anmeldung vom Handy/Tablet erfolgreich")
            journal("Handy/Tablet angemeldet: " + str(b.get("geraet") or "?")[:80])
        sicher = "; Secure" if (self.headers.get("X-Forwarded-Proto") == "https" or self.headers.get("Tailscale-User-Login")) else ""
        return self._send(200, {"ok": True}, extra={"Set-Cookie": f"{cookie}; Path=/; Max-Age={SITZUNG_TAGE * 86400}; HttpOnly; SameSite=Strict{sicher}"})

    def do_POST(self):
        u = urllib.parse.urlparse(self.path)
        if u.path == "/login":
            return self._anmelden()
        d = self._lade()
        if d is None:
            return
        if u.path == "/abmelden":
            auth_sitzung_entfernen(self._auth_sitzung())
            t = self._sitzung()
            if t and fern_daten(d)["sitzungen"].pop(_sitzung_hash(t), None):
                speichere(d)
            return self._send(200, {"ok": True}, extra={"Set-Cookie": ["sn_auth=; Path=/; Max-Age=0; HttpOnly; SameSite=Strict", "sn_sitzung=; Path=/; Max-Age=0; HttpOnly; SameSite=Strict"]})
        if not self._erlaubt(d):
            return self._send(401, {"fehler": "anmelden"})
        if self.headers.get("X-Token") != TOKEN:
            return self._send(403, {"fehler": "nicht erlaubt"})
        roh = self.rfile.read(int(self.headers.get("Content-Length") or 0))
        body = None if u.path in ("/api/excel", "/api/logo", "/api/kalk-import", "/api/gwplan-import") else json.loads(roh or b"{}")
        self._antwort(u.path, {}, body, roh)

    def _antwort(self, pfad, q, b, roh):
        if pfad in ("/api/ppsk-speichern", "/api/fern"):
            LOG.info("Aktion %s (Inhalt nicht protokolliert)", pfad)
        elif pfad not in ("/api/log", "/api/karten-vorschau"):
            LOG.info("Aktion %s %s", pfad, json.dumps(_maskiere(b), ensure_ascii=False)[:500] if isinstance(b, (dict, list)) else (urllib.parse.urlencode(q, doseq=True) if q else ""))
        try:
            d = lade()
            if self._fern() and not auth_sitzung_ok(self._auth_sitzung()) and (pfad in ("/api/fern", "/api/tailscale", "/api/beenden", "/api/log-loeschen", "/api/konsolen") or (pfad == "/api/einstellungen" and b is not None)):
                raise Fehler("Diese Einstellung lässt sich nur direkt am PC ändern.")
            if pfad == "/api/einstellungen":
                if b is None:
                    return self._send(200, {"konsole_id": d["konsole_id"], "konsole_name": d["konsole_name"], "cloud_key_gesetzt": bool(d["cloud_key"]),
                                            "log_aktiv": d["log_aktiv"], "logdatei": LOGDATEI, "speicher": speicher_text(), "ansicht": ansicht_pruefen(d.get("ansicht"))})
                if "log_aktiv" in b:
                    d["log_aktiv"] = bool(b["log_aktiv"]); speichere(d); log_einrichten(d["log_aktiv"])
                    return self._send(200, {"log": [f"✔ Protokoll {'eingeschaltet – Datei: ' + LOGDATEI if d['log_aktiv'] else 'ausgeschaltet'}"]})
                if b.get("cloud_key"):
                    d["cloud_key"] = b["cloud_key"].strip()
                for k in ("konsole_id", "konsole_name"):
                    if k in b:
                        d[k] = b[k]
                speichere(d); return self._send(200, {"log": ["✔ Verbindung gespeichert."]})
            if pfad == "/api/ansicht":
                d["ansicht"] = ansicht_pruefen(b); speichere(d)
                return self._send(200, {"ansicht": d["ansicht"]})
            if pfad == "/api/log":
                if not os.path.exists(LOGDATEI):
                    return self._send(200, {"log": ["(Protokolldatei ist leer oder noch nicht angelegt)"]})
                with open(LOGDATEI, encoding="utf-8", errors="replace") as f:
                    zeilen = f.read().splitlines()[-400:]
                return self._send(200, {"log": zeilen or ["(leer)"]})
            if pfad == "/api/log-loeschen":
                for i in range(0, 4):
                    pf = LOGDATEI + (f".{i}" if i else "")
                    if os.path.exists(pf):
                        open(pf, "w").close() if i == 0 else os.remove(pf)
                LOG.info("Protokoll geleert")
                return self._send(200, {"log": ["✔ Protokoll geleert."]})
            if pfad == "/api/konsolen":
                return self._send(200, {"konsolen": konsolen((b or {}).get("cloud_key") or d["cloud_key"])})
            if pfad == "/api/plan" and b is None:
                return self._send(200, {"roh": d["plan"], **plan_berechnen(d["plan"])})
            if pfad == "/api/plan":
                plan_berechnen(b); d["plan"] = b; speichere(d)
                return self._send(200, {"log": ["✔ Plan gespeichert."]})
            if pfad == "/api/excel":
                d["plan"] = excel_import(roh); speichere(d)
                return self._send(200, {"log": [f"✔ Aus Excel übernommen: {len(d['plan']['sparten'])} Sparten."]})
            if pfad == "/api/design" and b is None:
                return self._send(200, {"design": d["design"], "standard": DESIGN_STANDARD, "logo_uri": logo_daten_uri(d["design"]),
                                        "schriften": list(SCHRIFTEN)})
            if pfad == "/api/design":
                d["design"] = design_pruefen({**b.get("design", {}), "logo": d["design"]["logo"]}); speichere(d)
                return self._send(200, {"log": ["✔ Kartendesign gespeichert – wird ab jetzt für alle Zugangskarten verwendet."]})
            if pfad == "/api/logo":
                d["design"]["logo"] = logo_speichern(roh); speichere(d)
                return self._send(200, {"log": [f"✔ Logo übernommen ({len(roh) // 1024} KB)."], "logo_uri": logo_daten_uri(d["design"])})
            if pfad == "/api/logo-loeschen":
                logo_entfernen(); d["design"]["logo"] = ""; speichere(d)
                return self._send(200, {"log": ["✔ Logo entfernt."]})
            routen = {
                "/api/test": lambda: akt_test(d),
                "/api/lesen": lambda: akt_lesen(d, q.get("was", [""])[0]),
                "/api/abgleich": lambda: akt_abgleich(d, q.get("sparte", [""])[0]),
                "/api/netze": lambda: akt_netze(d, b["sparte"], bool(b.get("ausfuehren")), bool(b.get("nur_eins"))),
                "/api/ppsk": lambda: akt_ppsk(d, b["sparte"], b.get("art", "anzeigen")),
                "/api/schreibtest": lambda: akt_schreibtest(d),
                "/api/vergleich": lambda: akt_vergleich(d, q.get("sparte", [""])[0]),
                "/api/uebertragen": lambda: akt_uebertragen(d, b["sparte"], b.get("parzellen") or [], b.get("netze") or [], bool(b.get("ausfuehren"))),
                "/api/rueckgaengig": lambda: akt_rueckgaengig(d, b["sparte"]),
                "/api/journal": lambda: akt_journal(),
                "/api/ppsk-speichern": lambda: akt_ppsk_speichern(d, b["sparte"], b.get("aenderungen")),
                "/api/passwort": lambda: {"passwoerter": passwoerter_erzeugen(min(200, int(q.get("n", ["1"])[0])), d)},
                "/api/pw-regel": lambda: ({"regel": pw_regel(d)} if b is None else (d.__setitem__("pw_regel", {"praefix": str(b.get("praefix", "SN")), "ziffern": b.get("ziffern", 10)}) or speichere(d) or {"regel": pw_regel(d), "log": [f"✔ Regel gespeichert: {pw_regel(d)['praefix']} + {pw_regel(d)['ziffern']} Ziffern – gilt für alle neu erzeugten Passwörter."]})),
                "/api/system": lambda: akt_system(d),
                "/api/daten-liste": lambda: {"quellen": daten_liste()},
                "/api/daten": lambda: akt_daten(d, q.get("q", [""])[0], q.get("geheim", ["0"])[0] == "1"),
                "/api/daten-pruefen": lambda: akt_daten_pruefen(d),
                "/api/diagnose": lambda: akt_diagnose(d, bool(b.get("anonym", True))),
                "/api/ppsk-hochladen": lambda: akt_ppsk_hochladen(d, b["sparte"], bool(b.get("ausfuehren"))),
                "/api/karten": lambda: akt_karten(d, b["sparte"], b.get("auswahl", "alle")),
                "/api/karten-vorschau": lambda: akt_karten_vorschau(d, {**b.get("design", {}), "logo": d["design"]["logo"]}, bool(b.get("drucken"))),
                "/api/tarife": lambda: ({"tarife": tarife_pruefen(d["tarife"]), "modus": d.get("tarif_modus", "tarif"), "standard": TARIFE_STANDARD} if b is None else akt_tarife_speichern(d, b)),
                "/api/tarif-zuordnung": lambda: akt_tarif_zuordnen(d, b.get("aenderungen")),
                "/api/tarif-vergleich": lambda: akt_tarif_vergleich(d),
                "/api/tarif-erkennen": lambda: akt_tarif_erkennen(d),
                "/api/tarif-uebertragen": lambda: akt_tarif_uebertragen(d, b.get("netze") or [], b.get("regeln") or [], bool(b.get("ausfuehren"))),
                "/api/tarif-rueckgaengig": lambda: akt_tarif_rueckgaengig(d),
                "/api/kalkulation": lambda: akt_kalkulation(d, q.get("prognose", ["0"])[0] == "1"),
                "/api/kalk-annahmen": lambda: akt_kalk_annahmen(d, b),
                "/api/kalk-sparte": lambda: akt_kalk_sparte(d, b),
                "/api/kalk-import": lambda: akt_kalk_import(d, roh),
                "/api/gwplan": lambda: gwplan_berechnen(d),
                "/api/gwplan-sparte": lambda: akt_gwplan_sparte(d, b),
                "/api/gwplan-annahmen": lambda: akt_gwplan_annahmen(d, b),
                "/api/gwplan-zuruecksetzen": lambda: akt_gwplan_zuruecksetzen(d, (b or {}).get("was")),
                "/api/gwplan-import": lambda: akt_gwplan_import(d, roh),
                "/api/buchungen": lambda: akt_buchungen(d, q.get("sparte", [""])[0]) if b is None else akt_buchungen_speichern(d, b.get("sparte", ""), b.get("aenderungen")),
                "/api/fern": lambda: akt_fern(d) if b is None else akt_fern_speichern(d, b),
                "/api/tailscale": lambda: akt_tailscale(bool(b.get("an"))),
                "/api/start": lambda: akt_start(d),
                "/api/parzelle": lambda: akt_parzelle(d, q.get("sparte", [""])[0], q.get("p", [""])[0]),
                "/api/voucher": lambda: akt_voucher(d, b.get("anzahl", 10), b.get("minuten", 1440), b.get("name", "Gast"), bool(b.get("ausfuehren"))),
            }
            if pfad in routen:
                return self._send(200, routen[pfad]())
            if pfad == "/api/beenden":
                self._send(200, {"log": ["Beendet."]})
                threading.Thread(target=lambda: (time.sleep(0.5), os._exit(0)), daemon=True).start(); return
            self._send(404, {"fehler": "unbekannt"})
        except Fehler as e:
            LOG.warning("Meldung an Benutzer: %s", e)
            self._send(400, {"fehler": str(e)})
        except Exception as e:
            LOG.error("Unerwarteter Fehler bei %s:\n%s", pfad, traceback.format_exc())
            self._send(500, {"fehler": f"Unerwarteter Fehler: {type(e).__name__}: {e}" + (" – Details in der Protokolldatei." if lade()["log_aktiv"] else " – Protokoll einschalten (Verbindung) und erneut versuchen.")})


def main():
    global SERVER_HOST
    if not AUTH_PASSWORD:
        raise SystemExit("Zugriffsschutz fehlt: SPARTENET_PASSWORD oder SPARTENET_PASSWORD_FILE setzen.")
    if len(AUTH_PASSWORD) < 12:
        raise SystemExit("Das Manager-Passwort muss mindestens 12 Zeichen lang sein.")
    datenbank_starten()
    d = lade()
    log_einrichten(d["log_aktiv"])
    f = fern_daten(d)
    if HOST_OVERRIDE not in (None, "0.0.0.0", "127.0.0.1"):
        raise SystemExit("SPARTENET_HOST muss 127.0.0.1 oder 0.0.0.0 sein.")
    SERVER_HOST = HOST_OVERRIDE or ("0.0.0.0" if f["lan"] else "127.0.0.1")
    try:
        srv = ThreadingHTTPServer((SERVER_HOST, PORT), Handler)
    except OSError:
        print(f"Port {PORT} belegt – läuft der Manager schon? http://127.0.0.1:{PORT}")
        webbrowser.open(f"http://127.0.0.1:{PORT}"); return
    url = f"http://127.0.0.1:{PORT}"
    print(f"Datenspeicher: {speicher_text()}")
    print(f"SparteNet Manager {VERSION} (Cloud) läuft: {url}\nFenster offen lassen. Beenden mit Strg+C oder im Browser „Beenden“.")
    if SERVER_HOST == "0.0.0.0":
        print("Handy/Tablet im Heimnetz: " + ", ".join(f"http://{ip}:{PORT}" for ip in lan_adressen()) + " (Manager-Passwort oder Handy-PIN)")
    if not os.environ.get("SPARTENET_KEIN_BROWSER"):
        threading.Timer(0.8, lambda: webbrowser.open(url)).start()
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        print("Beendet.")



# =============================================================== Oberfläche
HTML = r"""<!doctype html><html lang="de"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<meta name="theme-color" content="#1d2f3e"><link rel="manifest" href="/manifest.webmanifest"><link rel="icon" href="/favicon.png"><link rel="apple-touch-icon" href="/apple-touch-icon.png">
<meta name="apple-mobile-web-app-capable" content="yes"><meta name="mobile-web-app-capable" content="yes"><meta name="apple-mobile-web-app-title" content="SparteNet"><meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
<title>SparteNet Manager</title>
<style>
:root{--navy:#1d2f3e;--green:#3a9a1f;--lgreen:#e7f3e1;--bg:#f5f7f4;--line:#d9e0d6;--red:#b42318;--amber:#9a6700;--text:#1d2f3e;--muted:#5d6b75}
*{box-sizing:border-box}body{margin:0;font-family:system-ui,-apple-system,Segoe UI,Roboto,Arial,sans-serif;background:var(--bg);color:var(--text)}
header{background:var(--navy);color:#fff;padding:14px 22px;display:flex;align-items:center;gap:16px;flex-wrap:wrap}
@media (max-width:600px){header{padding:12px 16px;gap:8px 12px}nav{padding:0 8px}nav button{padding:11px 10px}main{padding:16px}}
header b{font-size:22px}header b span{color:#6cc24a}header small{opacity:.7}#verb{font-size:13px;opacity:.85}
nav{display:flex;gap:4px;padding:0 22px;background:#fff;border-bottom:1px solid var(--line);flex-wrap:wrap}
nav button{border:0;background:none;padding:13px 16px;font-size:15px;cursor:pointer;color:var(--muted);border-bottom:3px solid transparent}
nav button.aktiv{color:var(--navy);border-bottom-color:var(--green);font-weight:600}
main{max-width:var(--main-b,1200px);margin:0 auto;padding:22px;position:relative}
#griff{position:absolute;top:0;right:0;width:12px;height:100%;cursor:ew-resize;z-index:5}#griff::after{content:"";position:absolute;top:calc(var(--vh,100vh) / 2);left:4px;width:4px;height:60px;margin-top:-30px;border-radius:3px;background:#c5cec1;opacity:.6}
#griff:hover::after,#griff.zieht::after{background:var(--green);opacity:1}
.teiler{cursor:col-resize;align-self:stretch;position:relative;min-height:200px}.teiler::after{content:"";position:absolute;top:40px;bottom:40px;left:2px;width:4px;border-radius:3px;background:#dfe5dc}.teiler:hover::after,.teiler.zieht::after{background:var(--green)}
body.zieht{user-select:none;cursor:ew-resize}body.zieht iframe{pointer-events:none}
main.mehrspaltig section.aktiv:not(#kartendesign):not(#daten){display:grid;grid-template-columns:repeat(auto-fill,minmax(min(100%,760px),1fr));gap:16px;align-items:start}
main.mehrspaltig section.aktiv:not(#kartendesign):not(#daten)>.karte{margin-bottom:0}
#ansicht{position:fixed;top:64px;right:16px;width:min(380px,calc(100vw - 32px));background:#fff;border:1px solid var(--line);border-radius:12px;box-shadow:0 10px 40px rgba(0,0,0,.22);padding:16px 18px;z-index:50;display:none;max-height:calc(var(--vh,100vh) - 90px);overflow:auto}
#ansicht.offen{display:block}#ansicht h3{margin:0 0 4px}#ansicht .feld output{font-size:13px}section{display:none}section.aktiv{display:block}
.karte{background:#fff;border:1px solid var(--line);border-radius:10px;padding:18px 20px;margin-bottom:16px}
h2{margin:0 0 6px;font-size:19px}h3{margin:0 0 8px;font-size:16px}p.hint{color:var(--muted);margin:4px 0 14px;font-size:14px}
label{display:block;font-size:13px;color:var(--muted);margin:10px 0 4px}
input,select{width:100%;padding:9px 10px;border:1px solid var(--line);border-radius:7px;font-size:15px;background:#fff}
.reihe{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:12px}
.knoepfe{display:flex;gap:8px;flex-wrap:wrap;margin-top:14px}
button.k{border:1px solid var(--navy);background:#fff;color:var(--navy);padding:9px 16px;border-radius:7px;font-size:14px;cursor:pointer}
label.k{display:inline-flex;align-items:center;border:1px solid var(--navy);background:#fff;color:var(--navy);padding:9px 16px;border-radius:7px;font-size:14px;cursor:pointer}
button.k:hover,label.k:hover{background:#eef2f5}button.p{background:var(--green);border-color:var(--green);color:#fff}button.p:hover{background:#318417}
button.r{background:var(--red);border-color:var(--red);color:#fff}button.r:hover{background:#8f1b13}button:disabled{opacity:.5;cursor:wait}
.log{background:#0f1a22;color:#d6f5c9;font-family:Consolas,monospace;font-size:13px;border-radius:8px;padding:12px;max-height:340px;overflow:auto;white-space:pre-wrap;margin-top:12px}
.log:empty{display:none}.fehler{color:#ffb4ab}
.tab{overflow:auto;max-height:var(--tab-h,520px);border:1px solid var(--line);border-radius:8px;margin-top:12px}.tab:empty{display:none}
table{border-collapse:collapse;width:100%;font-size:14px;background:#fff;font-variant-ligatures:none;font-feature-settings:"calt" 0,"liga" 0}
th{position:sticky;top:0;background:var(--navy);color:#fff;text-align:left;padding:8px 10px;font-weight:600;z-index:1}
td{padding:6px 10px;border-top:1px solid #eef1ec}tr.kopf td{background:#548235;color:#fff;font-weight:600}tr.dienst td{background:var(--lgreen)}
td input{padding:6px 8px;font-size:14px}.mono{font-family:Consolas,monospace}
.schritt{display:grid;grid-template-columns:44px 1fr;gap:14px;align-items:start}.schritt>div{min-width:0}.nr{width:40px;height:40px;border-radius:50%;background:var(--green);color:#fff;display:grid;place-items:center;font-weight:700}
.status{display:inline-block;padding:2px 8px;border-radius:12px;font-size:12px;background:#eee;color:#555;margin-left:6px}.status.ok{background:#dcf2d2;color:#24661a}
.kacheln{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:10px;margin-top:12px}
.kachel{border:1px solid var(--line);border-radius:8px;padding:10px 12px}.kachel b{font-size:24px;display:block}.kachel.gut b{color:var(--green)}.kachel.warn b{color:var(--amber)}.kachel.schlecht b{color:var(--red)}
.kd{display:grid;grid-template-columns:var(--kd-links,430px) 8px minmax(0,1fr);gap:8px;align-items:start}
.kd .karte{margin-bottom:12px;padding:14px 16px}.kd h3{margin-bottom:2px}
.kd .vorschau{position:sticky;top:12px}.kd iframe{width:100%;height:calc(var(--vh,100vh) - 150px);min-height:480px;border:1px solid var(--line);border-radius:10px;background:#8a949b}
.feld{display:grid;grid-template-columns:1fr auto;gap:4px 10px;align-items:center;margin-top:8px}.feld label{margin:0}
.feld input[type=range]{grid-column:1/3;padding:0}.feld output{font-size:13px;color:var(--text);font-variant-numeric:tabular-nums}
.feld input[type=color]{width:56px;height:32px;padding:2px;grid-column:2;grid-row:1}
.feld.chk{grid-template-columns:auto 1fr}.feld.chk input{width:auto}.feld.chk label{font-size:14px;color:var(--text)}
.feld textarea{grid-column:1/3;width:100%;padding:7px 9px;border:1px solid var(--line);border-radius:7px;font:inherit;font-size:14px;resize:vertical;min-height:38px}
.feld select{grid-column:1/3}.logo-mini{max-width:160px;max-height:70px;border:1px dashed var(--line);border-radius:6px;padding:4px;display:block;margin-top:8px}
#kd_status{font-size:13px;color:var(--muted)}#kd_status.dirty{color:var(--amber);font-weight:600}
@media (max-width:860px){.teiler,#griff{display:none}.kd{grid-template-columns:1fr}.kd .vorschau{position:static}.kd iframe{height:70vh}}
.pwleiste{display:flex;gap:8px;flex-wrap:wrap;align-items:center;margin-top:14px}.pwleiste input{max-width:260px}
#pw_st{font-size:13px;color:var(--muted);flex:1}#pw_st.dirty{color:var(--amber);font-weight:600}
td input.pwfeld{font-family:Consolas,'DejaVu Sans Mono',monospace;min-width:190px;font-variant-ligatures:none}
#tz_tab td:nth-child(2),#tz_tab td:nth-child(4),#tq_netz td:nth-child(2),#tq_qos td:nth-child(2){white-space:nowrap}#kk_tab td,#kk_tab th{white-space:nowrap}#kk_tab td:first-child{white-space:normal;min-width:150px}tr.geaendert td{background:#fff6dd}tr.falsch td{background:#fde8e6}tr.gesperrt td{color:var(--muted)}
#gp_tab td,#gp_tab th,#gp_st td,#gp_st th{white-space:nowrap}#gp_tab td:nth-child(2){white-space:normal;min-width:150px}#gp_st td:nth-child(3){white-space:normal;min-width:220px;font-size:12px}
.gp_in{width:64px;background:#fff8d6}.gp_in.w{width:84px}.gp_an h4{margin:14px 0 6px;color:var(--muted);font-size:13px}
.pwst{font-size:12px;white-space:nowrap}.pwst.f{color:var(--red)}.pwst.g{color:var(--amber)}
button.mini{border:1px solid var(--line);background:#fff;border-radius:6px;padding:4px 8px;font-size:12px;cursor:pointer;color:var(--navy);margin-right:3px}button.mini:hover{background:#eef2f5}
.balken{position:relative;height:16px;min-width:90px;background:#eef1ec;border-radius:8px;overflow:hidden}.balken i{position:absolute;inset:0 auto 0 0;background:var(--green)}
.balken i.w{background:#d4a017}.balken i.s{background:var(--red)}.balken span{position:relative;font-size:11px;padding-left:6px;line-height:16px;color:var(--text);font-weight:600}
.punkt{display:inline-block;width:9px;height:9px;border-radius:50%;background:#bbb;margin-right:6px}.punkt.on{background:var(--green)}.punkt.off{background:var(--red)}
.chart{position:relative;margin-top:8px}.chart svg{width:100%;height:auto;display:block}.chart .tip{position:absolute;pointer-events:none;background:var(--navy);color:#fff;font-size:12px;padding:6px 8px;border-radius:6px;white-space:nowrap;display:none;z-index:2}
.legende{display:flex;gap:16px;font-size:13px;color:var(--muted);margin-top:4px;flex-wrap:wrap}.legende b{display:inline-block;width:14px;height:4px;border-radius:2px;margin-right:6px;vertical-align:middle}
#sys_k .kachel b{font-size:21px;white-space:nowrap}#sys_ger td,#sys_ger th,#sys_top td{white-space:nowrap}
.kachel small{display:block;color:var(--muted);font-size:12px;margin-top:2px}
.dgrid{display:grid;grid-template-columns:var(--d-links,270px) 8px minmax(0,1fr);gap:8px;align-items:start}
.dliste{background:#fff;border:1px solid var(--line);border-radius:10px;padding:8px;max-height:calc(var(--vh,100vh) - 140px);overflow:auto;position:sticky;top:12px}
.dliste h4{margin:10px 8px 4px;font-size:12px;text-transform:uppercase;letter-spacing:.5px;color:var(--muted)}
.dliste button{display:flex;width:100%;justify-content:space-between;gap:8px;border:0;background:none;text-align:left;padding:7px 8px;border-radius:6px;font-size:14px;cursor:pointer;color:var(--text)}
.dliste button:hover{background:#eef2f5}.dliste button.aktiv{background:var(--lgreen);font-weight:600}
.dliste button em{font-style:normal;font-size:11px;padding:1px 7px;border-radius:10px;background:#eee;color:#666;align-self:center}.dliste button em.ok{background:#dcf2d2;color:#24661a}.dliste button em.nein{background:#fde8e6;color:var(--red)}
pre.json{background:#0f1a22;color:#d6f5c9;font-size:12.5px;border-radius:8px;padding:12px;max-height:620px;overflow:auto;margin-top:12px}
td.zelle{max-width:340px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
@media (max-width:860px){.dgrid{grid-template-columns:1fr}.dliste{position:static;max-height:300px}}

/* ---- Handy, Tablet, Fold */
header{padding-top:max(14px,env(safe-area-inset-top));padding-left:max(22px,env(safe-area-inset-left));padding-right:max(22px,env(safe-area-inset-right))}
nav{position:sticky;top:0;z-index:20}
@media (max-width:760px){
 header{padding:max(10px,env(safe-area-inset-top)) max(14px,env(safe-area-inset-right)) 10px max(14px,env(safe-area-inset-left));gap:6px 10px}
 header b{font-size:19px}header small{display:none}#verb{flex-basis:100%;order:9;font-size:12px}
 header .k{padding:7px 11px;font-size:13px}
 nav{flex-wrap:nowrap;overflow-x:auto;scrollbar-width:none;-webkit-overflow-scrolling:touch;padding:0 6px;gap:0;box-shadow:0 2px 6px rgba(0,0,0,.06)}
 nav::-webkit-scrollbar{display:none}nav button{white-space:nowrap;flex:0 0 auto;padding:12px 12px;font-size:14px}
 main{padding:12px max(12px,env(safe-area-inset-right)) calc(16px + env(safe-area-inset-bottom)) max(12px,env(safe-area-inset-left))}
 .karte{padding:14px;border-radius:12px;margin-bottom:12px}h2{font-size:18px}
 .knoepfe .k{flex:1 1 auto}.log{font-size:12px;max-height:260px}
 .kacheln{grid-template-columns:repeat(auto-fit,minmax(130px,1fr))}.kachel b{font-size:21px}
}
@media (max-width:360px){nav button{padding:12px 9px;font-size:13px}.kacheln{grid-template-columns:repeat(2,minmax(0,1fr))}.kachel{padding:8px;overflow-wrap:anywhere}.kachel b,#sys_k .kachel b{font-size:17px;white-space:normal}}
@media (pointer:coarse){#griff,.teiler{display:none}}
#logpfad{overflow-wrap:anywhere}
@media (pointer:coarse){button.k,label.k{min-height:44px}nav button{min-height:46px}input,select{font-size:16px;min-height:44px}td input,td select{min-height:38px}button.mini{padding:8px 10px;font-size:13px}}
@media (display-mode:standalone){#beenden_k{display:none}}
.schnell{display:grid;grid-template-columns:repeat(auto-fill,minmax(140px,1fr));gap:10px;margin-top:8px}
.schnell button{border:1px solid var(--line);background:#fff;border-radius:12px;padding:16px 10px;font-size:15px;cursor:pointer;color:var(--navy);text-align:center;min-height:70px}
.schnell button:hover{background:var(--lgreen)}.schnell button b{display:block;font-size:22px;margin-bottom:4px}
.pz{display:grid;grid-template-columns:minmax(0,1fr) minmax(170px,260px);gap:16px;align-items:center;margin-top:14px;border:2px solid var(--green);border-radius:14px;padding:16px}
.pz .qr svg{width:100%;height:auto;display:block;background:#fff}.pz dl{margin:0;display:grid;grid-template-columns:auto 1fr;gap:6px 12px;font-size:15px}.pz dt{color:var(--muted)}.pz dd{margin:0;font-weight:600;overflow-wrap:anywhere}
.pz .pw{font-family:Consolas,'DejaVu Sans Mono',monospace;font-size:24px;letter-spacing:1px;background:var(--lgreen);border-radius:8px;padding:8px 10px;margin:10px 0;overflow-wrap:anywhere;font-variant-ligatures:none}
@media (max-width:560px){.pz{grid-template-columns:1fr}.pz .qr{max-width:260px;margin:0 auto;width:100%}}
.code{font-family:Consolas,monospace;font-size:30px;font-weight:700;letter-spacing:3px;text-align:center;background:var(--lgreen);border-radius:10px;padding:14px;margin-top:12px}
.qrs{display:flex;gap:16px;flex-wrap:wrap;margin-top:12px}.qrs figure{margin:0;border:1px solid var(--line);border-radius:10px;padding:10px;text-align:center;width:220px}.qrs svg{width:180px;height:180px}
.qrs figcaption{font-size:13px;overflow-wrap:anywhere;margin-top:6px}.fern-nur{display:none}body.fern .fern-nur{display:block}body.fern .pc-nur{display:none!important}
.hinweis{background:#fff6dd;border:1px solid #f0d58a;border-radius:8px;padding:10px 12px;font-size:14px;margin-top:10px}
@media print{header,nav,.karte:not(.druck),.log{display:none!important}main{padding:0}}
</style></head><body>
<header><b>Sparte<span>Net</span></b><small>Manager __VERSION__ · Cloud</small><span id="verb"></span><div style="flex:1"></div><button class="k" style="background:none;color:#fff;border-color:#fff" onclick="ansichtPanel()" title="Breite, Größe und Tabellenhöhe an den Bildschirm anpassen">Ansicht</button><button class="k pc-nur" id="beenden_k" style="background:none;color:#fff;border-color:#fff" onclick="beenden()">Beenden</button></header>
<div id="ansicht"><h3>Ansicht anpassen</h3><p class="hint" style="margin:2px 0 6px">Für FHD bis 8K, normal oder curved. Wird gespeichert. Breite auch direkt am rechten Rand ziehen (Doppelklick = volle Breite).</p>
<div class="feld"><label for="an_breite_sel">Breite des Inhalts</label><output id="an_breite_o"></output><select id="an_breite_sel" onchange="ansSet('breite',+this.value)"><option value="1200">Standard (FHD)</option><option value="1600">Breit (WQHD)</option><option value="2200">Sehr breit (4K)</option><option value="3200">Ultra (5K / Curved)</option><option value="0">Volle Fensterbreite</option><option value="-1">Eigene …</option></select>
<input type="range" id="an_breite" min="800" max="6000" step="50" oninput="ansSet('breite',+this.value)"></div>
<div class="feld"><label for="an_zoom_sel">Größe (Skalierung)</label><output id="an_zoom_o"></output><select id="an_zoom_sel" onchange="ansSet('zoom',+this.value)"><option value="0">Automatisch nach Bildschirm</option><option value="0.8">80 %</option><option value="0.9">90 %</option><option value="1">100 %</option><option value="1.1">110 %</option><option value="1.25">125 %</option><option value="1.5">150 %</option><option value="1.75">175 %</option><option value="2">200 %</option><option value="2.5">250 %</option><option value="3">300 %</option></select></div>
<div class="feld"><label for="an_tabh_sel">Höhe der Tabellen</label><output id="an_tabh_o"></output><select id="an_tabh_sel" onchange="ansSet('tabh',+this.value)"><option value="0">An Fensterhöhe anpassen</option><option value="320">Niedrig</option><option value="520">Standard</option><option value="900">Hoch</option><option value="-1">Eigene …</option></select>
<input type="range" id="an_tabh" min="200" max="3000" step="20" oninput="ansSet('tabh',+this.value)"></div>
<div class="feld chk"><input type="checkbox" id="an_spalten" onchange="ansSet('spalten',this.checked)"><label for="an_spalten">Karten nebeneinander, wenn Platz ist (breite Monitore)</label></div>
<div class="knoepfe"><button class="k" onclick="ansZurueck()">Zurücksetzen</button><button class="k p" onclick="ansichtPanel(false)">Fertig</button></div></div>
<nav id="nav"></nav>
<main id="main"><div id="griff" title="Ziehen: Breite ändern · Doppelklick: volle Breite / Standard"></div>
<section id="start"><div class="karte"><div style="display:flex;align-items:center;gap:10px;flex-wrap:wrap"><h2 style="flex:1;margin:0">Überblick <span id="st_zeit" class="status"></span></h2><button class="k" onclick="startLaden()">Aktualisieren</button></div>
<div class="kacheln" id="st_k"></div><div class="log" id="log_start"></div></div>
<div class="karte"><h3>Parzelle nachschlagen</h3><p class="hint">WLAN-Name, Passwort und QR-Code einer Parzelle – zum Zeigen, Scannen lassen oder Teilen.</p>
<div class="reihe"><div><label for="st_sp">Sparte</label><select id="st_sp"></select></div><div><label for="st_p">Parzelle</label><input id="st_p" type="number" inputmode="numeric" min="1" max="199" placeholder="z. B. 47" onkeydown="if(event.key=='Enter')parzelleZeigen()"></div></div>
<div class="knoepfe"><button class="k p" onclick="parzelleZeigen()">Anzeigen</button></div><div class="log" id="log_pz"></div><div id="pz_karte"></div></div>
<div class="karte"><h3>Gast-Voucher schnell</h3><p class="hint">Erstellt einen Code für das Gäste-WLAN.</p>
<div class="knoepfe"><button class="k" onclick="schnellVoucher(120)">2 Stunden</button><button class="k" onclick="schnellVoucher(1440)">1 Tag</button><button class="k" onclick="schnellVoucher(10080)">1 Woche</button></div>
<div class="log" id="log_sv"></div><div id="sv_code"></div></div>
<div class="karte"><h3>Schnellzugriff</h3><div class="schnell">
<button onclick="zeige('tarife')"><b>⇅</b>Tarife</button><button onclick="zeige('uebertragen')"><b>⇪</b>Übertragen</button><button onclick="zeige('einrichten')"><b>⚿</b>Passwörter</button>
<button onclick="zeige('voucher')"><b>✉</b>Gast-Voucher</button><button onclick="zeige('system')"><b>▤</b>Systeminfo</button><button onclick="zeige('abgleich')"><b>✓</b>Abgleich</button></div>
<div class="knoepfe" id="install_k" style="display:none"><button class="k p" onclick="installieren()">Als App auf diesem Gerät installieren</button></div></div></section>

<section id="verbindung"><div class="karte fern-nur"><h2>Am Handy angemeldet</h2><p class="hint">Verbindung, API-Key, PIN und Heimnetz-Zugriff lassen sich nur am PC ändern. Alles andere geht hier genauso.</p>
<div class="knoepfe"><button class="k" onclick="abmelden()">Auf diesem Gerät abmelden</button></div></div>
<div class="karte pc-nur" id="fern_karte"><h2>Handy &amp; Tablet (App)</h2>
<p class="hint">Den Manager auf Handy, Tablet oder Fold als App nutzen. Er läuft weiter auf diesem PC – das Handy ist nur die Bedienung. Schutz: Manager-Passwort, optional Handy-PIN; Anmeldung bleibt __SITZUNG_TAGE__ Tage gültig.</p>
<h3>1. Optionale Handy-PIN festlegen</h3><div class="reihe" style="max-width:640px"><div><label for="fern_pin">Neue PIN (6–32 Zeichen) <span id="fern_pin_st" class="status"></span></label><input id="fern_pin" type="password" autocomplete="new-password" placeholder="z. B. 6–8 Ziffern"></div></div>
<div class="knoepfe"><button class="k p" onclick="fernPin()">PIN speichern</button><button class="k" onclick="fernAbmelden()">Alle Geräte abmelden</button></div>
<div id="fern_geraete" class="hint" style="margin-top:8px"></div>
<h3 style="margin-top:18px">2. Zugriff wählen</h3>
<div class="reihe"><div style="border:1px solid var(--line);border-radius:10px;padding:12px"><b>Von überall – mit Tailscale (empfohlen)</b>
<p class="hint">Verschlüsselt, auch aus der Gartensparte über Mobilfunk, und nur hier wird es eine echte App (HTTPS). Tailscale kostenlos auf PC und Handy installieren, mit demselben Konto anmelden, dann hier einschalten.</p>
<div id="ts_st" class="hint"></div><div class="knoepfe"><button class="k p" id="ts_an" onclick="tailscale(true)">Tailscale-Freigabe einschalten</button><button class="k" id="ts_aus" onclick="tailscale(false)">ausschalten</button></div></div>
<div style="border:1px solid var(--line);border-radius:10px;padding:12px"><b>Nur im eigenen WLAN/Heimnetz</b>
<p class="hint">Ohne Zusatzprogramm, aber nur wenn Handy und PC im selben Netz sind. Unverschlüsselt (http) – am Handy als Verknüpfung auf dem Startbildschirm statt echter App.</p>
<div class="feld chk"><input type="checkbox" id="fern_lan" onchange="fernLan()"><label for="fern_lan">Im Heimnetz erreichbar machen</label></div><div id="lan_st" class="hint"></div></div></div>
<h3 style="margin-top:18px">3. Auf dem Handy</h3>
<p class="hint">QR-Code mit der Kamera scannen → Manager-Passwort oder Handy-PIN eingeben → <b>Android (Chrome):</b> Menü ⋮ → „App installieren“ bzw. „Zum Startbildschirm hinzufügen“ · <b>iPhone/iPad (Safari):</b> Teilen □↑ → „Zum Home-Bildschirm“.</p>
<div class="qrs" id="fern_qr"></div><div class="knoepfe"><button class="k" onclick="fernLaden()">Aktualisieren</button></div><div class="log" id="log_fern"></div></div>
<div class="karte"><h2>Verbindung über die UniFi-Cloud</h2>
<p class="hint">Kein lokaler Zugriff nötig – alles läuft über api.ui.com. Die Daten bleiben bei Ihnen (Datenordner oder eigene MariaDB-Datenbank).</p>
<div class="reihe"><div><label>Site-Manager-API-Key (unifi.ui.com → Einstellungen → API Keys) <span id="key_st" class="status"></span></label><input id="cloud_key" type="password" placeholder="leer lassen = unverändert"></div>
<div><label>Konsole</label><select id="konsole"><option value="">– erst „Konsolen laden“ –</option></select></div></div>
<div class="knoepfe"><button class="k" onclick="konsolenLaden()">Konsolen laden</button><button class="k p" onclick="speichern()">Speichern</button><button class="k" onclick="testen()">Verbindung testen</button></div>
<div class="log" id="log_v"></div></div>
<div class="karte"><h2>Datenspeicher</h2><p class="hint">Hier liegen Einstellungen, Planung, Buchungen, Passwörter je Parzelle, Sicherungen und das Änderungsprotokoll: <b id="speicherort">…</b></p></div>
<div class="karte"><h2>Protokoll zur Fehlersuche</h2><p class="hint">Zeichnet alle Anfragen an die Cloud mit Antwort und Fehlern in <span id="logpfad">SparteNet_Manager.log</span> auf (Passwörter und Key werden nicht gespeichert). Nur bei Bedarf einschalten.</p>
<label style="display:flex;align-items:center;gap:10px;font-size:15px;color:var(--text)"><input type="checkbox" id="log_aktiv" style="width:auto" onchange="logSchalten()"> Protokoll einschalten</label>
<div class="knoepfe"><button class="k" onclick="logZeigen()">Protokoll anzeigen</button><button class="k" onclick="logLoeschen()">Protokoll leeren</button></div>
<div class="log" id="log_datei"></div></div>
<div class="karte"><h2>Diagnose-Datei für die Fehlersuche</h2><p class="hint">Liest alle Antworten der Konsole einmal aus (nur lesend) und speichert sie als Datei. Der API-Key steht nicht darin, Passwörter, Schlüssel und E-Mail-Adressen werden entfernt. Diese Datei kannst du zur Fehlersuche weitergeben – den API-Key bitte nie.</p>
<label style="display:flex;align-items:center;gap:10px;font-size:15px;color:var(--text)"><input type="checkbox" id="diag_anon" style="width:auto" checked> Clientnamen und MAC-Adressen der Endgeräte anonymisieren</label>
<div class="knoepfe"><button class="k p" onclick="diagnose()">Diagnose-Datei erstellen</button></div><div class="log" id="log_diag"></div></div></section>

<section id="lesen"><div class="karte"><h2>Auslesen</h2>
<div class="knoepfe"><button class="k" onclick="lesen('geraete')">Geräte</button><button class="k" onclick="lesen('clients')">Clients</button><button class="k" onclick="lesen('netze')">Netze / VLANs</button>
<button class="k" onclick="lesen('wlans')">WLANs</button><button class="k" onclick="lesen('voucher')">Voucher</button><button class="k p" onclick="csvSpeichern(LETZT,'export')">Als CSV</button></div>
<div class="log" id="log_l"></div><div class="tab" id="tab_l"></div></div></section>

<section id="planung"><div class="karte"><h2>Sparten am Gateway</h2><p class="hint">Hier direkt eintragen und speichern – oder aus dem VLAN-Planer (Excel) übernehmen. Reihenfolge = Steckplatz, neue Sparten immer unten anhängen.</p>
<div class="reihe"><div><label>Gateway-Nummer</label><input id="p_gw" type="number" min="1" max="254"></div><div><label>Gateway-Bezeichnung</label><input id="p_gwname"></div><div><label>WLAN-Präfix</label><input id="p_pre"></div></div>
<div class="tab" id="p_tab"></div>
<div class="knoepfe"><button class="k p" onclick="planSpeichern()">Speichern</button><label style="margin:0;display:flex;align-items:center;gap:8px" class="k">Aus Excel übernehmen<input type="file" id="xls" accept=".xlsx" onchange="excelHoch()" style="display:none"></label></div>
<div class="log" id="log_p"></div></div>
<div class="karte druck"><h2>IP-Plan</h2><label>Sparte</label><select id="plan_sp" onchange="planZeigen()"></select>
<div class="knoepfe"><button class="k" onclick="csvSpeichern(PLANZ,'ip-plan')">Als CSV</button><button class="k" onclick="window.print()">Drucken</button></div><div class="tab" id="tab_p"></div></div></section>

<section id="abgleich"><div class="karte"><h2>Abgleich: Plan ↔ Gateway</h2><p class="hint">Fehlende und abweichende Netze, Geräte und Endgeräte im falschen Netz. Nur lesend.</p>
<label>Sparte</label><select id="ab_sp"></select>
<div class="knoepfe"><button class="k p" onclick="abgleich()">Abgleich starten</button></div>
<div class="log" id="log_a"></div><div class="kacheln" id="kach_a"></div>
<h3 style="margin-top:18px" id="h_hin"></h3><div class="tab" id="tab_hin"></div>
<h3 style="margin-top:18px" id="h_feh"></h3><div class="tab" id="tab_feh"></div>
<h3 style="margin-top:18px" id="h_abw"></h3><div class="tab" id="tab_abw"></div>
<h3 style="margin-top:18px" id="h_cli"></h3><div class="tab" id="tab_cli"></div></div></section>

<section id="einrichten"><div class="karte"><h2>Sparte einrichten</h2><p class="hint">Immer zuerst „Vorschau“. Vor Änderungen eine Sicherung der Konsole machen.</p>
<label>Sparte</label><select id="ein_sp" onchange="ssid()"></select></div>
<div class="karte schritt"><div class="nr">1</div><div><h3>Fehlende Netze anlegen</h3><p class="hint">Vorlage ist ein vorhandenes Parzellennetz (z. B. BW-Paz.004): DHCP, Isolation, Firewall-Zone werden übernommen, nur Name, VLAN und Adressen geändert.</p>
<div class="knoepfe"><button class="k" onclick="netze(false,false)">Vorschau</button><button class="k p" onclick="netze(true,true)">Erstes Netz anlegen (Test)</button><button class="k r" onclick="netze(true,false)">Alle fehlenden anlegen</button></div></div></div>
<div class="karte schritt"><div class="nr">2</div><div><h3>WLANs prüfen</h3><p class="hint">Pächter <b id="ssid1"></b> (WPA2, PPSK) · Gäste <b id="ssid2"></b> (Hotspot/Voucher) · Vorstand <b id="ssid3"></b>.</p></div></div>
<div class="karte schritt"><div class="nr">3</div><div><h3>Passwörter je Parzelle</h3><p class="hint">Bereits verteilte Passwörter erst übernehmen, dann nur fehlende ergänzen. Gespeichert in PPSK_&lt;Kürzel&gt;.csv.</p>
<div class="knoepfe"><button class="k" onclick="ppsk('anzeigen')">Anzeigen</button><button class="k" onclick="ppsk('gateway')">Vom Gateway übernehmen</button><button class="k p" onclick="ppsk('fehlende')">Fehlende erzeugen</button>
<button class="k" onclick="ppsk('neu')">Alle neu erzeugen</button><button class="k" onclick="csvSpeichern(PPSK,'ppsk')">Als CSV</button></div>
<div class="pwleiste"><span style="font-size:14px">Regel für neue Passwörter:</span><input id="pr_pre" style="max-width:90px" maxlength="10"><span>+</span><input id="pr_z" type="number" min="6" max="30" style="max-width:80px"><span style="font-size:14px">Ziffern</span>
<span id="pr_bsp" class="mono" style="font-size:14px;color:var(--muted)"></span><button class="k" onclick="regelSpeichern()">Regel speichern</button></div>
<p class="hint" style="margin-top:6px">Jedes erzeugte Passwort ist einmalig – über alle Sparten und auch gegenüber früher vergebenen (Register nur als Prüfsumme gespeichert).</p>
<div id="pw_bereich" style="display:none"><p class="hint" style="margin-top:14px">Passwort direkt in der Tabelle ändern (8–63 Zeichen, keine Umlaute, jedes nur einmal). „neu“ = zufälliges Passwort, „sperren“ = Parzelle ohne Zugang, „↺“ = zurück. Erst <b>Änderungen speichern</b>, dann <b>Schritt 4</b>, damit es im WLAN gilt.</p>
<div class="pwleiste"><input id="pw_suche" placeholder="Suchen (Parzelle, Netz, Passwort)" oninput="pwFilter()"><span id="pw_st"></span>
<button class="k p" onclick="pwSpeichern()">Änderungen speichern</button><button class="k" onclick="pwVerwerfen()">Verwerfen</button></div>
<div class="tab" id="tab_pw"></div></div>
<h3 style="margin-top:16px">Zugangskarten mit WLAN-QR-Code</h3><p class="hint">Je Parzelle eine Seite, im gespeicherten Kartendesign. Erst „Anzeigen“ oder „Fehlende erzeugen“, dann in der Tabelle oben (Spalte „Drucken“) auswählen.</p>
<p class="hint">Format, Farben, Texte, QR-Größe und Logo: Reiter <a href="#" onclick="zeige('kartendesign');return false">Kartendesign</a>.</p>
<div class="knoepfe"><button class="k p" onclick="karten('alle')">Alle drucken</button><button class="k" onclick="karten('auswahl')">Ausgewählte drucken</button>
<button class="k" onclick="markiere(true)">Alle markieren</button><button class="k" onclick="markiere(false)">Keine markieren</button><button class="k" onclick="markiereGeaendert()">Zuletzt geänderte markieren</button></div></div></div>
<div class="karte schritt"><div class="nr">4</div><div><h3>Passwörter ins Pächter-WLAN laden</h3><p class="hint">Überträgt alle Unterschiede dieser Sparte (neu, geändert, gesperrt), mit Sicherung und Kontrolle. Einzelne Parzellen auswählen: Reiter <a href="#" onclick="zeige('uebertragen');return false">Übertragen</a>.</p>
<div class="knoepfe"><button class="k" onclick="schritt('ppsk-hochladen',false)">Vorschau</button><button class="k r" onclick="schritt('ppsk-hochladen',true)">Ausführen</button></div></div></div>
<div class="karte"><h3>Protokoll</h3><div class="log" id="log_e"></div><div class="tab" id="tab_e"></div></div></section>

<section id="uebertragen"><div class="karte"><h2>Änderungen an das Gateway übertragen</h2>
<p class="hint">Hier gehen alle Änderungen aus dem Manager über die UniFi-Cloud an das Gateway: fehlende Netze und Passwörter je Parzelle (neu, geändert, gesperrt). Immer erst „Unterschiede ermitteln“, dann auswählen und übertragen. Vor jeder Passwort-Übertragung wird der alte Stand gesichert.</p>
<div class="knoepfe"><button class="k" onclick="schreibtest()">1. Schreibzugriff prüfen</button></div><div class="log" id="log_st"></div></div>
<div class="karte"><h3>2. Unterschiede zwischen Manager und Gateway</h3><div class="reihe" style="max-width:520px"><div><label>Sparte</label><select id="ue_sp"></select></div></div>
<div class="knoepfe"><button class="k p" onclick="vergleich()">Unterschiede ermitteln</button></div><div class="log" id="log_ue"></div><div class="kacheln" id="ue_k"></div>
<div id="ue_bereich" style="display:none">
<h3 style="margin-top:16px" id="ue_h_netze"></h3><div class="tab" id="ue_netze"></div>
<h3 style="margin-top:16px" id="ue_h_ppsk"></h3><div class="tab" id="ue_ppsk"></div>
<div class="knoepfe"><button class="k" onclick="ueAlle(true)">Alle markieren</button><button class="k" onclick="ueAlle(false)">Keine markieren</button>
<button class="k" onclick="uebertragen(false)">Vorschau</button><button class="k r" onclick="uebertragen(true)">3. Ausgewählte übertragen</button></div></div>
<div class="knoepfe" style="margin-top:18px;border-top:1px solid var(--line);padding-top:14px"><button class="k" onclick="rueckgaengig()">Letzte Passwort-Übertragung rückgängig</button></div></div>
<div class="karte"><h3>Änderungsprotokoll</h3><p class="hint">Jede Übertragung mit Zeit und Ergebnis (ohne Passwörter) – Datei SparteNet_Aenderungen.log.</p>
<div class="knoepfe"><button class="k" onclick="journalZeigen()">Anzeigen</button></div><div class="log" id="log_jn"></div></div></section>

<section id="tarife"><div class="karte"><h2>Tarife</h2>
<p class="hint">Ein Tarif legt zwei Dinge fest: die <b>Bandbreite</b> (wird am Gateway als QoS-Regel „Geschwindigkeit begrenzen“ angelegt, die Netze des Tarifs werden darin eingetragen) und die <b>Netzgröße</b> (Subnetzmaske unter Netzwerke → Gateway-IP/Subnetz, dazu der passende DHCP-Bereich). „Endgeräte“ = Größe des DHCP-Bereichs, 0 = ganzer Bereich. Die Router-IP (z. B. 10.1.67.1) bleibt immer gleich.</p>
<div class="tab"><table id="tf_tab"></table></div>
<div class="knoepfe"><button class="k" onclick="tfNeu()">+ Tarif</button><button class="k" onclick="tfStandard()">Beispiel-Tarife einsetzen</button></div>
<div class="reihe" style="margin-top:12px"><div><label for="tf_modus">QoS-Regeln anlegen</label><select id="tf_modus" onchange="tfModusHint()"><option value="tarif">Eine Regel je Tarif – alle Netze des Tarifs in einer Regel</option><option value="netz">Eine Regel je Netz – jede Parzelle eine eigene Regel</option></select></div></div>
<p class="hint" id="tf_modus_hint"></p>
<div class="knoepfe"><button class="k p" onclick="tfSpeichern()">Tarife speichern</button></div><div class="log" id="log_tf"></div></div>

<div class="karte"><h3>Netze einem Tarif zuordnen</h3>
<p class="hint">Alle Netze vom Gateway (auch Vorstand, Gäste, Technik oder eigene) – jedes kann einen Tarif bekommen. Tarif wählen, „Zuordnung speichern“, dann unten übertragen. „Ist-Zustand erkennen“ schlägt für Parzellen ohne Tarif den passenden Tarif nach der heutigen Netzmaske vor.</p>
<div class="knoepfe"><button class="k p" onclick="tzLaden()">Netze laden &amp; Unterschiede ermitteln</button><button class="k" onclick="tzErkennen()">Ist-Zustand erkennen</button></div>
<div class="log" id="log_tz"></div><div class="kacheln" id="tz_k"></div>
<div id="tz_bereich" style="display:none">
<div class="reihe" style="margin-top:12px"><div><label for="tz_suche">Suchen</label><input id="tz_suche" placeholder="z. B. Paz. oder 10.1.5 oder Basic" oninput="tzFilter()"></div>
<div><label for="tz_massen">Für markierte Netze</label><div style="display:flex;gap:6px"><select id="tz_massen"></select><button class="k" onclick="tzMassen()">setzen</button></div></div></div>
<div class="tab" id="tz_tab"></div>
<div class="knoepfe"><button class="k" onclick="tzMarkAlle(true)">Sichtbare markieren</button><button class="k" onclick="tzMarkAlle(false)">Keine markieren</button><button class="k p" onclick="tzSpeichern()">Zuordnung speichern &amp; neu vergleichen</button><span id="tz_offen" class="status"></span></div>
</div></div>

<div class="karte"><h3>An das Gateway übertragen</h3>
<p class="hint">Zuerst oben „Unterschiede ermitteln“. QoS-Regeln, die der Manager anlegt, heißen „SparteNet-Tarif-…“ bzw. „SparteNet-Netz-…“ – andere QoS-Regeln am Gateway werden nie verändert. Vor jeder Übertragung wird der alte Stand gesichert.</p>
<h3 id="tq_h_qos" style="margin-top:12px"></h3><div class="tab" id="tq_qos"></div>
<h3 id="tq_h_netz" style="margin-top:12px"></h3><div class="tab" id="tq_netz"></div>
<div class="knoepfe" id="tq_kn" style="display:none"><button class="k" onclick="tqAlle(true)">Alle markieren</button><button class="k" onclick="tqAlle(false)">Keine markieren</button><button class="k" onclick="tqUebertragen(false)">Vorschau</button><button class="k r" onclick="tqUebertragen(true)">Ausgewählte übertragen</button></div>
<div class="log" id="log_tq"></div>
<div class="knoepfe" style="margin-top:18px;border-top:1px solid var(--line);padding-top:14px"><button class="k" onclick="tqRueckgaengig()">Letzte Tarif-Übertragung rückgängig</button></div></div>
</section>

<section id="kalkulation"><div class="karte"><div style="display:flex;gap:10px;align-items:center;flex-wrap:wrap"><h2 style="margin:0;flex:1">Kalkulation &amp; Auslastung</h2>
<label class="feld chk" style="margin:0;display:flex;gap:6px;align-items:center"><input type="checkbox" id="kk_prog" onchange="kkLaden()" style="width:auto"> Prognose für Sparten ohne Buchungen</label>
<button class="k p" onclick="kkLaden()">Berechnen</button></div>
<p class="hint">Gebuchte Parzellen × Tarifpreis je Sparte, Buchungsrate und Gesamtauslastung aller Sparten mit Buchungen. Kosten und Ergebnis nach den Annahmen der Kalkulation. Rechnet nur hier im Manager – am Gateway ändert sich nichts.</p>
<div class="kacheln" id="kk_k"></div><div class="log" id="log_kk"></div></div>
<div class="karte"><div style="display:flex;gap:10px;align-items:center;flex-wrap:wrap"><h3 style="margin:0;flex:1">Je Sparte</h3><button class="k" onclick="kkCsv()">Als CSV speichern</button></div>
<p class="hint">Investition, Masten mit Technik und Uplink je Sparte direkt in der Tabelle ändern (wird sofort gespeichert) oder aus der Kalkulation (Excel) übernehmen. Uplink leer = Standard aus den Annahmen.</p>
<div class="tab" id="kk_tab"></div></div>
<div class="karte"><h3>Buchungen erfassen</h3>
<p class="hint">Welche Parzelle welchen Tarif gebucht hat. Was im Reiter „Tarife“ einer Parzelle zugeordnet ist, steht automatisch hier – und umgekehrt. Ans Gateway (Bandbreite, Netzgröße) geht es über „Tarife“ → Übertragen.</p>
<div class="reihe"><div><label for="kb_sp">Sparte</label><select id="kb_sp" onchange="kbLaden()"></select></div>
<div><label for="kb_bereich">Parzellen (z. B. 1-20, 25, 31)</label><input id="kb_bereich" placeholder="1-20, 25"></div>
<div><label for="kb_tarif">Tarif</label><div style="display:flex;gap:6px"><select id="kb_tarif"></select><button class="k" onclick="kbMassen()">setzen</button></div></div></div>
<div class="kacheln" id="kb_k"></div><div class="tab" id="kb_tab"></div>
<div class="knoepfe"><button class="k p" onclick="kbSpeichern()">Buchungen speichern</button><button class="k" onclick="kbLaden(true)">Verwerfen</button><span id="kb_offen" class="status"></span></div><div class="log" id="log_kb"></div></div>
<div class="karte"><h3>Annahmen</h3><p class="hint">Aus der Kalkulation übernommen oder hier ändern. Tarifpreise (€ pro Jahr) stehen im Reiter „Tarife“.</p>
<div class="reihe" id="ka_form"></div><div class="knoepfe"><button class="k p" onclick="kaSpeichern()">Annahmen speichern</button></div><div class="log" id="log_ka"></div></div>
<div class="karte"><h3>Aus Excel übernehmen</h3><p class="hint"><b>Kalkulation</b> (Kalkulation_Sparten_WLAN.xlsx): Annahmen, Tarifpreise und je Sparten-Blatt Investition und Masten. <b>VLAN-Planer</b>: alle Sparten, die dort ein Gateway haben (Name, Kürzel, Parzellen, Gateway).</p>
<div class="knoepfe"><label class="k">Kalkulation oder VLAN-Planer wählen …<input type="file" id="kk_datei" accept=".xlsx" onchange="kkImport()" style="display:none"></label></div><div class="log" id="log_ki"></div></div>
</section>

<section id="netzplanung"><div class="karte"><div style="display:flex;gap:10px;align-items:center;flex-wrap:wrap"><h2 style="margin:0;flex:1">Netzplanung &amp; Einnahmen</h2>
<span id="gp_quelle" class="status"></span><button class="k" onclick="gpCsv()">Als CSV speichern</button><button class="k p" onclick="gpLaden()">Berechnen</button></div>
<p class="hint">Gateway-Standorte, Glasfaser von Sparte zu Sparte, 55 Parzellen je Gateway und einstellbare Buchungsquote – dieselbe Rechnung wie die Excel „Kleingarten_Gateway_Planung“. <b>Theoretische Einnahme</b> = Parzellen × Buchungsquote × Ø Tarifpreis. Rechnet nur hier im Manager – am Gateway ändert sich nichts.</p>
<div class="kacheln" id="gp_k"></div><div class="log" id="log_gp"></div></div>
<div class="karte"><h3>Einnahmen nach Tarif und Buchungsquote</h3>
<p class="hint">Preise aus dem Reiter „Tarife“. Der Tarifmix legt fest, wie sich die Kunden auf die Tarife verteilen (Anteile in %, werden auf 100 % umgerechnet). „Quote manuell“ in der Tabelle gilt immer vorrangig.</p>
<div class="reihe"><div><label for="gp_pq">Preis je Kunde</label><select id="gp_pq"><option value="tarife">nach Tarifmix</option><option value="fest">fester Preis (Einstellungen)</option></select></div>
<div><label for="gp_qm">Buchungsquote</label><select id="gp_qm"><option value="1">aus Alter und Leerstand</option><option value="2">feste Quote für alle</option></select></div>
<div><label for="gp_qf">Feste Quote (%)</label><input id="gp_qf" inputmode="decimal"></div>
<div><label for="gp_sz">Alter und Leerstand</label><select id="gp_sz"><option value="1">heute</option><option value="2">in 5 Jahren</option></select></div></div>
<div class="reihe" id="gp_mix" style="margin-top:10px"></div>
<div class="knoepfe"><button class="k p" onclick="gpSchnell()">Übernehmen</button></div>
<div class="tab" id="gp_tt"></div><div class="log" id="log_gps"></div></div>
<div class="karte"><div style="display:flex;gap:10px;align-items:center;flex-wrap:wrap"><h3 style="margin:0;flex:1">Je Sparte</h3>
<input id="gp_such" placeholder="Sparte suchen …" oninput="gpTabelle()" style="max-width:200px"><select id="gp_stf" onchange="gpTabelle()" style="max-width:220px"></select>
<label style="display:flex;gap:6px;align-items:center;margin:0"><input type="checkbox" id="gp_err" onchange="gpTabelle()" style="width:auto"> nur Fehler</label></div>
<p class="hint">Gelbe Felder werden sofort gespeichert. <b>Standort</b> = Nr. der Sparte, in der die Gateways stehen (eigene Nr. = selbst Standort). <b>Zuleitung von</b> = Nr. der Sparte, von der die Glasfaser kommt. <b>Reihenfolge</b> = welche Sparte die Gateways zuerst füllt. Kette A → B → C → D: alle Standort A, B Zuleitung A, C Zuleitung B, D Zuleitung C. Leer = Vorschlag bzw. berechneter Wert (grau).</p>
<div class="tab" id="gp_tab" style="--tab-h:640px"></div></div>
<div class="karte"><h3>Gateway-Standorte</h3><p class="hint">Alle Gateways eines Standorts teilen sich einen Internet-Anschluss – ein weiterer erst, wenn der Bedarf größer ist als die Kapazität.</p><div class="tab" id="gp_st"></div></div>
<div class="karte"><h3>Einstellungen</h3><p class="hint">Netz-Regeln, Buchungsquote, Kosten und Preise. Leeres Feld = Standardwert.</p><div id="gp_an"></div>
<div class="knoepfe"><button class="k p" onclick="gpAnSpeichern()">Einstellungen speichern</button><button class="k" onclick="gpReset('annahmen')">Auf Standard zurücksetzen</button></div><div class="log" id="log_gpa"></div></div>
<div class="karte"><h3>Aus Excel übernehmen</h3><p class="hint"><b>Kleingarten_Gateway_Planung.xlsx</b>: Sparten (Parzellen, Leerstand, Alter, Lage), Ihre gelben Spalten (Standort, Zuleitung, Reihenfolge, Quote …) und alle Annahmen. Ohne Import rechnet der Manager mit den eingebauten Daten aus dem Kleingartenentwicklungskonzept 2040.</p>
<div class="knoepfe"><label class="k">Gateway-Planung (Excel) wählen …<input type="file" id="gp_datei" accept=".xlsx" onchange="gpImport()" style="display:none"></label>
<button class="k" onclick="gpReset('wahl')">Eigene Zuordnungen löschen (Vorschlag)</button><button class="k" onclick="gpReset('daten')">Eingebaute Daten verwenden</button></div><div class="log" id="log_gpi"></div></div>
</section>

<section id="kartendesign"><div class="karte" style="display:flex;gap:10px;align-items:center;flex-wrap:wrap">
<h2 style="margin:0;flex:1;min-width:200px">Zugangskarten gestalten</h2><span id="kd_status"></span>
<button class="k p" onclick="designSpeichern()">Speichern</button><button class="k" onclick="testdruck()">Testseite drucken</button><button class="k" onclick="designStandard()">Standard wiederherstellen</button></div>
<div class="kd" id="kd_box"><div id="kd_form"></div><div class="teiler" data-k="kd" data-box="kd_box" title="Ziehen: Breite der Einstellungen ändern"></div>
<div class="vorschau"><iframe id="kd_vor" title="Vorschau Zugangskarte"></iframe><div class="log" id="log_kd"></div></div></div></section>

<section id="system"><div class="karte"><div style="display:flex;gap:10px;align-items:center;flex-wrap:wrap"><h2 style="margin:0;flex:1">Systeminfo</h2>
<label style="display:flex;align-items:center;gap:8px;margin:0;font-size:14px;color:var(--text)"><input type="checkbox" id="sys_auto" style="width:auto" onchange="sysAuto()"> alle 60 s aktualisieren</label>
<button class="k p" onclick="sysLaden()">Aktualisieren</button></div>
<div class="log" id="log_sys"></div><div class="kacheln" id="sys_k"></div></div>
<div class="karte"><h3>Internet – letzte 24 Stunden</h3><p class="hint" id="sys_ch_hint">Messwerte der UniFi-Cloud im 5-Minuten-Raster.</p><div id="sys_ch1" class="chart"></div><div id="sys_ch2" class="chart"></div>
<details style="margin-top:10px"><summary style="cursor:pointer;font-size:13px;color:var(--muted)">Rohwerte der UniFi-Cloud (letzter Messpunkt)</summary><pre class="json" id="sys_isp_roh"></pre></details></div>
<div class="karte"><h3>Geräte – Auslastung</h3><div class="tab" id="sys_ger"></div></div>
<div class="karte"><h3>Clients und Datenverkehr je Netz</h3><p class="hint" id="sys_netz_hint"></p><div class="tab" id="sys_netz"></div></div>
<div class="karte" id="sys_top_k" style="display:none"><h3>Größte Verbraucher (seit Verbindungsbeginn)</h3><div class="tab" id="sys_top"></div></div></section>

<section id="daten"><div class="karte"><div style="display:flex;gap:10px;align-items:center;flex-wrap:wrap"><h2 style="margin:0;flex:1">Alle Daten</h2>
<label style="display:flex;align-items:center;gap:8px;margin:0;font-size:14px;color:var(--text)"><input type="checkbox" id="d_geheim" style="width:auto" onchange="if(DAKT)datenLaden(DAKT)"> Passwörter/Schlüssel anzeigen</label>
<button class="k p" onclick="datenPruefen()">Verfügbarkeit prüfen</button></div>
<p class="hint">Alles, was die Konsole über die Cloud lesen lässt – nur lesend, am Gateway wird nichts geändert. Links eine Quelle wählen.</p><div class="log" id="log_d"></div></div>
<div class="dgrid" id="d_box"><div class="dliste" id="d_liste"></div><div class="teiler" data-k="dl" data-box="d_box" title="Ziehen: Breite der Liste ändern"></div>
<div class="karte" style="min-width:0"><h3 id="d_titel">–</h3><p class="hint mono" id="d_pfad"></p>
<div class="knoepfe" style="margin-top:4px"><input id="d_filter" placeholder="Filtern …" oninput="datenZeigen()" style="max-width:240px"><button class="k" id="d_btn_tab" onclick="DANS='tab';datenZeigen()">Tabelle</button><button class="k" onclick="DANS='json';datenZeigen()">JSON</button>
<button class="k" onclick="datenJson()">Als JSON speichern</button><button class="k" onclick="datenCsv()">Als CSV</button></div>
<div class="tab" id="d_tab"></div><pre class="json" id="d_json" style="display:none"></pre></div></div></section>

<section id="voucher"><div class="karte"><h2>Gast-Voucher</h2>
<div class="reihe"><div><label>Anzahl</label><input id="v_anz" type="number" value="10" min="1" max="500"></div>
<div><label>Gültigkeit</label><select id="v_min"><option value="120">2 Stunden</option><option value="480">8 Stunden</option><option value="1440" selected>1 Tag</option><option value="10080">1 Woche</option></select></div>
<div><label>Bezeichnung</label><input id="v_name" value="Gast"></div></div>
<div class="knoepfe"><button class="k" onclick="voucher(false)">Vorschau</button><button class="k p" onclick="voucher(true)">Erstellen</button><button class="k" onclick="voucherDruck()">Drucken</button></div>
<div class="log" id="log_vo"></div><div class="tab" id="tab_vo"></div></div></section>

<section id="hilfe"><div class="karte"><h2>Hilfe</h2><p class="hint">
<b>Schema:</b> Parzelle p auf Steckplatz n → VLAN 1000 + n·100 + p (Buchenweg: Parzelle 25 = VLAN 1125), Netz 10.&lt;Sparten-ID&gt;.p.0/24, Router .1, Geräte .10–.250. Vorstand 2000+n·10+1, Gäste +2, Technik +9. Namen BW-Paz.025, BW-Vorstand, BW-Gäste, BW-Technik.<br><br>
<b>Neue Sparte:</b> „Planung“ → Zeile anhängen, speichern · „Abgleich“ · „Einrichten“ Schritt 1–4 · Zugangskarten drucken · mit Handy testen.<br><br>
<b>Zugangskarten:</b> Aussehen im Reiter „Kartendesign“ einstellen und speichern – gedruckt wird unter „Einrichten“ Schritt 3. Logo-Datei und Design liegen im Programmordner.<br><br>
<b>Passwörter ändern:</b> „Einrichten“ Schritt 3 → „Anzeigen“, Passwort in der Tabelle ändern, „Änderungen speichern“. Dann Reiter „Übertragen“ → „Unterschiede ermitteln“ → „Ausgewählte übertragen“ und die Karte neu drucken.<br><br>
<b>Handy &amp; Tablet:</b> „Verbindung → Handy &amp; Tablet“: optional eine Handy-PIN festlegen, Tailscale-Freigabe (von überall, echte App) oder Heimnetz einschalten, QR-Code mit dem Handy scannen, Manager-Passwort oder PIN eingeben, „App installieren“. Der PC mit dem Manager muss dabei laufen.<br><br>
<b>Kalkulation:</b> Reiter „Kalkulation“ → „Aus Excel übernehmen“ (Kalkulation und/oder VLAN-Planer) · Buchungen je Parzelle erfassen (oder über „Tarife“) · Tabelle „Je Sparte“ zeigt Umsatz, Buchungsrate, Kosten, Deckungsbeitrag; oben die Gesamtauslastung aller Sparten mit Buchungen.<br><br>
<b>Tarife:</b> Reiter „Tarife“ → Tarife festlegen (Bandbreite Download/Upload, Netzmaske, Endgeräte) und speichern · „Netze laden“ · je Netz einen Tarif wählen (oder markieren und „für markierte setzen“) · „Zuordnung speichern“ · unten „Vorschau“, dann „Ausgewählte übertragen“. Bandbreite → QoS-Regel „SparteNet-Tarif-…“, Netzgröße → Subnetz und DHCP-Bereich des Netzes. Ein /29 mit DHCP .2–.6 lässt genau 5 Geräte zu, ein /28 mit .2–.11 genau 10.<br><br>
<b>Übertragen:</b> Erst „Schreibzugriff prüfen“. Wird das abgelehnt (403), den API-Key auf unifi.ui.com als Besitzer bzw. Super-Admin neu erstellen.<br><br>
<b>Systeminfo / Alle Daten:</b> nur lesend. Datenverkehr je Parzelle und einige Quellen der klassischen Schnittstelle gibt die Konsole über die Cloud nicht immer frei – „Alle Daten → Verfügbarkeit prüfen“ zeigt, was geht.<br><br>
<b>API-Key:</b> unifi.ui.com → Einstellungen → API Keys, angemeldet als Besitzer der Konsole. Der Key aus der Network-App („Integrationen“) funktioniert über die Cloud nicht.</p></div></section>
</main>
<script>
const T="__TOKEN__";let LETZT=null,PLAN=null,PLANZ=null,PPSK=null,PPSKSP=null,CODES=[],VMIN=0,EINST={};
const TABS=[["start","Start"],["verbindung","Verbindung"],["lesen","Auslesen"],["planung","Planung"],["abgleich","Abgleich"],["einrichten","Einrichten"],["uebertragen","Übertragen"],["tarife","Tarife"],["kalkulation","Kalkulation"],["netzplanung","Netzplanung"],["kartendesign","Kartendesign"],["voucher","Gast-Voucher"],["system","Systeminfo"],["daten","Alle Daten"],["hilfe","Hilfe"]];
const $=id=>document.getElementById(id);const nav=$("nav");TABS.forEach(([id,t])=>{const b=document.createElement("button");b.textContent=t;b.onclick=()=>zeige(id);b.id="n_"+id;nav.appendChild(b)});
function zeige(id){if(id=="start"&&!$("st_k").innerHTML&&typeof EINST!="undefined"&&EINST.konsole_id)startLaden().catch(()=>{});if(id=="verbindung")fernLaden().catch(()=>{});if(location.hash!="#"+id)history.replaceState(null,"","#"+id);setTimeout(()=>{const b=document.querySelector("nav button.aktiv");if(b&&b.scrollIntoView)b.scrollIntoView({inline:"center",block:"nearest"})},0);if(id=="kalkulation"&&!KK)kkLaden().catch(()=>{});if(id=="netzplanung"&&!GP)gpLaden().catch(()=>{});if(id=="kartendesign"&&!DESIGN)designLaden();if(id=="tarife"&&!TF)tfLaden();if(id=="system"&&!SYS)sysLaden();if(id=="daten"&&!DLISTE)datenListe();document.querySelectorAll("section").forEach(s=>s.classList.toggle("aktiv",s.id==id));document.querySelectorAll("nav button").forEach(b=>b.classList.toggle("aktiv",b.id=="n_"+id))}
async function api(pfad,body,logid){const el=logid&&$(logid);const kn=[...document.querySelectorAll("button")];kn.forEach(b=>b.disabled=true);if(el)el.textContent="… bitte warten (über die Cloud kann das einige Sekunden dauern)";
 try{const r=await fetch(pfad,{method:body===undefined?"GET":"POST",headers:{"X-Token":T,"Content-Type":"application/json"},body:body===undefined?undefined:(body instanceof Blob?body:JSON.stringify(body))});
 if(r.status==401||r.status==403){location.reload();return new Promise(()=>{})}const d=await r.json();if(!r.ok)throw new Error(d.fehler||r.status);if(el)el.textContent=d.log?d.log.join("\n"):"";return d}
 catch(e){if(el)el.innerHTML='<span class="fehler">✖ '+esc(e.message)+'</span>';throw e}finally{kn.forEach(b=>b.disabled=false)}}
function esc(s){return String(s??"").replace(/[&<>"]/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]))}
const SK=s=>Array.isArray(s)?s[0]:s,SL=s=>Array.isArray(s)?(s[1]||s[0]):s,SC=s=>Array.isArray(s)&&s[2]?" class='"+s[2]+"'":"";
function tabelle(id,sp,z,kl){$(id).innerHTML=z.length?"<table><tr>"+sp.map(s=>"<th>"+esc(SL(s))+"</th>").join("")+"</tr>"+z.map(r=>"<tr class='"+(kl?kl(r):"")+"'>"+sp.map(s=>"<td"+SC(s)+">"+esc(r[SK(s)])+"</td>").join("")+"</tr>").join("")+"</table>":""}
function csvSpeichern(d,name){if(!d||!d.zeilen.length)return alert("Keine Daten.");const sp=d.spalten.map(SK);const t="﻿"+[d.spalten.map(SL).join(";")].concat(d.zeilen.map(z=>sp.map(k=>'"'+String(z[k]??"").replace(/"/g,'""')+'"').join(";"))).join("\r\n");
 const a=document.createElement("a");a.href=URL.createObjectURL(new Blob([t],{type:"text/csv"}));a.download=name+".csv";a.click()}
async function logSchalten(){await api("/api/einstellungen",{log_aktiv:$("log_aktiv").checked},"log_datei")}
async function logZeigen(){await api("/api/log",undefined,"log_datei");const el=$("log_datei");el.scrollTop=el.scrollHeight}
async function logLoeschen(){if(confirm("Protokoll leeren?"))await api("/api/log-loeschen",{},"log_datei")}
async function einst(){EINST=await api("/api/einstellungen");if(FERN){try{const a=JSON.parse(localStorage.getItem("sn_ansicht")||"null");if(a){ANS={...ANS_STD,...a};ansAnwenden()}}catch(e){}}else if(EINST.ansicht){ANS={...ANS_STD,...EINST.ansicht};ansAnwenden()}$("log_aktiv").checked=!!EINST.log_aktiv;$("logpfad").textContent=EINST.logdatei;$("speicherort").textContent=EINST.speicher||"";const e=$("key_st");e.textContent=EINST.cloud_key_gesetzt?"hinterlegt":"fehlt";e.className="status"+(EINST.cloud_key_gesetzt?" ok":"");
 if(EINST.konsole_id)$("konsole").innerHTML=`<option value="${esc(EINST.konsole_id)}">${esc(EINST.konsole_name||EINST.konsole_id)}</option>`;$("verb").textContent=EINST.konsole_name?"· "+EINST.konsole_name:"";
 if(!EINST.cloud_key_gesetzt||!EINST.konsole_id)zeige("verbindung");else if(document.querySelector("section.aktiv")?.id=="start"&&!$("st_k").innerHTML)startLaden().catch(()=>{})}
async function konsolenLaden(){const d=await api("/api/konsolen",{cloud_key:$("cloud_key").value},"log_v");$("log_v").textContent="✔ "+d.konsolen.length+" Konsole(n) gefunden – wählen und speichern.";
 $("konsole").innerHTML=d.konsolen.map(k=>`<option value="${esc(k.id)}" ${k.id==EINST.konsole_id?"selected":""}>${esc(k.name)} · ${esc(k.modell)} · ${esc(k.firmware)}</option>`).join("")}
async function speichern(){const k=$("konsole");if(!k.value)return alert("Bitte erst „Konsolen laden“ und eine Konsole wählen.");
 await api("/api/einstellungen",{cloud_key:$("cloud_key").value,konsole_id:k.value,konsole_name:k.selectedOptions[0].text.split(" · ")[0]},"log_v");$("cloud_key").value="";einst()}
async function testen(){await api("/api/test",{},"log_v")}
async function lesen(w){const d=await api("/api/lesen?was="+w,undefined,"log_l");LETZT=d;$("log_l").textContent=d.zeilen.length+" Einträge";tabelle("tab_l",d.spalten,d.zeilen)}
function editor(roh){$("p_gw").value=roh.gateway;$("p_gwname").value=roh.gatewayname;$("p_pre").value=roh.praefix;const z=[...roh.sparten];while(z.length<10)z.push({name:"",kz:"",sid:"",n:""});
 $("p_tab").innerHTML="<table><tr><th>Steckplatz</th><th>Sparte (Name)</th><th>Kürzel</th><th>Sparten-ID (1–254)</th><th>Parzellen (1–199)</th></tr>"+z.map((s,i)=>`<tr><td>${i+1}</td><td><input data-f="name" value="${esc(s.name)}"></td><td><input data-f="kz" value="${esc(s.kz)}" style="max-width:110px"></td><td><input data-f="sid" type="number" value="${esc(s.sid)}" style="max-width:120px"></td><td><input data-f="n" type="number" value="${esc(s.n)}" style="max-width:120px"></td></tr>`).join("")+"</table>"}
async function planSpeichern(){const sp=[...$("p_tab").querySelectorAll("tr")].slice(1).map(tr=>{const o={};tr.querySelectorAll("input").forEach(i=>o[i.dataset.f]=i.type=="number"&&i.value?+i.value:i.value.trim());return o}).filter(s=>s.name);
 await api("/api/plan",{gateway:+$("p_gw").value||1,gatewayname:$("p_gwname").value,praefix:$("p_pre").value||"SparteNet.de",sparten:sp},"log_p");planLaden(true)}
async function excelHoch(){const f=$("xls").files[0];if(f){await api("/api/excel",f,"log_p");planLaden(true)}}
async function planLaden(still){try{PLAN=await api("/api/plan")}catch(e){$("log_p").innerHTML='<span class="fehler">✖ '+esc(e.message)+'</span>';return}
 editor(PLAN.roh);const o=PLAN.sparten.map(s=>`<option value="${esc(s.kz)}">${esc(s.name)} (${esc(s.kz)}, ${s.n} Parzellen, Steckplatz ${s.slot})</option>`).join("");
 $("plan_sp").innerHTML='<option value="">Alle Sparten</option>'+o;$("ein_sp").innerHTML=o;$("ab_sp").innerHTML=o+'<option value="">Alle Sparten</option>';$("ue_sp").innerHTML=o;$("st_sp").innerHTML=o;ssid();planZeigen()}
function ssid(){if(!PLAN)return;const kz=$("ein_sp").value,p=PLAN.praefix;$("ssid1").textContent=p+"-"+kz+"-Pächter";$("ssid2").textContent=p+"-"+kz+"-Gäste";$("ssid3").textContent=p+"-"+kz+"-Vorstand"}
function planZeigen(){if(!PLAN)return;const f=$("plan_sp").value,g=PLAN.gateway_netz;const z=[{bez:"Gateway (Hauptverteiler)",vlan:1,netz:g.netz,maske:"255.255.255.0",router:g.router,geraete:"Technik",zugang:"untagged",t:"kopf"}];
 PLAN.sparten.filter(s=>!f||s.kz==f).forEach(s=>{z.push({bez:"Sparte "+s.slot+": "+s.name+" ("+s.kz+", ID "+s.sid+", "+s.n+" Parzellen)",t:"kopf"});
 PLAN.netze.filter(n=>n.sparte==s.kz).forEach(n=>z.push({bez:n.art=="parzelle"?n.name+"  (Parzelle "+n.parzelle+")":n.name,vlan:n.vlan,netz:n.netz,maske:n.maske,router:n.router,geraete:n.dhcp_start+" – "+n.dhcp_ende,zugang:(n.ssid?n.ssid+" · ":"")+n.zugang,t:n.art=="parzelle"?"":"dienst"}))});
 PLANZ={spalten:[["bez","Netz"],["vlan","VLAN"],["netz","Subnetz"],["maske","Maske"],["router","Router-IP"],["geraete","Geräte-IPs"],["zugang","WLAN / Zugang"]],zeilen:z};tabelle("tab_p",PLANZ.spalten,z,r=>r.t||"")}
function kachel(t,v,a){return `<div class="kachel ${a}"><b>${v}</b>${t}</div>`}
async function abgleich(){const d=await api("/api/abgleich?sparte="+encodeURIComponent($("ab_sp").value),undefined,"log_a");
 $("kach_a").innerHTML=kachel("Netze fehlen",d.fehlen.length,d.fehlen.length?"warn":"gut")+kachel("Netze abweichend",d.abweichend.length,d.abweichend.length?"schlecht":"gut")+kachel("zusätzlich am Gateway",d.extra.length,"")+kachel("Hinweise Geräte/Clients",d.hinweise.length,d.hinweise.length?"schlecht":"gut");
 $("h_hin").textContent=d.hinweise.length?"Hinweise":"";tabelle("tab_hin",[["art","Art"],["name","Name"],["ip","IP"],["hinweis","Hinweis"]],d.hinweise);
 $("h_feh").textContent=d.fehlen.length?"Fehlende Netze ("+d.fehlen.length+")":"";tabelle("tab_feh",[["netz","Netz"],["vlan","VLAN"],["subnetz","Subnetz"]],d.fehlen);
 $("h_abw").textContent=d.abweichend.length?"Abweichungen":"";tabelle("tab_abw",[["netz","Netz laut Plan"],["soll","Soll"],["ist","Ist am Gateway"]],d.abweichend);
 $("h_cli").textContent=d.clients.length?"Verbundene Endgeräte":"";tabelle("tab_cli",[["name","Name"],["ip","IP"],["netz","Netz"]],d.clients)}
async function netze(aus,eins){const kz=$("ein_sp").value;if(!kz)return alert("Erst unter „Planung“ eine Sparte speichern.");
 if(aus&&!confirm((eins?"EIN Netz (das erste fehlende) anlegen?":"ALLE fehlenden Netze anlegen?")+"\nSparte: "+kz))return;await api("/api/netze",{sparte:kz,ausfuehren:aus,nur_eins:eins},"log_e")}
async function schritt(art,aus){const kz=$("ein_sp").value;if(!kz)return alert("Erst den Plan speichern.");if(aus&&!confirm("Wirklich ausführen?\nSparte: "+kz))return;await api("/api/"+art,{sparte:kz,ausfuehren:aus},"log_e")}
async function ppsk(art){const kz=$("ein_sp").value;if(pwOffen()&&!confirm("Es gibt ungespeicherte Passwort-Änderungen. Verwerfen?"))return;
 if(art=="neu"&&!confirm("ALLE Passwörter dieser Sparte neu erzeugen? Bereits verteilte Zugangskarten werden nach dem Hochladen ungültig."))return;
 const d=await api("/api/ppsk",{sparte:kz,art:art},"log_e");PPSKSP=d.sparte;pwSetzen(d.zeilen)}
let PWALT={},PWGEAENDERT=[];
function regelBeispiel(){const p=$("pr_pre").value,z=+$("pr_z").value||10;$("pr_bsp").textContent="Beispiel: "+p+"0123456789".repeat(3).slice(0,z)}
async function regelLaden(){const d=await api("/api/pw-regel");$("pr_pre").value=d.regel.praefix;$("pr_z").value=d.regel.ziffern;regelBeispiel()}
async function regelSpeichern(){const d=await api("/api/pw-regel",{praefix:$("pr_pre").value.trim(),ziffern:+$("pr_z").value},"log_e");$("pr_pre").value=d.regel.praefix;$("pr_z").value=d.regel.ziffern;regelBeispiel()}
function pwSetzen(zeilen){PPSK={spalten:[["Parzelle","Parzelle"],["Netz","Netz"],["WLAN","WLAN"],["Passwort","Passwort","mono"],["VLAN","VLAN"]],zeilen:zeilen};PWALT={};zeilen.forEach(r=>PWALT[r.Parzelle]=r.Passwort||"");
 $("pw_bereich").style.display="block";$("tab_e").innerHTML="";
 $("tab_pw").innerHTML="<table><tr><th>Drucken</th><th>Parzelle</th><th>Netz</th><th>WLAN</th><th>Passwort</th><th></th><th>VLAN</th><th>Status</th></tr>"+zeilen.map(r=>`<tr data-p="${esc(r.Parzelle)}"><td><input type="checkbox" class="kwahl" value="${esc(r.Parzelle)}" style="width:auto" ${r.Passwort?"":"disabled"}></td><td>${esc(r.Parzelle)}</td><td>${esc(r.Netz)}</td><td>${esc(r.WLAN)}</td>
 <td><input class="pwfeld" data-p="${esc(r.Parzelle)}" value="${esc(r.Passwort||"")}" maxlength="63" spellcheck="false" autocomplete="off" oninput="pwPruefen()"></td>
 <td style="white-space:nowrap"><button class="mini" onclick="pwNeu('${esc(r.Parzelle)}')" title="Zufälliges neues Passwort">neu</button><button class="mini" onclick="pwFeld('${esc(r.Parzelle)}','')" title="Zugang entfernen">sperren</button><button class="mini" onclick="pwFeld('${esc(r.Parzelle)}',PWALT['${esc(r.Parzelle)}'])" title="Ursprünglicher Wert">↺</button></td>
 <td>${esc(r.VLAN)}</td><td class="pwst"></td></tr>`).join("")+"</table>";pwPruefen();pwFilter()}
function pwFehler(pw){if(pw==="")return"";if(pw.length<8||pw.length>63)return"8–63 Zeichen";if(/[^\x20-\x7e]/.test(pw))return"keine Umlaute/Sonderzeichen";if(pw!==pw.trim())return"Leerzeichen am Rand";return""}
function pwPruefen(){const felder=[...document.querySelectorAll(".pwfeld")];const zahl={};felder.forEach(f=>{if(f.value)zahl[f.value]=(zahl[f.value]||0)+1});let ge=0,fe=0;
 felder.forEach(f=>{const tr=f.closest("tr"),st=tr.querySelector(".pwst"),alt=PWALT[f.dataset.p];let fehler=pwFehler(f.value);if(!fehler&&f.value&&zahl[f.value]>1)fehler="doppelt";
  const geaendert=f.value!==alt;tr.classList.toggle("geaendert",geaendert&&!fehler);tr.classList.toggle("falsch",!!fehler);tr.classList.toggle("gesperrt",!f.value);
  st.className="pwst"+(fehler?" f":geaendert?" g":"");st.textContent=fehler?"✖ "+fehler:geaendert?(f.value?"geändert":"wird gesperrt"):(f.value?"":"ohne Zugang");if(geaendert)ge++;if(fehler)fe++;
  const cb=tr.querySelector(".kwahl");cb.disabled=!f.value||geaendert;if(cb.disabled)cb.checked=false});
 const e=$("pw_st");e.textContent=fe?`✖ ${fe} ungültig – bitte korrigieren`:ge?`● ${ge} Änderung(en) noch nicht gespeichert`:"Alle Passwörter gespeichert";e.className=ge||fe?"dirty":"";return{ge,fe}}
function pwOffen(){return document.querySelectorAll("tr.geaendert,tr.falsch").length>0}
function pwFeld(p,w){const f=document.querySelector(`.pwfeld[data-p="${CSS.escape(p)}"]`);if(f){f.value=w;pwPruefen()}}
async function pwNeu(p){const d=await api("/api/passwort?n=1");pwFeld(p,d.passwoerter[0])}
function pwFilter(){const t=$("pw_suche").value.trim().toLowerCase();document.querySelectorAll("#tab_pw tr[data-p]").forEach(tr=>{const f=tr.querySelector(".pwfeld");tr.style.display=!t||(tr.textContent+" "+f.value).toLowerCase().includes(t)?"":"none"})}
function pwVerwerfen(){if(!pwOffen()||confirm("Alle ungespeicherten Änderungen verwerfen?"))document.querySelectorAll(".pwfeld").forEach(f=>{f.value=PWALT[f.dataset.p]});pwPruefen()}
async function pwSpeichern(){const{ge,fe}=pwPruefen();if(fe)return alert("Bitte erst die rot markierten Passwörter korrigieren.");if(!ge)return alert("Keine Änderungen.");
 const aend={};document.querySelectorAll(".pwfeld").forEach(f=>{if(f.value!==PWALT[f.dataset.p])aend[f.dataset.p]=f.value});
 if(Object.values(aend).some(v=>v==="")&&!confirm("Bei mindestens einer Parzelle wird der Zugang entfernt (leeres Passwort). Fortfahren?"))return;
 const d=await api("/api/ppsk-speichern",{sparte:$("ein_sp").value,aenderungen:aend},"log_e");PWGEAENDERT=d.geaendert.map(String);pwSetzen(d.zeilen);markiereGeaendert()}
function markiereGeaendert(){if(!PWGEAENDERT.length)return alert("In dieser Sitzung wurde noch nichts geändert.");document.querySelectorAll(".kwahl").forEach(c=>c.checked=!c.disabled&&PWGEAENDERT.includes(c.value))}
addEventListener("beforeunload",e=>{if(typeof pwOffen=="function"&&pwOffen()){e.preventDefault();e.returnValue=""}});
function markiere(an){document.querySelectorAll(".kwahl").forEach(c=>c.checked=an)}
async function karten(art){const kz=$("ein_sp").value;if(!PPSK)return alert("Erst unter Schritt 3 „Anzeigen“ oder „Fehlende erzeugen“.");
 let auswahl="alle";if(art=="auswahl"){auswahl=[...document.querySelectorAll(".kwahl:checked")].map(c=>c.value);if(!auswahl.length)return alert("Bitte in der Tabelle Parzellen markieren.")}
 const w=window.open("","_blank");let d;try{d=await api("/api/karten",{sparte:kz,auswahl:auswahl},"log_e")}catch(e){if(w)w.close();return}
 if(w){w.document.open();w.document.write(d.html);w.document.close()}else alert("Bitte Pop-ups für diese Seite erlauben.")}
async function voucher(aus){const b={anzahl:+$("v_anz").value,minuten:+$("v_min").value,name:$("v_name").value,ausfuehren:aus};if(aus&&!confirm(b.anzahl+" Voucher erstellen?"))return;
 const d=await api("/api/voucher",b,"log_vo");if(d.codes){CODES=d.codes;VMIN=d.minuten;tabelle("tab_vo",[["code","Voucher-Code","mono"]],CODES.map(c=>({code:c})))}}
function voucherDruck(){if(!CODES.length)return alert("Erst Voucher erstellen.");const g={120:"2 Stunden",480:"8 Stunden",1440:"1 Tag",10080:"1 Woche"}[VMIN]||VMIN+" Minuten";const w=window.open("","_blank");
 w.document.write(`<html><head><title>Voucher</title><style>body{font-family:Arial;margin:10mm}.k{display:inline-block;width:60mm;border:1px dashed #999;margin:2mm;padding:4mm;text-align:center;page-break-inside:avoid}.c{font-family:Consolas,monospace;font-size:20px;font-weight:bold;letter-spacing:2px;margin:2mm 0}</style></head><body>`+
 CODES.map(c=>`<div class="k"><div style="color:#3a9a1f;font-weight:bold">SparteNet.de · Gast-WLAN</div><div class="c">${esc(c)}</div><div style="font-size:12px">gültig ${g}</div></div>`).join("")+"<script>print()<\/script></body></html>");w.document.close()}
let DESIGN=null,DSTD=null,KDT=null,KDLOG="";
function kdHinweis(t){$("log_kd").textContent=KDLOG+(t?"\n"+t:"")}
const KD=[
 ["Papier & Layout",[["format","Papierformat","sel",[["A4","A4 (210 × 297 mm)"],["A5","A5 (148 × 210 mm)"],["A6","A6 (105 × 148 mm)"]]],["quer","Querformat","chk"],
  ["rand_mm","Seitenrand","rng",3,30,1,"mm"],["ausrichtung","Text ausrichten","sel",[["center","Mittig"],["left","Links"],["right","Rechts"]]],["fuss_unten","Fußzeile ganz unten","chk"]]],
 ["Texte",[["_hint","Platzhalter: {sparte} {kz} {parzelle} {wlan} · Enter = neue Zeile"],
  ["zeige_kopf","Kopfzeile","chk"],["t_kopf","","txt"],["t_titel","Überschrift","txt"],["zeige_unter","Untertitel","chk"],["t_unter","","txt"],
  ["zeige_scan","Hinweis unter dem QR-Code","chk"],["t_scan","","txt"],["zeige_zugang","WLAN-Name und Passwort anzeigen","chk"],["zeige_fuss","Fußzeile","chk"],["t_fuss","","txt"]]],
 ["Schrift",[["schrift","Schriftart","sel",[]],["gr_kopf","Kopfzeile","rng",6,40,1,"pt"],["gr_titel","Überschrift","rng",8,80,1,"pt"],["gr_text","Fließtext","rng",6,30,1,"pt"],
  ["gr_pw","Passwort","rng",8,40,1,"pt"],["gr_klein","Kleingedrucktes","rng",5,20,1,"pt"]]],
 ["Farben",[["farbe_akzent","Kopfzeile (Akzent)","col"],["farbe_text","Text","col"],["farbe_hell","Nebentext","col"],["farbe_seite","Seitenhintergrund","col"],["farbe_pw_hinter","Hintergrund Passwort","col"]]],
 ["QR-Code",[["qr_cm","Größe","rng",2,25,.5,"cm"],["farbe_qr","Farbe der Punkte","col"],["farbe_qr_hinter","Hintergrund","col"],["_hint","Dunkle Punkte auf hellem Grund, mindestens 3 cm – sonst lesen manche Handys den Code nicht. Passt nicht alles auf die Seite, werden QR-Code und Logo automatisch verkleinert. Für A6 empfiehlt sich Querformat."]]],
 ["Logo",[["_logo",""],["logo_ort","Platz","sel",[["oben","Oben"],["unten","Unten (über der Fußzeile)"]]],["logo_pos","Ausrichtung","sel",[["center","Mittig"],["left","Links"],["right","Rechts"]]],["logo_mm","Breite","rng",5,180,1,"mm"]]],
 ["Rahmen",[["rahmen","Rahmen anzeigen","chk"],["rahmen_mm","Stärke","rng",.2,5,.1,"mm"],["rahmen_radius","Ecken-Rundung","rng",0,20,1,"mm"],["farbe_rahmen","Rahmenfarbe","col"]]]];
function kdFeld([k,l,t,a,b,c,e]){const id="kd_"+k;
 if(k=="_hint")return `<p class="hint" style="margin:6px 0 2px">${esc(l)}</p>`;
 if(k=="_logo")return `<div class="feld"><label>Logo (PNG, JPG, SVG, WEBP · max. 2 MB, transparentes PNG empfohlen)</label></div><img id="kd_logo_mini" class="logo-mini" alt="" style="display:none">
  <div class="knoepfe" style="margin-top:8px"><label class="k" style="margin:0;color:var(--navy);cursor:pointer">Logo hochladen …<input type="file" id="kd_logo" accept="image/png,image/jpeg,image/gif,image/webp,image/svg+xml,.svg" onchange="logoHoch()" style="display:none"></label><button class="k" onclick="logoWeg()">Logo entfernen</button></div>`;
 if(t=="chk")return `<div class="feld chk"><input type="checkbox" id="${id}" data-k="${k}"><label for="${id}">${esc(l)}</label></div>`;
 if(t=="txt")return `<div class="feld">${l?`<label for="${id}">${esc(l)}</label>`:""}<textarea id="${id}" data-k="${k}" rows="1"></textarea></div>`;
 if(t=="col")return `<div class="feld"><label for="${id}">${esc(l)}</label><input type="color" id="${id}" data-k="${k}"></div>`;
 if(t=="rng")return `<div class="feld"><label for="${id}">${esc(l)}</label><output id="${id}_o"></output><input type="range" id="${id}" data-k="${k}" data-e="${e}" min="${a}" max="${b}" step="${c}"></div>`;
 if(t=="sel")return `<div class="feld"><label for="${id}">${esc(l)}</label><select id="${id}" data-k="${k}">${(k=="schrift"?KDSCHRIFT.map(x=>[x,x]):a).map(([v,n])=>`<option value="${esc(v)}">${esc(n)}</option>`).join("")}</select></div>`}
let KDSCHRIFT=[];
function kdAufbauen(){$("kd_form").innerHTML=KD.map(([h,f])=>`<div class="karte"><h3>${esc(h)}</h3>${f.map(kdFeld).join("")}</div>`).join("");
 $("kd_form").querySelectorAll("[data-k]").forEach(el=>{el.addEventListener("input",()=>{kdAusgabe(el);kdGeaendert()});el.addEventListener("change",()=>{kdAusgabe(el);kdGeaendert()})})}
function kdAusgabe(el){if(el.type=="range")$(el.id+"_o").textContent=String(+el.value).replace(".",",")+" "+el.dataset.e;
 if(el.tagName=="TEXTAREA"){el.style.height="auto";el.style.height=el.scrollHeight+2+"px"}}
function kdFuellen(g){$("kd_form").querySelectorAll("[data-k]").forEach(el=>{const v=g[el.dataset.k];if(el.type=="checkbox")el.checked=!!v;else el.value=v;kdAusgabe(el)})}
function kdLesen(){const g={};$("kd_form").querySelectorAll("[data-k]").forEach(el=>{g[el.dataset.k]=el.type=="checkbox"?el.checked:(el.type=="range"?+el.value:el.value)});return g}
function kdStatus(t,dirty){const e=$("kd_status");e.textContent=t;e.className=dirty?"dirty":""}
function kdGeaendert(){kdStatus("● Änderungen noch nicht gespeichert",true);clearTimeout(KDT);KDT=setTimeout(vorschau,250)}
function logoMini(uri){const i=$("kd_logo_mini");if(uri){i.src=uri;i.style.display="block"}else{i.removeAttribute("src");i.style.display="none"}}
async function designLaden(){const d=await api("/api/design");DESIGN=d.design;DSTD=d.standard;KDSCHRIFT=d.schriften;kdAufbauen();kdFuellen(DESIGN);logoMini(d.logo_uri);kdStatus("Gespeichertes Design",false);vorschau()}
async function vorschau(drucken){try{const r=await fetch("/api/karten-vorschau",{method:"POST",headers:{"X-Token":T,"Content-Type":"application/json"},body:JSON.stringify({design:kdLesen(),drucken:!!drucken})});
 const d=await r.json();if(!r.ok)throw new Error(d.fehler||r.status);KDLOG=(d.log||[]).join("\n");$("log_kd").textContent=KDLOG;return d}
 catch(e){$("log_kd").innerHTML='<span class="fehler">✖ '+esc(e.message)+'</span>'}}
const _vorschau=vorschau;vorschau=async function(drucken){const d=await _vorschau(drucken);if(d&&!drucken)$("kd_vor").srcdoc=d.html;return d};
async function designSpeichern(){await api("/api/design",{design:kdLesen()},"log_kd");DESIGN=kdLesen();kdStatus("✔ Gespeichert – gilt für alle Zugangskarten",false)}
function designStandard(){if(!confirm("Alle Einstellungen auf Standard zurücksetzen? (Das Logo bleibt; gespeichert wird erst mit „Speichern“.)"))return;kdFuellen(DSTD);kdGeaendert()}
async function testdruck(){const w=window.open("","_blank");const d=await vorschau(true);if(!d){if(w)w.close();return}if(w){w.document.open();w.document.write(d.html);w.document.close()}else alert("Bitte Pop-ups für diese Seite erlauben.")}
async function logoHoch(){const f=$("kd_logo").files[0];if(!f)return;const d=await api("/api/logo",f,"log_kd");logoMini(d.logo_uri);$("kd_logo").value="";vorschau()}
async function logoWeg(){if(!confirm("Logo entfernen?"))return;await api("/api/logo-loeschen",{},"log_kd");logoMini("");vorschau()}
let SYS=null,SYST=null,DLISTE=null,DAKT=null,DDATEN=null,DANS="tab";
const mbit=b=>b==null||b===""?"–":(b>=1e6?(b/1e6).toFixed(b>=1e8?0:1)+" Mbit/s":(b/1e3).toFixed(0)+" kbit/s");
const kbit=k=>k==null?"–":(k>=1e6?(k/1e6).toLocaleString("de-DE",{maximumFractionDigits:1})+" Gbit/s":k>=1000?(k/1000).toLocaleString("de-DE",{maximumFractionDigits:k>=100000?0:1})+" Mbit/s":Math.round(k)+" kbit/s");
const bytes=b=>!b?"0 B":b>=1e9?(b/1e9).toFixed(2)+" GB":b>=1e6?(b/1e6).toFixed(1)+" MB":(b/1e3).toFixed(0)+" kB";
const dauer=s=>{if(s==null||s==="")return"–";s=+s;const t=Math.floor(s/86400),h=Math.floor(s%86400/3600),m=Math.floor(s%3600/60);return t?t+" T "+h+" h":h?h+" h "+m+" min":m+" min"};
const zahl=(v,n=1)=>v==null||v===""?"–":(+v).toFixed(n).replace(".",",");
function balken(p){if(p==null||p==="")return"–";const k=p>=85?"s":p>=60?"w":"";return `<div class="balken"><i class="${k}" style="width:${Math.min(100,p)}%"></i><span>${zahl(p,0)} %</span></div>`}
function htab(id,sp,z){$(id).innerHTML=z.length?"<table><tr>"+sp.map(s=>"<th>"+esc(s[0])+"</th>").join("")+"</tr>"+z.map(r=>"<tr>"+sp.map(s=>"<td>"+s[1](r)+"</td>").join("")+"</tr>").join("")+"</table>":"<p class='hint' style='padding:10px'>Keine Daten.</p>"}
function kach(t,v,u,a){return `<div class="kachel ${a||""}"><b>${v}</b>${esc(t)}${u?`<small>${esc(u)}</small>`:""}</div>`}
function diagramm(id,punkte,serien,einheit,fmt){const el=$(id);const pz=punkte.filter(p=>serien.some(s=>p[s.k]!=null));if(!pz.length){el.innerHTML="";return}
 const W=900,H=200,L=84,R=10,T=10,B=26,max=Math.max(1,...pz.flatMap(p=>serien.map(s=>+p[s.k]||0)))*1.1;const t0=new Date(pz[0].t).getTime(),t1=new Date(pz[pz.length-1].t).getTime()||t0+1;
 const X=t=>L+(W-L-R)*((new Date(t).getTime()-t0)/Math.max(1,t1-t0)),Y=v=>T+(H-T-B)*(1-(+v||0)/max);let g="";
 for(let i=0;i<=4;i++){const v=max*i/4,y=Y(v);g+=`<line x1="${L}" x2="${W-R}" y1="${y}" y2="${y}" stroke="#e3e8e0"/><text x="${L-6}" y="${y+4}" text-anchor="end" font-size="11" fill="#5d6b75">${esc(fmt(v))}</text>`}
 for(let h=0;h<=6;h++){const t=t0+(t1-t0)*h/6,x=L+(W-L-R)*h/6;g+=`<text x="${x}" y="${H-8}" text-anchor="middle" font-size="11" fill="#5d6b75">${new Date(t).toLocaleTimeString("de-DE",{hour:"2-digit",minute:"2-digit"})}</text>`}
 serien.forEach(s=>{const pts=pz.filter(p=>p[s.k]!=null).map(p=>X(p.t).toFixed(1)+","+Y(p[s.k]).toFixed(1));if(!pts.length)return;
  g+=`<polygon points="${pts[0].split(",")[0]},${Y(0)} ${pts.join(" ")} ${pts[pts.length-1].split(",")[0]},${Y(0)}" fill="${s.f}" opacity=".12"/><polyline points="${pts.join(" ")}" fill="none" stroke="${s.f}" stroke-width="1.8"/>`});
 el.innerHTML=`<svg viewBox="0 0 ${W} ${H}" role="img" aria-label="${esc(einheit)}">${g}<line id="${id}_l" y1="${T}" y2="${H-B}" stroke="#1d2f3e" stroke-dasharray="3 3" style="display:none"/><rect x="${L}" y="${T}" width="${W-L-R}" height="${H-T-B}" fill="transparent"/></svg><div class="tip"></div>
 <div class="legende">${serien.map(s=>`<span><b style="background:${s.f}"></b>${esc(s.n)}</span>`).join("")}</div>`;
 const svg=el.querySelector("svg"),tip=el.querySelector(".tip"),ln=$(id+"_l");
 svg.onmousemove=e=>{const r=svg.getBoundingClientRect(),x=(e.clientX-r.left)*W/r.width;let b=pz[0],bd=1e9;pz.forEach(p=>{const d=Math.abs(X(p.t)-x);if(d<bd){bd=d;b=p}});
  ln.setAttribute("x1",X(b.t));ln.setAttribute("x2",X(b.t));ln.style.display="";tip.style.display="block";
  tip.innerHTML=new Date(b.t).toLocaleString("de-DE",{hour:"2-digit",minute:"2-digit",day:"2-digit",month:"2-digit"})+"<br>"+serien.map(s=>esc(s.n)+": <b>"+esc(fmt(b[s.k]))+"</b>").join("<br>");
  const px=X(b.t)*r.width/W;tip.style.left=Math.min(r.width-170,px+12)+"px";tip.style.top="10px"};svg.onmouseleave=()=>{tip.style.display="none";ln.style.display="none"}}
async function sysLaden(){let d;try{d=await api("/api/system",undefined,"log_sys")}catch(e){return}SYS=d;
 const gw=d.geraete.find(g=>g.gw)||d.geraete[0]||{},isp=d.isp.length?d.isp[d.isp.length-1]:{},z=d.site.zaehler||{},pr=d.site.prozent||{};
 const down=d.wan.rx_bps??gw.rx_bps,up=d.wan.tx_bps??gw.tx_bps,lat=isp.lat??d.wan.latenz,on=d.geraete.filter(g=>String(g.status).toUpperCase()=="ONLINE").length;
 const ca=d.clients_arten,wlan=ca.WIRELESS||0,lan=ca.WIRED||0;
 $("sys_k").innerHTML=kach("Download jetzt",mbit(down),d.wan.rx_bps!=null?"Internet-Anschluss":"Gateway-Uplink","gut")+kach("Upload jetzt",mbit(up),d.wan.tx_bps!=null?"Internet-Anschluss":"Gateway-Uplink","gut")+
  kach("Latenz",lat!=null?zahl(lat,0)+" ms":"–",isp.maxlat!=null?"max. "+zahl(isp.maxlat,0)+" ms":"",lat>80?"warn":"")+
  kach("Paketverlust",isp.verlust!=null?zahl(isp.verlust,1)+" %":"–","letzte 5 min",isp.verlust>1?"schlecht":"")+
  kach("Internet verfügbar",pr.wanUptime!=null?zahl(pr.wanUptime,1)+" %":(isp.uptime!=null?zahl(isp.uptime,0)+" %":"–"),d.site.isp||d.wan.isp||isp.isp||"",pr.wanUptime<99?"warn":"")+
  kach("Clients",d.clients_gesamt,`WLAN ${wlan} · Kabel ${lan}`+(z.guestClient!=null?` · Gäste ${z.guestClient}`:""))+
  kach("Geräte online",on+" / "+d.geraete.length,d.geraete.length-on?(d.geraete.length-on)+" offline":"alle erreichbar",on<d.geraete.length?"schlecht":"gut")+
  kach("Gateway CPU / RAM",(gw.cpu!=null?zahl(gw.cpu,0):"–")+" / "+(gw.ram!=null?zahl(gw.ram,0):"–")+" %",gw.name||"",(gw.cpu>85||gw.ram>90)?"warn":"");
 $("sys_ch_hint").textContent=(d.isp.length?"Messwerte der UniFi-Cloud im 5-Minuten-Raster ("+d.isp.length+" Werte).":"Keine Verlaufsdaten von der UniFi-Cloud erhalten.")+(d.isp_hinweise.length?" "+d.isp_hinweise.join(" "):"");
 $("sys_isp_roh").textContent=JSON.stringify(d.isp_roh||{},null,2);
 const vl=d.verlauf.length?d.verlauf:d.isp;if(d.verlauf.length)$("sys_ch_hint").textContent+=" Download/Upload: Datenverkehr am Internet-Anschluss laut Gateway (5-Minuten-Mittel, "+d.verlauf.length+" Werte).";
 else if(!d.isp.some(p=>p.down!=null||p.up!=null))$("sys_ch_hint").textContent+=" Download/Upload-Verlauf: vom Gateway nicht erhalten"+(d.verlauf_fehler?" ("+d.verlauf_fehler+")":"")+" – es wird nur die Latenz gezeigt.";
 diagramm("sys_ch1",vl,[{k:"down",n:"Download",f:"#3a9a1f"},{k:"up",n:"Upload",f:"#1f6fb2"}],"Durchsatz",kbit);
 diagramm("sys_ch2",d.isp,[{k:"lat",n:"Latenz Ø",f:"#9a6700"},{k:"maxlat",n:"Latenz max.",f:"#b42318"}],"Latenz",v=>v==null?"–":Math.round(v)+" ms");
 htab("sys_ger",[["Gerät",r=>`<span class="punkt ${String(r.status).toUpperCase()=="ONLINE"?"on":"off"}"></span>${esc(r.name)}${r.gw?" <span class='status ok'>Gateway</span>":""}`],["Modell",r=>esc(r.modell)],["IP",r=>esc(r.ip)],
  ["CPU",r=>balken(r.cpu)],["RAM",r=>balken(r.ram)],["Last",r=>zahl(r.load,2)],["Laufzeit",r=>dauer(r.uptime)],["↓ Uplink",r=>mbit(r.rx_bps)],["↑ Uplink",r=>mbit(r.tx_bps)],
  ["Ports",r=>r.ports?r.ports_auf+" / "+r.ports+(r.poe?` · PoE ${r.poe}`:""):"–"],["Funk",r=>(r.funk||"–").split(" · ").map(esc).join("<br>")],["Wiederholungen",r=>(r.retries||"–").split(" · ").map(esc).join("<br>")],["Clients",r=>r.clients??"–"],["Temp.",r=>r.temp!=null?zahl(r.temp,0)+" °C":"–"],
  ["Firmware",r=>esc(r.firmware||"")+(r.update?" <span class='status' style='background:#fff1c2;color:#7a5200'>Update</span>":"")]],d.geraete);
 const mitTraffic=d.top.length>0;$("sys_netz_hint").textContent=mitTraffic?"Datenverkehr seit Verbindungsbeginn der aktuell verbundenen Geräte.":"Anzahl verbundener Geräte je Netz. Datenverkehr je Parzelle liefert die Konsole über die Cloud nicht.";
 htab("sys_netz",[["Netz",r=>esc(r.netz)],["Clients",r=>r.clients]].concat(mitTraffic?[["↓ empfangen",r=>bytes(r.tx)],["↑ gesendet",r=>bytes(r.rx)],["gesamt",r=>bytes(r.rx+r.tx)]]:[]),d.je_netz);
 $("sys_top_k").style.display=mitTraffic?"":"none";
 if(mitTraffic)htab("sys_top",[["Gerät",r=>esc(r.name)],["IP",r=>esc(r.ip)],["Netz",r=>esc(r.netz)],["WLAN",r=>esc(r.wlan)],["Signal",r=>r.signal!=null?r.signal+" dBm":"–"],["↓ empfangen",r=>bytes(r.tx)],["↑ gesendet",r=>bytes(r.rx)],["verbunden",r=>dauer(r.seit)]],d.top)}
function sysAuto(){clearInterval(SYST);if($("sys_auto").checked)SYST=setInterval(()=>{if($("system").classList.contains("aktiv"))sysLaden()},60000)}
async function datenListe(){const d=await api("/api/daten-liste");DLISTE=d.quellen;let g="",h="";
 DLISTE.forEach(q=>{if(q.gruppe!=g){g=q.gruppe;h+=`<h4>${esc(g)}</h4>`}h+=`<button id="dq_${q.schluessel}" onclick="datenLaden('${q.schluessel}')"><span>${esc(q.titel)}</span><em></em></button>`});$("d_liste").innerHTML=h}
async function datenPruefen(){const d=await api("/api/daten-pruefen",undefined,"log_d");Object.entries(d.quellen).forEach(([k,v])=>{const e=document.querySelector("#dq_"+k+" em");if(!e)return;
 e.textContent=v.ok?v.anzahl:"–";e.className=v.ok?"ok":"nein";e.title=v.fehler||""})}
async function datenLaden(k){DAKT=k;document.querySelectorAll(".dliste button").forEach(b=>b.classList.toggle("aktiv",b.id=="dq_"+k));
 let d;try{d=await api("/api/daten?q="+k+"&geheim="+($("d_geheim").checked?1:0),undefined,"log_d")}catch(e){$("d_tab").innerHTML="";$("d_json").textContent="";return}
 DDATEN=d;$("d_titel").textContent=d.titel+" ("+d.anzahl+")";$("d_pfad").textContent=d.gruppe+" · "+d.pfad;datenZeigen()}
function flach(o,pre,aus,tiefe){if(o===null||typeof o!="object"){aus[pre||"Wert"]=o;return aus}
 if(Array.isArray(o)){aus[pre]=o.every(x=>x===null||typeof x!="object")?o.join(", "):(o.length?JSON.stringify(o):"");return aus}
 Object.entries(o).forEach(([k,v])=>{const n=pre?pre+"."+k:k;if(v&&typeof v=="object"&&!Array.isArray(v)&&tiefe<2)flach(v,n,aus,tiefe+1);else flach(v,n,aus,9)});return aus}
function datenZeilen(){if(!DDATEN)return{sp:[],z:[]};const r=DDATEN.roh;let z;
 if(Array.isArray(r))z=r.map(x=>flach(x,"",{},0));else{const f=flach(r,"",{},0);z=Object.entries(f).map(([k,v])=>({Feld:k,Wert:v}))}
 const t=$("d_filter").value.trim().toLowerCase();if(t)z=z.filter(x=>Object.values(x).join(" ").toLowerCase().includes(t));
 const sp=[];z.forEach(x=>Object.keys(x).forEach(k=>{if(!sp.includes(k))sp.push(k)}));return{sp:sp,z:z}}
function datenZeigen(){if(!DDATEN)return;const json=DANS=="json";$("d_json").style.display=json?"block":"none";$("d_tab").style.display=json?"none":"block";
 if(json){$("d_json").textContent=JSON.stringify(DDATEN.roh,null,2);return}
 const{sp,z}=datenZeilen(),zeig=sp.slice(0,45);
 $("d_tab").innerHTML=z.length?"<table><tr>"+zeig.map(k=>"<th>"+esc(k)+"</th>").join("")+"</tr>"+z.slice(0,1000).map(x=>"<tr>"+zeig.map(k=>{const v=x[k]==null?"":String(x[k]);return `<td class="zelle" title="${esc(v.slice(0,600))}">${esc(v.slice(0,160))}</td>`}).join("")+"</tr>").join("")+"</table>"
  +(sp.length>45?`<p class="hint" style="padding:8px">${sp.length-45} weitere Spalten – vollständig unter „JSON“ oder „Als CSV“.</p>`:""):"<p class='hint' style='padding:10px'>Keine Einträge.</p>"}
function datenJson(){if(!DDATEN)return alert("Erst eine Quelle wählen.");const a=document.createElement("a");a.href=URL.createObjectURL(new Blob([JSON.stringify(DDATEN.roh,null,2)],{type:"application/json"}));a.download="spartenet_"+DAKT+".json";a.click()}
function datenCsv(){if(!DDATEN)return alert("Erst eine Quelle wählen.");const{sp,z}=datenZeilen();csvSpeichern({spalten:sp,zeilen:z},"spartenet_"+DAKT)}
async function diagnose(){const d=await api("/api/diagnose",{anonym:$("diag_anon").checked},"log_diag");const a=document.createElement("a");a.href=URL.createObjectURL(new Blob([d.inhalt],{type:"application/json"}));a.download=d.name;a.click()}
const ANS_STD={breite:1200,zoom:0,tabh:520,spalten:false,kd:430,dl:270};let ANS={...ANS_STD},ANST=null;
function autoZoom(){const dpr=window.devicePixelRatio||1,phys=screen.width*dpr;const basis=phys>=7600?2.5:phys>=5000?2:phys>=3800?1.5:phys>=2500?1.25:1;return Math.max(1,Math.round(basis/dpr*4)/4)}
function vhSetzen(){const p=document.createElement("div");p.style.cssText="position:absolute;visibility:hidden;height:100px;width:1px";document.body.appendChild(p);
 const f=p.getBoundingClientRect().height/100||1;p.remove();document.documentElement.style.setProperty("--vh",(innerHeight/f)+"px")}
addEventListener("resize",vhSetzen);
function ansAnwenden(){const r=document.documentElement.style,z=ANS.zoom||autoZoom();document.body.style.zoom=z;vhSetzen();
 r.setProperty("--main-b",ANS.breite?ANS.breite+"px":"100%");r.setProperty("--tab-h",ANS.tabh?ANS.tabh+"px":"calc(var(--vh,100vh) - 240px)");
 r.setProperty("--kd-links",ANS.kd+"px");r.setProperty("--d-links",ANS.dl+"px");$("main").classList.toggle("mehrspaltig",!!ANS.spalten);
 const bs=$("an_breite_sel"),vb=[1200,1600,2200,3200,0];bs.value=vb.includes(ANS.breite)?ANS.breite:-1;$("an_breite").value=ANS.breite||6000;$("an_breite").disabled=!ANS.breite;
 $("an_breite_o").textContent=ANS.breite?ANS.breite+" px":"100 %";$("an_zoom_sel").value=ANS.zoom;$("an_zoom_o").textContent=Math.round(z*100)+" %"+(ANS.zoom?"":" (auto)");
 const ts=$("an_tabh_sel");ts.value=[0,320,520,900].includes(ANS.tabh)?ANS.tabh:-1;$("an_tabh").value=ANS.tabh||800;$("an_tabh").disabled=!ANS.tabh;$("an_tabh_o").textContent=ANS.tabh?ANS.tabh+" px":"Fenster";
 $("an_spalten").checked=!!ANS.spalten;if(typeof SYS!="undefined"&&SYS&&$("system").classList.contains("aktiv"))window.dispatchEvent(new Event("resize"))}
function ansSet(k,v){if(v===-1){v=k=="breite"?(ANS.breite||1800):(ANS.tabh||700)}ANS[k]=v;ansAnwenden();ansSpeichern()}
function ansSpeichern(){if(FERN){try{localStorage.setItem("sn_ansicht",JSON.stringify(ANS))}catch(e){}return}clearTimeout(ANST);ANST=setTimeout(()=>fetch("/api/ansicht",{method:"POST",headers:{"X-Token":T,"Content-Type":"application/json"},body:JSON.stringify(ANS)}).catch(()=>{}),500)}
function ansZurueck(){ANS={...ANS_STD};ansAnwenden();ansSpeichern()}
function ansichtPanel(an){const p=$("ansicht");p.classList.toggle("offen",an===undefined?!p.classList.contains("offen"):an)}
document.addEventListener("click",e=>{const p=$("ansicht");if(p.classList.contains("offen")&&!p.contains(e.target)&&!e.target.closest("header"))p.classList.remove("offen")});
function ziehen(e,bewegen,ende){e.preventDefault();document.body.classList.add("zieht");const mv=ev=>bewegen(ev),up=()=>{document.body.classList.remove("zieht");removeEventListener("pointermove",mv);removeEventListener("pointerup",up);ende&&ende()};addEventListener("pointermove",mv);addEventListener("pointerup",up)}
$("griff").addEventListener("pointerdown",e=>{const g=$("griff"),m=$("main");g.classList.add("zieht");
 ziehen(e,ev=>{const r=m.getBoundingClientRect(),f=m.offsetWidth/r.width,mitte=r.left+r.width/2;ANS.breite=Math.max(800,Math.round(2*Math.abs(ev.clientX-mitte)*f/10)*10);ansAnwenden()},()=>{g.classList.remove("zieht");ansSpeichern()})});
$("griff").addEventListener("dblclick",()=>ansSet("breite",ANS.breite?0:1200));
document.querySelectorAll(".teiler").forEach(t=>t.addEventListener("pointerdown",e=>{const box=$(t.dataset.box),k=t.dataset.k;t.classList.add("zieht");
 ziehen(e,ev=>{const r=box.getBoundingClientRect(),f=box.offsetWidth/r.width,w=(ev.clientX-r.left)*f;ANS[k]=Math.round(Math.min(box.offsetWidth-320,Math.max(k=="kd"?280:200,w)));ansAnwenden()},()=>{t.classList.remove("zieht");ansSpeichern()})}));
let UE=null;
async function schreibtest(){if(!confirm("Schreibzugriff prüfen?\nDabei wird ein Test-Voucher (1 Minute) angelegt und sofort wieder gelöscht. Sonst ändert sich nichts."))return;await api("/api/schreibtest",{},"log_st")}
async function vergleich(){const kz=$("ue_sp").value;if(!kz)return alert("Erst unter „Planung“ eine Sparte speichern.");const d=await api("/api/vergleich?sparte="+encodeURIComponent(kz),undefined,"log_ue");UE=d;
 const z=st=>d.ppsk.filter(p=>p.status==st).length;
 $("ue_k").innerHTML=kachel("Netze fehlen",d.netze.length,d.netze.length?"warn":"gut")+kachel("Passwörter neu",z("neu"),z("neu")?"warn":"gut")+kachel("Passwörter geändert",z("geaendert"),z("geaendert")?"warn":"gut")+kachel("Zugang entfernen",z("entfernen"),z("entfernen")?"schlecht":"gut")+kachel("aktuell",d.gleich,"gut")+(z("netz_fehlt")?kachel("Netz fehlt (Passwort wartet)",z("netz_fehlt"),"warn"):"");
 $("ue_bereich").style.display=(d.netze.length||d.ppsk.length)?"block":"none";
 $("ue_h_netze").textContent=d.netze.length?"Fehlende Netze ("+d.netze.length+")":"";
 $("ue_netze").innerHTML=d.netze.length?"<table><tr><th>Übertragen</th><th>Netz</th><th>VLAN</th><th>Subnetz</th></tr>"+d.netze.map(n=>`<tr><td><input type="checkbox" class="ue_n" value="${esc(n.Netz)}" style="width:auto" checked></td><td>${esc(n.Netz)}</td><td>${esc(n.VLAN)}</td><td>${esc(n.Subnetz)}</td></tr>`).join("")+"</table>":"";
 $("ue_h_ppsk").textContent=d.ppsk.length?"Passwörter je Parzelle ("+d.ppsk.length+" Unterschiede)":"";
 $("ue_ppsk").innerHTML=d.ppsk.length?"<table><tr><th>Übertragen</th><th>Parzelle</th><th>Netz</th><th>Status</th></tr>"+d.ppsk.map(p=>`<tr class="${p.status=="entfernen"?"falsch":p.status=="netz_fehlt"?"gesperrt":"geaendert"}"><td><input type="checkbox" class="ue_p" value="${esc(p.Parzelle)}" style="width:auto" checked></td><td>${esc(p.Parzelle)}</td><td>${esc(p.Netz)}</td><td>${esc(p.Status)}</td></tr>`).join("")+"</table>":""}
function ueAlle(an){document.querySelectorAll(".ue_n,.ue_p").forEach(c=>{if(!c.disabled)c.checked=an})}
async function uebertragen(aus){const kz=$("ue_sp").value,netze=[...document.querySelectorAll(".ue_n:checked")].map(c=>c.value),parz=[...document.querySelectorAll(".ue_p:checked")].map(c=>c.value);
 if(!netze.length&&!parz.length)return alert("Nichts ausgewählt.");
 if(aus&&!confirm(`Jetzt an das Gateway übertragen?\n\nSparte ${kz}\n${netze.length} Netz(e) anlegen\n${parz.length} Parzelle(n) Passwort setzen/ändern/entfernen\n\nVorher wird der alte Passwort-Stand gesichert.`))return;
 await api("/api/uebertragen",{sparte:kz,netze:netze,parzellen:parz,ausfuehren:aus},"log_ue");if(aus){const l=$("log_ue").textContent;await vergleich();$("log_ue").textContent=l+"\n\n"+$("log_ue").textContent}}
async function rueckgaengig(){const kz=$("ue_sp").value;if(!confirm("Die letzte Passwort-Übertragung für "+kz+" rückgängig machen?\nDas WLAN bekommt wieder den gesicherten Stand."))return;await api("/api/rueckgaengig",{sparte:kz},"log_ue")}
async function journalZeigen(){await api("/api/journal",undefined,"log_jn")}
let TF=null,TFL=[],TZ=null,TZAEND={};
function tfBereich(p,n){p=+p;n=+n||0;const start=p<=24?6:2,letzte=Math.pow(2,32-p)-2,platz=letzte-start+1;if(n>platz)return{fehler:"passt nicht – max. "+platz};const stop=n?start+n-1:letzte;return{text:"DHCP ."+start+"–."+stop+" · "+(stop-start+1)+" Geräte"}}
function tfMaske(p){const m=(0xffffffff<<(32-p))>>>0;return[m>>>24,(m>>16)&255,(m>>8)&255,m&255].join(".")}
function tfZeigen(){$("tf_tab").innerHTML="<tr><th>Tarif</th><th>Download Mbit/s</th><th>Upload Mbit/s</th><th>Preis €/Jahr</th><th>Netzmaske</th><th>Endgeräte</th><th>ergibt</th><th></th></tr>"+TFL.map((t,i)=>{const b=tfBereich(t.praefix,t.geraete);
 return `<tr><td><input class="tf_in" data-i="${i}" data-k="name" value="${esc(t.name)}" style="min-width:90px"></td><td><input class="tf_in" type="number" min="0.1" step="any" data-i="${i}" data-k="down" value="${esc(t.down)}" style="width:90px"></td><td><input class="tf_in" type="number" min="0.1" step="any" data-i="${i}" data-k="up" value="${esc(t.up)}" style="width:90px"></td><td><input class="tf_in" type="number" min="0" step="any" data-i="${i}" data-k="preis" value="${esc(t.preis??0)}" style="width:90px" title="${t.preis?(t.preis/12).toLocaleString("de-DE",{maximumFractionDigits:2})+" € im Monat":""}"></td>
 <td><select class="tf_in" data-i="${i}" data-k="praefix">${[24,25,26,27,28,29,30].map(p=>`<option value="${p}"${p==t.praefix?" selected":""}>/${p} · ${tfMaske(p)}</option>`).join("")}</select></td>
 <td><input class="tf_in" type="number" min="0" data-i="${i}" data-k="geraete" value="${esc(t.geraete)}" style="width:80px"></td><td class="tf_erg" data-i="${i}">${b.fehler?'<span class="fehler">'+esc(b.fehler)+"</span>":esc(b.text)}</td>
 <td><button class="k" onclick="tfWeg(${i})" title="Tarif entfernen">✕</button></td></tr>`}).join("");
 document.querySelectorAll(".tf_in").forEach(e=>e.oninput=e.onchange=()=>{const t=TFL[e.dataset.i];t[e.dataset.k]=e.dataset.k=="name"?e.value:e.value===""?"":+e.value;const b=tfBereich(t.praefix,t.geraete);
  document.querySelector(`.tf_erg[data-i="${e.dataset.i}"]`).innerHTML=b.fehler?'<span class="fehler">'+esc(b.fehler)+"</span>":esc(b.text)})}
function tfModusHint(){$("tf_modus_hint").textContent=$("tf_modus").value=="tarif"?"Wie in UniFi unter Einstellungen → QoS: eine Regel „SparteNet-Tarif-Basic“ mit allen Basic-Netzen. Bitte einmal prüfen, ob das Limit dann für jedes Netz einzeln oder für alle zusammen gilt (Geschwindigkeitstest in zwei Basic-Parzellen gleichzeitig). Teilen sich alle die Bandbreite, „eine Regel je Netz“ wählen.":"Jede Parzelle bekommt eine eigene Regel „SparteNet-Netz-BW-Paz.067“ – die Bandbreite ist sicher je Parzelle getrennt, dafür gibt es viele Regeln."}
async function tfLaden(){const d=await api("/api/tarife");TF=d;TFL=d.tarife.map(t=>({...t,alt:t.name}));tfZeigen();$("tf_modus").value=d.modus;tfModusHint();tzMassenFuellen()}
function tfNeu(){TFL.push({name:"Tarif "+(TFL.length+1),down:50,up:10,praefix:29,geraete:5,preis:0});tfZeigen()}
function tfWeg(i){if(!confirm("Tarif „"+TFL[i].name+"“ entfernen? Netze mit diesem Tarif sind danach ohne Tarif (erst nach „Speichern“)."))return;TFL.splice(i,1);tfZeigen()}
function tfStandard(){if(!confirm("Beispiel-Tarife Basic, Plus und Max einsetzen? Gespeichert wird erst mit „Tarife speichern“."))return;TFL=TF.standard.map(t=>({...t,alt:(TFL.find(x=>x.name==t.name)||{}).alt}));tfZeigen()}
async function tfSpeichern(){const d=await api("/api/tarife",{tarife:TFL,modus:$("tf_modus").value},"log_tf");TF.tarife=d.tarife;TF.modus=d.modus;TFL=d.tarife.map(t=>({...t,alt:t.name}));tfZeigen();tzMassenFuellen();if(TZ)tzZeigen()}
function tzOptionen(wert){return `<option value="">– kein Tarif –</option>`+(TF?TF.tarife:[]).map(t=>`<option value="${esc(t.name)}"${t.name==wert?" selected":""}>${esc(t.name)} · ${esc(t.down)}/${esc(t.up)} · /${t.praefix}</option>`).join("")}
function tzMassenFuellen(){$("tz_massen").innerHTML=tzOptionen("")}
async function tzLaden(){if(!TF)await tfLaden();if(Object.keys(TZAEND).length&&!confirm("Es gibt ungespeicherte Zuordnungen. Verwerfen?"))return;TZAEND={};
 const d=await api("/api/tarif-vergleich",undefined,"log_tz");TZ=d;tzZeigen()}
function tzZeigen(){const d=TZ,z=a=>d.ops.filter(o=>o.art==a).length;
 $("tz_k").innerHTML=kachel("Netze mit Tarif",d.zeilen.filter(r=>r.tarif).length,"gut")+kachel("Netze ändern",z("netz"),z("netz")?"warn":"gut")+kachel("QoS neu",z("qos_neu"),z("qos_neu")?"warn":"gut")+kachel("QoS ändern",z("qos_aendern"),z("qos_aendern")?"warn":"gut")+kachel("QoS löschen",z("qos_loeschen"),z("qos_loeschen")?"schlecht":"gut")+kachel("Hinweise",d.zeilen.filter(r=>r.warnung).length,d.zeilen.some(r=>r.warnung)?"warn":"gut");
 $("tz_bereich").style.display="block";
 $("tz_tab").innerHTML="<table><tr><th></th><th>Netz</th><th>VLAN</th><th>Subnetz jetzt</th><th>DHCP jetzt</th><th>QoS jetzt</th><th>Tarif</th><th>Ziel / Änderung</th><th>Hinweis</th></tr>"+d.zeilen.map(r=>{const w=r.id in TZAEND?TZAEND[r.id]:r.tarif;
  return `<tr data-id="${esc(r.id)}" data-such="${esc((r.name+" "+r.subnetz+" "+r.vlan+" "+r.tarif).toLowerCase())}" class="${r.id in TZAEND?"geaendert":r.status=="fehler"?"falsch":r.status=="aendern"?"geaendert":""}"><td><input type="checkbox" class="tz_m" style="width:auto"></td><td>${esc(r.name)}</td><td>${esc(r.vlan)}</td><td>${esc(r.subnetz)}</td><td>${esc(r.dhcp)}</td><td style="font-size:12px">${esc(r.qos||"–")}</td>
  <td><select class="tz_sel" data-id="${esc(r.id)}" style="min-width:170px">${tzOptionen(w)}</select></td><td style="font-size:12px">${r.id in TZAEND?"<i>ungespeichert</i>":esc(r.tarif?(r.status=="aendern"?r.aenderung:r.status=="gleich"?"✔ passt":r.aenderung)+(r.ziel?" → "+r.ziel:""):"")}</td><td style="font-size:12px">${esc(r.warnung)}</td></tr>`}).join("")+"</table>";
 document.querySelectorAll(".tz_sel").forEach(s=>s.onchange=()=>tzSetzen(s.dataset.id,s.value));tzFilter();tzOffen();tqZeigen()}
function tzSetzen(id,wert){const r=TZ.zeilen.find(x=>x.id==id);if(wert===r.tarif)delete TZAEND[id];else TZAEND[id]=wert;const s=document.querySelector(`.tz_sel[data-id="${CSS.escape(id)}"]`);if(s)s.value=wert;
 const tr=document.querySelector(`#tz_tab tr[data-id="${CSS.escape(id)}"]`);if(tr)tr.classList.toggle("geaendert",id in TZAEND||r.status=="aendern");tzOffen()}
function tzOffen(){const n=Object.keys(TZAEND).length;$("tz_offen").textContent=n?n+" ungespeichert":"alles gespeichert";$("tz_offen").classList.toggle("ok",!n)}
function tzFilter(){const q=$("tz_suche").value.trim().toLowerCase();document.querySelectorAll("#tz_tab tr[data-id]").forEach(tr=>tr.style.display=!q||tr.dataset.such.includes(q)?"":"none")}
function tzMarkAlle(an){document.querySelectorAll("#tz_tab tr[data-id]").forEach(tr=>{if(tr.style.display!="none"||!an)tr.querySelector(".tz_m").checked=an})}
function tzMassen(){const w=$("tz_massen").value,m=[...document.querySelectorAll("#tz_tab tr[data-id]")].filter(tr=>tr.style.display!="none"&&tr.querySelector(".tz_m").checked);if(!m.length)return alert("Erst Netze markieren (Häkchen links).");
 m.forEach(tr=>tzSetzen(tr.dataset.id,w));$("log_tz").textContent=m.length+" Netz(e) auf „"+(w||"kein Tarif")+"“ gesetzt – noch „Zuordnung speichern“."}
async function tzSpeichern(){if(Object.keys(TZAEND).length)await api("/api/tarif-zuordnung",{aenderungen:TZAEND},"log_tz");const l=$("log_tz").textContent;TZAEND={};const d=await api("/api/tarif-vergleich",undefined,"log_tz");TZ=d;tzZeigen();$("log_tz").textContent=l+"\n"+$("log_tz").textContent}
async function tzErkennen(){if(!TZ)await tzLaden();if(!TZ)return;const d=await api("/api/tarif-erkennen",{},"log_tz");let n=0;Object.entries(d.vorschlag).forEach(([id,t])=>{if(TZ.zeilen.some(r=>r.id==id)){tzSetzen(id,t);n++}});
 $("log_tz").textContent=n?n+" Netz(e) mit Vorschlag eingetragen (gelb markiert). Prüfen, dann „Zuordnung speichern“.":"Kein Vorschlag – alle Parzellen haben schon einen Tarif oder die Netzmaske passt zu keinem Tarif eindeutig."}
function tqZeigen(){const d=TZ,q=d.ops.filter(o=>o.art!="netz"),n=d.ops.filter(o=>o.art=="netz"),wort={qos_neu:"anlegen",qos_aendern:"ändern",qos_loeschen:"löschen"};
 $("tq_h_qos").textContent=q.length?"QoS-Regeln ("+q.length+")":"";$("tq_h_netz").textContent=n.length?"Netze: Subnetz / DHCP ("+n.length+")":"";
 $("tq_qos").innerHTML=q.length?"<table><tr><th>Übertragen</th><th>Regel</th><th>Aktion</th><th>Inhalt</th></tr>"+q.map(o=>`<tr class="${o.art=="qos_loeschen"?"falsch":"geaendert"}"><td><input type="checkbox" class="tq_r" value="${esc(o.name)}" style="width:auto" checked></td><td>${esc(o.name)}</td><td>${wort[o.art]}</td><td>${esc(o.text)}</td></tr>`).join("")+"</table>":"";
 $("tq_netz").innerHTML=n.length?"<table><tr><th>Übertragen</th><th>Netz</th><th>Änderung</th><th>Hinweis</th></tr>"+n.map(o=>{const r=d.zeilen.find(x=>x.id==o.id)||{};return `<tr class="geaendert"><td><input type="checkbox" class="tq_n" value="${esc(o.id)}" style="width:auto" checked></td><td>${esc(o.name)}</td><td>${esc(o.text)}</td><td style="font-size:12px">${esc(r.warnung||"")}</td></tr>`}).join("")+"</table>":"";
 $("tq_kn").style.display=(q.length||n.length)?"flex":"none";$("log_tq").textContent=(q.length||n.length)?"":"✔ Gateway entspricht den Tarifen – nichts zu übertragen."}
function tqAlle(an){document.querySelectorAll(".tq_r,.tq_n").forEach(c=>c.checked=an)}
async function tqUebertragen(aus){if(!TZ)return alert("Erst „Netze laden & Unterschiede ermitteln“.");if(Object.keys(TZAEND).length)return alert("Es gibt ungespeicherte Zuordnungen – erst „Zuordnung speichern & neu vergleichen“.");
 const regeln=[...document.querySelectorAll(".tq_r:checked")].map(c=>c.value),netze=[...document.querySelectorAll(".tq_n:checked")].map(c=>c.value);if(!regeln.length&&!netze.length)return alert("Nichts ausgewählt.");
 if(aus&&!confirm(`Jetzt an das Gateway übertragen?\n\n${regeln.length} QoS-Regel(n) anlegen/ändern/löschen\n${netze.length} Netz(e): Subnetz/DHCP ändern\n\n`+(netze.length?"Achtung: Geräte in verkleinerten Netzen mit IP außerhalb des neuen Bereichs verlieren kurz die Verbindung (WLAN aus/an hilft).\n\n":"")+"Vorher wird der alte Stand gesichert."))return;
 await api("/api/tarif-uebertragen",{regeln:regeln,netze:netze,ausfuehren:aus},"log_tq");if(aus){const l=$("log_tq").textContent;TZ=await api("/api/tarif-vergleich",undefined,"log_tz");tzZeigen();$("log_tq").textContent=l}}
async function tqRueckgaengig(){if(!confirm("Die letzte Tarif-Übertragung rückgängig machen?\nQoS-Regeln „SparteNet-…“ und geänderte Netze bekommen wieder den gesicherten Stand."))return;await api("/api/tarif-rueckgaengig",{},"log_tq");if(TZ){const l=$("log_tq").textContent;TZ=await api("/api/tarif-vergleich",undefined,"log_tz");tzZeigen();$("log_tq").textContent=l}}

const FERN=__FERN__==1;let INSTALL=null;
if(FERN)document.body.classList.add("fern");
if("serviceWorker" in navigator&&isSecureContext)navigator.serviceWorker.register("/sw.js").catch(()=>{});
addEventListener("beforeinstallprompt",e=>{e.preventDefault();INSTALL=e;$("install_k").style.display="flex"});
addEventListener("appinstalled",()=>{$("install_k").style.display="none"});
async function installieren(){if(!INSTALL)return;INSTALL.prompt();await INSTALL.userChoice;INSTALL=null;$("install_k").style.display="none"}
async function abmelden(){if(!confirm("Auf diesem Gerät abmelden?"))return;await fetch("/abmelden",{method:"POST",headers:{"X-Token":T}});location.reload()}
async function startLaden(){const d=await api("/api/start",undefined,"log_start");$("st_zeit").textContent=d.zeit;
 $("st_k").innerHTML=d.kacheln.map(k=>`<div class="kachel ${k.a}"><b>${esc(k.v)}</b>${esc(k.t)}<small>${esc(k.k||"")}</small></div>`).join("")}
async function parzelleZeigen(){const kz=$("st_sp").value,p=$("st_p").value;if(!kz)return alert("Erst unter „Planung“ eine Sparte speichern.");if(!p)return $("st_p").focus();
 $("pz_karte").innerHTML="";const d=await api("/api/parzelle?sparte="+encodeURIComponent(kz)+"&p="+encodeURIComponent(p),undefined,"log_pz");PZ=d;
 $("pz_karte").innerHTML=`<div class="pz"><div><dl><dt>Parzelle</dt><dd>${esc(d.parzelle)} · ${esc(d.sparte)}</dd><dt>Netz</dt><dd>${esc(d.netz)} (VLAN ${esc(d.vlan)})</dd><dt>WLAN</dt><dd>${esc(d.wlan)}</dd></dl>
 <div class="pw" id="pz_pw">${esc(d.passwort)}</div><div class="knoepfe" style="margin-top:4px"><button class="k" onclick="kopieren(PZ.passwort,'log_pz')">Passwort kopieren</button><button class="k" onclick="pzTeilen()">Teilen</button></div></div>
 <div class="qr" title="Mit der Handy-Kamera scannen – verbindet direkt mit dem WLAN">${d.qr}</div></div>`}
let PZ=null;
function pzTeilen(){teilen('WLAN Parzelle '+PZ.parzelle,'WLAN: '+PZ.wlan+'\nPasswort: '+PZ.passwort,'log_pz')}
async function kopieren(t,logid){try{await navigator.clipboard.writeText(t);$(logid).textContent="✔ In die Zwischenablage kopiert."}catch(e){prompt("Kopieren:",t)}}
async function teilen(titel,text,logid){if(navigator.share){try{await navigator.share({title:titel,text:text})}catch(e){}}else kopieren(text,logid)}
async function schnellVoucher(min){const dauer={120:"2 Stunden",1440:"1 Tag",10080:"1 Woche"}[min];if(!confirm("Einen Gast-Voucher für "+dauer+" erstellen?"))return;
 $("sv_code").innerHTML="";const d=await api("/api/voucher",{anzahl:1,minuten:min,name:"Gast",ausfuehren:true},"log_sv");const c=(d.codes||[])[0];
 if(c){const f=c.length==10?c.slice(0,5)+"-"+c.slice(5):c;$("sv_code").innerHTML=`<div class="code">${esc(f)}</div><p class="hint" style="text-align:center">Gültig ${dauer} ab der ersten Anmeldung im Gäste-WLAN</p><div class="knoepfe"><button class="k" onclick="teilen('Gast-WLAN','Gast-WLAN Zugangscode: ${esc(f)} (gültig ${dauer})','log_sv')">Teilen</button><button class="k" onclick="kopieren('${esc(f)}','log_sv')">Kopieren</button></div>`}}
async function fernLaden(){if(FERN)return;const d=await api("/api/fern",undefined,null);FERNST=d;
 $("fern_pin_st").textContent=d.pin_gesetzt?"festgelegt":"fehlt";$("fern_pin_st").className="status"+(d.pin_gesetzt?" ok":"");$("fern_lan").checked=d.lan;$("fern_lan").disabled=!!d.lan_env;
 $("fern_geraete").textContent=d.geraete.length?"Angemeldet: "+d.geraete.map(g=>(/Android/.test(g.geraet)?"Android":/iPhone|iPad/.test(g.geraet)?"iPhone/iPad":/Windows/.test(g.geraet)?"Windows":"Gerät")+" seit "+g.seit).join(" · "):"Noch kein Handy angemeldet.";
 const ts=d.tailscale;$("ts_st").innerHTML=!ts.installiert?"✖ Tailscale ist auf diesem PC nicht installiert – <b>tailscale.com/download</b>":!ts.aktiv?"⚠ Tailscale ist installiert, aber nicht angemeldet/aktiv.":ts.freigabe?"✔ Freigabe aktiv: <b>"+esc(ts.url)+"</b>":"Tailscale aktiv ("+esc(ts.name)+") – Freigabe noch aus.";
 $("ts_an").disabled=!ts.installiert||!ts.aktiv||ts.freigabe;$("ts_aus").disabled=!ts.freigabe;
 $("lan_st").innerHTML=d.lan_env?"Durch SPARTENET_HOST vorgegeben":d.lan_aktiv?(d.adressen.length?"✔ Erreichbar unter "+d.adressen.map(esc).join(", "):"✔ Eingeschaltet, aber keine Netzwerk-Adresse gefunden."):d.lan?"⚠ Eingeschaltet – wirkt nach Neustart des Managers.":"aus";
 $("fern_qr").innerHTML=Object.entries(d.qr).map(([u,s])=>`<figure>${s}<figcaption>${esc(u)}</figcaption></figure>`).join("")||'<p class="hint">Hier erscheinen QR-Codes, sobald ein Zugriff aktiv ist.</p>'}
let FERNST=null;
async function fernPin(){const p=$("fern_pin").value;if(!p)return $("fern_pin").focus();await api("/api/fern",{pin:p},"log_fern");$("fern_pin").value="";fernLaden()}
async function fernAbmelden(){if(!confirm("Alle Handy-, Tablet- und Browser-Sitzungen abmelden? Sie müssen sich danach erneut mit Manager-Passwort oder Handy-PIN anmelden."))return;await api("/api/fern",{abmelden:true},"log_fern");fernLaden()}
async function fernLan(){const an=$("fern_lan").checked;if(an&&!confirm("Den Manager im Heimnetz erreichbar machen?\nJedes Gerät im selben Netz sieht dann die Anmeldeseite – Zugriff nur mit Manager-Passwort oder optionaler Handy-PIN. Wirkt nach Neustart des Managers."))return $("fern_lan").checked=false;
 try{await api("/api/fern",{lan:an},"log_fern")}catch(e){$("fern_lan").checked=!an}fernLaden()}
async function tailscale(an){if(!confirm(an?"Tailscale-Freigabe einschalten?\nDer Manager ist dann für deine Geräte im Tailscale-Konto per HTTPS erreichbar (mit Manager-Passwort oder optionaler Handy-PIN).":"Tailscale-Freigabe ausschalten?"))return;await api("/api/tailscale",{an:an},"log_fern");fernLaden()}

let KK=null,KB=null,KBAEND={};
const eur=(v,n=0)=>v==null||v===""?"–":Number(v).toLocaleString("de-DE",{minimumFractionDigits:n,maximumFractionDigits:n})+" €";
const pct=v=>(v*100).toLocaleString("de-DE",{minimumFractionDigits:1,maximumFractionDigits:1})+" %";
function balken(v){const w=Math.round(Math.min(1,v)*100);return `<div class="balken" style="min-width:110px"><i class="${v<.3?"s":v<.6?"w":""}" style="width:${w}%"></i><span>${pct(v)}</span></div>`}
async function kkLaden(){const d=await api("/api/kalkulation?prognose="+($("kk_prog").checked?1:0),undefined,"log_kk");KK=d;const g=d.gesamt;
 $("kk_k").innerHTML=kachel("Auslastung (Sparten mit Buchungen)",pct(g.auslastung_konf),g.auslastung_konf>=.6?"gut":g.auslastung_konf>=.3?"warn":"schlecht")+
  kachel("gebuchte Parzellen",g.gebucht+" / "+g.parzellen_konf,"gut")+kachel("Sparten mit Buchungen",g.sparten_konf+" / "+g.sparten,"gut")+
  kachel("Auslastung aller eingetragenen",pct(g.auslastung_alle)+"<small>"+g.parzellen_alle+" Parzellen</small>","")+
  kachel("Umsatz / Jahr",eur(g.umsatz_brutto)+(g.ku?"":"<small>netto "+eur(g.umsatz)+"</small>"),"gut")+
  kachel("Deckungsbeitrag / Jahr",eur(g.db),g.db>=0?"gut":"schlecht")+
  kachel("Ergebnis nach zentralen Kosten",eur(g.ergebnis_vor_afa)+"<small>zentral "+eur(g.zentral)+" ("+(g.phase=="start"?"Startphase":"Ausbau")+")</small>",g.ergebnis_vor_afa>=0?"gut":"schlecht")+
  kachel("Ergebnis nach Abschreibung",eur(g.ergebnis)+"<small>AfA "+eur(g.afa)+"</small>",g.ergebnis>=0?"gut":"schlecht")+
  kachel("Kleinunternehmer-Grenze",g.ku?(g.ku_status.startsWith("unter")?"OK":"über"):"–",g.ku?(g.ku_status.startsWith("unter")?"gut":"schlecht"):"")+
  (g.ku?`<div class="kachel"><b style="font-size:16px">${esc(g.ku_status)}</b>Umsatz ${eur(g.umsatz_brutto)} von ${eur(g.ku_grenze)}<small>${g.ku_rest_parzellen!=null?"noch ca. "+g.ku_rest_parzellen+" Buchungen bis zur Grenze":""}</small></div>`:"");
 const T=d.tarife;let h="<table><tr><th>Sparte</th><th>Gateway</th><th>Parzellen</th><th>gebucht</th><th>Buchungsrate</th>"+T.map(t=>"<th>"+esc(t.name)+"<br><small>"+eur(t.preis)+"/J.</small></th>").join("")+
  "<th>Umsatz / Jahr</th><th>Ø € / Monat</th><th>Investition</th><th>Masten mit Technik</th><th>Uplink €/Monat</th><th>lfd. Kosten / Jahr</th><th>Deckungsbeitrag</th><th>Amortisation</th><th>Uplink-Bedarf</th><th>Status</th></tr>";
 for(const z of d.zeilen){h+=`<tr class="${z.status=="Prognose"?"gesperrt":""}"><td><b>${esc(z.name)}</b> <span class="mono" style="color:var(--muted)">${esc(z.kz)}</span></td><td>${esc(z.gateway)}</td><td>${z.n}</td><td>${z.status=="Prognose"?"≈ "+z.prognose:z.gebucht}</td><td>${balken(z.status=="Prognose"?z.prognose/z.n:z.rate)}</td>`+
  T.map(t=>"<td>"+(z.je[t.name]||"")+"</td>").join("")+`<td>${eur(z.umsatz_brutto)}</td><td>${z.erloes_monat?eur(z.erloes_monat,2):"–"}</td>
  <td><input class="kk_in" data-kz="${esc(z.kz)}" data-f="investition" value="${z.investition??""}" inputmode="decimal" style="width:110px"></td>
  <td><input class="kk_in" data-kz="${esc(z.kz)}" data-f="masten" value="${z.masten??""}" inputmode="numeric" style="width:70px"></td>
  <td><input class="kk_in" data-kz="${esc(z.kz)}" data-f="uplink" value="${z.uplink??""}" placeholder="${d.annahmen.uplink_monat}" inputmode="decimal" style="width:80px"></td>
  <td>${eur(z.kosten)}</td><td style="color:${z.db<0?"var(--red)":"inherit"}">${eur(z.db)}</td><td>${z.amortisation==null?"–":typeof z.amortisation=="number"?z.amortisation.toLocaleString("de-DE")+" J.":esc(z.amortisation)}</td>
  <td style="color:${z.uplink_warnung?"var(--red)":"inherit"}">${z.uplink_bedarf} Mbit/s</td><td>${esc(z.status)}</td></tr>`}
 h+=`<tr class="kopf"><td>Summe</td><td></td><td>${g.parzellen_alle}</td><td>${g.gebucht}</td><td>${balken(g.auslastung_alle)}</td>`+T.map(t=>"<td>"+(g.je[t.name]||"")+"</td>").join("")+
  `<td>${eur(g.umsatz_brutto)}</td><td></td><td>${eur(g.investition)}</td><td></td><td></td><td>${eur(g.kosten)}</td><td>${eur(g.db)}</td><td>${g.amortisation==null?"–":typeof g.amortisation=="number"?g.amortisation.toLocaleString("de-DE")+" J.":esc(g.amortisation)}</td><td></td><td></td></tr></table>`;
 $("kk_tab").innerHTML=d.zeilen.length?h:'<p class="hint" style="padding:12px">Noch keine Sparten – unter „Planung“ eintragen oder unten den VLAN-Planer übernehmen.</p>';
 document.querySelectorAll(".kk_in").forEach(e=>e.onchange=async()=>{await api("/api/kalk-sparte",{sparte:e.dataset.kz,[e.dataset.f]:e.value},"log_kk");kkLaden()});
 const alt=$("kb_sp").value;$("kb_sp").innerHTML=d.zeilen.map(z=>`<option value="${esc(z.kz)}">${esc(z.name)} (${esc(z.kz)})</option>`).join("");if(alt&&d.zeilen.some(z=>z.kz==alt))$("kb_sp").value=alt;
 $("kb_tarif").innerHTML='<option value="">– kein Tarif (nicht gebucht) –</option>'+T.map(t=>`<option value="${esc(t.name)}">${esc(t.name)} · ${eur(t.preis)}/Jahr</option>`).join("");
 kaZeigen(d.annahmen,d.texte);if(!KB&&d.zeilen.length)kbLaden(true)}
let GP=null;
const gz=(v,n=0)=>v==null||v===""?"–":Number(v).toLocaleString("de-DE",{minimumFractionDigits:n,maximumFractionDigits:n});
async function gpLaden(){gpZeigen(await api("/api/gwplan",undefined,"log_gp"))}
function gpZeigen(d){if(!d||!d.gesamt)return;GP=d;const g=d.gesamt,e=g.eigen;
 $("gp_quelle").textContent=d.quelle_daten;$("gp_quelle").className="status"+(d.quelle_daten.startsWith("Excel")?" ok":"");
 $("log_gp").textContent=(d.log||[]).join("\n");
 $("gp_k").innerHTML=kachel("theoretische Einnahmen / Jahr",eur(g.einnahme)+"<small>"+eur(g.einnahme_monat)+" im Monat"+(d.annahmen.KU==1?"":" · netto "+eur(g.einnahme_netto))+"</small>","gut")+
  kachel("Kunden (Buchungsquote)",gz(g.kunden)+"<small>"+pct(g.quote)+" von "+gz(g.parzellen)+" Parzellen</small>","gut")+
  kachel("Ø Preis je Kunde",eur(g.preis,2)+"<small>"+(g.preis_quelle=="tarife"?"nach Tarifmix":"fester Preis")+" · "+eur(g.preis/12,2)+" / Monat</small>","")+
  kachel("Standorte · Gateways · Internet",g.standorte+" · "+g.gateways+" · "+g.anschluesse+"<small>eigenständig: "+e.standorte+" · "+e.gateways+" · "+e.anschluesse+"</small>","")+
  kachel("Investition",eur(g.investition)+"<small>eigenständig "+eur(e.investition)+"</small>","")+
  kachel("laufende Kosten / Jahr",eur(g.laufend)+"<small>eigenständig "+eur(e.laufend)+" · zzgl. Zahlung "+eur(g.zahlung)+"</small>","")+
  kachel("Deckungsbeitrag / Jahr",eur(g.db)+"<small>vor zentralen Firmenkosten</small>",g.db>=0?"gut":"schlecht")+
  kachel("Amortisation",g.amortisation==null?"nie":gz(g.amortisation,1)+" J."+"<small>"+eur(g.inv_kunde)+" je Kunde</small>",g.amortisation!=null&&g.amortisation<=6?"gut":"warn")+
  kachel("Glasfaser zwischen Sparten",gz(g.faser)+" m","")+
  kachel("Prüfung",g.fehler?g.fehler+" Fehler":"OK",g.fehler?"schlecht":"gut")+
  (g.ist_gebucht?kachel("tatsächlich gebucht (Kalkulation)",gz(g.ist_gebucht)+"<small>"+eur(g.ist_einnahme)+" / Jahr</small>","gut"):"");
 const a=d.annahmen;if(document.activeElement==null||!document.activeElement.closest||!document.activeElement.closest("#netzplanung .reihe")){
  $("gp_pq").value=g.preis_quelle;$("gp_qm").value=String(a.Quote_Modus);$("gp_qf").value=String(+(a.Quote_fest*100).toFixed(2)).replace(".",",");$("gp_sz").value=String(a.Szenario);
  $("gp_mix").innerHTML=d.tarife.map(t=>`<div><label>Anteil ${esc(t.name)} (${eur(t.preis)}/Jahr) in %</label><input class="gp_mix" data-t="${esc(t.name)}" value="${String(t.mix).replace(".",",")}" inputmode="decimal"></div>`).join("")}
 let tt="<table><tr><th>Tarif</th><th>Preis / Jahr</th><th>Anteil</th><th>Kunden</th><th>Einnahmen / Jahr</th><th>Einnahmen / Monat</th></tr>";
 if(g.preis_quelle=="tarife"){for(const t of d.tarife){const j=g.je_tarif[t.name]||{kunden:0,einnahme:0};tt+=`<tr><td><b>${esc(t.name)}</b></td><td>${eur(t.preis)}</td><td>${pct(t.anteil)}</td><td>${gz(j.kunden)}</td><td>${eur(j.einnahme)}</td><td>${eur(j.einnahme/12)}</td></tr>`}}
 else tt+=`<tr><td>fester Preis</td><td>${eur(g.preis)}</td><td>100,0 %</td><td>${gz(g.kunden)}</td><td>${eur(g.einnahme)}</td><td>${eur(g.einnahme_monat)}</td></tr>`;
 tt+=`<tr class="kopf"><td>Alle Sparten</td><td>Ø ${eur(g.preis,2)}</td><td></td><td>${gz(g.kunden)}</td><td>${eur(g.einnahme)}</td><td>${eur(g.einnahme_monat)}</td></tr></table>`;$("gp_tt").innerHTML=tt;
 const alt=$("gp_stf").value;$("gp_stf").innerHTML='<option value="">alle Standorte</option>'+d.standorte.map(s=>`<option value="${s.nr}">${esc(s.name)} (${s.sparten} Sparten, ${s.gw} GW)</option>`).join("");if(d.standorte.some(s=>String(s.nr)==alt))$("gp_stf").value=alt;
 gpTabelle();
 $("gp_st").innerHTML="<table><tr><th>Nr.</th><th>Standort</th><th>Sparten (Reihenfolge)</th><th>Parzellen</th><th>Gateways</th><th>Belegung</th><th>Glasfaser­strecken</th><th>Aggregation</th><th>Kunden</th><th>Bedarf Mbit/s</th><th>Internet</th><th>Investition</th><th>laufend / Jahr</th><th>Prüfung</th></tr>"+
  d.standorte.map(s=>`<tr class="${s.pruefung.startsWith("Achtung")?"falsch":""}"><td>${s.nr}</td><td><b>${esc(s.name)}</b></td><td>${s.namen.map(esc).join(" → ")}</td><td>${s.parz}</td><td>${s.gw}</td><td>${balken(s.belegung)}</td><td>${s.straenge}</td><td>${s.agg}</td><td>${gz(s.kunden)}</td><td>${gz(s.bedarf)}</td><td>${s.anschluesse}</td><td>${eur(s.inv)}</td><td>${eur(s.lfd)}</td><td>${esc(s.pruefung)}</td></tr>`).join("")+
  `<tr class="kopf"><td></td><td>${d.standorte.length} Standorte</td><td></td><td>${gz(g.parzellen)}</td><td>${g.gateways}</td><td></td><td></td><td></td><td>${gz(g.kunden)}</td><td></td><td>${g.anschluesse}</td><td></td><td></td><td></td></tr></table>`;
 gpAnZeigen(d)}
function gpTabelle(){const d=GP;if(!d)return;const box=$("gp_tab"),y=box.scrollTop,x=box.scrollLeft;const such=$("gp_such").value.trim().toLowerCase(),stf=$("gp_stf").value,nurF=$("gp_err").checked;
 const inp=(z,f,wert,ph,w)=>`<input class="gp_in${w?" w":""}" data-nr="${z.nr}" data-f="${f}" value="${wert??""}" placeholder="${ph??""}" inputmode="decimal">`;
 const L=d.zeilen.filter(z=>(!such||z.name.toLowerCase().includes(such)||String(z.nr)==such)&&(!stf||String(z.standort)==stf)&&(!nurF||z.pruefung.startsWith("Fehler")));
 const sum=(k)=>L.reduce((s,z)=>s+(+z[k]||0),0);
 let h="<table><tr><th>Nr.</th><th>Sparte</th><th>Parzellen</th><th>Standort</th><th>Zuleitung von</th><th>Reihen­folge</th><th>Glasfaser m</th><th>versorgt durch</th><th>Quote %</th><th>Kunden</th><th>Einnahme / Jahr</th><th>Einnahme / Monat</th><th>tatsächlich gebucht</th><th>Investition</th><th>Deckungs­beitrag</th><th>Amorti­sation</th><th>Prüfung</th></tr>";
 for(const z of L){const w=z.w||{};const fe=z.pruefung.startsWith("Fehler");
  h+=`<tr class="${fe?"falsch":z.rolle=="Gateway-Standort"?"dienst":""}"><td>${z.nr}</td><td><b>${esc(z.name)}</b><br><small style="color:var(--muted)">${esc(z.stufe)} · ${esc(z.rolle)}</small></td>
  <td>${inp(z,"parz",w.parz,z.parz)}</td><td>${inp(z,"standort",w.standort,z.standort)}</td><td>${inp(z,"zuleitung",w.zuleitung,z.zuleitung??"")}</td><td>${inp(z,"reihenfolge",w.reihenfolge,"")}</td>
  <td>${inp(z,"entfernung",w.entfernung,z.faser_zul||"",1)}</td><td>${esc(z.versorgt)}</td>
  <td>${inp(z,"quote",w.quote!=null?String(+(w.quote*100).toFixed(2)).replace(".",","):"",(z.quote*100).toFixed(1).replace(".",","))}<br><small style="color:var(--muted)">${esc(z.herkunft)}</small></td>
  <td>${gz(z.kunden,1)}</td><td><b>${eur(z.einnahme)}</b></td><td>${eur(z.einnahme_monat)}</td><td>${z.ist_gebucht!=null?z.ist_gebucht+" · "+eur(z.ist_einnahme):"–"}</td>
  <td>${eur(z.investition)}</td><td style="color:${z.db<0?"var(--red)":"inherit"}">${eur(z.db)}</td><td>${z.amortisation==null?"nie":gz(z.amortisation,1)+" J."}</td><td>${esc(z.pruefung)}</td></tr>`}
 h+=`<tr class="kopf"><td></td><td>${L.length==d.zeilen.length?"Alle Sparten":L.length+" von "+d.zeilen.length+" Sparten"}</td><td>${gz(sum("parz"))}</td><td></td><td></td><td></td><td>${gz(sum("faser_zul"))}</td><td></td><td>${sum("parz")?pct(sum("kunden")/sum("parz")):"–"}</td><td>${gz(sum("kunden"))}</td><td>${eur(sum("einnahme"))}</td><td>${eur(sum("einnahme_monat"))}</td><td>${gz(sum("ist_gebucht"))}</td><td>${L.length==d.zeilen.length?eur(d.gesamt.investition):"–"}</td><td>${L.length==d.zeilen.length?eur(d.gesamt.db):"–"}</td><td></td><td></td></tr></table>`;
 box.innerHTML=L.length?h:'<p class="hint" style="padding:12px">Keine Sparte passt zum Filter.</p>';box.scrollTop=y;box.scrollLeft=x;
 box.querySelectorAll(".gp_in").forEach(e=>e.onchange=async()=>{const r=await api("/api/gwplan-sparte",{nr:+e.dataset.nr,[e.dataset.f]:e.value.trim()},"log_gp");if(r&&r.gesamt)gpZeigen(r)})}
function gpAnZeigen(d){if($("gp_an").dataset.fertig)return;const a=d.annahmen;
 $("gp_an").innerHTML=d.felder.map(([gr,fs],i)=>`<details class="gp_an"${i==0?" open":""}><summary style="cursor:pointer;font-weight:600;margin-top:8px">${esc(gr)}</summary><div class="reihe" style="margin-top:8px">`+
  fs.map(([k,t,ein])=>`<div><label>${esc(t)}${ein=="%"?" (%)":""}</label><input class="gp_ai" data-k="${k}" data-p="${ein=="%"?1:0}" value="${String(+(ein=="%"?a[k]*100:a[k]).toFixed(4)).replace(".",",")}" inputmode="decimal"></div>`).join("")+"</div></details>").join("");
 $("gp_an").dataset.fertig="1"}
async function gpAnSpeichern(){const an={};document.querySelectorAll(".gp_ai").forEach(e=>an[e.dataset.k]=e.value.trim());const r=await api("/api/gwplan-annahmen",{annahmen:an},"log_gpa");if(r&&r.gesamt){$("gp_an").dataset.fertig="";gpZeigen(r)}}
async function gpSchnell(){const mix={};document.querySelectorAll(".gp_mix").forEach(e=>mix[e.dataset.t]=e.value.trim()||"0");
 const r=await api("/api/gwplan-annahmen",{annahmen:{Quote_Modus:$("gp_qm").value,Quote_fest:$("gp_qf").value.trim(),Szenario:$("gp_sz").value},tarifmix:mix,preis_quelle:$("gp_pq").value},"log_gps");if(r&&r.gesamt){$("gp_an").dataset.fertig="";gpZeigen(r)}}
async function gpReset(was){if(!confirm(was=="wahl"?"Alle eigenen Zuordnungen (Standort, Zuleitung, Reihenfolge, Quote, Mengen) löschen?":was=="daten"?"Importierte Excel-Daten verwerfen und wieder die eingebauten Daten verwenden?":"Alle Einstellungen auf Standard zurücksetzen?"))return;
 const r=await api("/api/gwplan-zuruecksetzen",{was},was=="annahmen"?"log_gpa":"log_gpi");if(r&&r.gesamt){$("gp_an").dataset.fertig="";gpZeigen(r)}}
async function gpImport(){const f=$("gp_datei").files[0];if(!f)return;const r=await api("/api/gwplan-import",f,"log_gpi");$("gp_datei").value="";if(r&&r.gesamt){$("gp_an").dataset.fertig="";gpZeigen(r)}}
function gpCsv(){if(!GP)return;csvSpeichern({spalten:[["nr","Nr."],["name","Sparte"],["parz","Parzellen"],["leer","Leerstand"],["standort","Standort Nr."],["zuleitung","Zuleitung von Nr."],["versorgt","versorgt durch"],["faser_zul","Glasfaser Zuleitung m"],["quote_t","Buchungsquote"],["herkunft","Quote Herkunft"],["kunden_t","Kunden"],["einnahme_t","Einnahme / Jahr"],["monat_t","Einnahme / Monat"],["inv_t","Investition"],["db_t","Deckungsbeitrag / Jahr"],["pruefung","Prüfung"]],
 zeilen:GP.zeilen.map(z=>Object.assign({},z,{quote_t:(z.quote*100).toFixed(1).replace(".",",")+" %",kunden_t:String(z.kunden).replace(".",","),einnahme_t:String(z.einnahme).replace(".",","),monat_t:String(z.einnahme_monat).replace(".",","),inv_t:String(z.investition).replace(".",","),db_t:String(z.db).replace(".",",")}))},"SparteNet_Netzplanung")}
function kkCsv(){if(!KK)return;const T=KK.tarife;csvSpeichern({spalten:[["name","Sparte"],["kz","Kürzel"],["gateway","Gateway"],["n","Parzellen"],["gebucht","gebucht"],["rate_t","Buchungsrate"]].concat(T.map(t=>["t_"+t.name,t.name])).concat([["umsatz_brutto","Umsatz/Jahr"],["investition","Investition"],["kosten","lfd. Kosten/Jahr"],["db","Deckungsbeitrag"],["amortisation","Amortisation (J.)"],["status","Status"]]),
 zeilen:KK.zeilen.map(z=>Object.assign({},z,{rate_t:(z.rate*100).toFixed(1).replace(".",",")+" %"},Object.fromEntries(T.map(t=>["t_"+t.name,z.je[t.name]||0]))))},"SparteNet_Kalkulation")}
function kaZeigen(a,t){$("ka_form").innerHTML=Object.keys(t).map(k=>{const v=a[k];
 if(typeof v=="boolean")return `<div><label><input type="checkbox" class="ka_in" data-k="${k}" ${v?"checked":""} style="width:auto"> ${esc(t[k])}</label></div>`;
 if(k=="phase")return `<div><label>${esc(t[k])}</label><select class="ka_in" data-k="phase"><option value="auto"${v=="auto"?" selected":""}>automatisch (Kleinunternehmer → Startphase)</option><option value="start"${v=="start"?" selected":""}>Startphase</option><option value="voll"${v=="voll"?" selected":""}>Ausbau</option></select></div>`;
 return `<div><label>${esc(t[k])}</label><input class="ka_in" data-k="${k}" value="${String(v).replace(".",",")}" inputmode="decimal"></div>`}).join("")}
async function kaSpeichern(){const b={};document.querySelectorAll(".ka_in").forEach(e=>{b[e.dataset.k]=e.type=="checkbox"?e.checked:e.tagName=="SELECT"?e.value:e.value.replace(",",".")});await api("/api/kalk-annahmen",b,"log_ka");kkLaden()}
async function kkImport(){const f=$("kk_datei").files[0];if(!f)return;await api("/api/kalk-import",f,"log_ki");$("kk_datei").value="";KB=null;kkLaden()}
async function kbLaden(still){const kz=$("kb_sp").value;if(!kz)return;if(!still&&Object.keys(KBAEND).length&&!confirm("Ungespeicherte Buchungen verwerfen?"))return;KBAEND={};
 const d=await api("/api/buchungen?sparte="+encodeURIComponent(kz),undefined,"log_kb");KB=d;kbZeigen()}
function kbTarif(p){return p in KBAEND?KBAEND[p]:KB.zeilen[p-1].tarif}
function kbZeigen(){const T=KK?KK.tarife:[];const opt=w=>'<option value="">–</option>'+T.map(t=>`<option value="${esc(t.name)}"${t.name==w?" selected":""}>${esc(t.name)}</option>`).join("");
 $("kb_tab").innerHTML="<table><tr><th>Parzelle</th><th>Netz</th><th>Tarif</th></tr>"+KB.zeilen.map(z=>{const w=kbTarif(z.p);return `<tr class="${z.p in KBAEND?"geaendert":z.unbekannt?"falsch":""}"><td>${z.p}</td><td class="mono">${esc(z.netz)}</td><td><select class="kb_sel" data-p="${z.p}" style="min-width:140px">${opt(w)}</select>${z.unbekannt&&!(z.p in KBAEND)?" <small>Tarif „"+esc(z.tarif)+"“ fehlt</small>":""}</td></tr>`}).join("")+"</table>";
 document.querySelectorAll(".kb_sel").forEach(s=>s.onchange=()=>kbSetzen(+s.dataset.p,s.value));kbStand()}
function kbSetzen(p,w){if(w===KB.zeilen[p-1].tarif)delete KBAEND[p];else KBAEND[p]=w;const tr=document.querySelector(`.kb_sel[data-p="${p}"]`);if(tr){tr.value=w;tr.closest("tr").classList.toggle("geaendert",p in KBAEND)}kbStand()}
function kbStand(){const n=Object.keys(KBAEND).length,T=KK?KK.tarife:[],z={};let g=0;KB.zeilen.forEach(r=>{const w=kbTarif(r.p);if(w&&T.some(t=>t.name==w)){g++;z[w]=(z[w]||0)+1}});
 $("kb_k").innerHTML=kachel("gebucht",g+" / "+KB.n,"gut")+kachel("Buchungsrate",pct(g/KB.n),g/KB.n>=.6?"gut":"warn")+T.map(t=>kachel(esc(t.name),z[t.name]||0,"")).join("")+kachel("Umsatz / Jahr",eur(T.reduce((s,t)=>s+(z[t.name]||0)*t.preis,0)),"gut");
 $("kb_offen").textContent=n?n+" ungespeichert":"alles gespeichert";$("kb_offen").classList.toggle("ok",!n)}
function kbBereich(txt,max){const s=new Set();for(const teil of txt.split(/[,; ]+/).filter(Boolean)){const m=teil.match(/^(\d+)(?:-(\d+))?$/);if(!m)throw new Error("„"+teil+"“ verstehe ich nicht – Beispiel: 1-20, 25");let a=+m[1],b=+(m[2]||m[1]);if(a>b)[a,b]=[b,a];for(let p=a;p<=b;p++){if(p<1||p>max)throw new Error("Parzelle "+p+" gibt es nicht (1–"+max+")");s.add(p)}}return [...s]}
function kbMassen(){if(!KB)return;try{const ps=kbBereich($("kb_bereich").value,KB.n);if(!ps.length)return $("kb_bereich").focus();ps.forEach(p=>kbSetzen(p,$("kb_tarif").value));$("log_kb").textContent=ps.length+" Parzelle(n) auf „"+($("kb_tarif").value||"nicht gebucht")+"“ gesetzt – noch speichern."}catch(e){$("log_kb").innerHTML='<span class="fehler">✖ '+esc(e.message)+"</span>"}}
async function kbSpeichern(){if(!Object.keys(KBAEND).length)return $("log_kb").textContent="Nichts geändert.";await api("/api/buchungen",{sparte:KB.kz,aenderungen:KBAEND},"log_kb");const l=$("log_kb").textContent;KBAEND={};await kkLaden();await kbLaden(true);$("log_kb").textContent=l}
async function beenden(){if(confirm("SparteNet Manager beenden?")){await api("/api/beenden",{});document.body.innerHTML="<p style='padding:40px;font-family:Arial'>Beendet. Fenster kann geschlossen werden.</p>"}}
ansAnwenden();zeige(TABS.some(t=>t[0]==location.hash.slice(1))?location.hash.slice(1):"start");einst();planLaden(true);regelLaden();["pr_pre","pr_z"].forEach(i=>$(i).addEventListener("input",regelBeispiel));
</script></body></html>"""



if __name__ == "__main__":
    main()
