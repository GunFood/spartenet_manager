"""SparteNet Manager – Zugriff auf die UniFi-Cloud (api.ui.com) und das Gateway"""
from .einstellungen import *  # noqa: F401,F403 – alle Namen der vorherigen Module


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

__all__ = [_n for _n in dict(globals()) if not _n.startswith("__")]  # alle Namen an die folgenden Module weitergeben
