SparteNet Manager 4.2 (Cloud)
===============================

Funktioniert komplett über die UniFi-Cloud (api.ui.com). Kein lokaler Zugriff, kein VPN.
Benötigt nur Python 3 – keine Zusatzpakete.

### STARTEN
  - Linux (Nobara):  einmal ./installieren.sh (Menüeintrag), danach aus dem Anwendungsmenü  
                   oder direkt ./SparteNet_starten.sh
                   
  - Windows:         Doppelklick auf SparteNet_starten.bat

### ZUGRIFFSSCHUTZ
  Vor dem Start muss ein Manager-Passwort mit mindestens 12 Zeichen konfiguriert sein.
  Direktstart: SPARTENET_PASSWORD als Umgebungsvariable setzen.
  
  Docker Compose: SPARTENET_PASSWORD_FILE auf ein Docker Secret zeigen lassen (empfohlen):
````
  services:
    spartenet-manager:
      environment:
        SPARTENET_HOST: "0.0.0.0"
        SPARTENET_DATA_DIR: /data
        SPARTENET_PASSWORD_FILE: /run/secrets/spartenet_password
      volumes:
        - spartenet-daten:/data
      secrets:
        - spartenet_password
  volumes:
    spartenet-daten:
  secrets:
    spartenet_password:
      file: ./secrets/spartenet_password.txt
````
  
Persistente Daten (Konfiguration, WLAN-Passwörter, Sicherungen, Protokolle) gehören in ein beschreibbares Volume nach /data.
Dafür SPARTENET_DATA_DIR: /data setzen und das Volume nach /data mounten.
Das Passwort gilt für lokale und entfernte Zugriffe. Auf entfernten Handys kann zusätzlich die
bestehende Handy-PIN verwendet werden. Die Anmeldung bleibt bis zu 30 Tage gültig; „Abmelden“
beendet die Sitzung auf dem Gerät. Passwortänderungen erfordern einen Neustart des Managers.
Den Zugriff nicht unverschlüsselt ins Internet veröffentlichen; für Fernzugriff HTTPS/Tailscale nutzen.

### ERSTE SCHRITTE
  1. Verbindung: Site-Manager-API-Key (unifi.ui.com > Einstellungen > API Keys, als Besitzer erstellt)
     eintragen > "Konsolen laden" > Konsole wählen > Speichern > Verbindung testen.
  2. Planung: Sparten eintragen (Name, Kürzel, Sparten-ID, Parzellen) oder aus dem VLAN-Planer übernehmen.
  3. Abgleich: zeigt fehlende Netze und Geräte im falschen Netz.
  4. Einrichten: erst Vorschau, dann "Erstes Netz anlegen (Test)", prüfen, dann alle fehlenden.
     Passwörter je Parzelle erzeugen oder direkt in der Tabelle ändern ("neu", "sperren", "↺"),
     "Änderungen speichern", dann Schritt 4 "Ausführen", Karten der geänderten Parzellen drucken.
  5. Kartendesign: Format (A4/A5/A6, hoch oder quer), Farben, Schrift und Größen, Texte,
     QR-Code-Größe und -Farbe, Rahmen und Logo einstellen – mit Live-Vorschau. "Speichern" –
     danach werden alle Zugangskarten (Einrichten, Schritt 3) in diesem Design gedruckt.
     Platzhalter in Texten: {sparte} {kz} {parzelle} {wlan}. Beispiel-Logo: SparteNet_Logo_fuer_Karten.png
  6. Gast-Voucher erstellen und drucken.
  7. Systeminfo: Internet-Durchsatz, Latenz und Paketverlust (24 h), Auslastung aller Geräte
     (CPU, RAM, Uplink, Ports, Funk), Clients und – falls freigegeben – Datenverkehr je Parzelle.
  8. Alle Daten: jede lesbare Quelle (Network-API, UniFi-Cloud, klassische Schnittstelle) als Tabelle
     oder JSON, mit Export. "Verfügbarkeit prüfen" zeigt, was über die Cloud geht. Nur lesend.

### KALKULATION & AUSLASTUNG (Reiter "Kalkulation")
  1. "Aus Excel übernehmen": Kalkulation_Sparten_WLAN.xlsx (Annahmen, Tarifpreise, Investition und
     Masten je Sparten-Blatt) und/oder den VLAN-Planer (alle Sparten mit Gateway).
  2. Buchungen erfassen: Sparte wählen, Parzellen (z. B. "1-20, 25") und Tarif, "setzen", speichern.
     Tarife, die im Reiter "Tarife" einer Parzelle zugeordnet sind, zählen automatisch als Buchung – und umgekehrt.
  3. Tabelle "Je Sparte": gebuchte Parzellen je Tarif, Buchungsrate, Umsatz, laufende Kosten,
     Deckungsbeitrag, Amortisation, Uplink-Bedarf. Investition/Masten/Uplink direkt in der Tabelle änderbar.
  Oben: Gesamtauslastung aller Sparten mit Buchungen, Umsatz, Ergebnis, Kleinunternehmer-Grenze.
  "Prognose": Sparten ohne Buchungen mit der Buchungsquote aus den Annahmen hochrechnen.
  Tarifpreise (€ pro Jahr) stehen im Reiter "Tarife".

