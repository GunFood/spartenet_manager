"""SparteNet Manager – API-Schnittstelle für andere Programme (Buchhaltung, Zahlungseingang, n8n, Zapier, Home Assistant …)

Zugang mit API-Schlüssel (legt ein Administrator an, wird nur einmal angezeigt, gespeichert nur als Prüfsumme):
    Authorization: Bearer sn_<id>_<geheim>      oder      X-API-Key: sn_<id>_<geheim>

    GET  /api/v1/status                       – Verbindung testen
    POST /api/v1/ereignis                     – Ereignis melden (z. B. {"ereignis":"zahlung","sparte":"BW","parzelle":12,"betrag":120}) → Automationen
    POST /api/v1/buchung                      – Tarif buchen/entfernen ({"sparte":"BW","parzelle":12,"tarif":"Basic"}; "" = entfernen)
    GET  /api/v1/buchungen?sparte=BW          – Buchungen lesen
    GET  /api/v1/tarife                       – Tarife lesen

Rechte je Schlüssel: ereignis · buchen · lesen; optional nur bestimmte Sparten. Am Gateway ändert die API nichts.
"""
from .automation import *  # noqa: F401,F403 – alle Namen der vorherigen Module

API_RECHTE = {"ereignis": "Ereignisse melden (startet Automationen, z. B. Zahlung eingegangen)",
              "buchen": "Tarif buchen / Buchung entfernen (im Manager)",
              "lesen": "Buchungen und Tarife lesen"}
API_PRO_MINUTE = max(10, int(os.environ.get("SPARTENET_API_PRO_MINUTE", "120") or 120))
API_MAX_BYTES = 64_000
_API_ZAEHLER = {}
_API_LOCK = threading.Lock()
_SCHLUESSEL_RE = re.compile(r"^sn_([0-9a-f]{8})_([A-Za-z0-9_-]{20,80})$")
_EREIGNIS_FELDER = {"sparte": 10, "parzelle": 6, "betrag": 20, "referenz": 80, "email": 200, "name": 100, "tarif": 40, "text": 500, "waehrung": 5}


class ApiFehler(Exception):
    def __init__(self, code, text):
        super().__init__(text)
        self.code = code


def api_daten(d):
    a = d.get("api") if isinstance(d.get("api"), dict) else {}
    if not isinstance(a.get("schluessel"), dict):
        a["schluessel"] = {}
    d["api"] = a
    return a


def _hash(geheim):
    return hashlib.sha256(("SparteNet-API|" + geheim).encode()).hexdigest()


def api_schluessel_pruefen(d, kopf_auth, kopf_key):
    roh = str(kopf_key or "").strip()
    if not roh and str(kopf_auth or "").lower().startswith("bearer "):
        roh = str(kopf_auth)[7:].strip()
    m = _SCHLUESSEL_RE.match(roh)
    if not m:
        raise ApiFehler(401, "API-Schlüssel fehlt oder ist ungültig (Authorization: Bearer sn_… oder X-API-Key).")
    i, geheim = m.groups()
    s = api_daten(d)["schluessel"].get(i)
    if not s or not hmac.compare_digest(s.get("hash", ""), _hash(geheim)):
        raise ApiFehler(401, "API-Schlüssel ungültig.")
    if not s.get("aktiv", True):
        raise ApiFehler(403, "API-Schlüssel ist deaktiviert.")
    with _API_LOCK:
        jetzt = time.time()
        z = [t for t in _API_ZAEHLER.get(i, []) if jetzt - t < 60]
        if len(z) >= API_PRO_MINUTE:
            raise ApiFehler(429, f"Zu viele Anfragen – höchstens {API_PRO_MINUTE} je Minute.")
        z.append(jetzt)
        _API_ZAEHLER[i] = z
    return i, s


def _recht(s, recht):
    if recht not in (s.get("rechte") or []):
        raise ApiFehler(403, f"Dieser API-Schlüssel hat das Recht „{recht}“ nicht.")


def _sparte(s, d, kz, pflicht=True):
    kz = str(kz or "").strip().upper()
    if not kz:
        if pflicht:
            raise ApiFehler(400, "„sparte“ (Kürzel) fehlt.")
        return ""
    if kz not in kalk_sparten(d):
        raise ApiFehler(400, f"Sparte „{kz}“ gibt es nicht.")
    if s.get("sparten") and kz not in s["sparten"]:
        raise ApiFehler(403, f"Dieser API-Schlüssel darf die Sparte „{kz}“ nicht.")
    return kz


