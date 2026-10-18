package de.spartenet.manager.ui

import androidx.activity.compose.BackHandler
import androidx.compose.foundation.horizontalScroll
import androidx.compose.foundation.layout.Arrangement
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
import androidx.compose.material.icons.automirrored.filled.Send
import androidx.compose.material.icons.filled.Add
import androidx.compose.material.icons.filled.Email
import androidx.compose.material.icons.filled.Phone
import androidx.compose.material.icons.filled.Refresh
import androidx.compose.material.icons.filled.Search
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.Checkbox
import androidx.compose.material3.ExtendedFloatingActionButton
import androidx.compose.material3.FilterChip
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.ListItem
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.material3.VerticalDivider
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableIntStateOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.compose.foundation.layout.Box
import de.spartenet.manager.data.i
import de.spartenet.manager.data.liste
import de.spartenet.manager.data.o
import de.spartenet.manager.data.s
import de.spartenet.manager.data.textMap
import de.spartenet.manager.data.texte
import org.json.JSONObject

private val FILTER = listOf("offen" to "Offen", "meine" to "Für mich", "neu" to "Neu", "niemand" to "Nicht zugewiesen", "alle" to "Alle")

@Composable
fun TicketSeite(s: Sitzung, breit: Boolean, auftrag: String?, auftragErledigt: () -> Unit) {
    var filter by rememberSaveable { mutableStateOf("offen") }
    var suche by rememberSaveable { mutableStateOf("") }
    var gewaehlt by rememberSaveable { mutableStateOf<String?>(null) }
    var neu by rememberSaveable { mutableStateOf(false) }
    var stand by remember { mutableIntStateOf(0) }

    LaunchedEffect(auftrag) {
        if (auftrag == "neu") { neu = true; gewaehlt = null; auftragErledigt() }
    }

    val liste = rememberLaden(s, filter, stand) {
        val p = mutableMapOf<String, String>()
        when (filter) {
            "meine" -> { p["status"] = "offen"; p["zustaendig"] = "ich" }
            "niemand" -> { p["status"] = "offen"; p["zustaendig"] = "niemand" }
            else -> p["status"] = filter
        }
        s.api.get("/api/tickets", p)
    }

    BackHandler(enabled = gewaehlt != null || neu) { gewaehlt = null; neu = false }

    val listenTeil: @Composable (Modifier) -> Unit = { mod ->
        Box(mod) {
            Column(Modifier.fillMaxSize()) {
                Kopf("Anfragen", liste.daten?.texte("log")?.firstOrNull()) {
                    IconButton(onClick = { liste.laden() }) { Icon(Icons.Filled.Refresh, "Aktualisieren") }
                }
                Row(Modifier.fillMaxWidth().horizontalScrollRow().padding(horizontal = 12.dp), horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                    FILTER.forEach { (k, t) -> FilterChip(selected = filter == k, onClick = { filter = k }, label = { Text(t) }) }
                }
                OutlinedTextField(
                    value = suche, onValueChange = { suche = it }, singleLine = true,
                    leadingIcon = { Icon(Icons.Filled.Search, null) }, placeholder = { Text("Suchen (Nr., Betreff, Name, Parzelle)") },
                    modifier = Modifier.fillMaxWidth().padding(horizontal = 12.dp, vertical = 4.dp),
                )
                Laden(liste) { a ->
                    val q = suche.trim().lowercase()
                    val zeilen = a.liste("zeilen").filter { z ->
                        q.isEmpty() || listOf(z.s("nr"), z.s("betreff"), z.o("kontakt").s("name"), z.o("kontakt").s("email"), z.s("sparte"), z.s("parzelle"))
                            .any { it.lowercase().contains(q) }
                    }
                    if (zeilen.isEmpty()) Leer("Keine Anfragen in dieser Ansicht.")
                    else LazyColumn(Modifier.fillMaxSize()) {
                        items(zeilen, key = { it.s("id") }) { z ->
                            TicketZeile(z, z.s("id") == gewaehlt) { gewaehlt = z.s("id"); neu = false }
                            HorizontalDivider()
                        }
                        item { Spacer(Modifier.height(88.dp)) }
                    }
                }
            }
            if (s.darf("tickets", "schreiben")) {
                ExtendedFloatingActionButton(
                    onClick = { neu = true; gewaehlt = null },
                    icon = { Icon(Icons.Filled.Add, null) }, text = { Text("Neu") },
                    modifier = Modifier.align(Alignment.BottomEnd).padding(16.dp),
                )
            }
        }
    }

    val detailTeil: @Composable (Modifier) -> Unit = { mod ->
        Box(mod) {
            val meta = liste.daten
            when {
                neu -> TicketNeu(s, meta, zurueck = if (breit) null else ({ neu = false })) { id -> neu = false; gewaehlt = id; stand++ }
                gewaehlt != null -> TicketDetail(s, gewaehlt!!, meta, zurueck = if (breit) null else ({ gewaehlt = null }), oeffnen = { gewaehlt = it }) { stand++ }
                else -> Leer("Anfrage links auswählen.")
            }
        }
    }

    if (breit) {
        Row(Modifier.fillMaxSize()) {
            listenTeil(Modifier.width(380.dp).fillMaxHeight())
            VerticalDivider()
            detailTeil(Modifier.weight(1f).fillMaxHeight())
        }
    } else if (gewaehlt != null || neu) {
        detailTeil(Modifier.fillMaxSize())
    } else {
        listenTeil(Modifier.fillMaxSize())
    }
}

