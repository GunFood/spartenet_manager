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
import androidx.compose.material.icons.filled.Home
import androidx.compose.material.icons.filled.LinkOff
import androidx.compose.material.icons.filled.Person
import androidx.compose.material.icons.filled.Receipt
import androidx.compose.material.icons.filled.SupportAgent
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.NavigationBar
import androidx.compose.material3.NavigationBarItem
import androidx.compose.material3.RadioButton
import androidx.compose.foundation.layout.statusBarsPadding
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.res.painterResource
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
import de.spartenet.mitglied.data.AppUpdate
import de.spartenet.mitglied.hintergrund.Hintergrund
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

/** Bereiche der App (unten als Navigationsleiste) */
private enum class Bereich(val titel: String, val symbol: ImageVector) {
    START("Übersicht", Icons.Filled.Home),
    RECHNUNGEN("Rechnungen", Icons.Filled.Receipt),
    SUPPORT("Support", Icons.Filled.SupportAgent),
    PROFIL("Profil", Icons.Filled.Person),
}

/** Hauptbildschirm: Kopf mit Logos und Begrüßung, unten Übersicht (Tarif, Geräte), Rechnungen, Support und Profil. */
@Composable
fun Uebersicht(speicher: Speicher, token: String, ansicht: String, onAnsicht: (String) -> Unit, onAbgemeldet: () -> Unit) {
    val api = remember(token) { Api(speicher.server, token) }
    val scope = rememberCoroutineScope()
    val ctx = LocalContext.current
    val snackbar = remember { SnackbarHostState() }
    var daten by remember { mutableStateOf<JSONObject?>(null) }
    var fehler by remember { mutableStateOf<String?>(null) }
    var laedt by remember { mutableStateOf(false) }
    var wahl by remember { mutableStateOf<String?>(null) }
    var bereich by remember { mutableStateOf(Bereich.START) }
    var abmeldenFragen by remember { mutableStateOf(false) }
    var dialog by remember { mutableStateOf<String?>(null) }        // "upgrade", "downgrade", "neu", "verlaengern", "ticket"
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

    // App-Update: hat der Verein eine neuere Version hochgeladen, zeigt die App einen Hinweis mit „Aktualisieren“
    var update by remember { mutableStateOf<JSONObject?>(null) }
    LaunchedEffect(token) {
        update = try {
            api.post("/mein/app").optJSONObject("app")?.takeIf { AppUpdate.neuer(ctx, it.optLong("version_code")) }
        } catch (e: CancellationException) {
            throw e
        } catch (_: Exception) {
            null
        }
    }

    val d = daten
    val parzellen = d?.liste("parzellen") ?: emptyList()
    val p = parzellen.firstOrNull { it.s("id") == wahl } ?: parzellen.firstOrNull()
    LaunchedEffect(p?.s("id")) {                       // das Widget zeigt die zuletzt gewählte Parzelle
        val id = p?.s("id") ?: return@LaunchedEffect
        if (speicher.widgetParzelle != id) {
            speicher.widgetParzelle = id
            Hintergrund.jetzt(ctx)
        }
    }
    Scaffold(
        topBar = {
            Kopf(
                api = api, titel = speicher.titel.ifEmpty { "Mitgliederbereich" }, spartenLogo = p?.s("sparte_logo") ?: "",
                spartenName = p?.s("sparte_name") ?: "", name = d?.s("mitglied") ?: "", ansicht = ansicht,
                onAnsicht = { onAnsicht(ANSICHTEN[(ANSICHTEN.indexOfFirst { it.first == ansicht } + 1).mod(ANSICHTEN.size)].first) },
                onAktualisieren = { laden() }, onAbmelden = { abmeldenFragen = true },
            )
        },
        bottomBar = {
            NavigationBar {
                Bereich.entries.forEach { b ->
                    NavigationBarItem(selected = bereich == b, onClick = { bereich = b }, icon = { Icon(b.symbol, null) }, label = { Text(b.titel) })
                }
            }
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
                p == null && bereich != Bereich.PROFIL -> Text(
                    "Zu Ihrer E-Mail-Adresse ist gerade keine Parzelle hinterlegt. Bitte beim Verein melden.",
                    Modifier.align(Alignment.Center).padding(24.dp),
                )
                else -> {
                    val erlaubt = d.o("erlaubt") ?: JSONObject()
                    Column(
                        Modifier.fillMaxSize().verticalScroll(rememberScrollState()).padding(16.dp).widthIn(max = 900.dp),
                        verticalArrangement = Arrangement.spacedBy(12.dp),
                    ) {
                        if (laedt || beschaeftigt) LinearProgressIndicator(Modifier.fillMaxWidth())
                        update?.let { u ->
                            Karte("Neue App-Version ${u.s("version_name")}") {
                                Text(u.s("hinweis").ifEmpty { "Eine neue Version der App ist verfügbar." }, style = MaterialTheme.typography.bodyMedium)
                                Button(onClick = {
                                    aktion { AppUpdate.installieren(ctx, api.datei("/mein/app.apk").daten, u.s("sha256")) }
                                }) { Text("Aktualisieren") }
                            }
                        }
                        if (parzellen.size > 1 && p != null) {
                            FlowRow(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                                parzellen.forEach { x ->
                                    FilterChip(
                                        selected = x.s("id") == p.s("id"), onClick = { wahl = x.s("id") },
                                        label = { Text("${x.s("sparte_name")} · Parzelle ${x.s("parzelle")}") },
                                    )
                                }
                            }
                        }
                        if (p != null) StoerungsBanner(p.liste("stoerungen").map { it.s("text") }, d.s("stoerung_text"), d.s("stoerung_farbe"))
                        fehler?.let { Text(it, color = MaterialTheme.colorScheme.error) }
                        when (bereich) {
                            Bereich.START -> if (p != null) {
                                if (d.s("hinweis").isNotEmpty()) Text(d.s("hinweis"), color = MaterialTheme.colorScheme.onSurfaceVariant)
                                TarifKarte(d, p, erlaubt) { dialog = it }
                                if (erlaubt.b("geraete") || erlaubt.b("zugangskarte")) GeraeteKarte(api, p, erlaubt, ::aktion, ::melden)
                            }
                            Bereich.RECHNUNGEN -> if (p != null) {
                                if (erlaubt.b("zeige_rechnungen")) RechnungenKarte(p) { r ->
                                    aktion {
                                        val f = api.datei("/mein/rechnung", mapOf("id" to r.s("id")))
                                        pdfOeffnen(ctx, f)
                                    }
                                } else Text("Rechnungen werden hier nicht angezeigt.", color = MaterialTheme.colorScheme.onSurfaceVariant)
                            }
                            Bereich.SUPPORT -> if (p != null) SupportKarte(p, erlaubt) { dialog = "ticket" }
                            Bereich.PROFIL -> {
                                ProfilKarte(api, d.o("profil") ?: JSONObject(), erlaubt, ::aktion, ::melden, onEmail = { speicher.email = it; laden() }) { laden() }
                                if (p != null) PersonenKarte(api, p, erlaubt, ::aktion, ::melden) { laden() }
                                BenachrichtigungKarte(speicher, ::melden)
                                WidgetKarte()
                                AnsichtKarte(ansicht, onAnsicht)
                            }
                        }
                        Spacer(Modifier.height(24.dp))
                    }
                    if (p != null) when (val wie = dialog) {
                        null -> {}
                        "ticket" -> AnfrageDialog(d.texte("kategorien"), onAbbrechen = { dialog = null }) { kat, betreff, text ->
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

/** Kopf: „Mitgliederbereich“, darunter Spartenlogo und Firmenlogo, dann „Hallo Vorname Nachname“ */
@Composable
private fun Kopf(
    api: Api, titel: String, spartenLogo: String, spartenName: String, name: String, ansicht: String,
    onAnsicht: () -> Unit, onAktualisieren: () -> Unit, onAbmelden: () -> Unit,
) {
    Surface(color = MaterialTheme.colorScheme.primary, contentColor = MaterialTheme.colorScheme.onPrimary) {
        Column(Modifier.fillMaxWidth().statusBarsPadding().padding(start = 16.dp, end = 4.dp, bottom = 12.dp)) {
            Row(verticalAlignment = Alignment.CenterVertically) {
                Text(titel, Modifier.weight(1f), style = MaterialTheme.typography.titleLarge, fontWeight = FontWeight.SemiBold)
                val sym = ANSICHTEN.firstOrNull { it.first == ansicht } ?: ANSICHTEN[0]
                TextButton(onClick = onAnsicht, colors = ButtonDefaults.textButtonColors(contentColor = MaterialTheme.colorScheme.onPrimary)) {
                    Text(sym.second, style = MaterialTheme.typography.titleLarge)
                }
                IconButton(onClick = onAktualisieren) { Icon(Icons.Filled.Refresh, "Aktualisieren") }
                IconButton(onClick = onAbmelden) { Icon(Icons.AutoMirrored.Filled.Logout, "Abmelden") }
            }
            Row(Modifier.padding(top = 4.dp), verticalAlignment = Alignment.CenterVertically) {
                if (spartenLogo.isNotEmpty()) NetzBild(api, spartenLogo, spartenName.ifEmpty { "Spartenlogo" }, 48.dp)
                Image(painterResource(de.spartenet.mitglied.R.drawable.firmenlogo), "Firmenlogo", Modifier.size(48.dp))
            }
            if (name.isNotEmpty()) Text("Hallo $name", Modifier.padding(top = 6.dp), style = MaterialTheme.typography.titleMedium)
        }
    }
}

// ---- Karten ----------------------------------------------------------------------------------------------------

@Composable
internal fun Karte(titel: String, inhalt: @Composable () -> Unit) {
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
internal fun Hinweis(text: String, fehler: Boolean = false) {
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
    var trennen by remember { mutableStateOf(false) }
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
        val a = antwort
        if (erlaubt.b("geraete")) {
            if (a != null) {
                // Verbrauch der Endgeräte nach dem Tarif, z. B. „Basic: 3 von 5 Geräten“
                val anzahl = a.i("anzahl")
                val max = a.i("max")
                val tarif = a.s("tarif")
                Text(
                    (if (tarif.isNotEmpty()) "$tarif: " else "") + if (max > 0) "$anzahl von $max Geräten" else "$anzahl Geräte (unbegrenzt)",
                    style = MaterialTheme.typography.titleMedium, fontWeight = FontWeight.SemiBold,
                )
                if (max > 0) LinearProgressIndicator(
                    progress = { (anzahl.toFloat() / max).coerceIn(0f, 1f) }, modifier = Modifier.fillMaxWidth(),
                    color = if (anzahl >= max) MaterialTheme.colorScheme.error else MaterialTheme.colorScheme.primary,
                )
                if (max in 1..anzahl) Text(
                    "Alle Plätze belegt – trennen Sie ein Gerät oder wechseln Sie in einen größeren Tarif.",
                    style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.error,
                )
            }
            when {
                laedt && a == null -> LinearProgressIndicator(Modifier.fillMaxWidth())
                fehler != null -> Text(fehler ?: "", color = MaterialTheme.colorScheme.error)
                a != null && a.liste("geraete").isEmpty() -> Text(a.s("fehler").ifEmpty { "Gerade ist kein Gerät angemeldet." }, color = MaterialTheme.colorScheme.onSurfaceVariant)
                a != null -> a.liste("geraete").forEachIndexed { n, g ->
                    if (n > 0) HorizontalDivider()
                    Row(Modifier.fillMaxWidth().padding(vertical = 4.dp), verticalAlignment = Alignment.CenterVertically) {
                        Surface(color = MaterialTheme.colorScheme.primaryContainer, shape = MaterialTheme.shapes.small) {
                            Text("Gerät ${g.i("nr")}", Modifier.padding(horizontal = 8.dp, vertical = 2.dp), style = MaterialTheme.typography.labelMedium)
                        }
                        Column(Modifier.weight(1f).padding(start = 12.dp)) {
                            Text(g.s("name"), fontWeight = FontWeight.Medium)
                            if (g.s("art").isNotEmpty()) Text(g.s("art"), style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.onSurfaceVariant)
                        }
                    }
                }
            }
            val gesperrt = a?.liste("gesperrt") ?: emptyList()
            if (gesperrt.isNotEmpty()) {
                HorizontalDivider()
                Text("Getrennte Geräte", style = MaterialTheme.typography.labelLarge)
                gesperrt.forEach { g ->
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        Column(Modifier.weight(1f)) {
                            Text(g.s("name"))
                            Text("getrennt am ${g.s("zeit")}", style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.onSurfaceVariant)
                        }
                        TextButton(onClick = {
                            aktion {
                                melden(api.post("/mein/geraet_zulassen", JSONObject().put("id", p.s("id")).put("ref", g.s("ref"))).s("text"))
                                laden()
                            }
                        }) { Text("Wieder zulassen") }
                    }
                }
            }
        }
        FlowRow(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
            if (erlaubt.b("geraete")) OutlinedButton(onClick = { laden() }) { Text("Aktualisieren") }
            if (erlaubt.b("geraete") && erlaubt.b("geraete_trennen") && (a?.liste("geraete")?.isNotEmpty() == true)) {
                OutlinedButton(onClick = { trennen = true }) {
                    Icon(Icons.Filled.LinkOff, null, Modifier.size(18.dp))
                    Text("Gerät trennen", Modifier.padding(start = 6.dp))
                }
            }
            if (erlaubt.b("zugangskarte")) OutlinedButton(onClick = {
                aktion { melden(api.post("/mein/zugangskarte", JSONObject().put("id", p.s("id"))).s("text")) }
            }) { Text("Zugangskarte per E-Mail") }
        }
    }
    val liste = antwort?.liste("geraete") ?: emptyList()       // „a“ gilt nur innerhalb der Karte
    if (trennen && liste.isNotEmpty()) {
        TrennenDialog(liste, onAbbrechen = { trennen = false }) { ref ->
            trennen = false
            aktion {
                melden(api.post("/mein/geraet_trennen", JSONObject().put("id", p.s("id")).put("ref", ref).put("bestaetigt", true)).s("text"))
                laden()
            }
        }
    }
}

/** Auswahl, welches Gerät getrennt wird – mit ausdrücklicher Bestätigung */
@Composable
private fun TrennenDialog(geraete: List<JSONObject>, onAbbrechen: () -> Unit, onTrennen: (String) -> Unit) {
    var gewaehlt by remember { mutableStateOf<String?>(null) }
    AlertDialog(
        onDismissRequest = onAbbrechen,
        icon = { Icon(Icons.Filled.LinkOff, null) },
        title = { Text("Welches Gerät trennen?") },
        text = {
            Column(Modifier.heightIn(max = 420.dp).verticalScroll(rememberScrollState())) {
                Text(
                    "Das Gerät wird vom WLAN getrennt und gesperrt, bis Sie es unter „Getrennte Geräte“ wieder zulassen.",
                    style = MaterialTheme.typography.bodyMedium, color = MaterialTheme.colorScheme.onSurfaceVariant,
                )
                geraete.forEach { g ->
                    Row(
                        Modifier.fillMaxWidth().clickable { gewaehlt = g.s("ref") }.padding(vertical = 4.dp),
                        verticalAlignment = Alignment.CenterVertically,
                    ) {
                        RadioButton(selected = gewaehlt == g.s("ref"), onClick = { gewaehlt = g.s("ref") })
                        Text("Gerät ${g.i("nr")} · ${g.s("name")}")
                    }
                }
            }
        },
        confirmButton = { TextButton(onClick = { gewaehlt?.let(onTrennen) }, enabled = gewaehlt != null) { Text("Trennen") } },
        dismissButton = { TextButton(onClick = onAbbrechen) { Text("Abbrechen") } },
    )
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
private fun SupportKarte(p: JSONObject, erlaubt: JSONObject, onNeu: () -> Unit) {
    Karte("Support") {
        Text("Fragen, Störungen oder Wünsche? Legen Sie ein Ticket an – Sie bekommen die Antwort per E-Mail.",
            style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.onSurfaceVariant)
        if (erlaubt.b("neue_anfrage")) Button(onClick = onNeu) { Text("Ticket anlegen") }
        if (erlaubt.b("zeige_anfragen")) {
            Text("Meine Tickets", style = MaterialTheme.typography.labelLarge, modifier = Modifier.padding(top = 8.dp))
            val liste = p.liste("tickets")
            if (liste.isEmpty()) Text("Noch keine Tickets.", color = MaterialTheme.colorScheme.onSurfaceVariant)
            liste.forEachIndexed { n, t ->
                if (n > 0) HorizontalDivider()
                Column(Modifier.padding(vertical = 4.dp)) {
                    Text("${t.s("nr")} · ${t.s("status")} · ${t.s("erstellt").take(10)}", style = MaterialTheme.typography.labelMedium, color = MaterialTheme.colorScheme.onSurfaceVariant)
                    Text(t.s("betreff"))
                    if (t.s("loesung").isNotEmpty()) Text("Lösung: " + t.s("loesung"), style = MaterialTheme.typography.bodySmall)
                }
            }
        }
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
        title = { Text("Ticket anlegen") },
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
