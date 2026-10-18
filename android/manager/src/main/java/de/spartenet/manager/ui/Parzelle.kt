package de.spartenet.manager.ui

import androidx.compose.foundation.Canvas
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.aspectRatio
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.imePadding
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.widthIn
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.text.KeyboardActions
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.ContentCopy
import androidx.compose.material.icons.filled.Share
import androidx.compose.material.icons.filled.Visibility
import androidx.compose.material.icons.filled.VisibilityOff
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.FilterChip
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.geometry.Size
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalClipboardManager
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.AnnotatedString
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.ImeAction
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.unit.dp
import de.spartenet.manager.data.liste
import de.spartenet.manager.data.s
import de.spartenet.manager.data.texte
import kotlinx.coroutines.launch
import org.json.JSONObject

@Composable
fun ParzellenSeite(s: Sitzung, breit: Boolean) {
    val plan = rememberLaden(s, s) { s.api.get("/api/plan") }
    var kz by rememberSaveable { mutableStateOf("") }
    var nr by rememberSaveable { mutableStateOf("") }
    var ergebnis by remember { mutableStateOf<JSONObject?>(null) }
    var arbeitet by remember { mutableStateOf(false) }
    var zeigePw by remember { mutableStateOf(false) }
    val scope = rememberCoroutineScope()
    val clip = LocalClipboardManager.current
    val ctx = LocalContext.current

    fun suchen(k: String) {
        if (k.isEmpty() || nr.isEmpty()) return
        zeigePw = false
        s.ausfuehren(scope, { arbeitet = it }) {
            ergebnis = null
            ergebnis = s.api.get("/api/parzelle", mapOf("sparte" to k, "p" to nr))
        }
    }

    Column(Modifier.fillMaxSize()) {
        Kopf("Parzelle / WLAN", "WLAN-Name, Passwort und QR-Code einer Parzelle")
        Laden(plan) { pl ->
            val sparten = pl.liste("sparten")
            val aktiv = kz.takeIf { x -> sparten.any { it.s("kz") == x } } ?: sparten.firstOrNull()?.s("kz") ?: ""
            val max = sparten.firstOrNull { it.s("kz") == aktiv }?.optInt("n") ?: 0
            Column(Modifier.fillMaxSize().verticalScroll(rememberScrollState()).imePadding().padding(16.dp), verticalArrangement = Arrangement.spacedBy(12.dp)) {
                if (sparten.isEmpty()) Text("Im Manager ist noch keine Planung angelegt.")
                Row(Modifier.horizontalScrollRow(), horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                    sparten.forEach { sp ->
                        FilterChip(selected = sp.s("kz") == aktiv, onClick = { kz = sp.s("kz"); ergebnis = null },
                            label = { Text("${sp.s("kz")} · ${sp.s("name")}") })
                    }
                }
                Row(verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                    OutlinedTextField(
                        nr, { v -> nr = v.filter { it.isDigit() }.take(4) }, singleLine = true,
                        label = { Text(if (max > 0) "Parzelle (1–$max)" else "Parzelle") },
                        keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Number, imeAction = ImeAction.Search),
                        keyboardActions = KeyboardActions(onSearch = { suchen(aktiv) }),
                        modifier = Modifier.weight(1f),
                    )
                    Button(onClick = { suchen(aktiv) }, enabled = !arbeitet && nr.isNotEmpty() && aktiv.isNotEmpty()) { Text("Anzeigen") }
                }
                ergebnis?.let { e ->
                    val inhalt: @Composable () -> Unit = {
                        Card(Modifier.widthIn(max = 520.dp)) {
                            Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(6.dp)) {
                                Text("${e.s("sparte")} · Parzelle ${e.s("parzelle")}", style = MaterialTheme.typography.titleMedium, fontWeight = FontWeight.SemiBold)
                                Zeile("WLAN", e.s("wlan"))
                                Row(verticalAlignment = Alignment.CenterVertically) {
                                    Text("Passwort", Modifier.weight(0.4f), color = MaterialTheme.colorScheme.onSurfaceVariant)
                                    Text(if (zeigePw) e.s("passwort") else "••••••••••", Modifier.weight(0.6f), fontFamily = FontFamily.Monospace)
                                    IconButton(onClick = { zeigePw = !zeigePw }) {
                                        Icon(if (zeigePw) Icons.Filled.VisibilityOff else Icons.Filled.Visibility, if (zeigePw) "verbergen" else "zeigen")
                                    }
                                }
                                Zeile("Netz", listOf(e.s("netz"), e.s("vlan").let { if (it.isEmpty()) "" else "VLAN $it" }).filter { it.isNotEmpty() }.joinToString(" · "))
                                if (e.s("subnetz").isNotEmpty()) Zeile("Subnetz", e.s("subnetz"))
                                Row(horizontalArrangement = Arrangement.spacedBy(8.dp), modifier = Modifier.padding(top = 8.dp)) {
                                    OutlinedButton(onClick = {
                                        clip.setText(AnnotatedString(e.s("passwort")))
                                        scope.launch { s.melden("Passwort kopiert.") }
                                    }) { Icon(Icons.Filled.ContentCopy, null); Text(" Kopieren") }
                                    OutlinedButton(onClick = {
                                        teilen(ctx, "WLAN Parzelle ${e.s("parzelle")}",
                                            "WLAN für ${e.s("sparte")}, Parzelle ${e.s("parzelle")}\nWLAN-Name: ${e.s("wlan")}\nPasswort: ${e.s("passwort")}")
                                    }) { Icon(Icons.Filled.Share, null); Text(" Teilen") }
                                }
                            }
                        }
                    }
                    val qr: @Composable (Modifier) -> Unit = { m -> QrCode(e.texte("qr_matrix"), m) }
                    if (breit) {
                        Row(horizontalArrangement = Arrangement.spacedBy(24.dp)) {
                            Box(Modifier.weight(1f)) { inhalt() }
                            qr(Modifier.weight(1f).widthIn(max = 360.dp))
                        }
                    } else {
                        inhalt()
                        qr(Modifier.fillMaxWidth().widthIn(max = 360.dp).align(Alignment.CenterHorizontally))
                    }
                    Text("QR-Code mit der Handy-Kamera scannen, um direkt ins WLAN zu kommen.", style = MaterialTheme.typography.bodySmall,
                        color = MaterialTheme.colorScheme.onSurfaceVariant)
                }
            }
        }
    }
}

/** QR-Code aus der Modul-Matrix des Managers („0101…“ je Zeile) – immer schwarz auf weiß, damit er scanbar bleibt */
@Composable
fun QrCode(zeilen: List<String>, modifier: Modifier = Modifier) {
    if (zeilen.isEmpty()) return
    val n = zeilen.size
    Box(modifier.aspectRatio(1f).background(Color.White).padding(12.dp)) {
        Canvas(Modifier.fillMaxSize()) {
            val m = size.minDimension / n
            zeilen.forEachIndexed { y, z ->
                z.forEachIndexed { x, c ->
                    if (c == '1') drawRect(Color.Black, Offset(x * m, y * m), Size(m + 0.5f, m + 0.5f))
                }
            }
        }
    }
}
