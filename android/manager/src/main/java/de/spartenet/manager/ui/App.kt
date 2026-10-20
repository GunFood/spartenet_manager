package de.spartenet.manager.ui

import android.os.Build
import androidx.activity.compose.BackHandler
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxHeight
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.AccountCircle
import androidx.compose.material.icons.filled.ConfirmationNumber
import androidx.compose.material.icons.filled.Grass
import androidx.compose.material.icons.filled.Home
import androidx.compose.material.icons.filled.Inbox
import androidx.compose.material.icons.filled.MoreHoriz
import androidx.compose.material.icons.filled.People
import androidx.compose.material.icons.filled.Receipt
import androidx.compose.material.icons.filled.Timer
import androidx.compose.material.icons.filled.Warning
import androidx.compose.material.icons.filled.Wifi
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.Icon
import androidx.compose.material3.ListItem
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.NavigationBar
import androidx.compose.material3.NavigationBarItem
import androidx.compose.material3.NavigationDrawerItem
import androidx.compose.material3.NavigationRail
import androidx.compose.material3.NavigationRailItem
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.PermanentDrawerSheet
import androidx.compose.material3.Scaffold
import androidx.compose.material3.SnackbarHost
import androidx.compose.material3.SnackbarHostState
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.material3.SnackbarDuration
import androidx.compose.material3.SnackbarResult
import androidx.compose.ui.platform.LocalContext
import de.spartenet.manager.data.AppUpdate
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableIntStateOf
import androidx.compose.runtime.mutableLongStateOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.input.pointer.PointerEventPass
import androidx.compose.ui.input.pointer.pointerInput
import kotlinx.coroutines.CancellationException
import kotlinx.coroutines.delay
import androidx.compose.ui.platform.LocalConfiguration
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import de.spartenet.manager.data.Api
import de.spartenet.manager.data.ApiFehler
import de.spartenet.manager.data.Speicher
import de.spartenet.manager.data.o
import de.spartenet.manager.data.s

/** Bereiche der App – „recht“ ist der Bereich im Manager (Benutzer & Rechte) */
enum class Bereich(val titel: String, val icon: ImageVector, val recht: String?) {
    START("Start", Icons.Filled.Home, null),
    TICKETS("Anfragen", Icons.Filled.Inbox, "tickets"),
    MITGLIEDER("Mitglieder", Icons.Filled.People, "mitglieder"),
    BUCHUNGEN("Buchungen", Icons.Filled.Grass, "buchungen"),
    LAUFZEITEN("Laufzeiten", Icons.Filled.Timer, "buchungen"),
    PARZELLE("Parzelle / WLAN", Icons.Filled.Wifi, "start"),
    VOUCHER("Gast-Voucher", Icons.Filled.ConfirmationNumber, "voucher"),
    RECHNUNGEN("Rechnungen", Icons.Filled.Receipt, "rechnungen"),
    STOERUNGEN("Störungen", Icons.Filled.Warning, "auslesen"),
    KONTO("Mein Konto", Icons.Filled.AccountCircle, null),
}

