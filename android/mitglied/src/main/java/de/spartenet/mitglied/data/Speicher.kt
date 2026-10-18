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
 * Speichert Server-Adresse, E-Mail-Adresse und den Anmelde-Schlüssel der Mitglieder-App.
 * Der Schlüssel liegt nur verschlüsselt (AES-GCM, Schlüssel im Android Keystore, nicht exportierbar) auf dem Gerät.
 */
class Speicher(context: Context) {
    private val prefs = context.applicationContext.getSharedPreferences("spartenet_mitglied", Context.MODE_PRIVATE)

    var server: String
        get() = prefs.getString("server", "") ?: ""
        set(v) = prefs.edit().putString("server", v).apply()

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
        private const val ALIAS = "spartenet_mitglied_schluessel"
        private const val TRANSFORMATION = "AES/GCM/NoPadding"
    }
}
