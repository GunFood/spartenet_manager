package de.spartenet.manager.ui

import androidx.activity.compose.BackHandler
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxHeight
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.imePadding
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material.icons.filled.Add
import androidx.compose.material.icons.filled.Delete
import androidx.compose.material.icons.filled.Email
import androidx.compose.material.icons.filled.Phone
import androidx.compose.material.icons.filled.Refresh
import androidx.compose.material.icons.filled.Search
import androidx.compose.material3.Button
import androidx.compose.material3.ExtendedFloatingActionButton
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.ListItem
import androidx.compose.material3.ListItemDefaults
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Text
import androidx.compose.material3.VerticalDivider
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.unit.dp
import de.spartenet.manager.data.liste
import de.spartenet.manager.data.s
import de.spartenet.manager.data.textMap
import de.spartenet.manager.data.texte
import org.json.JSONObject

private const val NEU = "__neu__"

@Composable
fun MitgliederSeite(s: Sitzung, breit: Boolean, auftrag: String?, auftragErledigt: () -> Unit) {
    var suche by rememberSaveable { mutableStateOf("") }
    var gewaehlt by rememberSaveable { mutableStateOf<String?>(null) }
    val l = rememberLaden(s, s) { s.api.get("/api/mitglieder") }

    LaunchedEffect(auftrag) {
        if (auftrag == "neu") { gewaehlt = NEU; auftragErledigt() }
    }
    BackHandler(enabled = gewaehlt != null) { gewaehlt = null }

    val listenTeil: @Composable (Modifier) -> Unit = { mod ->
        Box(mod) {
            Column(Modifier.fillMaxSize()) {
                Kopf("Mitglieder", l.daten?.texte("log")?.firstOrNull()) {
                    IconButton(onClick = { l.laden() }) { Icon(Icons.Filled.Refresh, "Aktualisieren") }
                }
                OutlinedTextField(
                    value = suche, onValueChange = { suche = it }, singleLine = true,
                    leadingIcon = { Icon(Icons.Filled.Search, null) }, placeholder = { Text("Name, Parzelle, E-Mail, Telefon") },
                    modifier = Modifier.fillMaxWidth().padding(horizontal = 12.dp, vertical = 4.dp),
                )
                Laden(l) { a ->
                    val q = suche.trim().lowercase()
                    val zeilen = a.liste("zeilen").filter { z ->
                        q.isEmpty() || listOf("vorname", "nachname", "email", "telefon", "sparte", "parzelle", "tarif").any { z.s(it).lowercase().contains(q) } ||
                            "${z.s("sparte")} ${z.s("parzelle")}".lowercase().contains(q)
                    }
                    if (zeilen.isEmpty()) Leer(if (q.isEmpty()) "Noch keine Mitglieder." else "Nichts gefunden.")
                    else LazyColumn(Modifier.fillMaxSize()) {
                        items(zeilen, key = { it.s("id") }) { z ->
                            ListItem(
                                modifier = Modifier.clickableZeile { gewaehlt = z.s("id") },
                                colors = if (z.s("id") == gewaehlt) ListItemDefaults.colors(containerColor = MaterialTheme.colorScheme.secondaryContainer) else ListItemDefaults.colors(),
                                headlineContent = { Text("${z.s("nachname")}, ${z.s("vorname")}".trim(',', ' ')) },
                                supportingContent = { Text(listOf(z.s("email"), z.s("telefon")).filter { it.isNotEmpty() }.joinToString(" · ")) },
                                overlineContent = { if (z.s("sparte").isNotEmpty()) Text("${z.s("sparte")} · Parzelle ${z.s("parzelle")}") },
                                trailingContent = { if (z.s("tarif").isNotEmpty()) Marke(z.s("tarif")) },
                            )
                            HorizontalDivider()
                        }
                        item { Spacer(Modifier.height(88.dp)) }
                    }
                }
            }
            if (s.darf("mitglieder", "schreiben")) {
                ExtendedFloatingActionButton(
                    onClick = { gewaehlt = NEU }, icon = { Icon(Icons.Filled.Add, null) }, text = { Text("Neu") },
                    modifier = Modifier.align(Alignment.BottomEnd).padding(16.dp),
                )
            }
        }
    }

    val detailTeil: @Composable (Modifier) -> Unit = { mod ->
        Box(mod) {
            val g = gewaehlt
            val m = l.daten?.liste("zeilen")?.firstOrNull { it.s("id") == g }
            when {
                g == null -> Leer("Mitglied links auswählen.")
                g != NEU && m == null -> Leer("Mitglied nicht gefunden.")
                else -> MitgliedFormular(s, m, l.daten?.textMap("sparten") ?: emptyMap(), zurueck = if (breit) null else ({ gewaehlt = null })) { antwort, neueId ->
                    l.daten = antwort
                    gewaehlt = neueId
                }
            }
        }
    }

    if (breit) {
        Row(Modifier.fillMaxSize()) {
            listenTeil(Modifier.width(380.dp).fillMaxHeight())
            VerticalDivider()
            detailTeil(Modifier.weight(1f).fillMaxHeight())
        }
    } else if (gewaehlt != null) detailTeil(Modifier.fillMaxSize()) else listenTeil(Modifier.fillMaxSize())
}

