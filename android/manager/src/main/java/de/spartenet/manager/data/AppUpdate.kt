package de.spartenet.manager.data

import android.content.ActivityNotFoundException
import android.content.Context
import android.content.Intent
import android.net.Uri
import android.provider.Settings
import androidx.core.content.FileProvider
import androidx.core.content.pm.PackageInfoCompat
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import java.io.File
import java.security.MessageDigest

/**
 * Update der App: Der Manager stellt eine neue APK bereit (hochgeladen unter „Mitgliederbereich → App-Updates“).
 * Die App vergleicht die Versionsnummer, lädt die Datei, prüft die SHA-256-Prüfsumme und übergibt sie an den Android-Installer.
 * Android installiert sie nur, wenn sie mit demselben Schlüssel signiert ist wie die installierte App.
 */
object AppUpdate {
    /** versionCode der installierten App */
    fun installiert(ctx: Context): Long =
        PackageInfoCompat.getLongVersionCode(ctx.packageManager.getPackageInfo(ctx.packageName, 0))

    /** true, wenn die angebotene Version neuer ist */
    fun neuer(ctx: Context, versionCode: Long): Boolean = versionCode > 0 && versionCode > installiert(ctx)

    /**
     * prüft die Datei und startet die Installation. Fehlt die Erlaubnis „Unbekannte Apps installieren“, öffnet sich
     * die passende Einstellung – danach erneut auf „Aktualisieren“ tippen.
     */
    suspend fun installieren(ctx: Context, daten: ByteArray, sha256: String) {
        val ist = withContext(Dispatchers.Default) {
            MessageDigest.getInstance("SHA-256").digest(daten).joinToString("") { "%02x".format(it) }
        }
        if (sha256.isEmpty() || !ist.equals(sha256, ignoreCase = true)) {
            throw IllegalStateException("Die heruntergeladene Datei ist beschädigt (Prüfsumme stimmt nicht) – bitte erneut versuchen.")
        }
        if (!ctx.packageManager.canRequestPackageInstalls()) {
            try {
                ctx.startActivity(Intent(Settings.ACTION_MANAGE_UNKNOWN_APP_SOURCES, Uri.parse("package:" + ctx.packageName)).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK))
            } catch (_: ActivityNotFoundException) {
            }
            throw IllegalStateException("Bitte „Apps aus dieser Quelle zulassen“ einschalten und dann erneut auf „Aktualisieren“ tippen.")
        }
        val datei = withContext(Dispatchers.IO) {
            val dir = File(ctx.cacheDir, "update").apply { mkdirs() }
            dir.listFiles()?.forEach { it.delete() }
            File(dir, "update.apk").apply { writeBytes(daten) }
        }
        val uri = FileProvider.getUriForFile(ctx, ctx.packageName + ".dateien", datei)
        ctx.startActivity(
            Intent(Intent.ACTION_VIEW).setDataAndType(uri, "application/vnd.android.package-archive")
                .addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION or Intent.FLAG_ACTIVITY_NEW_TASK)
        )
    }
}
