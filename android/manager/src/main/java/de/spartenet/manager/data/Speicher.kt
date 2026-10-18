package de.spartenet.manager.data

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
 * Speichert Server-Adresse, Konto und den Geräte-Schlüssel.
 * Der Schlüssel liegt nur verschlüsselt (AES-GCM, Schlüssel im Android Keystore, nicht exportierbar) in den Einstellungen.
 * Das Passwort wird nie gespeichert.
 */
class Speicher(context: Context) {
    private val prefs = context.applicationContext.getSharedPreferences("spartenet", Context.MODE_PRIVATE)

    var server: String
        get() = prefs.getString("server", "") ?: ""
        set(v) = prefs.edit().putString("server", v).apply()

    var benutzer: String
        get() = prefs.getString("benutzer", "") ?: ""
        set(v) = prefs.edit().putString("benutzer", v).apply()

    /** "system", "hell" oder "dunkel" */
    var ansicht: String
        get() = prefs.getString("ansicht", "system") ?: "system"
        set(v) = prefs.edit().putString("ansicht", v).apply()

    /** Minuten ohne Aktivität bis zum automatischen Abmelden (vom Manager vorgegeben, 0 = nie) */
    var abmeldenMinuten: Int
        get() = prefs.getInt("abmelden_minuten", 0)
        set(v) = prefs.edit().putInt("abmelden_minuten", v).apply()

    /** letzte Bedienung (Uhrzeit in ms) – damit das Abmelden auch nach einem Neustart der App greift */
    var zuletztAktiv: Long
        get() = prefs.getLong("zuletzt_aktiv", 0L)
        set(v) = prefs.edit().putLong("zuletzt_aktiv", v).apply()

    /** „Zwei-Faktor-Code merken“: Merk-Schlüssel je Server und Konto, verschlüsselt wie der Geräte-Schlüssel */
    fun merken(server: String, benutzer: String): String? = entschluesseln("merken_" + schluesselName(server, benutzer))

    fun merkenSetzen(server: String, benutzer: String, wert: String?) {
        val k = "merken_" + schluesselName(server, benutzer)
        if (wert.isNullOrEmpty()) prefs.edit().remove(k).apply() else prefs.edit().putString(k, verschluesseln(wert)).apply()
    }

    /** App-Zugangstoken des eigenen Kontos, verschlüsselt je Server */
    fun zugangstoken(server: String): String? = entschluesseln("zugang_" + schluesselName(server, ""))

    fun zugangstokenSetzen(server: String, wert: String?) {
        val k = "zugang_" + schluesselName(server, "")
        if (wert.isNullOrBlank()) prefs.edit().remove(k).apply() else prefs.edit().putString(k, verschluesseln(wert.trim())).apply()
    }

    private fun schluesselName(server: String, benutzer: String): String =
        java.security.MessageDigest.getInstance("SHA-256").digest("$server|$benutzer".toByteArray()).joinToString("") { "%02x".format(it) }.take(24)

    private fun verschluesseln(v: String): String {
        val c = Cipher.getInstance(TRANSFORMATION)
        c.init(Cipher.ENCRYPT_MODE, schluessel())
        return Base64.encodeToString(c.iv + c.doFinal(v.toByteArray(Charsets.UTF_8)), Base64.NO_WRAP)
    }

    private fun entschluesseln(name: String): String? {
        val roh = prefs.getString(name, null) ?: return null
        return try {
            val bytes = Base64.decode(roh, Base64.NO_WRAP)
            val c = Cipher.getInstance(TRANSFORMATION)
            c.init(Cipher.DECRYPT_MODE, schluessel(), GCMParameterSpec(128, bytes, 0, 12))
            String(c.doFinal(bytes, 12, bytes.size - 12), Charsets.UTF_8)
        } catch (e: Exception) {
            prefs.edit().remove(name).apply()
            null
        }
    }

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
            val iv = c.iv
            val ct = c.doFinal(v.toByteArray(Charsets.UTF_8))
            prefs.edit().putString("token", Base64.encodeToString(iv + ct, Base64.NO_WRAP)).apply()
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
        private const val ALIAS = "spartenet_geraeteschluessel"
        private const val TRANSFORMATION = "AES/GCM/NoPadding"

        /** Geräte-ID aus „sna_<id>_<geheim>“ – zum Abmelden (Gerät am Manager entfernen) */
        fun geraeteId(token: String?): String? =
            token?.let { Regex("^sna_([0-9a-f]{10})_").find(it)?.groupValues?.get(1) }
    }
}