@Composable
private fun MitgliedFormular(s: Sitzung, m: JSONObject?, sparten: Map<String, String>, zurueck: (() -> Unit)?, gespeichert: (JSONObject, String?) -> Unit) {
    val schluessel = m?.s("id") ?: NEU
    var vorname by rememberSaveable(schluessel) { mutableStateOf(m?.s("vorname") ?: "") }
    var nachname by rememberSaveable(schluessel) { mutableStateOf(m?.s("nachname") ?: "") }
    var email by rememberSaveable(schluessel) { mutableStateOf(m?.s("email") ?: "") }
    var telefon by rememberSaveable(schluessel) { mutableStateOf(m?.s("telefon") ?: "") }
    var sparte by rememberSaveable(schluessel) { mutableStateOf(m?.s("sparte") ?: sparten.keys.firstOrNull() ?: "") }
    var parzelle by rememberSaveable(schluessel) { mutableStateOf(m?.s("parzelle") ?: "") }
    var notiz by rememberSaveable(schluessel) { mutableStateOf(m?.s("notiz") ?: "") }
    var arbeitet by remember { mutableStateOf(false) }
    var loeschenFragen by remember { mutableStateOf(false) }
    val scope = rememberCoroutineScope()
    val ctx = LocalContext.current
    val schreiben = s.darf("mitglieder", "schreiben")

    Column(Modifier.fillMaxSize()) {
        Row(verticalAlignment = Alignment.CenterVertically) {
            if (zurueck != null) IconButton(onClick = zurueck) { Icon(Icons.AutoMirrored.Filled.ArrowBack, "Zurück") }
            Text(if (m == null) "Neues Mitglied" else "${m.s("vorname")} ${m.s("nachname")}".trim(), Modifier.weight(1f)
                .padding(start = if (zurueck == null) 16.dp else 0.dp, top = 12.dp, bottom = 12.dp), style = MaterialTheme.typography.titleLarge)
            if (m != null && telefon.isNotBlank()) IconButton(onClick = { oeffnen(ctx, "tel:" + telefon.filter { it.isDigit() || it == '+' }) }) { Icon(Icons.Filled.Phone, "Anrufen") }
            if (m != null && email.isNotBlank()) IconButton(onClick = { oeffnen(ctx, "mailto:$email") }) { Icon(Icons.Filled.Email, "E-Mail schreiben") }
        }
        Column(Modifier.fillMaxSize().verticalScroll(rememberScrollState()).imePadding().padding(16.dp), verticalArrangement = Arrangement.spacedBy(10.dp)) {
            Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                OutlinedTextField(vorname, { vorname = it }, label = { Text("Vorname") }, singleLine = true, enabled = schreiben, modifier = Modifier.weight(1f))
                OutlinedTextField(nachname, { nachname = it }, label = { Text("Nachname *") }, singleLine = true, enabled = schreiben, modifier = Modifier.weight(1f))
            }
            OutlinedTextField(email, { email = it.trim() }, label = { Text("E-Mail") }, singleLine = true, enabled = schreiben, modifier = Modifier.fillMaxWidth(),
                keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Email))
            OutlinedTextField(telefon, { telefon = it }, label = { Text("Telefon") }, singleLine = true, enabled = schreiben, modifier = Modifier.fillMaxWidth(),
                keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Phone))
            Row(horizontalArrangement = Arrangement.spacedBy(8.dp), verticalAlignment = Alignment.CenterVertically) {
                if (sparten.isNotEmpty()) Auswahl("Sparte", sparte, listOf("") + sparten.keys, { if (it.isEmpty()) "–" else "$it · ${sparten[it] ?: ""}".trimEnd(' ', '·') }, Modifier.weight(1f), schreiben) { sparte = it }
                else OutlinedTextField(sparte, { sparte = it.uppercase() }, label = { Text("Sparte") }, singleLine = true, enabled = schreiben, modifier = Modifier.weight(1f))
                OutlinedTextField(parzelle, { v -> parzelle = v.filter { it.isDigit() }.take(4) }, label = { Text("Parzelle") }, singleLine = true, enabled = schreiben,
                    keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Number), modifier = Modifier.weight(1f))
            }
            OutlinedTextField(notiz, { notiz = it }, label = { Text("Notiz") }, enabled = schreiben, modifier = Modifier.fillMaxWidth().height(110.dp))
            if (m != null) {
                Text(listOf(m.s("tarif").let { if (it.isEmpty()) "kein Tarif gebucht" else "Tarif: $it" }, "angelegt ${m.s("angelegt")}", m.s("quelle"))
                    .filter { it.isNotBlank() }.joinToString(" · "), style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.onSurfaceVariant)
            }
            if (schreiben) {
                Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                    Button(
                        enabled = nachname.isNotBlank() && !arbeitet,
                        onClick = {
                            s.ausfuehren(scope, { arbeitet = it }) {
                                val mj = JSONObject().put("vorname", vorname).put("nachname", nachname).put("email", email).put("telefon", telefon)
                                    .put("sparte", sparte).put("parzelle", parzelle).put("notiz", notiz)
                                if (m != null) mj.put("id", m.s("id"))
                                val a = s.api.post("/api/mitglied-speichern", JSONObject().put("mitglied", mj))
                                s.meldenLog(a)
                                gespeichert(a, a.s("id").ifEmpty { null })
                            }
                        },
                    ) { Text(if (m == null) "Anlegen" else "Speichern") }
                    if (m != null) OutlinedButton(onClick = { loeschenFragen = true }, enabled = !arbeitet) {
                        Icon(Icons.Filled.Delete, null); Text(" Löschen")
                    }
                }
            }
        }
    }
    if (loeschenFragen && m != null) {
        Bestaetigen(
            "Mitglied löschen?",
            "${m.s("vorname")} ${m.s("nachname")} wird aus der Mitgliederliste entfernt. Buchung und WLAN der Parzelle bleiben unverändert. " +
                "Für eine vollständige Löschung nach DSGVO (mit Tickets) bitte die Funktion im Manager verwenden.",
            "Löschen",
            onJa = {
                loeschenFragen = false
                s.ausfuehren(scope, { arbeitet = it }) {
                    val a = s.api.post("/api/mitglied-loeschen", JSONObject().put("id", m.s("id")))
                    s.meldenLog(a)
                    gespeichert(a, null)
                }
            },
            onAbbrechen = { loeschenFragen = false },
        )
    }
}
