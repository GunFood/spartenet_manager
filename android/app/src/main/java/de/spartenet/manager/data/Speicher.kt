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