def api_anfrage(methode, pfad, q, roh, kopf):
    """bearbeitet eine Anfrage an /api/v1/…; gibt (HTTP-Status, Antwort) zurück"""
    try:
        if len(roh or b"") > API_MAX_BYTES:
            raise ApiFehler(413, "Anfrage zu groß.")
        b = {}
        if methode == "POST":
            try:
                b = json.loads(roh or b"{}")
            except (ValueError, UnicodeDecodeError):
                raise ApiFehler(400, "Ungültiges JSON.")
            if not isinstance(b, dict):
                raise ApiFehler(400, "JSON-Objekt erwartet.")
        d = lade()
        i, s = api_schluessel_pruefen(d, kopf.get("Authorization"), kopf.get("X-API-Key"))
        ANFRAGE.benutzer = f"API:{s.get('name') or i}"
        LOG.info("API %s %s von Schlüssel %s (%s)", methode, pfad, i, s.get("name"))
        if (pfad, methode) == ("/api/v1/status", "GET"):
            antwort = {"ok": True, "produkt": "SparteNet Manager", "version": VERSION, "schluessel": s.get("name"), "rechte": s.get("rechte"), "sparten": s.get("sparten") or "alle"}
        elif (pfad, methode) == ("/api/v1/tarife", "GET"):
            _recht(s, "lesen")
            antwort = {"tarife": [{k: t.get(k) for k in ("name", "preis", "down", "up") if k in t} for t in tarife_pruefen(d["tarife"])]}
        elif (pfad, methode) == ("/api/v1/buchungen", "GET"):
            _recht(s, "lesen")
            kz = _sparte(s, d, q.get("sparte", [""])[0], pflicht=False)
            alle = d.get("buchungen") or {}
            antwort = {"buchungen": {k: v for k, v in alle.items() if (not kz or k == kz) and (not s.get("sparten") or k in s["sparten"])}}
        elif (pfad, methode) == ("/api/v1/buchung", "POST"):
            _recht(s, "buchen")
            kz = _sparte(s, d, b.get("sparte"))
            p = str(b.get("parzelle") or "").strip()
            if not p.isdigit():
                raise ApiFehler(400, "„parzelle“ (Nummer) fehlt.")
            with SCHREIB_SPERRE:
                d = lade()
                r = akt_buchungen_speichern(d, kz, {p: str(b.get("tarif") or "")})
            antwort = {"ok": True, "sparte": kz, "parzelle": int(p), "tarif": str(b.get("tarif") or ""), "meldung": r["log"][0]}
        elif (pfad, methode) == ("/api/v1/ereignis", "POST"):
            _recht(s, "ereignis")
            typ = re.sub(r"[^a-z0-9_.-]", "", str(b.get("ereignis") or b.get("typ") or "").lower())[:40]
            if not typ:
                raise ApiFehler(400, "„ereignis“ fehlt (z. B. \"zahlung\" oder ein eigener Name).")
            daten = {k: text_einzeilig(b[k], n) for k, n in _EREIGNIS_FELDER.items() if b.get(k) not in (None, "")}
            if "sparte" in daten:
                daten["sparte"] = _sparte(s, d, daten["sparte"])
            elif s.get("sparten"):
                raise ApiFehler(403, "Dieser API-Schlüssel ist auf Sparten beschränkt – „sparte“ angeben.")
            if "parzelle" in daten:
                if not daten["parzelle"].isdigit():
                    raise ApiFehler(400, "„parzelle“ muss eine Nummer sein.")
                daten["parzelle"] = int(daten["parzelle"])
            if "betrag" in daten:
                try:
                    daten["betrag"] = f"{float(daten['betrag'].replace(',', '.')):.2f}"
                except ValueError:
                    raise ApiFehler(400, "„betrag“ muss eine Zahl sein.")
            daten["quelle"] = f"API:{s.get('name') or i}"
            art = typ if typ in ("zahlung", "buchung", "kuendigung") else "api"
            if art in ("buchung", "kuendigung"):
                raise ApiFehler(400, "Buchungen bitte über POST /api/v1/buchung – dann stimmen Daten und Automationen.")
            if art == "api":
                daten["ereignis_name"] = typ
            with SCHREIB_SPERRE:
                ergebnisse = automation_verarbeiten(art, daten, lade())
            journal(f"API-Ereignis „{typ}“ von {s.get('name') or i}: {len(ergebnisse)} Aktion(en)")
            antwort = {"ok": True, "ereignis": typ, "aktionen": ergebnisse}
        else:
            raise ApiFehler(404, "Unbekannter Endpunkt. Verfügbar: GET /api/v1/status, GET /api/v1/tarife, GET /api/v1/buchungen, POST /api/v1/buchung, POST /api/v1/ereignis")
        with SCHREIB_SPERRE:
            d2 = lade()
            x = api_daten(d2)["schluessel"].get(i)
            if x is not None:
                x["zuletzt"], x["anfragen"] = time.strftime("%Y-%m-%d %H:%M"), int(x.get("anfragen", 0)) + 1
                speichere(d2)
        return 200, antwort
    except ApiFehler as e:
        LOG.warning("API %s %s abgelehnt: %s", methode, pfad, e)
        return e.code, {"ok": False, "fehler": str(e)}
    except Fehler as e:
        return 400, {"ok": False, "fehler": str(e)}
    except Exception as e:
        ref = secrets.token_hex(3)
        LOG.error("API-Fehler %s bei %s:\n%s", ref, pfad, traceback.format_exc())
        return 500, {"ok": False, "fehler": f"Unerwarteter Fehler (Nr. {ref}, {type(e).__name__})."}
    finally:
        ANFRAGE.benutzer = None