/** Wurzel: Anmeldung prüfen, dann die App mit passender Navigation für Handy oder Tablet */
@Composable
fun Wurzel(speicher: Speicher, ansicht: String, onAnsicht: (String) -> Unit) {
    val snackbar = remember { SnackbarHostState() }
    var sitzung by remember { mutableStateOf<Sitzung?>(null) }
    var pruefen by remember { mutableIntStateOf(if (speicher.token != null) 1 else 0) }
    var startFehler by remember { mutableStateOf<String?>(null) }
    var hinweis by remember { mutableStateOf<String?>(null) }

    fun abmeldenLokal(grund: String?) {
        speicher.token = null
        sitzung = null
        pruefen = 0
        hinweis = grund
    }

    fun neueSitzung(api: Api, ich: org.json.JSONObject, version: String, minuten: Int) =
        Sitzung(api, ich, version, snackbar) { abmeldenLokal("Die Anmeldung ist abgelaufen oder wurde unter „Mein Konto“ gesperrt.") }
            .also { it.abmeldenMinuten = minuten; speicher.abmeldenMinuten = minuten }

    if (pruefen > 0 && sitzung == null) {
        LaunchedEffect(pruefen) {
            startFehler = null
            val api = Api(speicher.server, speicher.token, speicher.zugangstoken(speicher.server))
            val min = speicher.abmeldenMinuten
            if (min > 0 && speicher.zuletztAktiv > 0 && System.currentTimeMillis() - speicher.zuletztAktiv > min * 60_000L) {
                geraetEntfernen(api)
                abmeldenLokal(abgemeldetText(min))
                return@LaunchedEffect
            }
            try {
                val info = api.get("/api/v1/app/info")
                speicher.zuletztAktiv = System.currentTimeMillis()
                sitzung = neueSitzung(api, info.o("ich"), info.s("version"), info.optInt("abmelden_minuten", 0))
            } catch (e: ApiFehler) {
                if (e.abgemeldet) abmeldenLokal("Bitte neu anmelden.") else startFehler = e.message
            }
        }
        Surface(Modifier.fillMaxSize()) {
            if (startFehler == null) {
                Box(contentAlignment = Alignment.Center) { CircularProgressIndicator() }
            } else {
                Column(Modifier.padding(24.dp), horizontalAlignment = Alignment.CenterHorizontally) {
                    Spacer(Modifier.height(80.dp))
                    FehlerAnzeige(startFehler!!, onNeu = { pruefen++ })
                }
                Box(Modifier.fillMaxSize().padding(24.dp), contentAlignment = Alignment.BottomCenter) {
                    OutlinedButton(onClick = { abmeldenLokal(null) }) { Text("Anderen Server / neu anmelden") }
                }
            }
        }
        return
    }

    val s = sitzung
    if (s == null) {
        AnmeldeSeite(speicher, hinweis) { api, antwort ->
            speicher.token = antwort.s("token")
            api.token = antwort.s("token")
            hinweis = null
            sitzung = neueSitzung(api, antwort.o("ich"), antwort.s("version"), antwort.optInt("abmelden_minuten", 0))
        }
        return
    }

    // automatisch abmelden: jede Berührung zählt als Aktivität; geprüft wird alle 10 s und beim Zurückkehren in die App
    var letzte by remember(s) { mutableLongStateOf(System.currentTimeMillis()) }
    if (s.abmeldenMinuten > 0) {
        LaunchedEffect(s) {
            var gespeichert = 0L
            while (true) {
                val jetzt = System.currentTimeMillis()
                if (jetzt - letzte > s.abmeldenMinuten * 60_000L) {
                    geraetEntfernen(s.api)
                    abmeldenLokal(abgemeldetText(s.abmeldenMinuten))
                    break
                }
                if (letzte - gespeichert > 30_000L) {
                    speicher.zuletztAktiv = letzte
                    gespeichert = letzte
                }
                delay(10_000)
            }
        }
    }
    Box(Modifier.fillMaxSize().pointerInput(s) {
        awaitPointerEventScope {
            while (true) {
                awaitPointerEvent(PointerEventPass.Initial)
                val jetzt = System.currentTimeMillis()
                // nach Ablauf zählt die erste Berührung nicht mehr – die Prüfung oben meldet ab
                if (s.abmeldenMinuten == 0 || jetzt - letzte <= s.abmeldenMinuten * 60_000L) letzte = jetzt
            }
        }
    }) {
        Hauptansicht(s, speicher, ansicht, onAnsicht, snackbar) {
            abmeldenLokal("Abgemeldet.")
        }
    }
}

private fun abgemeldetText(min: Int) =
    "Automatisch abgemeldet nach ${if (min % 60 == 0) "${min / 60} Stunde(n)" else "$min Minuten"} ohne Bedienung (Einstellung im Manager)."

