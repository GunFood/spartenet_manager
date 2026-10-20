package de.spartenet.mitglied.data

import android.content.Context
import android.security.keystore.KeyGenParameterSpec
import android.security.keystore.KeyProperties
import android.util.Base64
import java.security.KeyStore
import javax.crypto.Cipher
import javax.crypto.KeyGenerator
import javax.crypto.SecretKey
import javax.crypto.spec.GCMParameterSpec

/**
 * Speichert E-Mail-Adresse und den Anmelde-Schlüssel der Mitglieder-App.
 * Der Schlüssel liegt nur verschlüsselt (AES-GCM, Schlüssel im Android Keystore, nicht exportierbar) auf dem Gerät.
 */
class Speicher(context: Context) {
    private val prefs = context.applicationContext.getSharedPreferences("spartenet_mitglied", Context.MODE_PRIVATE)

    /** Adresse des Managers – fest in der App, Mitglieder geben nur E-Mail-Adresse und Einmalcode ein */
    val server: String get() = SERVER

    /** Ansicht: "system", "hell" oder "dunkel" – wie im Manager */
    var ansicht: String
        get() = prefs.getString("ansicht", "system") ?: "system"
        set(v) = prefs.edit().putString("ansicht", v).apply()

    // ---- Benachrichtigungen und Widget ----
    /** Benachrichtigungen eingeschaltet */
    var meldungenAn: Boolean
        get() = prefs.getBoolean("meldungen_an", false)
        set(v) = prefs.edit().putBoolean("meldungen_an", v).apply()

    /** gewünschte Arten: stoerung, ticket, laufzeit, rechnung, antrag, geraete */
    var meldungArten: Set<String>
        get() = prefs.getStringSet("meldung_arten", null)?.toSet() ?: MELDUNG_ARTEN.map { it.first }.toSet()
        set(v) = prefs.edit().putStringSet("meldung_arten", v).apply()

    /** wie oft im Hintergrund nachgesehen wird (Minuten, mindestens 15 – Vorgabe von Android) */
    var intervall: Int
        get() = prefs.getInt("intervall", 30)
        set(v) = prefs.edit().putInt("intervall", v.coerceIn(15, 240)).apply()

    /** letzter bekannter Stand (zum Vergleichen – nur was für Benachrichtigungen nötig ist) */
    var zustand: String
        get() = prefs.getString("zustand", "") ?: ""
        set(v) = prefs.edit().putString("zustand", v).apply()

    /** zuletzt angezeigter Inhalt des Widgets */
    var widget: String
        get() = prefs.getString("widget", "") ?: ""
        set(v) = prefs.edit().putString("widget", v).apply()

    /** Parzelle, die das Widget zeigt (die zuletzt in der App gewählte) */
    var widgetParzelle: String
        get() = prefs.getString("widget_parzelle", "") ?: ""
        set(v) = prefs.edit().putString("widget_parzelle", v).apply()

    var email: String
        get() = prefs.getString("email", "") ?: ""
        set(v) = prefs.edit().putString("email", v).apply()

    var titel: String
        get() = prefs.getString("titel", "") ?: ""
        set(v) = prefs.edit().putString("titel", v).apply()

    var token: String?
        get() {
            val roh = prefs.getString("token", null) ?: return null
            return try {
                val bytes = Base64.decode(roh, Base64.NO_WRAP)
                val c = Cipher.getInstance(TRANSFORMATION)
                c.init(Cipher.DECRYPT_MODE, schluessel(), GCMParameterSpec(128, bytes, 0, 12))
                String(c.doFinal(bytes, 12, bytes.size - 12), Charsets.UTF_8)
            } catch (e: Exception) {
                prefs.edit().remove("token").apply()   // z. B. nach Wiederherstellung auf anderem Gerät → neu anmelden
                null
            }
        }
        set(v) {
            if (v == null) {
                prefs.edit().remove("token").apply()
                return
            }
            val c = Cipher.getInstance(TRANSFORMATION)
            c.init(Cipher.ENCRYPT_MODE, schluessel())
            prefs.edit().putString("token", Base64.encodeToString(c.iv + c.doFinal(v.toByteArray(Charsets.UTF_8)), Base64.NO_WRAP)).apply()
        }

    private fun schluessel(): SecretKey {
        val ks = KeyStore.getInstance("AndroidKeyStore").apply { load(null) }
        (ks.getEntry(ALIAS, null) as? KeyStore.SecretKeyEntry)?.let { return it.secretKey }
        val gen = KeyGenerator.getInstance(KeyProperties.KEY_ALGORITHM_AES, "AndroidKeyStore")
        gen.init(
            KeyGenParameterSpec.Builder(ALIAS, KeyProperties.PURPOSE_ENCRYPT or KeyProperties.PURPOSE_DECRYPT)
                .setBlockModes(KeyProperties.BLOCK_MODE_GCM)
                .setEncryptionPaddings(KeyProperties.ENCRYPTION_PADDING_NONE)
                .setKeySize(256)
                .build()
        )
        return gen.generateKey()
    }

    companion object {
        /** Arten der Benachrichtigungen (Schlüssel, Text in den Einstellungen) */
        val MELDUNG_ARTEN = listOf(
            "stoerung" to "Störungen im WLAN",
            "ticket" to "Antworten und Status meiner Tickets",
            "laufzeit" to "Laufzeit endet bald",
            "rechnung" to "Neue Rechnungen",
            "antrag" to "Entscheidung über meine Anträge",
            "geraete" to "Alle Geräteplätze belegt",
        )

        /**
         * Adresse des Managers – nicht als lesbarer Text in der APK, sondern verschleiert (XOR) und erst zur Laufzeit
         * zusammengesetzt. Das erschwert nur das einfache Auslesen; geschützt wird die Verbindung durch HTTPS (nur HTTPS erlaubt).
         * Neue Adresse: Bytes mit tools/adresse_verschleiern.py erzeugen.
         */
        private val A = intArrayOf(50, 103, 179, 94, 226, 126, 151, 66, 55, 114, 169, 79, 246, 33, 202, 67, 45, 127, 166, 64, 188, 45, 213, 64, 61, 114, 181, 90, 244, 42, 150, 9, 63)
        private val K = intArrayOf(0x5A, 0x13, 0xC7, 0x2E, 0x91, 0x44, 0xB8, 0x6D)
        val SERVER: String by lazy { String(CharArray(A.size) { (A[it] xor K[it % K.size]).toChar() }) }
        private const val ALIAS = "spartenet_mitglied_schluessel"
        private const val TRANSFORMATION = "AES/GCM/NoPadding"
    }
}
