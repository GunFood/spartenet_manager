SparteNet Manager 5.1 (Cloud)
===============================

Funktioniert komplett über die UniFi-Cloud (api.ui.com). Kein lokaler Zugriff, kein VPN.
Benötigt nur Python 3 – keine Zusatzpakete (nur für MariaDB/MySQL: PyMySQL, im Docker-Image enthalten).

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

### GATEWAY-ZUTEILUNG NACH BUCHUNG (Reiter "Netzplanung") – neu in 4.8
  Eingeschaltet bekommt eine Parzelle ihr VLAN-Netz erst, wenn sie bucht: am ersten Gateway ihres Standorts mit
  freiem Platz (Netzplanung "Parzellen je Gateway", Standard 55). Erst wenn Gateway 1 voll ist, kommt Gateway 2.
  Buchung gelöscht → das Netz kann entfernt werden; danach ist der Platz frei und die nächste Buchung füllt ihn zuerst.
  Die VLAN-ID bleibt fest an der Parzelle (Schema 4.7) – Passwort, Zugangskarte und VLAN ändern sich nie.
  Zugeteilte Parzellen werden nie automatisch umgezogen. Dienstnetze (Vorstand/Gäste/Technik) liegen am Gateway 1.
  Beim Einschalten bleiben vorhandene Buchungen dort, wo sie laut Netzplanung schon liegen.
  Am Gateway: "Als Planung übernehmen" → Konsole wählen → Reiter "Einrichten" → "Netze nach Buchungen":
  Vorschau, Auswahl, Ausführen. Beim Anlegen geht das Passwort der Parzelle gleich ins Pächter-WLAN; beim
  Entfernen werden zuerst die Zugänge im WLAN gelöscht (mit Sicherung), dann das Netz.
  Nur zwischen Gateways desselben Standorts (gleiche Glasfaser).

### AUTOMATIONEN (Reiter "Automationen") – neu in 4.8
  Regel = Wenn (Buchung, Kündigung, Zahlung über die API, eigenes API-Ereignis, Unterlage) + Nur wenn
  (Sparte, Tarif, Mindestbetrag) + Dann (E-Mail, Tarif buchen, Buchung entfernen, Webhook, Protokolleintrag).
  Platzhalter in Betreff/Text: {sparte} {sparte_name} {parzelle} {tarif} {preis} {betrag} {referenz} {email}
  {name} {datum} {wlan} {passwort} {netz} {vlan} {gateway} … (Liste in der Regel-Bearbeitung).
  "Probelauf" zeigt, was passieren würde – sendet und bucht nichts. Verlauf der letzten 300 Aktionen.
  E-Mails und Webhooks laufen im Hintergrund. Am Gateway ändert eine Automation nichts.
  E-Mail-Versand (SMTP) und API-Schlüssel richten nur Administratoren ein; Passwort optional als Docker-Secret
  (SPARTENET_SMTP_PASSWORD_FILE). Recht "Automationen" (kein/lesen/schreiben) in der Benutzerverwaltung.

### API-SCHNITTSTELLE FÜR ANDERE PROGRAMME – neu in 4.8
  Schlüssel unter "Automationen → API-Schnittstelle" anlegen (Rechte ereignis/buchen/lesen, optional nur bestimmte
  Sparten). Er wird nur einmal angezeigt und nur als Prüfsumme gespeichert. Aufruf mit
  "Authorization: Bearer sn_…" oder "X-API-Key: sn_…":
    GET  /api/v1/status · GET /api/v1/tarife · GET /api/v1/buchungen?sparte=BW
    POST /api/v1/ereignis  {"ereignis":"zahlung","sparte":"BW","parzelle":12,"betrag":"120.00","referenz":"RE-1","email":"…"}
    POST /api/v1/buchung   {"sparte":"BW","parzelle":12,"tarif":"Basic"}   ("" = Buchung entfernen)
  Höchstens 120 Anfragen je Minute und Schlüssel (SPARTENET_API_PRO_MINUTE). Zahlungsanbieter über n8n/Zapier/Make
  anbinden. Von außen nur über HTTPS (Reverse-Proxy, dann SPARTENET_PROXY=1).

