package de.spartenet.manager.ui

import android.content.ActivityNotFoundException
import android.content.Context
import android.content.Intent
import android.net.Uri
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.ArrowDropDown
import androidx.compose.material.icons.filled.ErrorOutline
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.DropdownMenu
import androidx.compose.material3.DropdownMenuItem
import androidx.compose.material3.Icon
import androidx.compose.material3.LinearProgressIndicator
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
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
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import de.spartenet.manager.data.ApiFehler
import kotlinx.coroutines.CancellationException
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Job
import kotlinx.coroutines.launch

/** Lädt Daten im Hintergrund; „laden()“ lädt neu. Fehler 401 meldet die Sitzung ab. */
class Ladezustand<T>(
    private val scope: CoroutineScope,
    private val sitzung: Sitzung?,
    private val block: suspend () -> T,
) {
    var daten by mutableStateOf<T?>(null)
    var fehler by mutableStateOf<String?>(null)
        private set
    var laedt by mutableStateOf(false)
        private set
    private var job: Job? = null

    fun laden() {
        job?.cancel()
        job = scope.launch {
            laedt = true
            fehler = null
            try {
                daten = block()
            } catch (e: CancellationException) {
                throw e
            } catch (e: Exception) {
                if (e is ApiFehler && e.abgemeldet) sitzung?.abgelaufen()
                fehler = e.message ?: "Unbekannter Fehler"
            } finally {
                laedt = false
            }
        }
    }
}

@Composable
fun <T> rememberLaden(sitzung: Sitzung?, vararg keys: Any?, block: suspend () -> T): Ladezustand<T> {
    val scope = rememberCoroutineScope()
    val l = remember(*keys) { Ladezustand(scope, sitzung, block) }
    LaunchedEffect(l) { l.laden() }
    return l
}

/** Führt eine Aktion aus und meldet Erfolg/Fehler über die Snackbar */
fun Sitzung.ausfuehren(scope: CoroutineScope, beschaeftigt: (Boolean) -> Unit = {}, aktion: suspend () -> Unit) {
    scope.launch {
        beschaeftigt(true)
        try {
            aktion()
        } catch (e: CancellationException) {
            throw e
        } catch (e: Exception) {
            if (e is ApiFehler && e.abgemeldet) abgelaufen()
            melden(e.message ?: "Fehler")
        } finally {
            beschaeftigt(false)
        }
    }
}

@Composable
fun <T> Laden(zustand: Ladezustand<T>, modifier: Modifier = Modifier, inhalt: @Composable (T) -> Unit) {
    val d = zustand.daten
    Box(modifier.fillMaxSize()) {
        when {
            d != null -> {
                inhalt(d)
                if (zustand.laedt) LinearProgressIndicator(Modifier.fillMaxWidth().align(Alignment.TopCenter))
                zustand.fehler?.let { Fehlerleiste(it, Modifier.align(Alignment.BottomCenter)) }
            }
            zustand.fehler != null -> FehlerAnzeige(zustand.fehler!!, onNeu = { zustand.laden() })
            else -> CircularProgressIndicator(Modifier.align(Alignment.Center))
        }
    }
}

@Composable
fun FehlerAnzeige(text: String, onNeu: (() -> Unit)? = null) {
    Column(
        Modifier.fillMaxSize().padding(24.dp),
        verticalArrangement = Arrangement.Center,
        horizontalAlignment = Alignment.CenterHorizontally,
    ) {
        Icon(Icons.Filled.ErrorOutline, null, tint = MaterialTheme.colorScheme.error, modifier = Modifier.size(48.dp))
        Text(text, Modifier.padding(top = 12.dp), style = MaterialTheme.typography.bodyLarge)
        if (onNeu != null) OutlinedButton(onClick = onNeu, modifier = Modifier.padding(top = 16.dp)) { Text("Erneut versuchen") }
    }
}

@Composable
fun Fehlerleiste(text: String, modifier: Modifier = Modifier) {
    Surface(modifier.fillMaxWidth(), color = MaterialTheme.colorScheme.errorContainer) {
        Text(text, Modifier.padding(12.dp), color = MaterialTheme.colorScheme.onErrorContainer)
    }
}

