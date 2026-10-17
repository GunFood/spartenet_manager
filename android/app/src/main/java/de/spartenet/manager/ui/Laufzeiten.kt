package de.spartenet.manager.ui

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Refresh
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.FilterChip
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import de.spartenet.manager.data.i
import de.spartenet.manager.data.liste
import de.spartenet.manager.data.o
import de.spartenet.manager.data.s
import de.spartenet.manager.data.texte
import org.json.JSONObject

private val LZ_FILTER = listOf("" to "Alle", "aktiv" to "Laufend", "offen" to "Am Gateway offen", "gesperrt" to "Gesperrt")

/** Laufzeiten der Tarife: wann endet der Zugang, verlängern, Zugang am Gateway sperren/freigeben */
@Composable
fun LaufzeitenSeite(s: Sitzung) {
    val l = rememberLaden(s, s) { s.api.get("/api/laufzeiten") }
    var filter by rememberSaveable { mutableStateOf("") }
    var arbeitet by remember { mutableStateOf(false) }
    var verlaengern by remember { mutableStateOf<JSONObject?>(null) }
    // Vorschau einer Gateway-Änderung: (Zeile, Aktion, Vorschautext)
    var zugang by remember { mutableStateOf<Triple<JSONObject, String, String>?>(null) }
    val scope = rememberCoroutineScope()
    val buchen = s.darf("buchungen", "schreiben")
    val gateway = s.darf("wlan_pw", "schreiben")

    fun ziel(z: JSONObject) = JSONObject().put("sparte", z.s("sparte")).put("parzelle", z.i("parzelle"))

    Column(Modifier.fillMaxSize()) {
        Kopf("Laufzeiten", l.daten?.texte("log")?.firstOrNull()) {
            IconButton(onClick = { l.laden() }) { Icon(Icons.Filled.Refresh, "Aktualisieren") }
        }
        Row(Modifier.fillMaxWidth().horizontalScrollRow().padding(horizontal = 12.dp), horizontalArrangement = Arrangement.spacedBy(8.dp)) {
            LZ_FILTER.forEach { (k, t) -> FilterChip(selected = filter == k, onClick = { filter = k }, label = { Text(t) }) }
        }
        Laden(l) { a ->
            val auto = a.o("einstellungen").optBoolean("gateway_auto")
            val zeilen = a.liste("zeilen").filter {
                val z = it.s("zustand")
                filter.isEmpty() || z == filter || (filter == "offen" && z.startsWith("offen"))
            }
            val ohne = a.liste("ohne_laufzeit")
            LazyColumn(Modifier.fillMaxSize()) {
                item {
                    Text(
                        if (auto) "Der Manager sperrt und gibt Zugänge am Gateway automatisch frei."
                        else "Am Gateway wird nur von Hand gesperrt/freigegeben (automatisch: Einstellung im Manager unter Tarife).",
                        Modifier.padding(horizontal = 16.dp, vertical = 6.dp), style = MaterialTheme.typography.bodySmall,
                        color = MaterialTheme.colorScheme.onSurfaceVariant,
                    )
                }
                if (zeilen.isEmpty()) item { Text("Keine Einträge in dieser Ansicht.", Modifier.padding(16.dp)) }
                items(zeilen, key = { "${it.s("sparte")}-${it.i("parzelle")}" }) { z ->
                    val zust = z.s("zustand")
                    Column(Modifier.fillMaxWidth().padding(horizontal = 16.dp, vertical = 10.dp)) {
                        Row(verticalAlignment = Alignment.CenterVertically) {
                            Column(Modifier.weight(1f)) {
                                Text("${z.s("sparte")} · Parzelle ${z.i("parzelle")}", fontWeight = FontWeight.SemiBold)
                                Text(listOf(z.s("tarif"), z.s("ende").let { if (it.isEmpty()) "" else "bis $it" }, z.s("rest")).filter { it.isNotEmpty() }.joinToString(" · "),
                                    style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.onSurfaceVariant)
                            }
                            when {
                                zust.startsWith("offen") -> Marke(z.s("text"), MaterialTheme.colorScheme.tertiaryContainer, MaterialTheme.colorScheme.onTertiaryContainer)
                                zust == "gesperrt" -> Marke("gesperrt", MaterialTheme.colorScheme.errorContainer, MaterialTheme.colorScheme.onErrorContainer)
                                else -> Marke(z.s("text").ifEmpty { zust })
                            }
                        }
                        if (z.s("fehler").isNotEmpty()) Text(z.s("fehler"), style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.error)
                        Row(horizontalArrangement = Arrangement.spacedBy(8.dp), modifier = Modifier.padding(top = 6.dp)) {
                            if (buchen && z.s("tarif").isNotEmpty()) OutlinedButton(onClick = { verlaengern = z }, enabled = !arbeitet) { Text("Verlängern") }
                            if (gateway) {
                                val aktion = if (z.optBoolean("gesperrt")) "freigeben" else "sperren"
                                OutlinedButton(enabled = !arbeitet, onClick = {
                                    s.ausfuehren(scope, { arbeitet = it }) {
                                        val v = s.api.post("/api/zugang", ziel(z).put("aktion", aktion))
                                        zugang = Triple(z, aktion, v.texte("log").firstOrNull() ?: "")
                                    }
                                }) { Text(if (aktion == "sperren") "Sperren" else "Freigeben") }
                            }
                        }
                    }
                    HorizontalDivider()
                }
                if (ohne.isNotEmpty()) item {
                    Column(Modifier.padding(16.dp)) {
                        Text("${ohne.size} gebuchte Parzelle(n) mit Laufzeit-Tarif ohne Startzeit: " +
                            ohne.take(15).joinToString(", ") { "${it.s("sparte")} ${it.i("parzelle")}" } + if (ohne.size > 15) " …" else "",
                            style = MaterialTheme.typography.bodySmall)
                        if (buchen) TextButton(enabled = !arbeitet, onClick = {
                            s.ausfuehren(scope, { arbeitet = it }) {
                                val r = s.api.post("/api/laufzeit-starten", JSONObject())
                                l.daten = r
                                s.meldenLog(r)
                            }
                        }) { Text("Laufzeit für diese Parzellen ab jetzt starten") }
                    }
                }
                item { Spacer(Modifier.height(24.dp)) }
            }
        }
    }

    verlaengern?.let { z ->
        var anzahl by remember(z) { mutableStateOf(1) }
        AlertDialog(
            onDismissRequest = { verlaengern = null },
            title = { Text("Laufzeit verlängern") },
            text = {
                Column {
                    Text("${z.s("sparte")} Parzelle ${z.i("parzelle")} · ${z.s("tarif")}" + (if (z.s("ende").isNotEmpty()) "\nbisher bis ${z.s("ende")}" else ""))
                    Text("Läuft die Zeit noch, wird ab dem bisherigen Ende verlängert, sonst ab jetzt. Ein gesperrter Zugang wird wieder freigegeben.",
                        Modifier.padding(top = 8.dp), style = MaterialTheme.typography.bodySmall)
                    Row(verticalAlignment = Alignment.CenterVertically, modifier = Modifier.padding(top = 12.dp)) {
                        OutlinedButton(onClick = { if (anzahl > 1) anzahl-- }) { Text("−") }
                        Text("$anzahl × Laufzeit", Modifier.padding(horizontal = 16.dp), fontWeight = FontWeight.SemiBold)
                        OutlinedButton(onClick = { if (anzahl < 120) anzahl++ }) { Text("+") }
                    }
                }
            },
            confirmButton = {
                TextButton(onClick = {
                    verlaengern = null
                    s.ausfuehren(scope, { arbeitet = it }) {
                        val r = s.api.post("/api/laufzeit-verlaengern", ziel(z).put("anzahl", anzahl))
                        l.daten = r
                        s.meldenLog(r)
                    }
                }) { Text("Verlängern") }
            },
            dismissButton = { TextButton(onClick = { verlaengern = null }) { Text("Abbrechen") } },
        )
    }

    zugang?.let { (z, aktion, vorschau) ->
        Bestaetigen(
            if (aktion == "sperren") "Zugang sperren?" else "Zugang freigeben?",
            "$vorschau\n\nJetzt am Gateway ausführen?",
            if (aktion == "sperren") "Sperren" else "Freigeben",
            onJa = {
                zugang = null
                s.ausfuehren(scope, { arbeitet = it }) {
                    val r = s.api.post("/api/zugang", ziel(z).put("aktion", aktion).put("ausfuehren", true))
                    l.daten = r
                    s.meldenLog(r)
                }
            },
            onAbbrechen = { zugang = null },
        )
    }
}