### TARIFE MIT LAUFZEIT (Reiter "Tarife") – neu in 5.1
  Jeder Tarif kann eine Laufzeit haben (Stunden, Tage, Wochen, Monate; 0 = unbegrenzt), z. B. "Tag" = 1 Tag, "Woche" = 7 Tage.
  Die Laufzeit beginnt mit der Buchung. Karte "Laufzeiten und Zugang": Ende je Parzelle, Verlängern (ab Ende bzw. ab jetzt),
  Zugang von Hand sperren/freigeben (mit Vorschau). Sperren = PPSK-Eintrag der Parzelle aus dem Pächter-WLAN nehmen; Netz, VLAN und
  Passwort bleiben, Freigeben trägt dasselbe Passwort wieder ein. "Übertragen" gibt gesperrte Parzellen nicht versehentlich frei.
  "Am Gateway automatisch sperren und freigeben" (nur Administratoren, ausdrücklich einschalten): der Zeitplan sperrt abgelaufene
  Parzellen innerhalb einer Minute und gibt sie nach Verlängerung bzw. neuer Buchung wieder frei; von Hand gesperrte bleiben gesperrt.
  Neue Auslöser für Automationen: laufzeit_erinnerung (einstellbar, z. B. 1 Tag vorher), laufzeit_ende, laufzeit_verlaengert,
  zugang_gesperrt, zugang_freigegeben; neue Aktion "Laufzeit verlängern" (z. B. nach Zahlungseingang über die API).
  Platzhalter {laufzeit}, {laufzeit_start}, {laufzeit_ende}. API: GET /api/laufzeiten, POST /api/laufzeit-verlaengern
  {"sparte","parzelle","anzahl"}, POST /api/zugang {"sparte","parzelle","aktion":"sperren|freigeben","ausfuehren"}.

### ANMELDUNG – neu in 5.1
  Neue Anmeldeseite (Handy, Tablet, PC; hell/dunkel) mit "Angemeldet bleiben", Passwort anzeigen und Hinweis bei Feststelltaste.
  Benutzer → "Anmeldung und Sicherheit" (Administratoren):
  • Browser automatisch abmelden nach 10 Min. bis 8 Std. ohne Aktivität (Standard 30 Min.; eine Minute vorher ein Hinweis,
    alle offenen Tabs zählen gemeinsam; auch der Server beendet die Sitzung)
  • Android-App automatisch abmelden (Standard aus)
  • Zwei-Faktor-Code merken: 8 Stunden bis 30 Tage – danach fragt der Browser bzw. die App den Code erneut ab. "Mein Konto →
    Gemerkte Geräte vergessen" und Zurücksetzen der Zwei-Faktor-Anmeldung machen gemerkte Geräte sofort ungültig.

### RECHNUNGEN UND ZAHLUNGSABGLEICH (Reiter "Rechnungen") – neu in 5.0
  Rechnungslauf je Jahr: für jede gebuchte Parzelle mit Mitglied eine Rechnung über den Jahrespreis des Tarifs.
  PDF (ohne Zusatzpakete) mit GiroCode zum Scannen in der Banking-App, Versand per E-Mail mit PDF im Anhang.
  Kleinunternehmer (§ 19 UStG) oder mit Umsatzsteuer; Rechnungen werden nie gelöscht, nur storniert.
  Kontoauszug (CSV-Export der Bank) hochladen: Zuordnung über Rechnungsnummer, sonst Betrag + Name bzw. Parzelle;
  prüfen, übernehmen – jede Zahlung löst "Zahlung eingegangen" aus. Schon übernommene Buchungen werden erkannt.
  API: POST /api/v1/ereignis {"ereignis":"zahlung","referenz":"RE-2026-0001","betrag":"180"} bucht die Rechnung.

### VERTRÄGE, RUNDSCHREIBEN, DATENSCHUTZ (Reiter "Mitglieder") – neu in 5.0
  Verträge je Buchung (automatisch bei der Buchung): Beginn, Laufzeit, Verlängerung, Kündigungsfrist, Kündigung.
  Automationen "Kündigungsfrist läuft bald ab", "Vertrag gekündigt", "Vertrag endet"; optional Buchung zum Ende entfernen.
  Rundschreiben: E-Mail mit Layout an Mitglieder nach Sparte/Tarif, Test an sich selbst, Versand im Hintergrund.
  Datenschutz: Auskunft je Mitglied als Datei, Löschung auf Knopfdruck (Tickets anonymisiert, Rechnungen gesperrt
  aufbewahrt). E-Mail-Adressen im Automations-Verlauf nur für Konten mit Recht "Mitglieder".