@Composable
private fun TicketZeile(z: JSONObject, aktiv: Boolean, onClick: () -> Unit) {
    val st = z.s("status")
    ListItem(
        modifier = Modifier.clickableZeile(onClick),
        colors = if (aktiv) androidx.compose.material3.ListItemDefaults.colors(containerColor = MaterialTheme.colorScheme.secondaryContainer)
        else androidx.compose.material3.ListItemDefaults.colors(),
        overlineContent = {
            Text(listOf(z.s("nr"), z.s("kategorie"), ort(z)).filter { it.isNotEmpty() }.joinToString(" · "))
        },
        headlineContent = { Text(z.s("betreff"), maxLines = 2, overflow = TextOverflow.Ellipsis, fontWeight = if (st == "neu") FontWeight.Bold else null) },
        supportingContent = {
            Text(listOf(z.o("kontakt").s("name"), z.s("zustaendig").let { if (it.isEmpty()) "nicht zugewiesen" else "→ $it" }, z.s("geaendert").ifEmpty { z.s("erstellt") })
                .filter { it.isNotEmpty() }.joinToString(" · "), maxLines = 1, overflow = TextOverflow.Ellipsis)
        },
        trailingContent = {
            Column(horizontalAlignment = Alignment.End) {
                Marke(statusText(st))
                if (z.s("prioritaet") in listOf("hoch", "dringend")) {
                    Spacer(Modifier.height(4.dp))
                    Marke(z.s("prioritaet"), prioFarbe(z.s("prioritaet")), MaterialTheme.colorScheme.surface)
                }
            }
        },
    )
}

private fun ort(z: JSONObject): String = if (z.s("sparte").isNotEmpty() || z.s("parzelle").isNotEmpty())
    "${z.s("sparte")} ${z.s("parzelle")}".trim() else ""

fun statusText(st: String) = when (st) {
    "neu" -> "neu"; "bearbeitung" -> "in Bearbeitung"; "wartet" -> "wartet"; "erledigt" -> "erledigt"; else -> st
}

