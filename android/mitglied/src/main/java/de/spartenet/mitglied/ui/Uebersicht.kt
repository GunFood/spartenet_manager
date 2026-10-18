package de.spartenet.mitglied.ui

import android.content.ActivityNotFoundException
import android.graphics.BitmapFactory
import android.content.Context
import android.content.Intent
import android.net.Uri
import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.BoxWithConstraints
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.FlowRow
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.heightIn
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.widthIn
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.Logout
import androidx.compose.material.icons.filled.ArrowDropDown
import androidx.compose.material.icons.filled.PictureAsPdf
import androidx.compose.material.icons.filled.Refresh
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.DropdownMenu
import androidx.compose.material3.DropdownMenuItem
import androidx.compose.material3.FilterChip
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.LinearProgressIndicator
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Scaffold
import androidx.compose.material3.SnackbarHost
import androidx.compose.material3.SnackbarHostState
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.material3.TopAppBar
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.foundation.Image
import androidx.compose.foundation.layout.size
import androidx.compose.ui.graphics.ImageBitmap
import androidx.compose.ui.graphics.asImageBitmap
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.ImeAction
import androidx.compose.ui.text.input.KeyboardCapitalization
import androidx.compose.ui.unit.dp
import androidx.core.content.FileProvider
import de.spartenet.mitglied.data.Api
import de.spartenet.mitglied.data.ApiFehler
import de.spartenet.mitglied.data.Datei
import de.spartenet.mitglied.data.Speicher
import de.spartenet.mitglied.data.b
import de.spartenet.mitglied.data.d
import de.spartenet.mitglied.data.geld
import de.spartenet.mitglied.data.i
import de.spartenet.mitglied.data.liste
import de.spartenet.mitglied.data.o
import de.spartenet.mitglied.data.rangHoeher
import de.spartenet.mitglied.data.s
import de.spartenet.mitglied.data.texte
import de.spartenet.mitglied.data.zahlen
import kotlinx.coroutines.CancellationException
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import org.json.JSONObject
import java.io.File