### NETZPLANUNG & EINNAHMEN (Reiter "Netzplanung") – neu in 4.2
  Gleiche Rechnung wie Kleingarten_Gateway_Planung.xlsx (liegt im Ordner): 88 Kleingartenanlagen aus dem
  Kleingartenentwicklungskonzept 2040 sind eingebaut, ein Excel-Import ist nicht nötig.
  1. Tabelle "Je Sparte" (gelbe Felder, sofort gespeichert): Standort = Nr. der Sparte mit den Gateways,
     Zuleitung von = Nr. der Sparte, von der die Glasfaser kommt (Kette A -> B -> C -> D möglich),
     Reihenfolge, Glasfaser m, Quote %, Parzellen. Leer = Vorschlag bzw. berechneter Wert.
  2. 55 Parzellen je Gateway, der Reihe nach gefüllt; ein Internet-Anschluss je Standort (ein weiterer
     erst, wenn der Bedarf größer ist). Kein Richtfunk, Tiefbau 0 €/m (änderbar).
  3. Theoretische Einnahme je Sparte = Parzellen × Buchungsquote × Ø Tarifpreis; oben die Summe aller
     Sparten pro Jahr und Monat. Ø Preis aus den Tarifpreisen (Reiter "Tarife") und dem Tarifmix
     oder ein fester Preis. Buchungsquote: aus Alter und Leerstand (heute / in 5 Jahren) oder fest;
     "Quote %" je Sparte gilt immer vorrangig. Wo im Reiter "Kalkulation" schon gebucht ist, steht
     die tatsächliche Buchung daneben.
  4. Standorte (Gateways, Internet, Kosten), Investition, laufende Kosten, Deckungsbeitrag,
     Amortisation, Vergleich "jede Sparte eigenständig", Prüfung der Zuordnung, CSV-Export.
  5. "Aus Excel übernehmen": Kleingarten_Gateway_Planung.xlsx (Sparten, gelbe Spalten, Annahmen).

### VLAN-PLANER (VLAN_Planer_SparteNet.xlsx) – MEHRERE GATEWAYS
  Blatt "Sparten": alle 88 Kleingartenanlagen (Kleingartenentwicklungskonzept 2040) mit Parzellen.
    Je Sparte die Gateway-Nr. wählen, optional die Reihenfolge am Gateway (1 = erster Steckplatz).
    Kürzel und Sparten-ID sind Vorschläge und änderbar (müssen einmalig sein).
  Blatt "Gateways": Bezeichnung je Gateway, Belegung der 10 Steckplätze, Status/Fehler.
  Blatt "Eingabe": in B4 das Gateway wählen – Übersicht, VLAN-Plan, Beispiele zeigen dieses Gateway.
  In den Manager übernehmen: B4 wählen, Datei speichern, im Manager Planung > "Aus Excel übernehmen".

### PASSWORT-REGEL
  Neu erzeugte WLAN-Passwörter: SN + 10 Ziffern (z. B. SN4827130596), einstellbar unter Einrichten > Schritt 3.
  Jedes Passwort ist einmalig – über alle Sparten und gegenüber allen früher vergebenen.
  Das Register SparteNet_Passwort_Register.txt enthält nur Prüfsummen, keine Passwörter. Nicht löschen.

### ÄNDERUNGEN ÜBERTRAGEN (Reiter "Übertragen")
  1. "Schreibzugriff prüfen" (legt einen Test-Voucher an und löscht ihn sofort wieder).
  2. Sparte wählen > "Unterschiede ermitteln": fehlende Netze und Passwörter (neu/geändert/zu entfernen).
  3. Auswählen > "Vorschau" > "Ausgewählte übertragen". Danach liest der Manager zur Kontrolle nach.
  Vor jeder Passwort-Übertragung wird der alte Stand gesichert (SparteNet_Sicherung_<Kürzel>_*.json,
  enthält Passwörter – vertraulich). "Letzte Passwort-Übertragung rückgängig" spielt ihn zurück.
  Jede Übertragung steht ohne Passwörter in SparteNet_Aenderungen.log.

### HANDY, TABLET, FOLD – ALS APP
  Der Manager läuft auf dem PC, Handy/Tablet sind die Bedienung (PC muss an sein, Manager offen).
  Am PC: Verbindung > "Handy & Tablet":
1. Optional eine separate Handy-PIN festlegen (6–32 Zeichen). Ohne PIN ist der Zugriff vom Handy
       weiterhin mit dem Manager-Passwort möglich.
   