### PÄCHTER-SEITE, STÖRUNGEN, WOCHENBERICHT – neu in 5.0
  /portal (anfangs aus, einschalten unter "Tickets"): Anfrage stellen, Stand abfragen, Zugangskarte neu anfordern –
  die Karte (PDF mit QR-Code) geht nur an die hinterlegte E-Mail des Mitglieds; Grenzen gegen massenhafte Anfragen.
  Störungsüberwachung ("Systeminfo"): Geräte der Konsole regelmäßig prüfen, bei Ausfall Ticket + Automation "Störung".
  Wochenbericht ("Automationen"): Buchungen, Anfragen, Zahlungen, offene Rechnungen, Störungen, Verträge.
  Zeitplan im Hintergrund jede Minute (SPARTENET_ZEITPLAN=0 schaltet ab), Zeitzone SPARTENET_ZEITZONE (Europe/Berlin).

### E-MAIL: SMTP-LOGIN – neu in 5.0
  "Anmeldung": SMTP-Login (AUTH LOGIN, Standard), AUTH PLAIN, automatisch oder keine. Benutzername leer = Absender.
  Port 587 mit STARTTLS oder 465 mit SSL/TLS. Verständliche Meldungen bei abgelehnter Anmeldung oder falschem Port.

### APP-SCHNITTSTELLE (z. B. eigene Android-App) – neu in 5.0
  POST /api/v1/app/anmelden {"benutzer","passwort","code" (bei 2FA),"geraet"} → {"token": "sna_…"}.
  Danach alle /api/…-Funktionen mit "Authorization: Bearer sna_…" – mit den Rechten des Kontos (kein X-Token nötig).
  GET /api/app-uebersicht (Zahlen für den Startbildschirm), GET /api/v1/app/info, GET /api/v1/app/funktionen
  (alle Funktionen mit nötigem Recht). Geräte unter "Benutzer → Mein Konto" entfernen; gültig 365 Tage (SPARTENET_APP_TAGE).

### ANDROID-APP FÜR HANDY UND TABLET (Ordner android/)
  Native App (Kotlin/Compose): Start-Übersicht, Anfragen bearbeiten und beantworten, Mitglieder, Buchungen, WLAN einer Parzelle
  mit QR-Code, Gast-Voucher, Rechnungen als PDF, Störungen, Geräteverwaltung. Tablet mit Seitenleiste und Liste/Detail.
  APK über GitHub Actions (Workflow "Android-App", Artefakt "SparteNet-App") oder Android Studio – Details in android/README.md.
  GET /api/buchungen ohne "sparte" liefert die Sparten-Liste, /api/parzelle zusätzlich "qr_matrix" (für Apps).

### E-MAIL MIT LAYOUT UND VORLAGEN (Reiter "Automationen") – neu in 4.9
  Layout für alle E-Mails: Kopfzeile mit Logo (aus "Kartendesign"), Farben, Schrift, Breite, Fußzeile (Impressum).
  Vorschau mit Beispieldaten, Test-E-Mail. Vorlagen mit Editor (fett, kursiv, Überschriften, Listen, Link, Platzhalter),
  in Regeln und Ticket-Antworten auswählbar. Versand als HTML mit Text-Alternative; unsichere Inhalte werden entfernt.

### MITGLIEDER (Reiter "Mitglieder") – neu in 4.9
  Vorname, Nachname, E-Mail, Telefon, Sparte, Parzelle, Notiz – mit gebuchtem Tarif der Parzelle. Anlegen von Hand,
  per Excel/CSV (Vorschau, dann Übernehmen; gleiche E-Mail bzw. Parzelle + Nachname wird aktualisiert) oder über die
  API (POST /api/v1/mitglied, GET /api/v1/mitglieder – Recht "mitglieder"). Export als CSV. Hinweis auf gebuchte
  Parzellen ohne Mitglied. In E-Mails: {vorname} {nachname} {telefon}; "an den Kunden" nutzt die E-Mail des Mitglieds.
  Auslöser für Automationen: "Mitglied angelegt". Recht "Mitglieder" (kein/lesen/schreiben).

