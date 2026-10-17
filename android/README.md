# SparteNet – Android-App (Handy und Tablet)

Native App (Kotlin, Jetpack Compose, Material 3) für den **SparteNet Manager ab Version 5.0**.
Sie nutzt ausschließlich die App-Schnittstelle des Managers (`/api/v1/app/…` und `/api/…` mit `Authorization: Bearer sna_…`)
und hat genau die Rechte des Benutzerkontos, mit dem sie angemeldet wird.

## Funktionen

| Bereich | Was geht in der App | nötiges Recht im Manager |
|---|---|---|
| Start | offene/neue/eigene/dringende Anfragen, Störungen, gebuchte Parzellen, Mitglieder, offene Rechnungen | angemeldet |
| Anfragen | Liste mit Filtern und Suche, Details mit Verlauf, Status/Priorität/Kategorie/Zuständig ändern, „Mir zuweisen“, interne Notiz oder Antwort per E-Mail, neue Anfrage | Tickets lesen/schreiben |
| Mitglieder | Liste mit Suche, anlegen, ändern, löschen, anrufen, E-Mail schreiben | Mitglieder lesen/schreiben |
| Buchungen | Tarif je Parzelle und Sparte ändern (mit Bestätigung; am Gateway wird nichts direkt geändert) | Buchungen lesen/schreiben |
| Parzelle / WLAN | WLAN-Name, Passwort (verdeckt), QR-Code zum Scannen, kopieren/teilen | Start lesen |
| Gast-Voucher | aus Vorlage erstellen (erst Vorschau, dann Bestätigung), Codes kopieren/teilen, Voucher am Gateway ansehen | Voucher lesen/schreiben |
| Rechnungen | Liste nach Jahr/Status mit Summen, Rechnung als PDF öffnen | Rechnungen lesen |
| Störungen | überwachte Geräte, offline seit, Verlauf; „Jetzt prüfen“ (Administrator) | Auslesen lesen |
| Mein Konto | Ansicht Hell/Dunkel/System, angemeldete Geräte sehen und entfernen, Abmelden | angemeldet |

**Tablet:** ab 600 dp Breite Navigationsleiste an der Seite, ab 1000 dp feste Seitenleiste; Anfragen und Mitglieder als
Liste und Detail nebeneinander. Hoch- und Querformat werden unterstützt.

## Sicherheit

* Das Passwort wird **nicht** gespeichert. Nach der Anmeldung (mit Zwei-Faktor-Code, falls eingeschaltet) erhält die App einen
  eigenen Geräte-Schlüssel. Er liegt AES-GCM-verschlüsselt in den App-Einstellungen; der Schlüssel dazu steckt im
  **Android Keystore** und ist nicht exportierbar. Sicherung/Geräteübertragung ist für die App ausgeschaltet.
* Jedes Gerät erscheint im Manager unter **Mein Konto → Apps und Geräte** und kann dort gesperrt werden.
  „Abmelden“ in der App entfernt das Gerät auch am Manager.
* Die App protokolliert weder Schlüssel noch Passwörter.
* Für den Betrieb über das Internet bitte **https://** verwenden (z. B. hinter einem Reverse-Proxy).
  `http://` ist nur für das eigene Netz gedacht – die App warnt dabei sichtbar. Wer kein http braucht, setzt in
  `app/src/main/res/xml/network_security_config.xml` `cleartextTrafficPermitted="false"`.

## APK bauen

### A) GitHub Actions (ohne eigene Installation)
Der Workflow `.github/workflows/android.yml` baut bei jeder Änderung unter `android/` eine **Debug-APK** und legt sie als
Artefakt „SparteNet-App“ am Workflow-Lauf ab (Actions → Lauf → Artifacts). Die APK auf dem Handy öffnen und
„Installation aus unbekannten Quellen“ für den Browser/Dateimanager erlauben.

Signierte Release-APK (optional): im Repository unter *Settings → Secrets and variables → Actions* anlegen:
`SPARTENET_KEYSTORE_B64` (Keystore als Base64: `base64 -w0 spartenet.jks`), `SPARTENET_KEYSTORE_PASSWORT`,
`SPARTENET_KEY_ALIAS`, `SPARTENET_KEY_PASSWORT`. Den Keystore gut aufbewahren – ohne ihn lassen sich spätere Updates nicht installieren.

### B) Android Studio
Ordner `android/` öffnen (Android Studio Ladybug oder neuer, JDK 17), Gradle-Sync abwarten, dann *Run* oder
*Build → Build App Bundle(s)/APK(s)*. Auf der Kommandozeile: `./gradlew assembleDebug` → `app/build/outputs/apk/debug/`.

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
