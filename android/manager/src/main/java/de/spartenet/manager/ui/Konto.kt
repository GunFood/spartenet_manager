package de.spartenet.manager.ui

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.widthIn
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ExitToApp
import androidx.compose.material.icons.filled.Delete
import androidx.compose.material3.Button
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.SegmentedButton
import androidx.compose.material3.SegmentedButtonDefaults
import androidx.compose.material3.SingleChoiceSegmentedButtonRow
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
import de.spartenet.manager.data.Speicher
import de.spartenet.manager.data.liste
import de.spartenet.manager.data.s
import kotlinx.coroutines.CancellationException
import kotlinx.coroutines.launch
import org.json.JSONObject

@Composable
fun KontoSeite(s: Sitzung, speicher: Speicher, ansicht: String, onAnsicht: (String) -> Unit, onAbmelden: () -> Unit) {
    val geraete = rememberLaden(s, s) { s.api.get("/api/app-geraete") }
    val scope = rememberCoroutineScope()
    var abmeldenFragen by remember { mutableStateOf(false) }
    var entfernen by remember { mutableStateOf<JSONObject?>(null) }
    val meineId = Speicher.geraeteId(s.api.token)

    Column(Modifier.fillMaxSize().verticalScroll(rememberScrollState())) {
        Kopf("Mein Konto")
        Column(Modifier.widthIn(max = 640.dp).padding(16.dp), verticalArrangement = Arrangement.spacedBy(12.dp)) {
            Kachel("Angemeldet", Modifier.fillMaxWidth()) {
                Column {
                    Zeile("Benutzer", s.name + if (s.admin) " (Administrator)" else "")
                    if (s.rechtText.isNotEmpty()) Zeile("Rechte", s.rechtText)
                    Zeile("Manager", s.api.basis)
                    Zeile("Version", "Manager ${s.version}")
                    Zeile("Abmelden", if (s.abmeldenMinuten > 0) "automatisch nach ${s.abmeldenMinuten} Min. ohne Bedienung" else "nur von Hand")
                    if (s.api.unverschluesselt) Text("Verbindung über http:// ist unverschlüsselt.", color = MaterialTheme.colorScheme.error,
                        style = MaterialTheme.typography.bodySmall)
                }
            }
            Text("Ansicht", style = MaterialTheme.typography.titleSmall)
            val wahl = listOf("system" to "System", "hell" to "Hell", "dunkel" to "Dunkel")
            SingleChoiceSegmentedButtonRow(Modifier.fillMaxWidth()) {
                wahl.forEachIndexed { i, (k, t) ->
                    SegmentedButton(selected = ansicht == k, onClick = { onAnsicht(k) }, shape = SegmentedButtonDefaults.itemShape(i, wahl.size)) { Text(t) }
                }
            }
            Text("Apps und Geräte", style = MaterialTheme.typography.titleSmall)
            Text("Geräte, die mit Ihrem Konto angemeldet sind. Ein entferntes Gerät muss sich neu anmelden.",
                style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.onSurfaceVariant)
            Laden(geraete, Modifier.fillMaxWidth()) { a ->
                Column {
                    a.liste("geraete").forEach { g ->
                        Row(Modifier.fillMaxWidth().padding(vertical = 6.dp), verticalAlignment = Alignment.CenterVertically) {
                            Column(Modifier.weight(1f)) {
                                Text(g.s("name") + if (g.s("id") == meineId) " – dieses Gerät" else "", fontWeight = FontWeight.SemiBold)
                                Text("angemeldet ${g.s("angelegt")} · zuletzt ${g.s("zuletzt").ifEmpty { "–" }} · gültig bis ${g.s("ablauf")}",
                                    style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.onSurfaceVariant)
                            }
                            if (g.s("id") != meineId) IconButton(onClick = { entfernen = g }) { Icon(Icons.Filled.Delete, "Gerät entfernen") }
                        }
                        HorizontalDivider()
                    }
                }
            }
            Button(onClick = { abmeldenFragen = true }, modifier = Modifier.padding(top = 12.dp)) {
                Icon(Icons.AutoMirrored.Filled.ExitToApp, null)
                Text("  Abmelden")
            }
        }
    }

    entfernen?.let { g ->
        Bestaetigen("Gerät entfernen?", "„${g.s("name")}“ wird abgemeldet und muss sich neu anmelden.", "Entfernen",
            onJa = {
                entfernen = null
                s.ausfuehren(scope) {
                    val r = s.api.post("/api/app-geraet-entfernen", JSONObject().put("id", g.s("id")))
                    geraete.daten = r
                    s.meldenLog(r)
                }
            },
            onAbbrechen = { entfernen = null })
    }
    if (abmeldenFragen) {
        Bestaetigen("Abmelden?", "Der Geräte-Schlüssel wird am Manager entfernt und auf diesem Gerät gelöscht.", "Abmelden",
            onJa = {
                abmeldenFragen = false
                scope.launch {
                    try {
                        if (meineId != null) s.api.post("/api/app-geraet-entfernen", JSONObject().put("id", meineId))
                    } catch (e: CancellationException) {
                        throw e
                    } catch (_: Exception) {
                        // offline: lokal trotzdem abmelden – das Gerät kann im Manager unter „Mein Konto“ entfernt werden
                    }
                    onAbmelden()
                }
            },
            onAbbrechen = { abmeldenFragen = false })
    }
}
