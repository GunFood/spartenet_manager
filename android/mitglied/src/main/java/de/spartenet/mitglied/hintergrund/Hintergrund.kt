package de.spartenet.mitglied.hintergrund

import android.content.ComponentName
import android.content.Context
import android.appwidget.AppWidgetManager
import androidx.work.Constraints
import androidx.work.CoroutineWorker
import androidx.work.ExistingPeriodicWorkPolicy
import androidx.work.ExistingWorkPolicy
import androidx.work.NetworkType
import androidx.work.OneTimeWorkRequestBuilder
import androidx.work.PeriodicWorkRequestBuilder
import androidx.work.WorkManager
import androidx.work.WorkerParameters
import de.spartenet.mitglied.data.Api
import de.spartenet.mitglied.data.ApiFehler
import de.spartenet.mitglied.data.Speicher
import de.spartenet.mitglied.data.b
import de.spartenet.mitglied.data.i
import de.spartenet.mitglied.data.liste
import de.spartenet.mitglied.data.o
import de.spartenet.mitglied.data.s
import kotlinx.coroutines.CancellationException
import org.json.JSONObject
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale
import java.util.concurrent.TimeUnit

/**
 * Hintergrund-Abgleich: alle 15–60 Minuten (Einstellung) fragt die App beim Manager nach – für das Widget „Meine Geräte“
 * und für Benachrichtigungen. Ohne Firebase: die App holt die Daten selbst (mit ihrem Anmelde-Schlüssel), es wird nichts
 * an Dritte geschickt. Läuft nur, wenn man angemeldet ist und Benachrichtigungen oder ein Widget eingeschaltet sind.
 */
object Hintergrund {
    private const val PERIODISCH = "spartenet_abgleich"
    private const val EINMAL = "spartenet_abgleich_jetzt"
    private val netz = Constraints.Builder().setRequiredNetworkType(NetworkType.CONNECTED).build()

    fun widgetsVorhanden(ctx: Context): Boolean =
        AppWidgetManager.getInstance(ctx).getAppWidgetIds(ComponentName(ctx, GeraeteWidget::class.java)).isNotEmpty()

    /** regelmäßigen Abgleich einplanen oder beenden – je nach Anmeldung, Benachrichtigungen und Widget */
    fun planen(ctx: Context) {
        val sp = Speicher(ctx)
        val wm = WorkManager.getInstance(ctx)
        if (sp.token == null || (!sp.meldungenAn && !widgetsVorhanden(ctx))) {
            wm.cancelUniqueWork(PERIODISCH)
            return
        }
        val auftrag = PeriodicWorkRequestBuilder<AbgleichWorker>(sp.intervall.toLong(), TimeUnit.MINUTES).setConstraints(netz).build()
        wm.enqueueUniquePeriodicWork(PERIODISCH, ExistingPeriodicWorkPolicy.UPDATE, auftrag)
    }

    /** sofort einmal abgleichen (z. B. nach dem Anmelden oder wenn das Widget angelegt wird) */
    fun jetzt(ctx: Context) {
        if (Speicher(ctx).token == null) return
        WorkManager.getInstance(ctx).enqueueUniqueWork(EINMAL, ExistingWorkPolicy.REPLACE, OneTimeWorkRequestBuilder<AbgleichWorker>().setConstraints(netz).build())
    }

    /** beim Abmelden: Abgleich beenden, Stand vergessen, Widget zeigt „Bitte anmelden“ */
    fun stoppen(ctx: Context) {
        val sp = Speicher(ctx)
        WorkManager.getInstance(ctx).cancelUniqueWork(PERIODISCH)
        WorkManager.getInstance(ctx).cancelUniqueWork(EINMAL)
        sp.zustand = ""
        sp.widget = GeraeteWidget.hinweis("Bitte in der App anmelden.").toString()
        GeraeteWidget.aktualisieren(ctx)
    }

    /** Inhalt des Widgets aus Tarif und Geräteliste */
    fun widgetDaten(p: JSONObject?, g: JSONObject?, mehrere: Boolean): JSONObject {
        val stand = "aktualisiert " + SimpleDateFormat("HH:mm", Locale.GERMANY).format(Date())
        if (p == null) return GeraeteWidget.hinweis("Keine Parzelle hinterlegt.")
        val titel = "SparteNet · " + (if (mehrere) p.s("sparte_name") + " · " else "") + "Parzelle " + p.s("parzelle")
        if (g == null) return JSONObject().put("titel", titel).put("verbrauch", p.s("tarif").ifEmpty { "kein Tarif" }).put("prozent", -1)
            .put("geraete", "Geräteanzeige ist ausgeschaltet.").put("stand", stand)
        val anzahl = g.i("anzahl")
        val max = g.i("max")
        val tarif = g.s("tarif")
        val verbrauch = (if (tarif.isNotEmpty()) "$tarif: " else "") + if (max > 0) "$anzahl von $max Geräten" else "$anzahl Geräte"
        val liste = g.liste("geraete")
        val zeilen = liste.take(6).joinToString("\n") { "Gerät ${it.i("nr")} · ${it.s("name")}" } +
            (if (liste.size > 6) "\n… und ${liste.size - 6} weitere" else "")
        return JSONObject().put("titel", titel).put("verbrauch", verbrauch)
            .put("prozent", if (max > 0) (anzahl * 100 / max).coerceIn(0, 100) else -1)
            .put("geraete", zeilen.ifEmpty { g.s("fehler").ifEmpty { "Gerade ist kein Gerät angemeldet." } }).put("stand", stand)
    }
}

class AbgleichWorker(ctx: Context, params: WorkerParameters) : CoroutineWorker(ctx, params) {
    override suspend fun doWork(): Result {
        val ctx = applicationContext
        val sp = Speicher(ctx)
        val token = sp.token ?: return Result.success()
        val api = Api(sp.server, token)
        return try {
            val d = api.post("/mein/daten")
            val parzellen = d.liste("parzellen")
            val p = parzellen.firstOrNull { it.s("id") == sp.widgetParzelle } ?: parzellen.firstOrNull()
            val erlaubt = d.o("erlaubt") ?: JSONObject()
            // Geräte für alle Parzellen (Benachrichtigung „alle Plätze belegt“), für das Widget die gewählte
            val geraete = mutableMapOf<String, JSONObject>()
            if (erlaubt.b("geraete")) {
                for (x in parzellen) {
                    try {
                        geraete[x.s("id")] = api.post("/mein/geraete", JSONObject().put("id", x.s("id")))
                    } catch (e: ApiFehler) {
                        if (e.abgemeldet) throw e
                    }
                }
            }
            sp.widget = Hintergrund.widgetDaten(p, p?.let { geraete[it.s("id")] }, parzellen.size > 1).toString()
            GeraeteWidget.aktualisieren(ctx)
            Meldungen.vergleichen(ctx, sp, d, geraete, meldenAn = sp.meldungenAn)
            Result.success()
        } catch (e: CancellationException) {
            throw e
        } catch (e: ApiFehler) {
            if (e.abgemeldet) {
                sp.widget = GeraeteWidget.hinweis("Bitte in der App neu anmelden.").toString()
                GeraeteWidget.aktualisieren(ctx)
                Result.success()
            } else {
                Result.retry()
            }
        } catch (_: Exception) {
            Result.retry()
        }
    }
}
