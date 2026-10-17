package de.spartenet.manager.ui

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.imePadding
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.systemBarsPadding
import androidx.compose.foundation.layout.widthIn
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Visibility
import androidx.compose.material.icons.filled.VisibilityOff
import androidx.compose.material.icons.filled.Wifi
import androidx.compose.material3.Button
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Surface
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
import androidx.compose.ui.text.input.ImeAction
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.text.input.PasswordVisualTransformation
import androidx.compose.ui.text.input.VisualTransformation
import androidx.compose.ui.unit.dp
import de.spartenet.manager.data.Api
import de.spartenet.manager.data.ApiFehler
import de.spartenet.manager.data.Speicher
import kotlinx.coroutines.launch
import org.json.JSONObject

@Composable
fun AnmeldeSeite(speicher: Speicher, hinweis: String?, onAngemeldet: (Api, JSONObject) -> Unit) {
    var server by remember { mutableStateOf(speicher.server) }
    var benutzer by remember { mutableStateOf(speicher.benutzer) }
    var passwort by remember { mutableStateOf("") }
    var code by remember { mutableStateOf("") }
    var geraet by remember { mutableStateOf(geraeteName()) }
    var zeigeCode by remember { mutableStateOf(false) }
    var zeigePw by remember { mutableStateOf(false) }
    var laedt by remember { mutableStateOf(false) }
    var fehler by remember { mutableStateOf<String?>(null) }
    val scope = rememberCoroutineScope()

    val http = Api.normalisieren(server).startsWith("http://")

    fun anmelden() {
        if (server.isBlank() || benutzer.isBlank() || passwort.isEmpty()) {
            fehler = "Bitte Server, Benutzer und Passwort eingeben."
            return
        }
        scope.launch {
            laedt = true
            fehler = null
            val api = Api(server, null)
            try {
                val a = api.anmelden(benutzer.trim().lowercase(), passwort, code, geraet.ifBlank { "Android" })
                speicher.server = api.basis
                speicher.benutzer = benutzer.trim().lowercase()
                passwort = ""
                code = ""
                onAngemeldet(api, a)
            } catch (e: ApiFehler) {
                if (e.zweiterFaktor) zeigeCode = true
                fehler = e.message
            } finally {
                laedt = false
            }
        }
    }

    Surface(Modifier.fillMaxSize()) {
        Box(Modifier.fillMaxSize().systemBarsPadding().imePadding(), contentAlignment = Alignment.TopCenter) {
            Column(
                Modifier.widthIn(max = 480.dp).fillMaxWidth().verticalScroll(rememberScrollState()).padding(24.dp),
                verticalArrangement = Arrangement.spacedBy(12.dp),
            ) {
                Spacer(Modifier.height(24.dp))
                Row(verticalAlignment = Alignment.CenterVertically) {
                    Icon(Icons.Filled.Wifi, null, tint = MaterialTheme.colorScheme.primary, modifier = Modifier.size(40.dp))
                    Column(Modifier.padding(start = 12.dp)) {
                        Text("SparteNet", style = MaterialTheme.typography.headlineMedium, fontWeight = FontWeight.Bold)
                        Text("Manager-App für Handy und Tablet", color = MaterialTheme.colorScheme.onSurfaceVariant)
                    }
                }
                Spacer(Modifier.height(8.dp))
                hinweis?.let { Text(it, color = MaterialTheme.colorScheme.tertiary) }
                OutlinedTextField(
                    value = server, onValueChange = { server = it },
                    label = { Text("Adresse des Managers") },
                    placeholder = { Text("https://manager.example.de") },
                    singleLine = true, modifier = Modifier.fillMaxWidth(),
                    keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Uri, imeAction = ImeAction.Next),
                    supportingText = if (http) {
                        { Text("Achtung: http:// ist unverschlüsselt – nur im eigenen Netz verwenden.", color = MaterialTheme.colorScheme.error) }
                    } else null,
                )
                OutlinedTextField(
                    value = benutzer, onValueChange = { benutzer = it },
                    label = { Text("Benutzername") }, singleLine = true, modifier = Modifier.fillMaxWidth(),
                    keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Ascii, imeAction = ImeAction.Next, autoCorrectEnabled = false),
                )
                OutlinedTextField(
                    value = passwort, onValueChange = { passwort = it },
                    label = { Text("Passwort") }, singleLine = true, modifier = Modifier.fillMaxWidth(),
                    visualTransformation = if (zeigePw) VisualTransformation.None else PasswordVisualTransformation(),
                    keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Password, imeAction = if (zeigeCode) ImeAction.Next else ImeAction.Done),
                    trailingIcon = {
                        IconButton(onClick = { zeigePw = !zeigePw }) {
                            Icon(if (zeigePw) Icons.Filled.VisibilityOff else Icons.Filled.Visibility, if (zeigePw) "Passwort verbergen" else "Passwort zeigen")
                        }
                    },
                )
                if (zeigeCode) {
                    OutlinedTextField(
                        value = code, onValueChange = { v -> code = v.filter { it.isDigit() }.take(8) },
                        label = { Text("Code aus der Authenticator-App") }, singleLine = true, modifier = Modifier.fillMaxWidth(),
                        keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.NumberPassword, imeAction = ImeAction.Done),
                    )
                }
                OutlinedTextField(
                    value = geraet, onValueChange = { geraet = it.take(60) },
                    label = { Text("Name dieses Geräts") }, singleLine = true, modifier = Modifier.fillMaxWidth(),
                    supportingText = { Text("Erscheint im Manager unter „Mein Konto → Apps und Geräte“ und kann dort gesperrt werden.") },
                )
                fehler?.let { Text(it, color = MaterialTheme.colorScheme.error) }
                Button(onClick = { anmelden() }, enabled = !laedt, modifier = Modifier.fillMaxWidth().height(52.dp)) {
                    if (laedt) CircularProgressIndicator(Modifier.size(22.dp), strokeWidth = 2.dp) else Text("Anmelden")
                }
                if (!zeigeCode) {
                    androidx.compose.material3.TextButton(onClick = { zeigeCode = true }) { Text("Zwei-Faktor-Code eingeben") }
                }
                Text(
                    "Das Passwort wird nicht gespeichert. Die App erhält einen eigenen Geräte-Schlüssel, der verschlüsselt im Android-Keystore liegt.",
                    style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.onSurfaceVariant,
                )
            }
        }
    }
}