### ANFRAGEN / TICKETS (Reiter "Tickets") – neu in 4.9
  Tickets mit Nummer (T-0001), Kategorie, Priorität, Status (neu, in Bearbeitung, wartet, erledigt), zuständigem
  Benutzer und Verlauf. Antwort per E-Mail an den Kontakt (mit Layout, optional Vorlage) oder interne Notiz.
  Kontakt wird automatisch dem Mitglied zugeordnet (E-Mail oder Parzelle). Über die API: POST /api/v1/ticket,
  GET /api/v1/ticket?nr= (Recht "tickets"). Automationen: "Neue Anfrage", "Ticket zugewiesen" (z. B. E-Mail an
  {zustaendig_email} – E-Mail je Benutzerkonto unter "Benutzer"), "Ticket erledigt". Recht "Tickets".

### UNTERLAGEN: ORDNER WÄHLEN UND ANLEGEN – neu in 4.8.4
  Beim Hochladen "In Ordner hochladen" als Auswahl (mit Anzahl Dateien); "+ Neuer Ordner …" legt beim Hochladen
  einen neuen an. "Ordner verwalten": Ordner anlegen (auch leer), Ordner anklicken = filtern, leere eigene Ordner
  entfernen. In der Liste lässt sich der Ordner jeder Datei per Auswahl ändern.

### WLAN-NAMEN VOM GATEWAY (Reiter "Einrichten", Schritt 2) – neu in 4.8.3
  Heißen die WLANs am Gateway anders als nach Schema ("SparteNet.de-BW-Pächter" …): "WLANs vom Gateway abrufen",
  je Sparte Pächter- (PPSK), Gäste- und Vorstand-WLAN wählen und speichern. Vorgeschlagen wird das PPSK-WLAN, dessen
  Schlüssel auf Parzellennetze der Sparte zeigen. Danach nutzen Passwörter vom Gateway übernehmen, Übertragen,
  Vergleich, Zugangskarten, Parzelle nachschlagen und der Voucher-Druck diesen Namen; die Passwortliste
  (PPSK_<Kürzel>.csv) wird angepasst. "Namen nach Schema" stellt den Standard wieder her.

### PARZELLEN EINZELN EINEM GATEWAY ZUORDNEN – neu in 4.8.2
  Netzplanung → "Gateway-Zuteilung nach Buchung" → "Parzellen einzeln einem Gateway zuordnen": je Parzelle
  Automatisch oder Gateway 1…n. Gebuchte Parzellen werden verschoben (fest zugeordnet); noch nicht gebuchte bekommen
  eine Vorgabe für die spätere Buchung. "Auf möglichst wenige Gateways verdichten" legt alle nicht fest zugeordneten
  Buchungen ab Gateway 1 zusammen – bei kleiner Buchungsrate reicht so ein Gateway.
  Am Gateway: "Einrichten → Netze nach Buchungen" legt verschobene Netze am neuen Gateway an und bietet das alte Netz
  am bisherigen Gateway zum Entfernen an (vorausgewählt, mit Vorschau).
  Netzplanung → "Gateways bemessen nach": allen Parzellen (Vollausbau), erwarteten Kunden (Buchungsquote) oder
  tatsächlichen Buchungen – Investition und laufende Kosten rechnen dann nur mit den nötigen Gateways.

### GAST-VOUCHER (Reiter "Gast-Voucher") – neu in 4.8.1
  Vorlagen: Gültigkeit, Geräte je Voucher, Datenvolumen, Download/Upload (0 = unbegrenzt) und Text für den Ausdruck.
  "Voucher am Gateway → Auslesen": alle Voucher mit Status (unbenutzt, in Benutzung, voll belegt, abgelaufen) und Vorlage;
  Einstellungen ohne Vorlage werden als Vorschlag angezeigt ("Als Vorlage übernehmen").
  Erstellen nach Vorlage: Vorschau → "Erstellen und übertragen" legt die Voucher am Gateway an.
  Drucken im Kartendesign wie die Zugangskarten: Gast-WLAN der gewählten Sparte mit QR-Code, Voucher-Code, Laufzeit und
  "Gültig bis" (bei schon benutzten Vouchern die Endzeit vom Gateway, sonst "… nach der ersten Anmeldung" oder auf Wunsch
  ab jetzt berechnet). Je Voucher eine Seite; "Kleine Etiketten" für viele auf einem Blatt. Löschen mit Vorschau.
  Zeitzone für den Ausdruck: Europe/Berlin (SPARTENET_ZEITZONE).