/** Hauptbildschirm: Tarif mit Laufzeit, Geräte im Parzellen-Netz, Rechnungen, Anfragen. Auf Tablets zweispaltig. */
@Composable
fun Uebersicht(speicher: Speicher, token: String, onAbgemeldet: () -> Unit) {
    val api = remember(token) { Api(speicher.server, token) }
    val scope = rememberCoroutineScope()
    val ctx = LocalContext.current
    val snackbar = remember { SnackbarHostState() }
    var daten by remember { mutableStateOf<JSONObject?>(null) }
    var fehler by remember { mutableStateOf<String?>(null) }
    var laedt by remember { mutableStateOf(false) }
    var wahl by remember { mutableStateOf<String?>(null) }
    var abmeldenFragen by remember { mutableStateOf(false) }
    var dialog by remember { mutableStateOf<String?>(null) }        // "upgrade", "downgrade", "neu", "verlaengern", "anfrage"
    var beschaeftigt by remember { mutableStateOf(false) }

    fun melden(text: String) {
        scope.launch { snackbar.showSnackbar(text) }
    }

    fun laden() {
        scope.launch {
            laedt = true
            fehler = null
            try {
                val d = api.post("/mein/daten")
                daten = d
                if (d.s("titel").isNotEmpty()) speicher.titel = d.s("titel")
            } catch (e: CancellationException) {
                throw e
            } catch (e: Exception) {
                if (e is ApiFehler && e.abgemeldet) onAbgemeldet() else fehler = e.message
            } finally {
                laedt = false
            }
        }
    }

    fun aktion(block: suspend () -> Unit) {
        if (beschaeftigt) return
        scope.launch {
            beschaeftigt = true
            try {
                block()
            } catch (e: CancellationException) {
                throw e
            } catch (e: Exception) {
                if (e is ApiFehler && e.abgemeldet) onAbgemeldet() else melden(e.message ?: "Fehler")
            } finally {
                beschaeftigt = false
            }
        }
    }

    LaunchedEffect(token) { laden() }

    val d = daten
    Scaffold(
        topBar = {
            TopAppBar(
                navigationIcon = {
                    val p0 = d?.liste("parzellen")?.let { l -> l.firstOrNull { it.s("id") == wahl } ?: l.firstOrNull() }
                    Row(Modifier.padding(start = 8.dp), verticalAlignment = Alignment.CenterVertically) {
                        d?.s("logo_verein")?.takeIf { it.isNotEmpty() }?.let { NetzBild(api, it, "Vereinslogo") }
                        p0?.s("sparte_logo")?.takeIf { it.isNotEmpty() }?.let { NetzBild(api, it, p0.s("sparte_name")) }
                    }
                },
                title = {
                    Column {
                        Text(speicher.titel.ifEmpty { "Mitgliederbereich" }, fontWeight = FontWeight.SemiBold)
                        if (d != null && d.s("mitglied").isNotEmpty()) Text("Hallo " + d.s("mitglied"), style = MaterialTheme.typography.bodySmall)
                    }
                },
                actions = {
                    IconButton(onClick = { laden() }) { Icon(Icons.Filled.Refresh, "Aktualisieren") }
                    IconButton(onClick = { abmeldenFragen = true }) { Icon(Icons.AutoMirrored.Filled.Logout, "Abmelden") }
                },
            )
        },
        snackbarHost = { SnackbarHost(snackbar) },
    ) { pad ->
        Box(Modifier.padding(pad).fillMaxSize()) {
            when {
                d == null && fehler != null -> Column(Modifier.align(Alignment.Center).padding(24.dp), horizontalAlignment = Alignment.CenterHorizontally) {
                    Text(fehler ?: "", color = MaterialTheme.colorScheme.error)
                    OutlinedButton(onClick = { laden() }, modifier = Modifier.padding(top = 12.dp)) { Text("Erneut versuchen") }
                }
                d == null -> CircularProgressIndicator(Modifier.align(Alignment.Center))
                else -> {
                    val parzellen = d.liste("parzellen")
                    val p = parzellen.firstOrNull { it.s("id") == wahl } ?: parzellen.firstOrNull()
                    if (p == null) {
                        Text(
                            "Zu Ihrer E-Mail-Adresse ist gerade keine Parzelle hinterlegt. Bitte beim Verein melden.",
                            Modifier.align(Alignment.Center).padding(24.dp),
                        )
                    } else {
                        BoxWithConstraints(Modifier.fillMaxSize()) {
                            val breit = maxWidth >= 840.dp
                            Column(Modifier.fillMaxSize().verticalScroll(rememberScrollState()).padding(16.dp), verticalArrangement = Arrangement.spacedBy(12.dp)) {
                                if (laedt || beschaeftigt) LinearProgressIndicator(Modifier.fillMaxWidth())
                                if (parzellen.size > 1) {
                                    FlowRow(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                                        parzellen.forEach { x ->
                                            FilterChip(
                                                selected = x.s("id") == p.s("id"), onClick = { wahl = x.s("id") },
                                                label = { Text("${x.s("sparte_name")} · Parzelle ${x.s("parzelle")}") },
                                            )
                                        }
                                    }
                                }
                                StoerungsBanner(p.liste("stoerungen").map { it.s("text") }, d.s("stoerung_text"), d.s("stoerung_farbe"))
                                if (d.s("hinweis").isNotEmpty()) Text(d.s("hinweis"), color = MaterialTheme.colorScheme.onSurfaceVariant)
                                fehler?.let { Text(it, color = MaterialTheme.colorScheme.error) }
                                val erlaubt = d.o("erlaubt") ?: JSONObject()
                                val tarif: @Composable () -> Unit = { TarifKarte(d, p, erlaubt) { dialog = it } }
                                val geraete: @Composable () -> Unit = {
                                    if (erlaubt.b("geraete") || erlaubt.b("zugangskarte")) GeraeteKarte(api, p, erlaubt, ::aktion, ::melden)
                                }
                                val rechnungen: @Composable () -> Unit = {
                                    if (erlaubt.b("zeige_rechnungen")) RechnungenKarte(p) { r ->
                                        aktion {
                                            val f = api.datei("/mein/rechnung", mapOf("id" to r.s("id")))
                                            pdfOeffnen(ctx, f)
                                        }
                                    }
                                }
                                val anfragen: @Composable () -> Unit = {
                                    if (erlaubt.b("zeige_anfragen") || erlaubt.b("neue_anfrage")) AnfragenKarte(p, erlaubt) { dialog = "anfrage" }
                                }
                                if (breit) {
                                    Row(horizontalArrangement = Arrangement.spacedBy(16.dp)) {
                                        Column(Modifier.weight(1f), verticalArrangement = Arrangement.spacedBy(12.dp)) { tarif(); geraete() }
                                        Column(Modifier.weight(1f), verticalArrangement = Arrangement.spacedBy(12.dp)) { rechnungen(); anfragen() }
                                    }
                                } else {
                                    tarif(); geraete(); rechnungen(); anfragen()
                                }
                                Spacer(Modifier.height(24.dp))
                            }
                        }
                        when (val wie = dialog) {
                            null -> {}
                            "anfrage" -> AnfrageDialog(d.texte("kategorien"), onAbbrechen = { dialog = null }) { kat, betreff, text ->
                                aktion {
                                    val r = api.post("/mein/ticket", JSONObject().put("id", p.s("id")).put("kategorie", kat).put("betreff", betreff).put("text", text))
                                    dialog = null
                                    melden(r.s("text"))
                                    laden()
                                }
                            }
                            else -> TarifDialog(d, p, wie, onAbbrechen = { dialog = null }) { art, name ->
                                aktion {
                                    val r = api.post("/mein/buchen", JSONObject().put("id", p.s("id")).put("art", art).put("tarif", name))
                                    dialog = null
                                    val url = r.s("url")
                                    if (url.isNotEmpty()) {
                                        oeffnen(ctx, url)
                                        melden("Bezahlseite geöffnet – nach der Zahlung hier aktualisieren.")
                                    } else {
                                        melden(r.s("text"))
                                    }
                                    laden()
                                }
                            }
                        }
                    }
                }
            }
        }
    }

    if (abmeldenFragen) {
        AlertDialog(
            onDismissRequest = { abmeldenFragen = false },
            title = { Text("Abmelden?") },
            text = { Text("Danach ist für die nächste Anmeldung wieder ein Code per E-Mail nötig.") },
            confirmButton = {
                TextButton(onClick = {
                    abmeldenFragen = false
                    scope.launch {
                        try {
                            api.post("/mein/abmelden")
                        } catch (e: CancellationException) {
                            throw e
                        } catch (_: Exception) {
                        }
                        onAbgemeldet()
                    }
                }) { Text("Abmelden") }
            },
            dismissButton = { TextButton(onClick = { abmeldenFragen = false }) { Text("Abbrechen") } },
        )
    }
}

