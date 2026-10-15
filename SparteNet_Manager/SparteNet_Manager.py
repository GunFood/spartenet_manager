#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SparteNet Manager (Cloud) – Bedienoberfläche für UniFi Cloud Gateways in Kleingartensparten

Funktioniert vollständig über die UniFi-Cloud (api.ui.com) – kein lokaler Zugriff, kein VPN.
Benötigt nur Python 3 (für MariaDB/MySQL zusätzlich PyMySQL).

Start:  ./SparteNet_starten.sh  ·  oder  python3 SparteNet_Manager.py
Der Browser öffnet sich unter http://127.0.0.1:8765

Der Programmcode liegt im Ordner spartenet/ – je Aufgabe eine Datei, in dieser Reihenfolge
(jede Datei baut auf den vorherigen auf):
  basis            Pfade, Umgebungsvariablen, Protokoll, Standardwerte, Kartendesign
  speicher         Dateien im Datenordner oder MariaDB/MySQL, Änderungsprotokoll, Logo
  einstellungen    Einstellungen laden und speichern
  cloud            Zugriff auf die UniFi-Cloud und das Gateway
  plan             Sparten, Parzellen, VLANs, Netze, Passwort-Regeln, Excel-Import
  qrcode           QR-Code ohne Zusatzpakete
  ppsk             Auslesen, Abgleich, Passwörter je Parzelle, Übertragen, Rückgängig
  system           Systeminfo, alle Daten, Diagnose, Ansicht
  karten           Zugangskarten und Gast-Voucher
  tarife           Tarife: Bandbreite (QoS) und Netzgröße
  auth             Manager-Passwort, Handy-PIN, Sitzungen
  fern             Handy & Tablet, Tailscale, Überblick
  pwa              Web-App: Icons, Manifest, Anmeldeseite
  kalkulation      Buchungen, Umsatz, Auslastung
  netzplanung_daten, netzplanung   Gateway-Standorte, Glasfaser, Buchungsquote, Einnahmen
  benutzer         Benutzerkonten und Zugriffsrechte je Bereich
  update           Aktualisierung von GitHub (wie bei Nextcloud)
  oberflaeche      HTML, CSS und JavaScript der Web-App
  webserver        Anfragen, Rechteprüfung, Start

Schema:
  Parzelle p auf Steckplatz n:  VLAN 1000 + n·100 + p  (Steckplatz 10: 3000 + p)   Netz 10.<Sparten-ID>.p.0/24
  Vorstand 2000 + n·10 + 1 (10.S.200.0/24) · Gäste +2 (10.S.201.0/24) · Technik +9 (10.S.250.0/24)
  Namen: BW-Paz.001, BW-Vorstand, BW-Gäste, BW-Technik · WLANs: <Präfix>-BW-Pächter, -Gäste, -Vorstand
"""
import json
import os
import re
import sys

MITGELIEFERT = os.path.dirname(os.path.abspath(__file__))


def _version(ordner):
    try:
        with open(os.path.join(ordner, "spartenet", "basis.py"), encoding="utf-8") as f:
            m = re.search(r'^VERSION\s*=\s*"([^"]+)"', f.read(), re.M)
        return tuple(int(x) for x in re.findall(r"\d+", m.group(1))[:4]) if m else (0,)
    except OSError:
        return (0,)


def _aktiv_datei():
    daten = os.path.abspath(os.environ.get("SPARTENET_DATA_DIR") or os.path.dirname(os.path.abspath(sys.argv[0])))
    return os.path.join(daten, "updates", "aktiv.json")


def _code_ordner():
    """aktualisierte Version aus dem Datenordner (updates/), wenn sie neuer ist als die mitgelieferte"""
    if os.environ.get("SPARTENET_UPDATE_AUS") == "1":
        return MITGELIEFERT, None
    try:
        with open(_aktiv_datei(), encoding="utf-8") as f:
            a = json.load(f)
    except (OSError, ValueError):
        return MITGELIEFERT, None
    if not isinstance(a, dict) or not a.get("ordner") or a.get("fehler"):
        return MITGELIEFERT, None
    p = os.path.join(os.path.dirname(_aktiv_datei()), os.path.basename(a["ordner"]))
    if os.path.isfile(os.path.join(p, "spartenet", "webserver.py")) and _version(p) > _version(MITGELIEFERT):
        return p, a
    return MITGELIEFERT, None


def _laden():
    ordner, aktiv = _code_ordner()
    sys.path.insert(0, ordner)
    try:
        from spartenet.webserver import main
        return main
    except Exception as e:  # neue Version startet nicht → automatisch zurück zur mitgelieferten
        if ordner == MITGELIEFERT:
            raise
        print(f"Die aktualisierte Version startet nicht ({type(e).__name__}: {e}) – zurück zur mitgelieferten Version.")
        try:
            aktiv["fehler"] = f"{type(e).__name__}: {e}"[:300]
            with open(_aktiv_datei(), "w", encoding="utf-8") as f:
                json.dump(aktiv, f, ensure_ascii=False, indent=1)
        except OSError:
            pass
        sys.path.remove(ordner)
        for name in [n for n in sys.modules if n == "spartenet" or n.startswith("spartenet.")]:
            del sys.modules[name]
        sys.path.insert(0, MITGELIEFERT)
        from spartenet.webserver import main
        return main


if __name__ == "__main__":
    _laden()()
