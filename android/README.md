# SparteNet – Android-Apps (Handy und Tablet)

Zwei getrennte Apps in einem Projekt – jede mit eigener Paket-ID, eigenem Symbol und eigener Anmeldung:

| App | Modul | Paket | für wen | Anmeldung |
|---|---|---|---|---|
| **SparteNet Manager** (grün) | `manager/` | `de.spartenet.manager` | Vorstand und Mitarbeiter | Benutzername, Passwort (+ Zwei-Faktor) und eigener App-Zugangstoken |
| **SparteNet Mitglied** (blau) | `mitglied/` | `de.spartenet.mitglied` | Pächter/Mitglieder | E-Mail-Adresse + Code per E-Mail (kein Passwort) |

Die Mitglieder-App hat **keinen** Zugang zum Manager – nur zum Mitgliederbereich der eigenen Parzelle(n).

## SparteNet Mitglied (`mitglied/`)

Nutzt den Mitgliederbereich des Managers (ab 5.6, muss im Manager eingeschaltet sein: Reiter „Tickets“ → „Mitgliederbereich“).

* **Anmelden:** nur E-Mail-Adresse → Einmalcode kommt per E-Mail → Code eingeben. Die Internetadresse des Managers ist fest
  in der App: vor dem Bauen in `android/gradle.properties` `spartenetServer=https://wlan.meine-sparte.de` eintragen (oder
  Umgebungsvariable `SPARTENET_SERVER`; bei GitHub Actions als Repository-Variable unter *Settings → Secrets and variables →
  Actions → Variables* `SPARTENET_SERVER`). Ohne hinterlegte Adresse fragt die App einmal danach. Die App bekommt
  einen eigenen Schlüssel `snm_…` (180 Tage gültig, nur als Prüfsumme gespeichert, verschlüsselt im Android Keystore).
  „Abmelden“ entfernt den Schlüssel auch am Manager; der Administrator kann alle Mitglieder-Apps auf einmal abmelden.
* **Mein Tarif:** Tarif, Laufzeit mit Resttagen, offener Betrag, Sperre; Upgrade jederzeit, kleinerer Tarif als Antrag
  (Freigabe im Ticket), Neu buchen, Verlängern – je nach Einstellung im Manager; mit Bezahldienst öffnet sich die Bezahlseite.
* **Geräte im WLAN:** angemeldete Geräte im Netz der Parzelle (IP 10.<Sparte>.<Parzelle>.<Gerät>), Zugangskarte per E-Mail.
* **Rechnungen** als PDF öffnen, **Anfragen** ansehen und neue stellen.
* **Tablet:** ab 840 dp zwei Spalten. Mehrere Parzellen mit derselben E-Mail-Adresse: Auswahl oben.
* Schnittstelle: `POST /mein/info`, `/mein/code`, `/mein/anmelden` (`"app": true`), danach mit `Authorization: Bearer snm_…`:
  `/mein/daten`, `/mein/geraete`, `/mein/buchen`, `/mein/ticket`, `/mein/zugangskarte`, `/mein/abmelden`, `GET /mein/rechnung?id=`.

## SparteNet Manager (`manager/`)

Native App (Kotlin, Jetpack Compose, Material 3) für den **SparteNet Manager ab Version 5.3** (App-Zugangstoken).
Sie nutzt ausschließlich die App-Schnittstelle des Managers (`/api/v1/app/…` und `/api/…` mit `Authorization: Bearer sna_…`)
und hat genau die Rechte des Benutzerkontos, mit dem sie angemeldet wird.

### Funktionen

| Bereich | Was geht in der App | nötiges Recht im Manager |
|---|---|---|
| Start | offene/neue/eigene/dringende Anfragen, Störungen, gebuchte Parzellen, Mitglieder, offene Rechnungen | angemeldet |
| Anfragen | Liste mit Filtern und Suche, Details mit Verlauf, Status/Priorität/Kategorie/Zuständig ändern, „Mir zuweisen“, interne Notiz oder Antwort per E-Mail, neue Anfrage | Tickets lesen/schreiben |
| Mitglieder | Liste mit Suche, anlegen, ändern, löschen, anrufen, E-Mail schreiben | Mitglieder lesen/schreiben |
| Buchungen | Tarif je Parzelle und Sparte ändern (mit Bestätigung; am Gateway wird nichts direkt geändert) | Buchungen lesen/schreiben |
| Parzelle / WLAN | WLAN-Name, Passwort (verdeckt), QR-Code zum Scannen, kopieren/teilen | Start lesen |
| Gast-Voucher | aus Vorlage erstellen (erst Vorschau, dann Bestätigung), Codes kopieren/teilen, Voucher am Gateway ansehen | Voucher lesen/schreiben |
| Laufzeiten | Tarife mit Laufzeit: Ende je Parzelle, verlängern, Zugang am Gateway sperren/freigeben (mit Vorschau) | Buchungen lesen/schreiben, Gateway: WLAN-Passwörter schreiben |
| Rechnungen | Liste nach Jahr/Status mit Summen, Rechnung als PDF öffnen | Rechnungen lesen |
| Störungen | überwachte Geräte, offline seit, Verlauf; „Jetzt prüfen“ (Administrator) | Auslesen lesen |
| Mein Konto | Ansicht Hell/Dunkel/System, angemeldete Geräte sehen und entfernen, Abmelden | angemeldet |