// ---- Karten ----------------------------------------------------------------------------------------------------

@Composable
private fun Karte(titel: String, inhalt: @Composable () -> Unit) {
    Card(Modifier.fillMaxWidth(), colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surfaceContainerLow)) {
        Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
            Text(titel, style = MaterialTheme.typography.titleMedium, color = MaterialTheme.colorScheme.primary, fontWeight = FontWeight.SemiBold)
            inhalt()
        }
    }
}

@Composable
private fun Wert(beschriftung: String, wert: String, unten: String = "", modifier: Modifier = Modifier) {
    Column(modifier) {
        Text(beschriftung, style = MaterialTheme.typography.labelMedium, color = MaterialTheme.colorScheme.onSurfaceVariant)
        Text(wert, style = MaterialTheme.typography.titleLarge, fontWeight = FontWeight.Bold)
        if (unten.isNotEmpty()) Text(unten, style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.onSurfaceVariant)
    }
}

@Composable
private fun Hinweis(text: String, fehler: Boolean = false) {
    Surface(
        color = if (fehler) MaterialTheme.colorScheme.errorContainer else MaterialTheme.colorScheme.secondaryContainer,
        shape = MaterialTheme.shapes.small, modifier = Modifier.fillMaxWidth(),
    ) {
        Text(
            text, Modifier.padding(10.dp), style = MaterialTheme.typography.bodyMedium,
            color = if (fehler) MaterialTheme.colorScheme.onErrorContainer else MaterialTheme.colorScheme.onSecondaryContainer,
        )
    }
}

private fun hoeher(t: JSONObject, p: JSONObject): Boolean = rangHoeher(t.zahlen("rang"), p.zahlen("rang").takeIf { it.isNotEmpty() })

