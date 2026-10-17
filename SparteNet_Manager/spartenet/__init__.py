"""SparteNet Manager – Programmcode, je Aufgabe eine Datei.

Reihenfolge (jede Datei übernimmt mit „from .vorher import *“ alle Namen der vorherigen):
basis → speicher → einstellungen → cloud → plan → qrcode → ppsk → system → karten → voucher → tarife → auth → fern → pwa
→ kalkulation → netzplanung_daten → netzplanung → zuteilung → umzug → benutzer → update → unterlagen → sicherung → zweifaktor → automation → mitglieder → tickets → pdf → rechnungen → vertraege → rundschreiben → datenschutz → zeitplan → laufzeit → portal → app → schnittstelle → oberflaeche → webserver

Neue Funktionen in die passende Datei schreiben; braucht eine Funktion etwas aus einer späteren Datei,
dort innerhalb der Funktion importieren (Beispiel: akt_start in fern.py).
"""
