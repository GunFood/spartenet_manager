package de.spartenet.mitglied.ui

import android.os.Build
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.imePadding
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.systemBarsPadding
import androidx.compose.foundation.layout.widthIn
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.text.KeyboardActions
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Wifi
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.ImeAction
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.unit.dp
import de.spartenet.mitglied.data.Api
import de.spartenet.mitglied.data.Speicher
import de.spartenet.mitglied.data.s
import kotlinx.coroutines.CancellationException
import kotlinx.coroutines.launch

/**
 * Anmeldung in zwei Schritten: Adresse + E-Mail → Code per E-Mail anfordern → Code eingeben.
 * Kein Passwort. Enter (Tastatur „Weiter“/„Fertig“) löst jeweils den nächsten Schritt aus.
 */
@Composable
fun Anmeldung(speicher: Speicher, onAngemeldet: (String) -> Unit) {
    val scope = rememberCoroutineScope()
    var server by remember { mutableStateOf(speicher.server) }
    var email by remember { mutableStateOf(speicher.email) }
    var code by remember { mutableStateOf("") }
    var codeGesendet by remember { mutableStateOf(false) }
    var hinweis by remember { mutableStateOf<String?>(null) }
    var fehler by remember { mutableStateOf<String?>(null) }
    var laedt by remember { mutableStateOf(false) }
    val titel = speicher.titel.ifEmpty { "Mitgliederbereich" }

    fun codeAnfordern() {
        if (laedt) return
        if (server.isBlank() || !email.contains("@")) {
            fehler = "Bitte die Adresse des Vereins und Ihre E-Mail-Adresse eintragen."
            return
        }
        scope.launch {
            laedt = true; fehler = null
            try {
                val api = Api(server, null)
                val info = api.info()
                speicher.server = api.basis
                speicher.email = email.trim()
                speicher.titel = info.s("titel")
                hinweis = api.codeAnfordern(email)
                codeGesendet = true
            } catch (e: CancellationException) {
                throw e
            } catch (e: Exception) {
                fehler = e.message
            } finally {
                laedt = false
            }
        }
    }

    fun anmelden() {
        if (laedt) return
        if (code.trim().length != 6) {
            fehler = "Bitte den 6-stelligen Code aus der E-Mail eingeben."
            return
        }
        scope.launch {
            laedt = true; fehler = null
            try {
                val geraet = listOf(Build.MANUFACTURER, Build.MODEL).filter { !it.isNullOrBlank() }.joinToString(" ").ifEmpty { "Android" }
                onAngemeldet(Api(speicher.server, null).anmelden(email, code, geraet))
            } catch (e: CancellationException) {
                throw e
            } catch (e: Exception) {
                fehler = e.message
            } finally {
                laedt = false
            }
        }
    }

    Box(
        Modifier.fillMaxSize().background(
            Brush.verticalGradient(listOf(MaterialTheme.colorScheme.primary, MaterialTheme.colorScheme.primaryContainer, MaterialTheme.colorScheme.background))
        ).systemBarsPadding().imePadding(),
        contentAlignment = Alignment.TopCenter,
    ) {
        Column(
            Modifier.widthIn(max = 520.dp).fillMaxWidth().verticalScroll(rememberScrollState()).padding(20.dp),
            horizontalAlignment = Alignment.CenterHorizontally,
            verticalArrangement = Arrangement.spacedBy(12.dp),
        ) {
            Icon(Icons.Filled.Wifi, null, tint = MaterialTheme.colorScheme.onPrimary, modifier = Modifier.padding(top = 24.dp).size(56.dp))
            Text("SparteNet", style = MaterialTheme.typography.headlineMedium, color = MaterialTheme.colorScheme.onPrimary, fontWeight = FontWeight.Bold)
            Text(titel, style = MaterialTheme.typography.titleMedium, color = MaterialTheme.colorScheme.onPrimary)
            Card(Modifier.fillMaxWidth().padding(top = 12.dp)) {
                Column(Modifier.padding(20.dp), verticalArrangement = Arrangement.spacedBy(12.dp)) {
                    Text("Anmelden", style = MaterialTheme.typography.titleLarge, fontWeight = FontWeight.SemiBold)
                    Text(
                        "Mit der E-Mail-Adresse, die beim Verein für Ihre Parzelle hinterlegt ist. Sie bekommen einen Code per E-Mail – ein Passwort ist nicht nötig.",
                        style = MaterialTheme.typography.bodyMedium, color = MaterialTheme.colorScheme.onSurfaceVariant,
                    )
                    OutlinedTextField(
                        server, { server = it; codeGesendet = false }, Modifier.fillMaxWidth(), label = { Text("Adresse des Vereins") },
                        placeholder = { Text("z. B. wlan.meine-sparte.de") }, singleLine = true, enabled = !laedt,
                        keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Uri, imeAction = ImeAction.Next),
                        supportingText = { Text("Steht auf der Zugangskarte oder bekommen Sie vom Vorstand.") },
                    )
                    if (server.trim().startsWith("http://")) {
                        Text("⚠ Unverschlüsselte Verbindung – nur im eigenen Netz verwenden.", color = MaterialTheme.colorScheme.error, style = MaterialTheme.typography.bodySmall)
                    }
                    OutlinedTextField(
                        email, { email = it; codeGesendet = false }, Modifier.fillMaxWidth(), label = { Text("E-Mail-Adresse") }, singleLine = true, enabled = !laedt,
                        keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Email, imeAction = ImeAction.Send),
                        keyboardActions = KeyboardActions(onSend = { codeAnfordern() }),
                    )
                    if (!codeGesendet) {
                        Button(onClick = { codeAnfordern() }, enabled = !laedt, modifier = Modifier.fillMaxWidth()) { Text("Code per E-Mail senden") }
                    } else {
                        hinweis?.let { Text(it, color = MaterialTheme.colorScheme.tertiary, style = MaterialTheme.typography.bodyMedium) }
                        OutlinedTextField(
                            code, { code = it.filter(Char::isDigit).take(6) }, Modifier.fillMaxWidth(), label = { Text("Code aus der E-Mail") }, singleLine = true,
                            enabled = !laedt, textStyle = MaterialTheme.typography.headlineSmall,
                            keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.NumberPassword, imeAction = ImeAction.Done),
                            keyboardActions = KeyboardActions(onDone = { anmelden() }),
                        )
                        Button(onClick = { anmelden() }, enabled = !laedt, modifier = Modifier.fillMaxWidth()) { Text("Anmelden") }
                        TextButton(onClick = { codeAnfordern() }, enabled = !laedt) { Text("Code erneut senden") }
                    }
                    if (laedt) CircularProgressIndicator(Modifier.align(Alignment.CenterHorizontally))
                    fehler?.let { Text(it, color = MaterialTheme.colorScheme.error) }
                }
            }
            Text(
                "Diese App ist für Mitglieder. Für Vorstand und Mitarbeiter gibt es die App „SparteNet Manager“.",
                style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.onSurfaceVariant,
            )
        }
    }
}