@Composable
private fun TicketDetail(s: Sitzung, id: String, meta: JSONObject?, zurueck: (() -> Unit)?, oeffnen: (String) -> Unit, geaendert: () -> Unit) {
    val l = rememberLaden(s, id) { s.api.get("/api/ticket", mapOf("id" to id)) }
    val scope = rememberCoroutineScope()
    val ctx = LocalContext.current
    var arbeitet by remember { mutableStateOf(false) }
    var text by rememberSaveable(id) { mutableStateOf("") }
    var anKontakt by rememberSaveable(id) { mutableStateOf(false) }
    var abschluss by remember(id) { mutableStateOf(false) }
    var loesung by rememberSaveable(id) { mutableStateOf("") }
    var abMail by rememberSaveable(id) { mutableStateOf(true) }
    val schreiben = s.darf("tickets", "schreiben")

    val status = meta?.textMap("status")?.takeIf { it.isNotEmpty() } ?: linkedMapOf("neu" to "neu", "bearbeitung" to "in Bearbeitung", "wartet" to "wartet auf Rückmeldung", "erledigt" to "erledigt")
    val prios = meta?.textMap("prioritaeten")?.takeIf { it.isNotEmpty() } ?: linkedMapOf("niedrig" to "niedrig", "normal" to "normal", "hoch" to "hoch", "dringend" to "dringend")
    val konten = listOf("") + (meta?.texte("konten") ?: emptyList())
    val kategorien = meta?.texte("kategorien") ?: emptyList()

    fun speichern(feld: String, wert: String) {
        s.ausfuehren(scope, { arbeitet = it }) {
            val a = s.api.post("/api/ticket-speichern", JSONObject().put("ticket", JSONObject().put("id", id).put(feld, wert)))
            l.daten = a
            s.meldenLog(a)
            geaendert()
        }
    }

    Column(Modifier.fillMaxSize()) {
        Row(verticalAlignment = Alignment.CenterVertically) {
            if (zurueck != null) IconButton(onClick = zurueck) { Icon(Icons.AutoMirrored.Filled.ArrowBack, "Zurück") }
            Text(l.daten?.o("ticket")?.s("nr") ?: "Anfrage", Modifier.weight(1f).padding(start = if (zurueck == null) 16.dp else 0.dp, top = 12.dp, bottom = 12.dp),
                style = MaterialTheme.typography.titleLarge)
            IconButton(onClick = { l.laden() }) { Icon(Icons.Filled.Refresh, "Aktualisieren") }
        }
        Laden(l) { a ->
            val t = a.o("ticket")
            val k = t.o("kontakt")
            val zu = t.s("status") == "geschlossen"
            val darf = schreiben && !zu
            Column(Modifier.fillMaxSize().verticalScroll(rememberScrollState()).imePadding().padding(16.dp), verticalArrangement = Arrangement.spacedBy(12.dp)) {
                Text(t.s("betreff"), style = MaterialTheme.typography.titleMedium, fontWeight = FontWeight.SemiBold)
                Text(listOf(t.s("kategorie"), ort(t), "angelegt ${t.s("erstellt")}", t.s("quelle")).filter { it.isNotBlank() }.joinToString(" · "),
                    style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.onSurfaceVariant)
                if (k.length() > 0) {
                    Card(colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surfaceContainerLow)) {
                        Row(Modifier.fillMaxWidth().padding(12.dp), verticalAlignment = Alignment.CenterVertically) {
                            Column(Modifier.weight(1f)) {
                                Text(k.s("name").ifEmpty { "Kontakt" }, fontWeight = FontWeight.SemiBold)
                                if (k.s("email").isNotEmpty()) Text(k.s("email"), style = MaterialTheme.typography.bodySmall)
                                if (k.s("telefon").isNotEmpty()) Text(k.s("telefon"), style = MaterialTheme.typography.bodySmall)
                            }
                            if (k.s("telefon").isNotEmpty()) IconButton(onClick = { oeffnen(ctx, "tel:" + k.s("telefon").filter { it.isDigit() || it == '+' }) }) {
                                Icon(Icons.Filled.Phone, "Anrufen")
                            }
                            if (k.s("email").isNotEmpty()) IconButton(onClick = { oeffnen(ctx, "mailto:" + k.s("email")) }) { Icon(Icons.Filled.Email, "E-Mail") }
                        }
                    }
                }
                Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                    Auswahl("Status", t.s("status"), status.keys.filter { it != "geschlossen" || zu }, { status[it] ?: it }, Modifier.weight(1f), darf && !arbeitet) { speichern("status", it) }
                    Auswahl("Priorität", t.s("prioritaet"), prios.keys.toList(), { prios[it] ?: it }, Modifier.weight(1f), darf && !arbeitet) { speichern("prioritaet", it) }
                }
                Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                    Auswahl("Zuständig", t.s("zustaendig"), konten, { if (it.isEmpty()) "niemand" else if (it == s.name) "$it (ich)" else it },
                        Modifier.weight(1f), darf && !arbeitet) { speichern("zustaendig", it) }
                    if (kategorien.isNotEmpty())
                        Auswahl("Kategorie", t.s("kategorie"), kategorien, { it }, Modifier.weight(1f), darf && !arbeitet) { speichern("kategorie", it) }
                }
                if (zu) {
                    Card(colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.secondaryContainer)) {
                        Column(Modifier.fillMaxWidth().padding(12.dp)) {
                            Text("✔ Geschlossen am ${t.s("geschlossen")}", fontWeight = FontWeight.SemiBold)
                            if (t.s("loesung").isNotEmpty()) Text("Lösung: ${t.s("loesung")}")
                            if (schreiben) TextButton(enabled = !arbeitet, onClick = {
                                s.ausfuehren(scope, { arbeitet = it }) {
                                    val r = s.api.post("/api/ticket-schliessen", JSONObject().put("id", id).put("wieder_oeffnen", true))
                                    l.daten = r; s.meldenLog(r); geaendert()
                                }
                            }) { Text("Wieder öffnen") }
                        }
                    }
                } else if (schreiben) {
                    OutlinedButton(onClick = { abschluss = true }, enabled = !arbeitet) { Text("Abschließen …") }
                }
                a.optJSONObject("mitglied")?.let { m ->
                    Text("Mitglied: ${m.s("name")} · ${m.s("sparte")} Parzelle ${m.s("parzelle")}" + (if (m.s("tarif").isNotEmpty()) " · ${m.s("tarif")}" else ""),
                        style = MaterialTheme.typography.bodyMedium, color = MaterialTheme.colorScheme.primary)
                }
                val frueher = a.liste("frueher")
                if (frueher.isNotEmpty()) {
                    Text("Frühere Anfragen (${frueher.size})", style = MaterialTheme.typography.titleSmall)
                    frueher.take(10).forEach { f ->
                        Card(onClick = { oeffnen(f.s("id")) }, colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surfaceContainerLow)) {
                            Column(Modifier.fillMaxWidth().padding(10.dp)) {
                                Text("${f.s("nr")} · ${f.s("erstellt").take(10)} · ${statusText(f.s("status"))}", style = MaterialTheme.typography.labelMedium)
                                Text(f.s("betreff"), maxLines = 2, overflow = TextOverflow.Ellipsis)
                                if (f.s("loesung").isNotEmpty()) Text("Lösung: ${f.s("loesung")}", style = MaterialTheme.typography.bodySmall, maxLines = 2, overflow = TextOverflow.Ellipsis)
                            }
                        }
                    }
                }
                if (darf && t.s("zustaendig") != s.name) {
                    TextButton(onClick = { speichern("zustaendig", s.name) }, enabled = !arbeitet) { Text("Mir zuweisen") }
                }
                if (t.s("text").isNotBlank()) {
                    Card(colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surfaceContainer)) {
                        Text(t.s("text"), Modifier.padding(12.dp))
                    }
                }
                Text("Verlauf", style = MaterialTheme.typography.titleSmall)
                t.liste("verlauf").reversed().forEach { v ->
                    val art = v.s("art")
                    Column(Modifier.fillMaxWidth().padding(vertical = 4.dp)) {
                        Text("${v.s("zeit")} · ${v.s("wer")} · ${when (art) { "antwort" -> "Antwort"; "kommentar" -> "Notiz"; "aenderung" -> "Änderung"; "angelegt" -> "angelegt"; else -> art }}",
                            style = MaterialTheme.typography.labelSmall, color = MaterialTheme.colorScheme.onSurfaceVariant)
                        Text(v.s("text"), style = if (art == "aenderung" || art == "angelegt") MaterialTheme.typography.bodySmall else MaterialTheme.typography.bodyMedium)
                    }
                    HorizontalDivider()
                }
                if (darf) {
                    Text(if (anKontakt) "Antwort per E-Mail an den Kontakt" else "Interne Notiz", style = MaterialTheme.typography.titleSmall)
                    OutlinedTextField(value = text, onValueChange = { text = it }, modifier = Modifier.fillMaxWidth().height(140.dp),
                        placeholder = { Text(if (anKontakt) "Text der E-Mail (Platzhalter wie {name} sind möglich)" else "Notiz – nur intern sichtbar") })
                    if (k.s("email").isNotEmpty()) {
                        Row(verticalAlignment = Alignment.CenterVertically) {
                            Checkbox(checked = anKontakt, onCheckedChange = { anKontakt = it })
                            Text("als E-Mail an ${k.s("email")} senden")
                        }
                    }
                    Button(
                        onClick = {
                            s.ausfuehren(scope, { arbeitet = it }) {
                                val r = s.api.post("/api/ticket-kommentar", JSONObject().put("id", id).put("text", text).put("an_kontakt", anKontakt))
                                l.daten = r
                                text = ""
                                s.meldenLog(r)
                                geaendert()
                            }
                        },
                        enabled = text.isNotBlank() && !arbeitet,
                    ) {
                        Icon(Icons.AutoMirrored.Filled.Send, null)
                        Text(if (anKontakt) "  E-Mail senden" else "  Notiz speichern")
                    }
                }
                Spacer(Modifier.height(24.dp))
            }
        }
    }
    if (abschluss) {
        val kontaktMail = l.daten?.o("ticket")?.o("kontakt")?.s("email")?.isNotEmpty() == true
        AbschlussDialog(loesung, { loesung = it }, abMail && kontaktMail, { abMail = it }, kontaktMail, onJa = {
            abschluss = false
            s.ausfuehren(scope, { arbeitet = it }) {
                val r = s.api.post("/api/ticket-schliessen", JSONObject().put("id", id).put("loesung", loesung).put("an_kontakt", abMail && kontaktMail))
                l.daten = r; loesung = ""; s.meldenLog(r); geaendert()
            }
        }, onNein = { abschluss = false })
    }
}