### UMZUGSHILFE (Reiter "Abgleich") – neu in 4.8
  Für Gateways mit dem alten Schema (z. B. Buchenweg): erst das Gateway aus der Netzplanung übernehmen und die
  Konsole wählen, dann "Vorschau". Netze mit gleichem Namen bekommen VLAN, Subnetz, Router-IP und DHCP-Bereich
  aus der Planung; Netzmaske (Tarif) und Netz-ID bleiben, Passwörter/Tarife/Port-Profile gelten weiter.
  Reihenfolge automatisch ohne doppelte VLANs/Subnetze; Blockiertes (z. B. VLAN schon von einem fremden Netz belegt)
  wird angezeigt. "Nur das erste umstellen" zum Testen, "Umzug rückgängig" stellt den vorherigen Stand her.
  Geräte in umgestellten Netzen brauchen danach eine neue IP (WLAN aus/an); feste IPs und Firewall-Regeln prüfen.

### TESTS – neu in 4.8
  python -m unittest discover -s tests -t .      (ohne Gateway; startet einen Testserver auf einem freien Port)
  Mit MariaDB: zusätzlich TEST_SPARTENET_DB_HOST/_PORT/_USER/_PASSWORD/_NAME setzen (eigene, leere Testdatenbank!).
  GitHub Actions (.github/workflows/tests.yml): Tests mit Dateispeicher und MariaDB, Docker-Image bauen und starten.

### UNTERLAGEN, DRUCKEN, DATENSICHERUNG, ZWEI-FAKTOR, FARBSCHEMA – neu in 4.8
  Unterlagen: Dateien (PDF, Bilder, Office, CSV, ZIP) allgemein oder je Sparte; keine Webseiten/SVG/Programme.
  Jeder Kasten hat oben links "Drucken / PDF" (im Druckdialog "Als PDF speichern").
  Datensicherung (Systeminfo): eine Datei mit allem, optional AES-256-verschlüsselt; täglich automatisch nach
  datensicherungen/ (SPARTENET_SICHERUNG=0 schaltet ab); Einspielen sichert vorher den jetzigen Stand.
  Zwei-Faktor-Anmeldung (Benutzer → Mein Konto) mit Authenticator-App und 8 Notfall-Codes; optional Pflicht für Admins.
  Rechte je Sparte: Konten können auf bestimmte Sparten beschränkt werden.
  Farbschema: "Ansicht" bzw. Knopf ◐/☀/☾ oben rechts – wie das System, hell oder dunkel (je Browser gespeichert).
  Sicherheit: Größengrenzen, Anmeldesperre je Konto, Schreibsperre, atomares Speichern, CSV-Formelschutz, CSP.
  Docker: HEALTHCHECK über /status.

