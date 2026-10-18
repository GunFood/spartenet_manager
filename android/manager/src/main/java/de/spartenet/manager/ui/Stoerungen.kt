package de.spartenet.manager.ui

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Refresh
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import de.spartenet.manager.data.liste
import de.spartenet.manager.data.o
import de.spartenet.manager.data.s
import org.json.JSONObject

@Composable
fun StoerungenSeite(s: Sitzung) {
    val l = rememberLaden(s, s) { s.api.get("/api/ueberwachung") }
    val scope = rememberCoroutineScope()
    var arbeitet by remember { mutableStateOf(false) }
    Column(Modifier.fillMaxSize()) {
        Kopf("Störungen", "Überwachte Gateways und Access Points") {
            IconButton(onClick = { l.laden() }) { Icon(Icons.Filled.Refresh, "Aktualisieren") }
        }
        Laden(l) { a ->
            val e = a.o("einstellungen")
            val geraete = a.liste("geraete")
            val offline = geraete.filter { it.s("offline_seit").isNotEmpty() }
            Column(Modifier.fillMaxSize().verticalScroll(rememberScrollState()).padding(16.dp), verticalArrangement = Arrangement.spacedBy(10.dp)) {
                Text(
                    if (e.optBoolean("aktiv")) "Überwachung eingeschaltet" + (a.s("letzte").let { if (it.isEmpty()) "" else " · letzte Prüfung $it" })
                    else "Überwachung ausgeschaltet (im Manager unter System einschalten)",
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                )
                if (a.s("fehler").isNotEmpty()) Fehlerleiste(a.s("fehler"))
                Kachel("Zustand") {
                    if (geraete.isEmpty()) Text("Noch keine Geräte erfasst.")
                    else if (offline.isEmpty()) Text("✔ Alle ${geraete.size} Geräte erreichbar", color = MaterialTheme.colorScheme.primary, fontWeight = FontWeight.SemiBold)
                    else Text("⚠ ${offline.size} von ${geraete.size} Geräten offline", color = MaterialTheme.colorScheme.error, fontWeight = FontWeight.SemiBold)
                }
                if (s.admin) {
                    OutlinedButton(enabled = !arbeitet, onClick = {
                        s.ausfuehren(scope, { arbeitet = it }) {
                            val r = s.api.post("/api/ueberwachung-speichern", JSONObject().put("jetzt", true))
                            l.daten = r
                            s.meldenLog(r)
                        }
                    }) { Text("Jetzt prüfen") }
                }
                Text("Geräte", style = MaterialTheme.typography.titleSmall)
                geraete.forEach { g ->
                    val off = g.s("offline_seit").isNotEmpty()
                    Row(Modifier.fillMaxWidth().padding(vertical = 4.dp), verticalAlignment = Alignment.CenterVertically) {
                        Column(Modifier.weight(1f)) {
                            Text(g.s("name").ifEmpty { "(ohne Name)" }, fontWeight = FontWeight.SemiBold)
                            Text(listOf(g.s("modell"), g.s("ip")).filter { it.isNotEmpty() }.joinToString(" · "), style = MaterialTheme.typography.bodySmall,
                                color = MaterialTheme.colorScheme.onSurfaceVariant)
                        }
                        if (off) Marke("offline seit ${g.s("offline_seit")}", MaterialTheme.colorScheme.errorContainer, MaterialTheme.colorScheme.onErrorContainer)
                        else Marke(g.s("status").ifEmpty { "online" })
                    }
                    HorizontalDivider()
                }
                val verlauf = a.optJSONArray("verlauf")
                if (verlauf != null && verlauf.length() > 0) {
                    Text("Verlauf", style = MaterialTheme.typography.titleSmall)
                    for (i in 0 until minOf(verlauf.length(), 30)) {
                        val v = verlauf.opt(i)
                        Text(
                            if (v is JSONObject) "${v.s("zeit")} · ${v.s("geraet")} " + (if (v.s("art") == "offline") "offline" else "wieder online" + v.s("dauer").let { if (it.isEmpty()) "" else " (nach $it Min.)" })
                            else v.toString(),
                            style = MaterialTheme.typography.bodySmall,
                        )
                    }
                }
            }
        }
    }
}