/** Gerät am Manager abmelden – ohne Verbindung trotzdem lokal abmelden */
private suspend fun geraetEntfernen(api: Api) {
    val id = Speicher.geraeteId(api.token) ?: return
    try {
        api.post("/api/app-geraet-entfernen", org.json.JSONObject().put("id", id))
    } catch (e: CancellationException) {
        throw e
    } catch (_: Exception) {
    }
}

@Composable
private fun Hauptansicht(
    s: Sitzung,
    speicher: Speicher,
    ansicht: String,
    onAnsicht: (String) -> Unit,
    snackbar: SnackbarHostState,
    onAbmelden: () -> Unit,
) {
    val erlaubt = remember(s) { Bereich.entries.filter { it.recht == null || s.darf(it.recht) } }
    var bereich by rememberSaveable { mutableStateOf(Bereich.START) }
    var mehrOffen by rememberSaveable { mutableStateOf(false) }
    // Sprung von der Startseite mit Auftrag (z. B. „neues Ticket“)
    var auftrag by remember { mutableStateOf<String?>(null) }

    val cfg = LocalConfiguration.current
    val breit = cfg.screenWidthDp >= 600 && cfg.screenHeightDp >= 480
    val sehrBreit = cfg.screenWidthDp >= 1000

    fun gehe(b: Bereich, a: String? = null) {
        bereich = b
        auftrag = a
        mehrOffen = false
    }

    // App-Update: hat der Administrator eine neuere Version hochgeladen, bietet die App sie an (einmal je Anmeldung)
    val ctx = LocalContext.current
    LaunchedEffect(s) {
        val info = try {
            s.api.get("/api/v1/app/update").optJSONObject("app")
        } catch (e: CancellationException) {
            throw e
        } catch (_: Exception) {
            null
        }
        if (info != null && AppUpdate.neuer(ctx, info.optLong("version_code"))) {
            val hinweis = info.optString("hinweis").takeIf { it.isNotEmpty() }?.let { " – $it" } ?: ""
            val r = snackbar.showSnackbar(
                "Neue App-Version ${info.optString("version_name")} verfügbar$hinweis", actionLabel = "Aktualisieren",
                withDismissAction = true, duration = SnackbarDuration.Indefinite,
            )
            if (r == SnackbarResult.ActionPerformed) {
                try {
                    AppUpdate.installieren(ctx, s.api.datei("/api/v1/app/update.apk").daten, info.optString("sha256"))
                } catch (e: CancellationException) {
                    throw e
                } catch (e: Exception) {
                    snackbar.showSnackbar(e.message ?: "Update fehlgeschlagen.")
                }
            }
        }
    }

    BackHandler(enabled = bereich != Bereich.START || mehrOffen) {
        if (mehrOffen) mehrOffen = false else gehe(Bereich.START)
    }

    val inhalt: @Composable (Modifier) -> Unit = { mod ->
        Box(mod) {
            if (mehrOffen && !breit) {
                MehrSeite(erlaubt.filter { it !in hauptpunkte(erlaubt) }) { gehe(it) }
            } else {
                when (bereich) {
                    Bereich.START -> StartSeite(s, erlaubt, breit) { b, a -> gehe(b, a) }
                    Bereich.TICKETS -> TicketSeite(s, breit, auftrag) { auftrag = null }
                    Bereich.MITGLIEDER -> MitgliederSeite(s, breit, auftrag) { auftrag = null }
                    Bereich.BUCHUNGEN -> BuchungenSeite(s)
                    Bereich.LAUFZEITEN -> LaufzeitenSeite(s)
                    Bereich.PARZELLE -> ParzellenSeite(s, breit)
                    Bereich.VOUCHER -> VoucherSeite(s, breit)
                    Bereich.RECHNUNGEN -> RechnungenSeite(s)
                    Bereich.STOERUNGEN -> StoerungenSeite(s)
                    Bereich.KONTO -> KontoSeite(s, speicher, ansicht, onAnsicht, onAbmelden)
                }
            }
        }
    }

    Scaffold(
        snackbarHost = { SnackbarHost(snackbar) },
        bottomBar = {
            if (!breit) {
                val haupt = hauptpunkte(erlaubt)
                NavigationBar {
                    haupt.forEach { b ->
                        NavigationBarItem(
                            selected = bereich == b && !mehrOffen,
                            onClick = { gehe(b) },
                            icon = { Icon(b.icon, null) },
                            label = { Text(kurz(b)) },
                        )
                    }
                    if (erlaubt.size > haupt.size) {
                        NavigationBarItem(
                            selected = mehrOffen || bereich !in haupt,
                            onClick = { mehrOffen = true },
                            icon = { Icon(Icons.Filled.MoreHoriz, null) },
                            label = { Text("Mehr") },
                        )
                    }
                }
            }
        },
    ) { innen ->
        if (!breit) {
            inhalt(Modifier.padding(innen).fillMaxSize())
        } else {
            Row(Modifier.padding(innen).fillMaxSize()) {
                if (sehrBreit) {
                    PermanentDrawerSheet(Modifier.width(260.dp)) {
                        Column(Modifier.verticalScroll(rememberScrollState()).padding(12.dp)) {
                            Text("SparteNet", Modifier.padding(16.dp), style = MaterialTheme.typography.titleLarge, fontWeight = FontWeight.Bold,
                                color = MaterialTheme.colorScheme.primary)
                            erlaubt.forEach { b ->
                                NavigationDrawerItem(
                                    label = { Text(b.titel) },
                                    icon = { Icon(b.icon, null) },
                                    selected = bereich == b,
                                    onClick = { gehe(b) },
                                )
                            }
                            HorizontalDivider(Modifier.padding(vertical = 12.dp))
                            Text("${s.name} · Manager ${s.version}", Modifier.padding(16.dp), style = MaterialTheme.typography.bodySmall,
                                color = MaterialTheme.colorScheme.onSurfaceVariant)
                        }
                    }
                } else {
                    NavigationRail(Modifier.fillMaxHeight()) {
                        Column(Modifier.verticalScroll(rememberScrollState())) {
                            erlaubt.forEach { b ->
                                NavigationRailItem(
                                    selected = bereich == b,
                                    onClick = { gehe(b) },
                                    icon = { Icon(b.icon, null) },
                                    label = { Text(kurz(b)) },
                                )
                            }
                        }
                    }
                }
                inhalt(Modifier.weight(1f).fillMaxHeight())
            }
        }
    }
}