@Composable
fun Leer(text: String) {
    Box(Modifier.fillMaxSize().padding(24.dp), contentAlignment = Alignment.Center) {
        Text(text, color = MaterialTheme.colorScheme.onSurfaceVariant)
    }
}

/** Auswahlfeld ohne experimentelle APIs */
@Composable
fun <T> Auswahl(
    beschriftung: String,
    wert: T,
    optionen: List<T>,
    text: (T) -> String,
    modifier: Modifier = Modifier,
    aktiv: Boolean = true,
    onWahl: (T) -> Unit,
) {
    var offen by remember { mutableStateOf(false) }
    Box(modifier) {
        OutlinedButton(onClick = { offen = true }, enabled = aktiv, modifier = Modifier.fillMaxWidth()) {
            Column(Modifier.weight(1f)) {
                Text(beschriftung, style = MaterialTheme.typography.labelSmall, color = MaterialTheme.colorScheme.onSurfaceVariant)
                Text(text(wert), maxLines = 1, overflow = TextOverflow.Ellipsis)
            }
            Icon(Icons.Filled.ArrowDropDown, null)
        }
        DropdownMenu(expanded = offen, onDismissRequest = { offen = false }) {
            optionen.forEach { o ->
                DropdownMenuItem(text = { Text(text(o)) }, onClick = { offen = false; onWahl(o) })
            }
        }
    }
}

@Composable
fun Kachel(titel: String, modifier: Modifier = Modifier, onClick: (() -> Unit)? = null, inhalt: @Composable () -> Unit) {
    val farben = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surfaceContainerLow)
    val innen: @Composable () -> Unit = {
        Column(Modifier.padding(16.dp)) {
            Text(titel, style = MaterialTheme.typography.titleSmall, color = MaterialTheme.colorScheme.primary, fontWeight = FontWeight.SemiBold)
            Box(Modifier.padding(top = 8.dp)) { inhalt() }
        }
    }
    if (onClick != null) Card(onClick = onClick, modifier = modifier, colors = farben) { innen() }
    else Card(modifier = modifier, colors = farben) { innen() }
}

@Composable
fun Marke(text: String, farbe: Color = MaterialTheme.colorScheme.secondaryContainer, textFarbe: Color = MaterialTheme.colorScheme.onSecondaryContainer) {
    Surface(color = farbe, shape = MaterialTheme.shapes.small) {
        Text(text, Modifier.padding(horizontal = 8.dp, vertical = 2.dp), style = MaterialTheme.typography.labelMedium, color = textFarbe)
    }
}

@Composable
fun prioFarbe(prio: String): Color = when (prio) {
    "dringend" -> MaterialTheme.colorScheme.error
    "hoch" -> Color(0xFFE65100)
    "niedrig" -> MaterialTheme.colorScheme.outline
    else -> MaterialTheme.colorScheme.secondary
}

@Composable
fun Zeile(links: String, rechts: String) {
    Row(Modifier.fillMaxWidth().padding(vertical = 2.dp)) {
        Text(links, Modifier.weight(0.4f), color = MaterialTheme.colorScheme.onSurfaceVariant)
        Text(rechts, Modifier.weight(0.6f))
    }
}

@Composable
fun Bestaetigen(titel: String, text: String, ja: String, onJa: () -> Unit, onAbbrechen: () -> Unit) {
    AlertDialog(
        onDismissRequest = onAbbrechen,
        title = { Text(titel) },
        text = { Text(text) },
        confirmButton = { TextButton(onClick = onJa) { Text(ja) } },
        dismissButton = { TextButton(onClick = onAbbrechen) { Text("Abbrechen") } },
    )
}

fun teilen(ctx: Context, betreff: String, text: String) {
    val i = Intent(Intent.ACTION_SEND).setType("text/plain").putExtra(Intent.EXTRA_SUBJECT, betreff).putExtra(Intent.EXTRA_TEXT, text)
    ctx.startActivity(Intent.createChooser(i, betreff))
}

fun oeffnen(ctx: Context, uri: String) {
    try {
        ctx.startActivity(Intent(Intent.ACTION_VIEW, Uri.parse(uri)))
    } catch (_: ActivityNotFoundException) {
    }
}