### VLAN-PLANUNG AUS DER NETZPLANUNG – neu in 4.7
  Die Netzplanung ist die Vorlage: Standort, Gateways (je 55 Parzellen) und Reihenfolge ergeben den VLAN-Plan.
  Schema (eindeutig je Standort, weil alle Gateways eines Standorts an derselben Glasfaser hängen):
    Parzelle     VLAN = 1000 + 200 × (VLAN-Block − 1) + Parzelle  → letzte zwei Ziffern = Parzellennummer
                 Block 1: 1001–1199 · Block 2: 1201–1399 · … · Block 15: 3801–3999 (höchstens 15 Sparten je Standort)
    Vorstand     VLAN 100 + Sparten-ID · Gäste 200 + Sparten-ID · Technik 300 + Sparten-ID (Sparten-ID = Nr. 1–88, überall eindeutig)
    Subnetze     10.<Sparten-ID>.<Parzelle>.0/24 · Vorstand .200 · Gäste .201 · Technik .250 (überall eindeutig)
    VLAN-Block   Reihenfolge der Sparte am Standort (1 = Standort-Sparte), in der Tabelle fest einstellbar (1–15)
  Je Gateway: höchstens 55 Parzellen + Vorstand/Gäste/Technik der Sparten, deren erste Parzellen dort liegen.
  Eine Sparte kann sich über mehrere Gateways erstrecken (z. B. Parzellen 1–55 an GW 1, 56–110 an GW 2).
  Kürzel je Sparte (2–5 Zeichen A–Z/0–9, eindeutig) sind vorbelegt und in der Tabelle änderbar.
  Netzplanung → "VLAN-Plan je Gateway": Standort wählen, je Gateway "In Planung übernehmen" (die bisherige
  Planung wird gesichert) oder "VLAN-Liste als CSV". Danach Konsole des Gateways wählen, Abgleich, Einrichten.
  Passwörter je Parzelle (PPSK_<Kürzel>.csv) behalten die Parzellen der anderen Gateways einer Sparte.
  Achtung bei bestehenden Gateways: Das neue Schema ändert VLANs und Subnetze (Sparten-ID = Nr. aus dem Konzept,
  z. B. Buchenweg 20 statt 1). Der Abgleich zeigt die Unterschiede; Änderungen am Gateway nur mit Vorschau.
  Kleingarten_Gateway_Planung.xlsx: Blatt "Anlagen" mit Kürzel und VLAN-Block, Blatt "Netz" rechts mit dem VLAN-Plan.

### AKTUALISIERUNG (Reiter "Systeminfo" → "Aktualisierung", nur Administratoren) – neu in 4.6
  Wie bei Nextcloud: Der Manager prüft regelmäßig (Standard alle 24 Stunden) auf GitHub, ob es eine neuere
  Version gibt; Administratoren sehen dann oben "⬆ Update x.y". "Jetzt aktualisieren" führt Schritt für Schritt:
    1 neue Version prüfen · 2 Sicherung der Daten (updates/sicherung_vor_<Version>_<Zeit>.json)
    3 herunterladen (genau der geprüfte Commit) · 4 Inhalt prüfen · 5 entpacken nach updates/<Version>-<Commit>/
    6 Selbsttest (neue Version wird in einem eigenen Prozess geladen) · 7 Wartungsmodus · 8 umschalten, Neustart
  Der Neustart passiert im selben Prozess (im Docker-Container ohne Neubau); die Seite lädt danach selbst neu.
  "Vorherige Version" schaltet zurück. Startet eine neue Version nicht, nimmt der Manager automatisch wieder
  die mitgelieferte Version. Wird das Docker-Image mit einer neueren Version gebaut, gilt immer die neuere.
  Quelle (Kanal): main (jeder Stand auf GitHub main), release (nur veröffentlichte Releases) oder ein Zweig.
  Optional "automatisch installieren" (nur nachts 2–5 Uhr). Öffentlicher Status: http://<server>:8765/status
  Umgebungsvariablen: SPARTENET_UPDATE_REPO (Standard GunFood/spartenet_manager), SPARTENET_UPDATE_PRUEFEN=0 (aus),
  SPARTENET_UPDATE_AUS=1 (immer mitgelieferte Version), SPARTENET_UPDATE_TOKEN_FILE (nur bei privatem Repository:
  Docker-Secret mit einem GitHub-Token, das nur lesen darf). Der Server braucht Zugang zu api.github.com.
  Hinweis: Die erste Version mit Update-Funktion (4.6) muss einmal per Docker-Neubau installiert werden.