**Tablet:** ab 600 dp Breite Navigationsleiste an der Seite, ab 1000 dp feste Seitenleiste; Anfragen und Mitglieder als
Liste und Detail nebeneinander. Hoch- und Querformat werden unterstützt.

### Sicherheit

* **App-Zugangstoken:** Beim Einrichten fragt die App nach dem Zugangstoken des eigenen Kontos (Manager → Mein Konto →
  Apps und Geräte → App-Zugangstokens; jeder Benutzer kann beliebig viele anlegen, z. B. einen je Gerät). Er wird
  verschlüsselt gespeichert und bei jeder Anfrage als `X-App-Token` mitgeschickt. Wird der Token entfernt, fragt die App
  beim nächsten Anmelden nach einem neuen.
* Das Passwort wird **nicht** gespeichert. Nach der Anmeldung (mit Zwei-Faktor-Code, falls eingeschaltet) erhält die App einen
  eigenen Geräte-Schlüssel. Er liegt AES-GCM-verschlüsselt in den App-Einstellungen; der Schlüssel dazu steckt im
  **Android Keystore** und ist nicht exportierbar. Sicherung/Geräteübertragung ist für die App ausgeschaltet.
* Jedes Gerät erscheint im Manager unter **Mein Konto → Apps und Geräte** und kann dort gesperrt werden.
  „Abmelden“ in der App entfernt das Gerät auch am Manager.
* Die App protokolliert weder Schlüssel noch Passwörter.
* **Automatisch abmelden:** stellt der Administrator im Manager (Benutzer → Anmeldung und Sicherheit) eine Zeit für die App ein,
  meldet sie sich nach so vielen Minuten ohne Bedienung ab – auch wenn die App zwischendurch geschlossen war.
* **Zwei-Faktor-Code merken:** ist das im Manager eingeschaltet, fragt die App den Code nach richtiger Eingabe für die eingestellte
  Zeit nicht erneut ab (Merk-Schlüssel verschlüsselt im Keystore; nach Zurücksetzen der Zwei-Faktor-Anmeldung ungültig).
* Für den Betrieb über das Internet bitte **https://** verwenden (z. B. hinter einem Reverse-Proxy).
  `http://` ist nur für das eigene Netz gedacht – die App warnt dabei sichtbar. Wer kein http braucht, setzt in
  `app/src/main/res/xml/network_security_config.xml` `cleartextTrafficPermitted="false"`.

## APK bauen

### A) GitHub Actions (ohne eigene Installation)
Der Workflow `.github/workflows/android.yml` baut bei jeder Änderung unter `android/` beide Apps als **Debug-APK** und legt sie als
Artefakte „SparteNet-Manager-App“ und „SparteNet-Mitglieder-App“ am Workflow-Lauf ab (Actions → Lauf → Artifacts). Die APK auf dem Handy öffnen und
„Installation aus unbekannten Quellen“ für den Browser/Dateimanager erlauben.

Signierte Release-APK (optional): im Repository unter *Settings → Secrets and variables → Actions* anlegen:
`SPARTENET_KEYSTORE_B64` (Keystore als Base64: `base64 -w0 spartenet.jks`), `SPARTENET_KEYSTORE_PASSWORT`,
`SPARTENET_KEY_ALIAS`, `SPARTENET_KEY_PASSWORT`. Den Keystore gut aufbewahren – ohne ihn lassen sich spätere Updates nicht installieren.

### B) Android Studio
Ordner `android/` öffnen (Android Studio Ladybug oder neuer, JDK 17), Gradle-Sync abwarten, dann *Run* oder
*Build → Build App Bundle(s)/APK(s)*. Oben die Ausführung „manager“ (Manager-App) oder „mitglied“ (Mitglieder-App) wählen.
Auf der Kommandozeile: `./gradlew :manager:assembleDebug` → `manager/build/outputs/apk/debug/`, `./gradlew :mitglied:assembleDebug` →
`mitglied/build/outputs/apk/debug/`. Beide Apps können mit demselben Keystore signiert werden.

Für eine lokale Release-Signatur `android/keystore.properties` anlegen (liegt nicht im Repo):
```
storeFile=/pfad/zu/spartenet.jks
storePassword=…
keyAlias=spartenet
keyPassword=…
```

## Technik
* minSdk 26 (Android 8.0), targetSdk 35, Kotlin 2.0, Compose BOM 2024.12, Material 3 (dynamische Farben ab Android 12)
* keine Netzwerk-Bibliotheken: `HttpURLConnection` + `org.json`
* Debug-Build hat die Paket-ID `de.spartenet.manager.debug` und kann neben der Release-Version installiert sein
