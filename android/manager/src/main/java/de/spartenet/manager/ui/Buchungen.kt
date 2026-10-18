package de.spartenet.manager.ui

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Refresh
import androidx.compose.material3.Button
import androidx.compose.material3.FilterChip
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableIntStateOf
import androidx.compose.runtime.mutableStateMapOf
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
import de.spartenet.manager.data.s
import de.spartenet.manager.data.texte
import org.json.JSONObject

private val FILTER_B = listOf("alle" to "Alle", "gebucht" to "Gebucht", "frei" to "Frei")

@Composable
fun BuchungenSeite(s: Sitzung) {
    val sparten = rememberLaden(s, s) { s.api.get("/api/buchungen") }
    var kz by rememberSaveable { mutableStateOf("") }
    var filter by rememberSaveable { mutableStateOf("alle") }
    var stand by remember { mutableIntStateOf(0) }
    val aenderungen = remember(kz, stand) { mutableStateMapOf<String, String>() }
    var fragen by remember { mutableStateOf(false) }
    var arbeitet by remember { mutableStateOf(false) }
    val scope = rememberCoroutineScope()
    val schreiben = s.darf("buchungen", "schreiben")

    Column(Modifier.fillMaxSize()) {
        Kopf("Buchungen", "Tarif je Parzelle") {
            IconButton(onClick = { sparten.laden(); stand++ }) { Icon(Icons.Filled.Refresh, "Aktualisieren") }
        }
        Laden(sparten) { sl ->
            val liste = sl.liste("sparten")
            val aktiv = kz.takeIf { x -> liste.any { it.s("kz") == x } } ?: liste.firstOrNull()?.s("kz") ?: ""
            if (aktiv != kz) LaunchedEffect(aktiv) { kz = aktiv }
            if (liste.isEmpty()) Leer("Noch keine Sparten im Manager eingetragen.")
            else Column(Modifier.fillMaxSize()) {
                Row(Modifier.fillMaxWidth().horizontalScrollRow().padding(horizontal = 12.dp), horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                    liste.forEach { sp ->
                        FilterChip(selected = sp.s("kz") == aktiv, onClick = { kz = sp.s("kz") }, label = { Text("${sp.s("kz")} · ${sp.s("name")}") })
                    }
                }
                val l = rememberLaden(s, aktiv, stand) { s.api.get("/api/buchungen", mapOf("sparte" to aktiv)) }
                Laden(l) { b ->
                    val tarife = listOf("") + b.texte("tarife")
                    val zeilen = b.liste("zeilen")
                    val gebucht = zeilen.count { (aenderungen[it.s("p")] ?: it.s("tarif")).isNotEmpty() }
                    Column(Modifier.fillMaxSize()) {
                        Row(Modifier.fillMaxWidth().padding(horizontal = 12.dp), verticalAlignment = Alignment.CenterVertically) {
                            Text("$gebucht von ${b.i("n")} gebucht", Modifier.weight(1f), style = MaterialTheme.typography.bodyMedium)
                            FILTER_B.forEach { (k, t) ->
                                FilterChip(selected = filter == k, onClick = { filter = k }, label = { Text(t) }, modifier = Modifier.padding(start = 6.dp))
                            }
                        }
                        val sicht = zeilen.filter {
                            val t = aenderungen[it.s("p")] ?: it.s("tarif")
                            filter == "alle" || (filter == "gebucht" && t.isNotEmpty()) || (filter == "frei" && t.isEmpty())
                        }
                        LazyColumn(Modifier.weight(1f)) {
                            items(sicht, key = { it.s("p") }) { z ->
                                val p = z.s("p")
                                val wert = aenderungen[p] ?: z.s("tarif")
                                val geaendert = aenderungen.containsKey(p)
                                Row(
                                    Modifier.fillMaxWidth().padding(horizontal = 16.dp, vertical = 6.dp),
                                    verticalAlignment = Alignment.CenterVertically,
                                ) {
                                    Column(Modifier.width(130.dp)) {
                                        Text("Parzelle $p", fontWeight = if (geaendert) FontWeight.Bold else null,
                                            color = if (geaendert) MaterialTheme.colorScheme.primary else MaterialTheme.colorScheme.onSurface)
                                        if (z.optBoolean("unbekannt")) Text("Tarif unbekannt", style = MaterialTheme.typography.labelSmall, color = MaterialTheme.colorScheme.error)
                                        if (z.optBoolean("gesperrt")) Text("Zugang gesperrt", style = MaterialTheme.typography.labelSmall, color = MaterialTheme.colorScheme.error)
                                        else if (z.s("ende").isNotEmpty()) Text((if (z.s("laufzeit_status") == "aktiv") "bis " else "abgelaufen ") + z.s("ende"),
                                            style = MaterialTheme.typography.labelSmall, color = MaterialTheme.colorScheme.onSurfaceVariant)
                                    }
                                    Auswahl("Tarif", wert, tarife, { it.ifEmpty { "– nicht gebucht –" } }, Modifier.weight(1f), schreiben && !arbeitet) { neu ->
                                        if (neu == z.s("tarif")) aenderungen.remove(p) else aenderungen[p] = neu
                                    }
                                }
                                HorizontalDivider()
                            }
                        }
                        if (aenderungen.isNotEmpty()) {
                            Surface(tonalElevation = 3.dp) {
                                Row(Modifier.fillMaxWidth().padding(12.dp), verticalAlignment = Alignment.CenterVertically) {
                                    Text("${aenderungen.size} Änderung(en)", Modifier.weight(1f))
                                    TextButton(onClick = { aenderungen.clear() }) { Text("Verwerfen") }
                                    Spacer(Modifier.width(8.dp))
                                    Button(onClick = { fragen = true }, enabled = !arbeitet) { Text("Speichern") }
                                }
                            }
                        }
                    }
                }
            }
        }
    }

    if (fragen) {
        val text = aenderungen.entries.sortedBy { it.key.toIntOrNull() ?: 0 }
            .joinToString("\n") { "Parzelle ${it.key}: ${it.value.ifEmpty { "nicht mehr gebucht" }}" }
        Bestaetigen(
            "Buchungen speichern?", "$kz\n$text\n\nAm Gateway ändert sich dadurch noch nichts: neue Parzellen-Netze werden nur vorgemerkt. Angelegt bzw. übertragen wird erst nach Vorschau und Bestätigung im Manager (Netzplanung, Tarife).",
            "Speichern",
            onJa = {
                fragen = false
                s.ausfuehren(scope, { arbeitet = it }) {
                    val ae = JSONObject()
                    aenderungen.forEach { (p, t) -> ae.put(p, t) }
                    val a = s.api.post("/api/buchungen", JSONObject().put("sparte", kz).put("aenderungen", ae))
                    s.meldenLog(a)
                    stand++
                }
            },
            onAbbrechen = { fragen = false },
        )
    }
}