@Composable
private fun TarifKarte(d: JSONObject, p: JSONObject, erlaubt: JSONObject, onWahl: (String) -> Unit) {
    Karte("Mein Tarif") {
        val tarif = p.s("tarif")
        if (tarif.isEmpty()) {
            Text("Für diese Parzelle ist noch kein Tarif gebucht.", color = MaterialTheme.colorScheme.onSurfaceVariant)
        } else {
            val lz = p.o("laufzeit")
            FlowRow(horizontalArrangement = Arrangement.spacedBy(24.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                Wert("Tarif", tarif)
                if (lz != null) {
                    Wert("Laufzeit", if (lz.b("aktiv")) "bis " + lz.s("ende").take(10) else "abgelaufen", if (lz.b("aktiv")) "noch ${lz.i("rest_tage")} Tag(e)" else lz.s("ende"))
                } else {
                    Wert("Laufzeit", "unbegrenzt")
                }
                Wert("Offen", geld(p.d("offen")))
            }
            if (p.b("gesperrt")) Hinweis("Der WLAN-Zugang ist gerade gesperrt (Laufzeit abgelaufen) – mit einer Verlängerung wird er wieder freigegeben.", fehler = true)
        }
        p.o("auftrag")?.let { a ->
            Hinweis("Offener Zahlungsauftrag ${a.s("referenz")} (${a.s("tarif")}, ${geld(a.d("betrag"))}) – wird gebucht, sobald die Zahlung bestätigt ist.")
        }
        val antraege = p.liste("antraege")
        antraege.forEach { a ->
            val was = when (a.s("art")) { "wechsel" -> "Wechsel zu"; "neu" -> "Buchung"; "verlaengern" -> "Verlängerung"; else -> "" }
            Hinweis("⏳ Antrag ${a.s("nr")}: $was ${a.s("tarif")} – wartet auf Freigabe durch den Verein.")
        }
        val tarife = d.liste("tarife")
        val ups = tarife.filter { it.s("name") != tarif && hoeher(it, p) }
        val downs = tarife.filter { it.s("name") != tarif && !hoeher(it, p) }
        val knoepfe = buildList {
            if (tarif.isEmpty() && erlaubt.b("neubuchung") && tarife.isNotEmpty()) add("neu" to "Tarif buchen")
            if (tarif.isNotEmpty() && erlaubt.b("tarifwechsel") && ups.isNotEmpty()) add("upgrade" to "⬆ Upgrade")
            if (tarif.isNotEmpty() && erlaubt.b("downgrade") && downs.isNotEmpty() && antraege.isEmpty()) add("downgrade" to "⬇ Kleinerer Tarif")
            val lzText = p.s("tarif_laufzeit")
            if (tarif.isNotEmpty() && erlaubt.b("verlaengern") && lzText.isNotEmpty() && lzText != "unbegrenzt" && antraege.isEmpty()) add("verlaengern" to "Verlängern ($lzText)")
        }
        if (knoepfe.isNotEmpty()) {
            FlowRow(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                knoepfe.forEach { (art, text) -> OutlinedButton(onClick = { onWahl(art) }) { Text(text) } }
            }
        }
    }
}

@Composable
private fun GeraeteKarte(api: Api, p: JSONObject, erlaubt: JSONObject, aktion: (suspend () -> Unit) -> Unit, melden: (String) -> Unit) {
    var antwort by remember(p.s("id")) { mutableStateOf<JSONObject?>(null) }
    var laedt by remember(p.s("id")) { mutableStateOf(false) }
    var fehler by remember(p.s("id")) { mutableStateOf<String?>(null) }
    val scope = rememberCoroutineScope()
    fun laden() {
        if (!erlaubt.b("geraete")) return
        scope.launch {
            laedt = true; fehler = null
            try {
                antwort = api.post("/mein/geraete", JSONObject().put("id", p.s("id")))
            } catch (e: CancellationException) {
                throw e
            } catch (e: Exception) {
                fehler = e.message
            } finally {
                laedt = false
            }
        }
    }
    LaunchedEffect(p.s("id")) { laden() }
    Karte(if (erlaubt.b("geraete")) "Meine Geräte im WLAN" else "WLAN-Zugang") {
        if (erlaubt.b("geraete")) {
            val a = antwort
            Text(
                "Geräte, die gerade im Netz Ihrer Parzelle angemeldet sind – erkennbar an der IP-Adresse" +
                    (a?.s("netz")?.takeIf { it.isNotEmpty() }?.let { " ($it)" } ?: "") + ". Die letzte Zahl ist das Gerät.",
                style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.onSurfaceVariant,
            )
            when {
                laedt && a == null -> LinearProgressIndicator(Modifier.fillMaxWidth())
                fehler != null -> Text(fehler ?: "", color = MaterialTheme.colorScheme.error)
                a != null && a.liste("geraete").isEmpty() -> Text(a.s("fehler").ifEmpty { "Gerade ist kein Gerät angemeldet." }, color = MaterialTheme.colorScheme.onSurfaceVariant)
                a != null -> a.liste("geraete").forEachIndexed { n, g ->
                    if (n > 0) HorizontalDivider()
                    Row(Modifier.fillMaxWidth().padding(vertical = 4.dp), verticalAlignment = Alignment.CenterVertically) {
                        Column(Modifier.weight(1f)) {
                            Text(g.s("name"), fontWeight = FontWeight.Medium)
                            Text("${g.s("ip")} · ${g.s("art")}", style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.onSurfaceVariant)
                        }
                        Surface(color = MaterialTheme.colorScheme.primaryContainer, shape = MaterialTheme.shapes.small) {
                            Text("Nr. ${g.s("geraet")}", Modifier.padding(horizontal = 8.dp, vertical = 2.dp), style = MaterialTheme.typography.labelMedium)
                        }
                    }
                }
            }
        }
        FlowRow(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
            if (erlaubt.b("geraete")) OutlinedButton(onClick = { laden() }) { Text("Aktualisieren") }
            if (erlaubt.b("zugangskarte")) OutlinedButton(onClick = {
                aktion { melden(api.post("/mein/zugangskarte", JSONObject().put("id", p.s("id"))).s("text")) }
            }) { Text("Zugangskarte per E-Mail") }
        }
    }
}

@Composable
private fun RechnungenKarte(p: JSONObject, onOeffnen: (JSONObject) -> Unit) {
    Karte("Meine Rechnungen") {
        val liste = p.liste("rechnungen")
        if (liste.isEmpty()) Text("Noch keine Rechnungen.", color = MaterialTheme.colorScheme.onSurfaceVariant)
        liste.forEachIndexed { n, r ->
            if (n > 0) HorizontalDivider()
            Row(Modifier.fillMaxWidth().clickable { onOeffnen(r) }.padding(vertical = 6.dp), verticalAlignment = Alignment.CenterVertically) {
                Column(Modifier.weight(1f)) {
                    Text(r.s("nr"), fontWeight = FontWeight.Medium)
                    Text("${r.s("datum")} · ${r.s("status")}", style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.onSurfaceVariant)
                }
                Text(geld(r.d("brutto")), fontWeight = FontWeight.SemiBold)
                Icon(Icons.Filled.PictureAsPdf, "PDF öffnen", Modifier.padding(start = 8.dp), tint = MaterialTheme.colorScheme.primary)
            }
        }
    }
}

@Composable
private fun AnfragenKarte(p: JSONObject, erlaubt: JSONObject, onNeu: () -> Unit) {
    Karte("Meine Anfragen") {
        if (erlaubt.b("zeige_anfragen")) {
            val liste = p.liste("tickets")
            if (liste.isEmpty()) Text("Keine Anfragen.", color = MaterialTheme.colorScheme.onSurfaceVariant)
            liste.forEachIndexed { n, t ->
                if (n > 0) HorizontalDivider()
                Column(Modifier.padding(vertical = 4.dp)) {
                    Text("${t.s("nr")} · ${t.s("status")} · ${t.s("erstellt").take(10)}", style = MaterialTheme.typography.labelMedium, color = MaterialTheme.colorScheme.onSurfaceVariant)
                    Text(t.s("betreff"))
                    if (t.s("loesung").isNotEmpty()) Text("Lösung: " + t.s("loesung"), style = MaterialTheme.typography.bodySmall)
                }
            }
        }
        if (erlaubt.b("neue_anfrage")) Button(onClick = onNeu) { Text("Neue Anfrage") }
    }
}

// ---- Dialoge ---------------------------------------------------------------------------------------------------

@Composable
private fun TarifDialog(d: JSONObject, p: JSONObject, wie: String, onAbbrechen: () -> Unit, onBestaetigen: (String, String) -> Unit) {
    val tarif = p.s("tarif")
    val bezahlen = d.s("modus") == "bezahldienst"
    val liste: List<JSONObject> = when (wie) {
        "verlaengern" -> listOf(
            JSONObject().put("name", tarif).put("preis", p.d("tarif_preis")).put("down", p.d("tarif_down")).put("up", p.d("tarif_up"))
                .put("geraete", p.i("tarif_geraete")).put("laufzeit", p.s("tarif_laufzeit"))
        )
        "upgrade" -> d.liste("tarife").filter { it.s("name") != tarif && hoeher(it, p) }
        "downgrade" -> d.liste("tarife").filter { it.s("name") != tarif && !hoeher(it, p) }
        else -> d.liste("tarife")
    }
    var gewaehlt by remember { mutableStateOf(if (wie == "verlaengern") tarif else null) }
    val titel = when (wie) { "upgrade" -> "Upgrade"; "downgrade" -> "Kleinerer Tarif"; "verlaengern" -> "Laufzeit verlängern"; else -> "Tarif buchen" }
    val hinweis = when (wie) {
        "upgrade" -> "Ein Upgrade ist jederzeit möglich" + if (bezahlen) " – nach der Bezahlung sofort gebucht." else " und wird sofort gebucht."
        "downgrade" -> "Ein Wechsel in einen kleineren Tarif muss vom Verein freigegeben werden. Sie bekommen per E-Mail Bescheid."
        else -> if (bezahlen) "Sie werden zur Bezahlung weitergeleitet; gebucht wird, sobald die Zahlung bestätigt ist." else "Ihr Antrag geht an den Verein und wird nach der Freigabe gebucht."
    }
    val knopf = when {
        wie == "downgrade" -> "Antrag stellen"
        bezahlen -> "Weiter zur Bezahlung"
        wie == "upgrade" -> "Jetzt wechseln"
        else -> "Antrag senden"
    }
    AlertDialog(
        onDismissRequest = onAbbrechen,
        title = { Text(titel) },
        text = {
            Column(Modifier.heightIn(max = 480.dp).verticalScroll(rememberScrollState()), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                Text(hinweis, style = MaterialTheme.typography.bodyMedium, color = MaterialTheme.colorScheme.onSurfaceVariant)
                liste.forEach { t ->
                    val aktiv = t.s("name") == gewaehlt
                    Card(
                        onClick = { gewaehlt = t.s("name") }, modifier = Modifier.fillMaxWidth(),
                        border = BorderStroke(if (aktiv) 2.dp else 1.dp, if (aktiv) MaterialTheme.colorScheme.primary else MaterialTheme.colorScheme.outlineVariant),
                    ) {
                        Column(Modifier.padding(12.dp)) {
                            Row(verticalAlignment = Alignment.CenterVertically) {
                                Text(t.s("name"), Modifier.weight(1f), style = MaterialTheme.typography.titleMedium, fontWeight = FontWeight.SemiBold)
                                Text(geld(t.d("preis")), fontWeight = FontWeight.Bold)
                            }
                            val geraete = t.i("geraete")
                            Text(
                                "${t.d("down").toInt()} / ${t.d("up").toInt()} Mbit/s · " + (if (geraete > 0) "$geraete Geräte" else "Geräte unbegrenzt") + " · Laufzeit: ${t.s("laufzeit")}",
                                style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.onSurfaceVariant,
                            )
                        }
                    }
                }
            }
        },
        confirmButton = { TextButton(onClick = { gewaehlt?.let { onBestaetigen(if (wie == "upgrade" || wie == "downgrade") "wechsel" else wie, it) } }, enabled = gewaehlt != null) { Text(knopf) } },
        dismissButton = { TextButton(onClick = onAbbrechen) { Text("Abbrechen") } },
    )
}

@Composable
private fun AnfrageDialog(kategorien: List<String>, onAbbrechen: () -> Unit, onSenden: (String, String, String) -> Unit) {
    var kat by remember { mutableStateOf(kategorien.firstOrNull() ?: "Sonstiges") }
    var offen by remember { mutableStateOf(false) }
    var betreff by remember { mutableStateOf("") }
    var text by remember { mutableStateOf("") }
    AlertDialog(
        onDismissRequest = onAbbrechen,
        title = { Text("Neue Anfrage") },
        text = {
            Column(Modifier.widthIn(min = 280.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                Box {
                    OutlinedButton(onClick = { offen = true }, modifier = Modifier.fillMaxWidth()) {
                        Text("Worum geht es? $kat", Modifier.weight(1f))
                        Icon(Icons.Filled.ArrowDropDown, null)
                    }
                    DropdownMenu(expanded = offen, onDismissRequest = { offen = false }) {
                        kategorien.forEach { k -> DropdownMenuItem(text = { Text(k) }, onClick = { kat = k; offen = false }) }
                    }
                }
                OutlinedTextField(
                    betreff, { betreff = it.take(160) }, Modifier.fillMaxWidth(), label = { Text("Betreff") }, singleLine = true,
                    keyboardOptions = KeyboardOptions(capitalization = KeyboardCapitalization.Sentences, imeAction = ImeAction.Next),
                )
                OutlinedTextField(
                    text, { text = it.take(5000) }, Modifier.fillMaxWidth().heightIn(min = 120.dp), label = { Text("Nachricht") },
                    keyboardOptions = KeyboardOptions(capitalization = KeyboardCapitalization.Sentences),
                )
            }
        },
        confirmButton = { TextButton(onClick = { onSenden(kat, betreff.trim(), text.trim()) }, enabled = betreff.isNotBlank()) { Text("Senden") } },
        dismissButton = { TextButton(onClick = onAbbrechen) { Text("Abbrechen") } },
    )
}

// ---- Hilfen ----------------------------------------------------------------------------------------------------

/** hervorgehobene Störungsmeldung (Ausfall eines Geräts) – Farbe aus dem Manager */
@Composable
fun StoerungsBanner(meldungen: List<String>, zusatz: String, farbe: String) {
    if (meldungen.isEmpty()) return
    val f = try {
        androidx.compose.ui.graphics.Color(android.graphics.Color.parseColor(farbe.ifEmpty { "#b42318" }))
    } catch (_: IllegalArgumentException) {
        MaterialTheme.colorScheme.error
    }
    Surface(
        color = f.copy(alpha = 0.12f), shape = MaterialTheme.shapes.medium,
        border = BorderStroke(2.dp, f), modifier = Modifier.fillMaxWidth(),
    ) {
        Column(Modifier.padding(14.dp), verticalArrangement = Arrangement.spacedBy(6.dp)) {
            meldungen.forEach { m ->
                Row(verticalAlignment = Alignment.Top) {
                    Text("⚠", color = f, style = MaterialTheme.typography.titleLarge, modifier = Modifier.padding(end = 8.dp))
                    Text(m, color = f, fontWeight = FontWeight.SemiBold)
                }
            }
            if (zusatz.isNotEmpty()) Text(zusatz, style = MaterialTheme.typography.bodyMedium)
        }
    }
}

/** Logo vom Manager laden (Vereins- oder Spartenlogo, öffentlich) und klein anzeigen */
@Composable
fun NetzBild(api: Api, pfad: String, beschreibung: String, groesse: androidx.compose.ui.unit.Dp = 40.dp) {
    var bild by remember(pfad) { mutableStateOf<ImageBitmap?>(null) }
    LaunchedEffect(pfad) {
        bild = try {
            val roh = api.datei(pfad).daten
            withContext(Dispatchers.Default) { BitmapFactory.decodeByteArray(roh, 0, roh.size)?.asImageBitmap() }
        } catch (e: CancellationException) {
            throw e
        } catch (_: Exception) {
            null
        }
    }
    bild?.let { Image(it, beschreibung, Modifier.padding(end = 6.dp).size(groesse), contentScale = ContentScale.Fit) }
}

fun oeffnen(ctx: Context, uri: String) {
    try {
        ctx.startActivity(Intent(Intent.ACTION_VIEW, Uri.parse(uri)))
    } catch (_: ActivityNotFoundException) {
    }
}

/** PDF im Cache ablegen und mit einer PDF-App öffnen (ohne Speicher-Berechtigung) */
suspend fun pdfOeffnen(ctx: Context, dat: Datei) {
    val sicher = dat.name.replace(Regex("[^A-Za-z0-9._-]"), "_")
    val f = withContext(Dispatchers.IO) {
        val dir = File(ctx.cacheDir, "pdf").apply { mkdirs() }
        dir.listFiles()?.forEach { if (it.lastModified() < System.currentTimeMillis() - 86_400_000L) it.delete() }
        File(dir, sicher).apply { writeBytes(dat.daten) }
    }
    val uri = FileProvider.getUriForFile(ctx, ctx.packageName + ".dateien", f)
    val i = Intent(Intent.ACTION_VIEW).setDataAndType(uri, "application/pdf").addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)
    try {
        ctx.startActivity(i)
    } catch (_: ActivityNotFoundException) {
        val teilen = Intent(Intent.ACTION_SEND).setType("application/pdf").putExtra(Intent.EXTRA_STREAM, uri).addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)
        ctx.startActivity(Intent.createChooser(teilen, dat.name))
    }
}
