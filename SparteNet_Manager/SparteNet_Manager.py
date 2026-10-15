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
  benutzer         Benutzerkonten und Zugriffsrechte
  oberflaeche      HTML, CSS und JavaScript der Web-App
  webserver        Anfragen, Rechteprüfung, Start

Schema:
  Parzelle p auf Steckplatz n:  VLAN 1000 + n·100 + p  (Steckplatz 10: 3000 + p)   Netz 10.<Sparten-ID>.p.0/24
  Vorstand 2000 + n·10 + 1 (10.S.200.0/24) · Gäste +2 (10.S.201.0/24) · Technik +9 (10.S.250.0/24)
  Namen: BW-Paz.001, BW-Vorstand, BW-Gäste, BW-Technik · WLANs: <Präfix>-BW-Pächter, -Gäste, -Vorstand
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from spartenet.webserver import main  # noqa: E402

if __name__ == "__main__":
    main()