@Composable
private fun AbschlussDialog(loesung: String, onLoesung: (String) -> Unit, abMail: Boolean, onMail: (Boolean) -> Unit, mailMoeglich: Boolean, onJa: () -> Unit, onNein: () -> Unit) {
    androidx.compose.material3.AlertDialog(
        onDismissRequest = onNein,
        title = { Text("Ticket abschließen") },
        text = {
            Column {
                Text("Was wurde getan? Die Lösung sieht der Pächter auch auf der Pächter-Seite.", style = MaterialTheme.typography.bodySmall)
                OutlinedTextField(loesung, onLoesung, modifier = Modifier.fillMaxWidth().height(130.dp).padding(top = 8.dp), placeholder = { Text("Lösung") })
                if (mailMoeglich) Row(verticalAlignment = Alignment.CenterVertically) {
                    Checkbox(checked = abMail, onCheckedChange = onMail); Text("Kontakt per E-Mail informieren")
                }
            }
        },
        confirmButton = { TextButton(onClick = onJa, enabled = loesung.isNotBlank()) { Text("Abschließen") } },
        dismissButton = { TextButton(onClick = onNein) { Text("Abbrechen") } },
    )
}

@Composable
private fun TicketNeu(s: Sitzung, meta: JSONObject?, zurueck: (() -> Unit)?, angelegt: (String) -> Unit) {
    val scope = rememberCoroutineScope()
    var betreff by rememberSaveable { mutableStateOf("") }
    var text by rememberSaveable { mutableStateOf("") }
    var sparte by rememberSaveable { mutableStateOf("") }
    var parzelle by rememberSaveable { mutableStateOf("") }
    var name by rememberSaveable { mutableStateOf("") }
    var email by rememberSaveable { mutableStateOf("") }
    var telefon by rememberSaveable { mutableStateOf("") }
    var prio by rememberSaveable { mutableStateOf("normal") }
    var kategorie by rememberSaveable { mutableStateOf("") }
    var zustaendig by rememberSaveable { mutableStateOf("") }
    var arbeitet by remember { mutableStateOf(false) }
    val kategorien = meta?.texte("kategorien") ?: emptyList()
    val konten = listOf("") + (meta?.texte("konten") ?: emptyList())

    Column(Modifier.fillMaxSize()) {
        Row(verticalAlignment = Alignment.CenterVertically) {
            if (zurueck != null) IconButton(onClick = zurueck) { Icon(Icons.AutoMirrored.Filled.ArrowBack, "Zurück") }
            Text("Neue Anfrage", Modifier.padding(start = if (zurueck == null) 16.dp else 0.dp, top = 12.dp, bottom = 12.dp), style = MaterialTheme.typography.titleLarge)
        }
        Column(Modifier.fillMaxSize().verticalScroll(rememberScrollState()).imePadding().padding(16.dp), verticalArrangement = Arrangement.spacedBy(10.dp)) {
            OutlinedTextField(betreff, { betreff = it }, label = { Text("Betreff *") }, singleLine = true, modifier = Modifier.fillMaxWidth())
            OutlinedTextField(text, { text = it }, label = { Text("Beschreibung") }, modifier = Modifier.fillMaxWidth().height(140.dp))
            Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                OutlinedTextField(sparte, { sparte = it.uppercase().take(10) }, label = { Text("Sparte (Kürzel)") }, singleLine = true, modifier = Modifier.weight(1f))
                OutlinedTextField(parzelle, { v -> parzelle = v.filter { it.isDigit() }.take(4) }, label = { Text("Parzelle") }, singleLine = true,
                    keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Number), modifier = Modifier.weight(1f))
            }
            Text("Kontakt (optional)", style = MaterialTheme.typography.titleSmall)
            OutlinedTextField(name, { name = it }, label = { Text("Name") }, singleLine = true, modifier = Modifier.fillMaxWidth())
            Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                OutlinedTextField(email, { email = it.trim() }, label = { Text("E-Mail") }, singleLine = true,
                    keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Email), modifier = Modifier.weight(1f))
                OutlinedTextField(telefon, { telefon = it }, label = { Text("Telefon") }, singleLine = true,
                    keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Phone), modifier = Modifier.weight(1f))
            }
            Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                Auswahl("Priorität", prio, listOf("niedrig", "normal", "hoch", "dringend"), { it }, Modifier.weight(1f)) { prio = it }
                if (kategorien.isNotEmpty()) Auswahl("Kategorie", kategorie.ifEmpty { kategorien.first() }, kategorien, { it }, Modifier.weight(1f)) { kategorie = it }
            }
            Auswahl("Zuständig", zustaendig, konten, { if (it.isEmpty()) "niemand" else it }, Modifier.fillMaxWidth()) { zustaendig = it }
            Button(
                enabled = betreff.isNotBlank() && !arbeitet,
                onClick = {
                    s.ausfuehren(scope, { arbeitet = it }) {
                        val t = JSONObject().put("betreff", betreff).put("text", text).put("prioritaet", prio).put("zustaendig", zustaendig)
                        if (kategorien.isNotEmpty()) t.put("kategorie", kategorie.ifEmpty { kategorien.first() })
                        if (sparte.isNotBlank() || parzelle.isNotBlank()) t.put("sparte", sparte).put("parzelle", parzelle)
                        if (name.isNotBlank()) t.put("name", name)
                        if (email.isNotBlank()) t.put("email", email)
                        if (telefon.isNotBlank()) t.put("telefon", telefon)
                        val a = s.api.post("/api/ticket-speichern", JSONObject().put("ticket", t))
                        s.meldenLog(a)
                        angelegt(a.o("ticket").s("id"))
                    }
                },
                modifier = Modifier.fillMaxWidth(),
            ) { Text("Anfrage anlegen") }
        }
    }
}

/** waagerecht scrollbare Zeile (für Filter-Chips auf schmalen Handys) */
@Composable
fun Modifier.horizontalScrollRow(): Modifier = this.then(Modifier.horizontalScroll(rememberScrollState()))
