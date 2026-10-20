package de.spartenet.mitglied.hintergrund

import android.Manifest
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.content.Context
import android.content.Intent
import android.content.pm.PackageManager
import android.os.Build
import androidx.core.app.NotificationCompat
import androidx.core.app.NotificationManagerCompat
import androidx.core.content.ContextCompat
import de.spartenet.mitglied.MainActivity
import de.spartenet.mitglied.R
import de.spartenet.mitglied.data.Speicher
import de.spartenet.mitglied.data.b
import de.spartenet.mitglied.data.d
import de.spartenet.mitglied.data.geld
import de.spartenet.mitglied.data.i
import de.spartenet.mitglied.data.liste
import de.spartenet.mitglied.data.o
import de.spartenet.mitglied.data.s
import org.json.JSONArray
import org.json.JSONObject

/**
 * Benachrichtigungen: vergleicht den neuen Stand mit dem zuletzt gemerkten und meldet nur Neues –
 * Störungen, Ticket-Antworten, Laufzeitende, neue Rechnungen, entschiedene Anträge, volle Geräteplätze.
 * Beim ersten Abgleich wird nur gemerkt (keine Flut alter Meldungen).
 */
object Meldungen {
    private const val KANAL = "meldungen"

    fun kanalAnlegen(ctx: Context) {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            val k = NotificationChannel(KANAL, "Mitgliederbereich", NotificationManager.IMPORTANCE_DEFAULT)
            k.description = "Störungen, Tickets, Laufzeit, Rechnungen und Geräte"
            ctx.getSystemService(NotificationManager::class.java).createNotificationChannel(k)
        }
    }

    fun erlaubt(ctx: Context): Boolean =
        Build.VERSION.SDK_INT < 33 || ContextCompat.checkSelfPermission(ctx, Manifest.permission.POST_NOTIFICATIONS) == PackageManager.PERMISSION_GRANTED

    fun senden(ctx: Context, schluessel: String, titel: String, text: String) {
        if (!erlaubt(ctx)) return
        kanalAnlegen(ctx)
        val oeffnen = PendingIntent.getActivity(
            ctx, schluessel.hashCode(), Intent(ctx, MainActivity::class.java).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TOP),
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE,
        )
        val n = NotificationCompat.Builder(ctx, KANAL)
            .setSmallIcon(R.drawable.ic_launcher_foreground)
            .setContentTitle(titel)
            .setContentText(text)
            .setStyle(NotificationCompat.BigTextStyle().bigText(text))
            .setContentIntent(oeffnen)
            .setAutoCancel(true)
            .build()
        try {
            NotificationManagerCompat.from(ctx).notify(schluessel.hashCode(), n)
        } catch (_: SecurityException) {
        }
    }

    private fun menge(a: JSONArray?): Set<String> = if (a == null) emptySet() else (0 until a.length()).map { a.optString(it) }.toSet()

    fun vergleichen(ctx: Context, sp: Speicher, d: JSONObject, geraete: Map<String, JSONObject>, meldenAn: Boolean) {
        val alt = try {
            if (sp.zustand.isNotEmpty()) JSONObject(sp.zustand) else null
        } catch (_: Exception) {
            null
        }
        val arten = sp.meldungArten
        val neu = JSONObject()
        val parzellen = d.liste("parzellen")
        for (p in parzellen) {
            val id = p.s("id")
            val vorher = alt?.optJSONObject(id)
            val wo = if (parzellen.size > 1) " (${p.s("sparte_name")} · Parzelle ${p.s("parzelle")})" else ""
            val melde = meldenAn && vorher != null
            // Störungen
            val st = p.liste("stoerungen").map { it.s("text") }.toSet()
            if (melde && "stoerung" in arten) (st - menge(vorher!!.optJSONArray("st"))).forEach { senden(ctx, "st$id$it", "Störung im WLAN$wo", it) }
            // Tickets: neuer Status oder Lösung
            val tk = JSONObject()
            p.liste("tickets").forEach { t -> tk.put(t.s("nr"), t.s("status") + "|" + t.s("loesung")) }
            if (melde && "ticket" in arten) {
                val tv = vorher!!.optJSONObject("tk") ?: JSONObject()
                p.liste("tickets").forEach { t ->
                    val vorherT = tv.optString(t.s("nr"), "")
                    if (vorherT.isNotEmpty() && vorherT != t.s("status") + "|" + t.s("loesung")) {
                        val text = "Status: ${t.s("status")}" + (if (t.s("loesung").isNotEmpty()) " – ${t.s("loesung")}" else "")
                        senden(ctx, "tk${t.s("nr")}${t.s("status")}", "Ticket ${t.s("nr")}: ${t.s("betreff")}$wo", text)
                    }
                }
            }
            // neue Rechnungen
            val re = p.liste("rechnungen").map { it.s("id") }.toSet()
            if (melde && "rechnung" in arten) {
                val vorherRe = menge(vorher!!.optJSONArray("re"))
                p.liste("rechnungen").filter { it.s("id") !in vorherRe }.forEach {
                    senden(ctx, "re${it.s("id")}", "Neue Rechnung ${it.s("nr")}$wo", "Betrag ${geld(it.d("brutto"))} – in der App unter „Rechnungen“.")
                }
            }
            // Anträge: verschwundener offener Antrag = entschieden
            val an = p.liste("antraege").map { it.s("nr") }.toSet()
            if (melde && "antrag" in arten) (menge(vorher!!.optJSONArray("an")) - an).forEach {
                senden(ctx, "an$it", "Ihr Antrag $it ist entschieden$wo", "Der Verein hat über Ihren Antrag entschieden – Details per E-Mail und in der App.")
            }
            // Laufzeit endet in höchstens 3 Tagen – je Laufzeitende einmal
            val lz = p.o("laufzeit")
            var lzGemeldet = vorher?.optString("lz", "") ?: ""
            if (lz != null && lz.b("aktiv") && lz.i("rest_tage") <= 3 && lzGemeldet != lz.s("ende")) {
                if (melde && "laufzeit" in arten) senden(ctx, "lz$id${lz.s("ende")}", "Laufzeit endet bald$wo", "Ihr Tarif ${p.s("tarif")} läuft am ${lz.s("ende")} ab – jetzt in der App verlängern.")
                lzGemeldet = lz.s("ende")
            }
            // alle Geräteplätze belegt – einmal, bis wieder Platz ist
            val g = geraete[id]
            val voll = g != null && g.i("max") > 0 && g.i("anzahl") >= g.i("max")
            if (melde && "geraete" in arten && voll && !vorher!!.optBoolean("voll")) {
                senden(ctx, "voll$id", "Alle Geräteplätze belegt$wo", "${g!!.i("anzahl")} von ${g.i("max")} Geräten im WLAN – trennen Sie ein Gerät oder wechseln Sie den Tarif.")
            }
            neu.put(id, JSONObject().put("st", JSONArray(st.toList())).put("tk", tk).put("re", JSONArray(re.toList())).put("an", JSONArray(an.toList()))
                .put("lz", lzGemeldet).put("voll", voll))
        }
        sp.zustand = neu.toString()
    }
}