# ---- Verwaltung (nur Administratoren) --------------------------------------------------------------
def akt_api(d):
    liste = [{"id": i, **{k: s.get(k) for k in ("name", "rechte", "sparten", "aktiv", "angelegt", "von", "zuletzt", "anfragen")}}
             for i, s in api_daten(d)["schluessel"].items()]
    liste.sort(key=lambda x: (x["name"] or "").lower())
    return {"schluessel": liste, "rechte": API_RECHTE, "pro_minute": API_PRO_MINUTE, "log": []}


def akt_api_schluessel_neu(d, b, ich):
    name = text_einzeilig(b.get("name") or "", 60).strip()
    if not name:
        raise Fehler("Bitte einen Namen angeben (z. B. „Buchhaltung“ oder „n8n“).")
    rechte = [r for r in API_RECHTE if r in (b.get("rechte") or [])]
    if not rechte:
        raise Fehler("Bitte mindestens ein Recht wählen.")
    sparten = sorted({str(x).strip().upper() for x in (b.get("sparten") or []) if str(x).strip()})
    bekannt = set(kalk_sparten(d))
    falsch = [x for x in sparten if x not in bekannt]
    if falsch:
        raise Fehler("Unbekannte Sparte(n): " + ", ".join(falsch))
    a = api_daten(d)
    i = secrets.token_hex(4)
    while i in a["schluessel"]:
        i = secrets.token_hex(4)
    geheim = secrets.token_urlsafe(32)
    a["schluessel"][i] = {"name": name, "hash": _hash(geheim), "rechte": rechte, "sparten": sparten, "aktiv": True,
                          "angelegt": time.strftime("%Y-%m-%d %H:%M"), "von": ich}
    speichere(d)
    journal(f"API-Schlüssel angelegt: {name} ({', '.join(rechte)}{'; Sparten ' + ', '.join(sparten) if sparten else ''}) durch {ich}")
    r = akt_api(d)
    r["neu"] = f"sn_{i}_{geheim}"
    r["log"] = [f"✔ API-Schlüssel „{name}“ angelegt. Jetzt kopieren – er wird nur dieses eine Mal angezeigt."]
    return r


def akt_api_schluessel_aendern(d, b, ich):
    a = api_daten(d)
    i = str(b.get("id") or "")
    s = a["schluessel"].get(i)
    if not s:
        raise Fehler("API-Schlüssel nicht gefunden.")
    if b.get("loeschen"):
        del a["schluessel"][i]
        text = f"gelöscht: {s['name']}"
    else:
        s["aktiv"] = bool(b.get("aktiv"))
        text = f"{'aktiviert' if s['aktiv'] else 'deaktiviert'}: {s['name']}"
    speichere(d)
    journal(f"API-Schlüssel {text} durch {ich}")
    r = akt_api(d)
    r["log"] = [f"✔ API-Schlüssel {text}."]
    return r


__all__ = [_n for _n in dict(globals()) if not _n.startswith("__")]  # alle Namen an die folgenden Module weitergeben
