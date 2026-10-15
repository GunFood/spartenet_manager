"""SparteNet Manager – Grundeinstellungen: Pfade, Umgebungsvariablen, Protokoll, Standardwerte, Kartendesign"""
import base64, concurrent.futures, copy, csv, hashlib, hmac, io, ipaddress, json, shutil, socket, subprocess, os, re, secrets, ssl, sys, threading, time, urllib.error, urllib.parse, urllib.request, webbrowser, zipfile
import xml.etree.ElementTree as ET
import logging, logging.handlers, traceback
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from http.cookies import SimpleCookie, CookieError


VERSION = "4.5"
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


def vlan_parzelle(slot, p):
    m, q = (slot, p) if p <= 99 else (slot + 1, p - 100)
    return (1000 + m * 100 if m <= 9 else 3000) + q


class Fehler(Exception):
    pass

__all__ = [_n for _n in dict(globals()) if not _n.startswith("__")]  # alle Namen an die folgenden Module weitergeben
