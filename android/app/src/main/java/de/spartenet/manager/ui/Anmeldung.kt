package de.spartenet.manager.ui

import androidx.compose.foundation.background
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
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.ImeAction
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.text.input.PasswordVisualTransformation
import androidx.compose.ui.text.input.VisualTransformation
import androidx.compose.ui.unit.dp
import de.spartenet.manager.data.Api
import de.spartenet.manager.data.ApiFehler
import de.spartenet.manager.data.Speicher
import de.spartenet.manager.data.s
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
            val name = benutzer.trim().lowercase()
            val gemerkt = speicher.merken(api.basis, name)
            try {
                val a = api.anmelden(name, passwort, code, geraet.ifBlank { "Android" }, gemerkt)
                speicher.server = api.basis
                speicher.benutzer = name
                a.s("merken").takeIf { it.isNotEmpty() }?.let { speicher.merkenSetzen(api.basis, name, it) }
                speicher.abmeldenMinuten = a.optInt("abmelden_minuten", 0)
                speicher.zuletztAktiv = System.currentTimeMillis()
                passwort = ""
                code = ""
                onAngemeldet(api, a)
            } catch (e: ApiFehler) {
                if (e.zweiterFaktor) {
                    zeigeCode = true
                    if (gemerkt != null && code.isBlank()) speicher.merkenSetzen(api.basis, name, null)   // gemerkter Code gilt nicht mehr
                }
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
                Spacer(Modifier.height(12.dp))
                Box(
                    Modifier.fillMaxWidth().clip(RoundedCornerShape(24.dp))
                        .background(Brush.linearGradient(listOf(Color(0xFF14321F), Color(0xFF2F7A1F))))
                        .padding(24.dp)
                ) {
                    Column {
                        Row(verticalAlignment = Alignment.CenterVertically) {
                            Box(Modifier.size(48.dp).clip(RoundedCornerShape(14.dp)).background(Color.White.copy(alpha = 0.15f)), contentAlignment = Alignment.Center) {
                                Icon(Icons.Filled.Wifi, null, tint = Color(0xFF9BE07F), modifier = Modifier.size(30.dp))
                            }
                            Text("SparteNet", Modifier.padding(start = 12.dp), style = MaterialTheme.typography.headlineSmall,
                                fontWeight = FontWeight.Bold, color = Color.White)
                        }
                        Text("Anmelden", Modifier.padding(top = 18.dp), style = MaterialTheme.typography.headlineMedium,
                            fontWeight = FontWeight.Bold, color = Color.White)
                        Text("WLAN der Kleingarten-Sparte verwalten – Anfragen, Mitglieder, Buchungen und Laufzeiten.",
                            color = Color(0xFFC9E3C4), style = MaterialTheme.typography.bodyMedium)
                    }
                }
                Spacer(Modifier.height(4.dp))
                hinweis?.let {
                    Surface(color = MaterialTheme.colorScheme.secondaryContainer, shape = RoundedCornerShape(12.dp), modifier = Modifier.fillMaxWidth()) {
                        Text(it, Modifier.padding(12.dp), color = MaterialTheme.colorScheme.onSecondaryContainer)
                    }
                }
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
                fehler?.let {
                    Surface(color = MaterialTheme.colorScheme.errorContainer, shape = RoundedCornerShape(12.dp), modifier = Modifier.fillMaxWidth()) {
                        Text(it, Modifier.padding(12.dp), color = MaterialTheme.colorScheme.onErrorContainer)
                    }
                }
                Button(onClick = { anmelden() }, enabled = !laedt, modifier = Modifier.fillMaxWidth().height(52.dp)) {
                    if (laedt) CircularProgressIndicator(Modifier.size(22.dp), strokeWidth = 2.dp) else Text("Anmelden")
                }
                if (!zeigeCode) {
                    androidx.compose.material3.TextButton(onClick = { zeigeCode = true }) { Text("Zwei-Faktor-Code eingeben") }
                }
                Text(
                    "Das Passwort wird nicht gespeichert. Die App erhält einen eigenen Geräte-Schlüssel, der verschlüsselt im Android-Keystore liegt. " +
                        "Ist „Zwei-Faktor-Code merken“ im Manager eingeschaltet, fragt die App den Code für diese Zeit nicht erneut ab.",
                    style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.onSurfaceVariant,
                )
            }
        }
    }
}