2. QR-Code mit dem Handy scannen, Manager-Passwort oder eingerichtete Handy-PIN eingeben, dann
       Android/Chrome: Menü ⋮ > "App installieren"   ·   iPhone/iPad/Safari: Teilen > "Zum Home-Bildschirm".
   
  Anmeldungen gelten 30 Tage. Nach 5 falschen PIN- bzw. Passwortversuchen je Client-Adresse folgt
  eine 5-minütige Sperre. "Alle Geräte abmelden" am PC widerruft auch Manager-Passwort-Sitzungen.
  Am Handy nicht änderbar: API-Key, Konsole, PIN, Heimnetz-Zugriff, Beenden.
  Neuer Reiter "Start": Überblick, Parzelle nachschlagen (Passwort + QR-Code zum Scannen/Teilen),
  Gast-Voucher mit einem Tipp.

### TARIFE (Reiter "Tarife")
  Ein Tarif = Bandbreite (Download/Upload) + Netzgröße (Netzmaske + Zahl der Endgeräte).
  Voreingestellt: Basic 30/10 Mbit/s, /29, 5 Geräte · Plus 60/20, /28, 10 Geräte · Max 100/40, /24, ganzer Bereich.
  Alle Werte änderbar, weitere Tarife möglich. "Tarife speichern".
  1. "Netze laden & Unterschiede ermitteln" – alle Netze des Gateways (Parzellen, Vorstand, Gäste, eigene).
  2. Je Netz einen Tarif wählen – oder suchen, markieren, "Für markierte Netze … setzen".
     "Ist-Zustand erkennen" schlägt für Parzellen ohne Tarif den Tarif nach der heutigen Netzmaske vor.
  3. "Zuordnung speichern & neu vergleichen".
  4. Unten auswählen > "Vorschau" > "Ausgewählte übertragen". Der Manager liest danach zur Kontrolle nach.
  Bandbreite: QoS-Regel "SparteNet-Tarif-<Name>" (Geschwindigkeit begrenzen), alle Netze des Tarifs darin.
    Alternativ "eine Regel je Netz" (SparteNet-Netz-<Netz>). Andere QoS-Regeln werden nie verändert.
    Einmal prüfen: Geschwindigkeitstest in zwei Parzellen desselben Tarifs gleichzeitig. Teilen sie sich
    die Bandbreite, auf "eine Regel je Netz" umstellen.
  Netzgröße: Subnetz des Netzes (Router-IP bleibt, z. B. 10.1.67.1/29) und DHCP-Bereich
    (/29: .2–.6 = 5 Geräte, /28 mit 10 Geräten: .2–.11, /24: .6–.254 – wie bisher am Gateway).
    Geräte mit IP außerhalb eines verkleinerten Netzes werden vorher angezeigt; sie brauchen eine neue IP (WLAN aus/an).
  Vorher wird gesichert (SparteNet_Sicherung_Tarife_*.json). "Letzte Tarif-Übertragung rückgängig" spielt zurück.

### ANSICHT (FHD bis 8K, normal und curved)
  Oben rechts "Ansicht": Breite des Inhalts (Standard, Breit, 4K, Ultra/Curved, volle Breite oder eigene),
  Größe/Skalierung (automatisch nach Bildschirm oder 80–300 %), Höhe der Tabellen (auch an Fensterhöhe),
  "Karten nebeneinander" für breite Monitore. Breite auch direkt am rechten Rand des Inhalts ziehen
  (Doppelklick = volle Breite). In Kartendesign und Alle Daten lässt sich der Trenner zwischen linker
  und rechter Spalte ziehen. Alles wird gespeichert.

### SICHERHEIT
  Zugangsdaten stehen in SparteNet_Manager.json, Passwörter in PPSK_<Kürzel>.csv – nicht weitergeben.
  Das Kartendesign steht ebenfalls in SparteNet_Manager.json, das Logo in SparteNet_Kartenlogo.<png/jpg/svg>.
  Jeder Zugriff auf die Oberfläche und API erfordert eine Anmeldung mit dem Manager-Passwort; auf
  entfernten Handys kann zusätzlich die eingerichtete PIN verwendet werden. Die Oberfläche lauscht
  standardmäßig nur auf 127.0.0.1. Angemeldete Handy-Geräte stehen (nur als Prüfsumme) in
  SparteNet_Manager.json. Manager-Passwort-Sitzungen werden bis zum Neustart im Speicher gehalten.

### DIAGNOSE-DATEI (Fehlersuche)
  Verbindung > "Diagnose-Datei erstellen": liest alles einmal aus (nur lesend) und speichert
  SparteNet_Diagnose_<Datum>.json – ohne API-Key, Passwörter, Schlüssel und E-Mail-Adressen,
  Clientnamen/MACs wahlweise anonymisiert. Diese Datei zur Fehlersuche weitergeben, nie den API-Key.

### VERBINDUNGSTEST OHNE OBERFLÄCHE
  ./sparteNet_verbindungstest.py
