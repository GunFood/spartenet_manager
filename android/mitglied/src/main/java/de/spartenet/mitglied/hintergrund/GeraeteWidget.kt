package de.spartenet.mitglied.hintergrund

import android.app.PendingIntent
import android.appwidget.AppWidgetManager
import android.appwidget.AppWidgetProvider
import android.content.ComponentName
import android.content.Context
import android.content.Intent
import android.view.View
import android.widget.RemoteViews
import de.spartenet.mitglied.MainActivity
import de.spartenet.mitglied.R
import de.spartenet.mitglied.data.Speicher
import de.spartenet.mitglied.data.i
import de.spartenet.mitglied.data.s
import org.json.JSONObject

/** Widget „Meine Geräte“: Tarif mit Verbrauch (z. B. „Basic: 3 von 5 Geräten“), Balken und die Geräte; Tippen öffnet die App */
class GeraeteWidget : AppWidgetProvider() {
    override fun onUpdate(ctx: Context, manager: AppWidgetManager, ids: IntArray) {
        zeichnen(ctx, manager, ids)
        Hintergrund.planen(ctx)
        Hintergrund.jetzt(ctx)
    }

    override fun onEnabled(ctx: Context) {
        Hintergrund.planen(ctx)
    }

    override fun onDisabled(ctx: Context) {
        Hintergrund.planen(ctx)
    }

    companion object {
        fun hinweis(text: String): JSONObject =
            JSONObject().put("titel", "SparteNet · Meine Geräte").put("verbrauch", text).put("prozent", -1).put("geraete", "").put("stand", "")

        /** alle Widgets mit dem gespeicherten Stand neu zeichnen */
        fun aktualisieren(ctx: Context) {
            val m = AppWidgetManager.getInstance(ctx)
            val ids = m.getAppWidgetIds(ComponentName(ctx, GeraeteWidget::class.java))
            if (ids.isNotEmpty()) zeichnen(ctx, m, ids)
        }

        private fun zeichnen(ctx: Context, m: AppWidgetManager, ids: IntArray) {
            val sp = Speicher(ctx)
            val w = try {
                if (sp.widget.isNotEmpty()) JSONObject(sp.widget) else null
            } catch (_: Exception) {
                null
            } ?: hinweis(if (sp.token == null) "Bitte in der App anmelden." else "Wird geladen …")
            val v = RemoteViews(ctx.packageName, R.layout.widget_geraete)
            v.setTextViewText(R.id.w_titel, w.s("titel"))
            v.setTextViewText(R.id.w_verbrauch, w.s("verbrauch"))
            v.setTextViewText(R.id.w_geraete, w.s("geraete"))
            v.setTextViewText(R.id.w_stand, w.s("stand"))
            val prozent = w.i("prozent", -1)
            v.setViewVisibility(R.id.w_balken, if (prozent >= 0) View.VISIBLE else View.GONE)
            if (prozent >= 0) v.setProgressBar(R.id.w_balken, 100, prozent, false)
            val oeffnen = PendingIntent.getActivity(
                ctx, 0, Intent(ctx, MainActivity::class.java).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TOP),
                PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE,
            )
            v.setOnClickPendingIntent(R.id.w_wurzel, oeffnen)
            m.updateAppWidget(ids, v)
        }
    }
}