private fun hauptpunkte(erlaubt: List<Bereich>): List<Bereich> {
    val wunsch = listOf(Bereich.START, Bereich.TICKETS, Bereich.MITGLIEDER, Bereich.PARZELLE, Bereich.KONTO)
    val ausgewaehlt = wunsch.filter { it in erlaubt }
    return if (erlaubt.size <= 5) erlaubt else ausgewaehlt.take(4)
}

private fun kurz(b: Bereich) = when (b) {
    Bereich.PARZELLE -> "Parzelle"
    Bereich.VOUCHER -> "Voucher"
    Bereich.MITGLIEDER -> "Mitglieder"
    Bereich.KONTO -> "Konto"
    else -> b.titel
}

@Composable
private fun MehrSeite(punkte: List<Bereich>, onWahl: (Bereich) -> Unit) {
    Column(Modifier.fillMaxSize().verticalScroll(rememberScrollState())) {
        Text("Weitere Bereiche", Modifier.padding(16.dp), style = MaterialTheme.typography.titleLarge)
        punkte.forEach { b ->
            ListItem(
                headlineContent = { Text(b.titel) },
                leadingContent = { Icon(b.icon, null) },
                modifier = Modifier.clickableZeile { onWahl(b) },
            )
            HorizontalDivider()
        }
    }
}

fun Modifier.clickableZeile(onClick: () -> Unit): Modifier = this.clickable(onClick = onClick)

/** Gerätename als Vorschlag bei der Anmeldung */
fun geraeteName(): String = listOf(Build.MANUFACTURER.replaceFirstChar { it.uppercase() }, Build.MODEL).distinct().joinToString(" ").take(60)
