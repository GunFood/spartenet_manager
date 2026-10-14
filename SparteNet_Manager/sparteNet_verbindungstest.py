#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SparteNet – Verbindungstest für das UniFi Cloud Gateway

  Fern (Gateway an einem anderen Ort):  über die UniFi-Cloud api.ui.com (Cloud-Connector)
  Lokal (gleiches Netz):                direkt über https://<IP des Gateways>

Start:   ./sparteNet_verbindungstest.py        (oder: python3 sparteNet_verbindungstest.py)
Nur lesende Aufrufe – am Gateway wird nichts verändert. Benötigt nur Python 3, keine Zusatzpakete.

API-Key:  unifi.ui.com → API (Site Manager API-Key) – für den Fernzugriff
          lokal: UniFi Network → Einstellungen → Control Plane → Integrationen
Der Key kann auch vorab gesetzt werden:  export UNIFI_KEY='...'
"""
import getpass, json, os, ssl, sys, time, urllib.error, urllib.request
from datetime import datetime

CLOUD = os.environ.get("SPARTENET_CLOUD_URL", "https://api.ui.com")
GRUEN, ROT, GELB, FETT, AUS = ("\033[32m", "\033[31m", "\033[33m", "\033[1m", "\033[0m") if sys.stdout.isatty() else ("",) * 5
BERICHT = []


def zeile(text=""):
    print(text)
    BERICHT.append(text.replace(GRUEN, "").replace(ROT, "").replace(GELB, "").replace(FETT, "").replace(AUS, ""))


def ok(t): zeile(f"{GRUEN}✔{AUS} {t}")
def fehler(t): zeile(f"{ROT}✖{AUS} {t}")
def info(t): zeile(f"{GELB}ℹ{AUS} {t}")


ERKLAERUNG = {
    401: "API-Key ungültig oder gelöscht – neuen Key erstellen und vollständig kopieren.",
    403: "Key hat keine Berechtigung für diese Konsole (anderes UniFi-Konto?) oder Funktion nicht freigegeben.",
    404: "Pfad nicht gefunden – Network-App bzw. Konsolen-Firmware zu alt, oder Konsole offline.",
    429: "Zu viele Anfragen – eine Minute warten und erneut starten.",
    502: "Konsole antwortet nicht über die Cloud – ist sie online und mit unifi.ui.com verbunden?",
    503: "Dienst vorübergehend nicht erreichbar – später erneut versuchen.",
}


class ApiFehler(Exception):
    def __init__(self, code, text):
        super().__init__(text); self.code = code


def hole(url, key, unsicher=False):
    req = urllib.request.Request(url, headers={"X-API-KEY": key, "Accept": "application/json"})
    ctx = ssl._create_unverified_context() if unsicher else ssl.create_default_context()
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=25, context=ctx) as r:
            roh = r.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        raise ApiFehler(e.code, e.read().decode("utf-8", "replace")[:300])
    except urllib.error.URLError as e:
        raise ApiFehler(0, f"keine Verbindung: {e.reason}")
    except TimeoutError:
        raise ApiFehler(0, "Zeitüberschreitung")
    ms = int((time.time() - t0) * 1000)
    try:
        return json.loads(roh), ms
    except json.JSONDecodeError:
        raise ApiFehler(-1, "Antwort ist kein JSON (falscher Pfad?): " + roh[:120])


def schritt(nr, titel, url, key, unsicher=False):
    zeile(f"\n{FETT}Schritt {nr}: {titel}{AUS}")
    try:
        daten, ms = hole(url, key, unsicher)
        return daten, ms
    except ApiFehler as e:
        grund = ERKLAERUNG.get(e.code, "")
        fehler(f"{'HTTP ' + str(e.code) if e.code > 0 else 'Fehler'}: {e}")
        if grund:
            info(grund)
        if e.code == 0:
            info("Internetverbindung prüfen. Lokal: stimmt die IP, ist der Rechner im Netz des Gateways?")
        return None, 0


def liste(daten):
    if isinstance(daten, dict):
        return daten.get("data", []) or []
    return daten or []


def tabelle(zeilen, spalten):
    if not zeilen:
        zeile("   (keine Einträge)"); return
    br = {k: min(32, max(len(k), *(len(str(z.get(k, "") or "")) for z in zeilen))) for k in spalten}
    zeile("   " + "  ".join(k.ljust(br[k]) for k in spalten))
    for z in zeilen[:25]:
        zeile("   " + "  ".join(str(z.get(k, "") or "")[:32].ljust(br[k]) for k in spalten))
    if len(zeilen) > 25:
        zeile(f"   … und {len(zeilen) - 25} weitere")


def konsole_waehlen(key):
    daten, ms = schritt(1, "UniFi-Cloud erreichen und Konsolen auflisten (api.ui.com/v1/hosts)", f"{CLOUD}/v1/hosts", key)
    if daten is None:
        return None
    hosts = liste(daten)
    ok(f"Cloud erreichbar ({ms} ms) – {len(hosts)} Konsole(n) in deinem Konto")
    if not hosts:
        fehler("Keine Konsole gefunden. Ist das Gateway in diesem UniFi-Konto (unifi.ui.com) eingetragen?"); return None
    auswahl = []
    for h in hosts:
        rs = h.get("reportedState") or {}
        auswahl.append({
            "nr": len(auswahl) + 1,
            "name": rs.get("name") or rs.get("hostname") or h.get("hardwareId", "")[:12],
            "modell": (rs.get("hardware") or {}).get("shortname") or rs.get("model") or h.get("type", ""),
            "firmware": rs.get("version") or ((rs.get("firmware") or {}).get("version", "") if isinstance(rs.get("firmware"), dict) else ""),
            "ip": h.get("ipAddress") or rs.get("ip", ""),
            "id": h.get("id", ""),
        })
    tabelle(auswahl, ["nr", "name", "modell", "firmware", "ip"])
    if len(auswahl) == 1:
        wahl = auswahl[0]
    else:
        while True:
            e = input(f"\nWelche Konsole testen? Nummer 1–{len(auswahl)}: ").strip()
            if e.isdigit() and 1 <= int(e) <= len(auswahl):
                wahl = auswahl[int(e) - 1]; break
    ok(f"Gewählt: {wahl['name']} ({wahl['modell']})")
    return wahl


def main():
    print(f"{FETT}SparteNet – Verbindungstest Cloud Gateway{AUS}\n")
    zeile(f"Datum: {datetime.now():%d.%m.%Y %H:%M}")
    print("Wo steht das Gateway?\n  1 = an einem anderen Ort (über die UniFi-Cloud)\n  2 = im gleichen Netz wie dieser Rechner")
    modus = (input("Auswahl [1]: ").strip() or "1")
    key = os.environ.get("UNIFI_KEY") or getpass.getpass("API-Key einfügen (Eingabe bleibt unsichtbar): ").strip()
    if not key:
        sys.exit("Kein API-Key eingegeben.")

    if modus == "2":
        ip = input("IP-Adresse des Gateways [192.168.1.1]: ").strip() or "192.168.1.1"
        basis, unsicher, nr = f"https://{ip}/proxy/network/integration", True, 1
        zeile(f"Modus: lokal · {ip}")
    else:
        zeile("Modus: Fernzugriff über api.ui.com")
        konsole = konsole_waehlen(key)
        if not konsole:
            return abschluss(False)
        basis, unsicher, nr = f"{CLOUD}/v1/connector/consoles/{konsole['id']}/proxy/network/integration", False, 2

    daten, ms = schritt(nr, "Network-App erreichen (/v1/info)", f"{basis}/v1/info", key, unsicher)
    if daten is None:
        if modus != "2":
            info("Der Cloud-Connector braucht eine aktuelle Konsolen-Firmware (UniFi OS 5.x) und eine aktuelle Network-App.")
        return abschluss(False)
    ok(f"Network-App antwortet ({ms} ms) – Version {daten.get('applicationVersion', '?')}")

    daten, ms = schritt(nr + 1, "Sites auslesen (/v1/sites)", f"{basis}/v1/sites", key, unsicher)
    sites = liste(daten) if daten is not None else []
    if not sites:
        if daten is not None:
            fehler("Keine Site gefunden.")
        return abschluss(False)
    site = sites[0]
    ok(f"{len(sites)} Site(s) – verwendet: {site.get('name', '')} (ID {site.get('id', '')})")

    s = f"{basis}/v1/sites/{site['id']}"
    ergebnisse = {}
    for i, (titel, pfad, spalten) in enumerate([
        ("Geräte (Gateway, Switches, Access Points)", "/devices?limit=200", ["name", "model", "ipAddress", "state", "firmwareVersion"]),
        ("Verbundene Clients", "/clients?limit=200", ["name", "type", "ipAddress"]),
        ("Netze / VLANs", "/networks?limit=200", ["name", "vlanId", "enabled"]),
        ("WLANs", "/wifi/broadcasts?limit=200", ["name", "type", "enabled"]),
    ], start=nr + 2):
        daten, ms = schritt(i, titel, s + pfad, key, unsicher)
        if daten is None:
            ergebnisse[titel] = None; continue
        eintraege = liste(daten)
        gesamt = daten.get("totalCount", len(eintraege)) if isinstance(daten, dict) else len(eintraege)
        ok(f"{gesamt} {'Eintrag' if gesamt == 1 else 'Einträge'} ({ms} ms)")
        tabelle(eintraege, spalten)
        ergebnisse[titel] = gesamt
    abschluss(all(v is not None for v in ergebnisse.values()))


def abschluss(erfolg):
    zeile("\n" + "=" * 60)
    if erfolg:
        ok(f"{FETT}Verbindung funktioniert. Die API ist einsatzbereit.{AUS}")
    else:
        fehler(f"{FETT}Test nicht vollständig erfolgreich – Hinweise oben beachten.{AUS}")
    pfad = os.path.join(os.path.dirname(os.path.abspath(__file__)), f"sparteNet_test_{datetime.now():%Y%m%d_%H%M}.txt")
    try:
        with open(pfad, "w", encoding="utf-8") as f:
            f.write("\n".join(BERICHT) + "\n")
        print(f"\nBericht gespeichert (ohne API-Key): {pfad}")
    except OSError:
        pass
    if sys.stdin.isatty():
        input("\nEnter zum Beenden ")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nAbgebrochen.")