### BENUTZERKONTEN UND ZUGRIFFSRECHTE JE BEREICH (Reiter "Benutzer") – Konten seit 4.4, Rechte je Bereich neu in 4.5
  Anmeldung mit Benutzername und Passwort. Das Konto "admin" ist fest eingebaut: Benutzername leer lassen
  oder "admin" und das Manager-Passwort (SPARTENET_PASSWORD bzw. Secret spartenet_password).
  Der Administrator legt im Reiter "Benutzer" weitere Konten an. Kontoart:
    Administrator      alles, auch Benutzerkonten
    Gesperrt           keine Anmeldung; offene Sitzungen werden sofort beendet (Bereichsrechte bleiben gespeichert)
    Rechte je Bereich  für jedes Arbeitsblatt bzw. jede Funktion einzeln: kein Zugriff (ausgeblendet),
                       lesen (ansehen, Vorschau) oder lesen und schreiben (ändern, ans Gateway übertragen)
  Bereiche: Start · Auslesen/Abgleich/Systeminfo/Alle Daten · Planung · Netze und WLANs anlegen ·
    WLAN-Passwörter je Parzelle · Tarife festlegen und übertragen · Tarif buchen (Parzelle ↔ Tarif, Buchungen) ·
    Kalkulation · Netzplanung · Zugangskarten/Kartendesign · Gast-Voucher · Verbindung/Protokoll/Diagnose
  Vorlagen zum schnellen Start: Nur lesen · Lesen und schreiben · Vorstand Sparte (lesen + WLAN-Passwörter,
    Tarif buchen, Karten, Voucher) · Kasse (Tarif buchen und Kalkulation, sonst lesen) – danach je Bereich anpassen.
  Beispiel: Vorlage "Nur lesen", dann "WLAN-Passwörter" und "Tarif buchen" auf "lesen und schreiben".
  Der Server prüft jede Anfrage; Reiter ohne Zugriff sind ausgeblendet, Bereiche mit "lesen" zeigen "nur lesen".
  Jeder sieht unter "Mein Konto" seine Rechte und kann sein Passwort ändern. Passwörter mind. 12 Zeichen,
  nur als PBKDF2-Prüfsumme gespeichert; 5 Fehlversuche → 5 Minuten Sperre. Das Änderungsprotokoll nennt,
  wer etwas geändert hat. Die Handy-PIN darf alles außer Verbindungs-Einstellungen und Benutzerverwaltung.

### PROGRAMMAUFBAU – neu in 4.4
  SparteNet_Manager.py startet nur noch; der Code liegt im Ordner spartenet/ – je Aufgabe eine Datei
  (basis, speicher, einstellungen, cloud, plan, qrcode, ppsk, system, karten, tarife, auth, fern, pwa,
  kalkulation, netzplanung_daten, netzplanung, benutzer, update, oberflaeche, webserver). Beim Kopieren oder
  Aktualisieren immer den ganzen Ordner SparteNet_Manager mit dem Unterordner spartenet/ nehmen.

### DATENBANK (MariaDB/MySQL) – neu in 4.3
  Mit SPARTENET_DB_HOST speichert der Manager alles in der Datenbank statt in Dateien: Einstellungen,
  Planung, Buchungen, Netzplanung, Passwörter je Parzelle (PPSK), Sicherungen, Änderungsprotokoll,
  Passwort-Register (nur Prüfsummen) und Kartenlogo. Nur das technische Protokoll bleibt eine Datei.
  Docker Compose:
    1. .env.example nach .env kopieren, SPARTENET_DB_HOST/PORT/NAME/USER eintragen
       (MariaDB-Container im selben Compose-Netz: Dienstname; MariaDB auf dem Docker-Host: host.docker.internal).
    2. Datenbank-Passwort nur in ./secrets/spartenet_db_password.txt (eine Zeile) – nicht in .env, nicht ins Git.
       Die Datei muss für den Container-Benutzer (UID 10001) lesbar sein, wie spartenet_password.txt.
    3. docker compose up -d --build
  Rechte des Datenbank-Benutzers: CREATE, SELECT, INSERT, UPDATE, DELETE auf die Datenbank, z. B.
    GRANT CREATE, SELECT, INSERT, UPDATE, DELETE ON spartenet.* TO 'spartenet'@'%';
  Beim ersten Start legt der Manager die Tabellen an (sn_daten, sn_dateien, sn_journal,
  sn_passwort_register, sn_meta). Ist die Datenbank leer, übernimmt er die bisherigen Dateien aus /data
  und verschiebt sie nach /data/in_Datenbank_uebernommen_<Datum>/ (enthält Passwörter – nach Prüfung löschen).
  Weitere Variablen: SPARTENET_DB_SSL=1 (TLS), SPARTENET_DB_SSL_CA=/pfad/ca.pem.
  Wo gespeichert wird, steht im Reiter „Verbindung“ unter „Datenspeicher“ und beim Start im Container-Log.
  Sicherung: regelmäßig mysqldump der Datenbank (enthält WLAN-Passwörter und den Cloud-Key – sicher aufbewahren).

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
