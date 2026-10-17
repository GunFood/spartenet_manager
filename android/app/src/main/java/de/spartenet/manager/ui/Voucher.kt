package de.spartenet.manager.ui

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.FlowRow
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.imePadding
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.widthIn
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.ContentCopy
import androidx.compose.material.icons.filled.Share
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.FilterChip
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.SegmentedButton
import androidx.compose.material3.SegmentedButtonDefaults
import androidx.compose.material3.SingleChoiceSegmentedButtonRow
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
import androidx.compose.ui.platform.LocalClipboardManager
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.AnnotatedString
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import de.spartenet.manager.data.i
import de.spartenet.manager.data.liste
import de.spartenet.manager.data.s
import de.spartenet.manager.data.texte
import kotlinx.coroutines.launch
import org.json.JSONObject

@Composable
fun VoucherSeite(s: Sitzung, breit: Boolean) {
    var reiter by rememberSaveable { mutableStateOf(0) }
    Column(Modifier.fillMaxSize()) {
        Kopf("Gast-Voucher")
        SingleChoiceSegmentedButtonRow(Modifier.fillMaxWidth().padding(horizontal = 16.dp, vertical = 4.dp)) {
            listOf("Erstellen", "Am Gateway").forEachIndexed { idx, t ->
                SegmentedButton(selected = reiter == idx, onClick = { reiter = idx }, shape = SegmentedButtonDefaults.itemShape(idx, 2)) { Text(t) }
            }
        }
        if (reiter == 0) VoucherErstellen(s) else VoucherListe(s)
    }
}

@Composable
private fun VoucherErstellen(s: Sitzung) {
    val vorlagen = rememberLaden(s, s) { s.api.get("/api/voucher-vorlagen") }
    var vorlage by rememberSaveable { mutableStateOf("") }
    var anzahl by rememberSaveable { mutableStateOf("1") }
    var name by rememberSaveable { mutableStateOf("") }
    var vorschau by remember { mutableStateOf<List<String>?>(null) }
    var ergebnis by remember { mutableStateOf<JSONObject?>(null) }
    var fragen by remember { mutableStateOf(false) }
    var arbeitet by remember { mutableStateOf(false) }
    val scope = rememberCoroutineScope()
    val clip = LocalClipboardManager.current
    val ctx = LocalContext.current
    val schreiben = s.darf("voucher", "schreiben")

    fun body(ausfuehren: Boolean) = JSONObject().put("vorlage", vorlage).put("anzahl", anzahl.toIntOrNull() ?: 1).put("name", name).put("ausfuehren", ausfuehren)

    Laden(vorlagen) { v ->
        val liste = v.liste("vorlagen")
        val aktiv = liste.firstOrNull { it.s("id") == vorlage } ?: liste.firstOrNull()
        val vid = aktiv?.s("id") ?: ""
        Column(Modifier.fillMaxSize().verticalScroll(rememberScrollState()).imePadding().padding(16.dp), verticalArrangement = Arrangement.spacedBy(12.dp)) {
            Text("Vorlage", style = MaterialTheme.typography.titleSmall)
            FlowRow(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                liste.forEach { x ->
                    FilterChip(selected = x.s("id") == vid, onClick = { vorlage = x.s("id"); vorschau = null },
                        label = { Text(x.s("name")) })
                }
            }
            aktiv?.let { a ->
                Text(
                    listOf(
                        dauer(a.i("minuten")),
                        "${a.i("geraete", 1)} Gerät(e)",
                        if (a.i("daten_mb") > 0) "${a.i("daten_mb")} MB" else "Datenvolumen unbegrenzt",
                        if (a.i("down_kbps") > 0) "↓ ${a.i("down_kbps") / 1000.0} Mbit/s" else "",
                        if (a.i("up_kbps") > 0) "↑ ${a.i("up_kbps") / 1000.0} Mbit/s" else "",
                    ).filter { it.isNotEmpty() }.joinToString(" · "),
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                )
            }
            Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                OutlinedTextField(anzahl, { x -> anzahl = x.filter { it.isDigit() }.take(4); vorschau = null }, label = { Text("Anzahl") }, singleLine = true,
                    keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Number), modifier = Modifier.weight(0.35f))
                OutlinedTextField(name, { name = it.take(40); vorschau = null }, label = { Text("Name/Notiz (optional)") }, singleLine = true, modifier = Modifier.weight(0.65f))
            }
            if (!schreiben) Text("Ihr Konto darf Voucher nur ansehen.", color = MaterialTheme.colorScheme.onSurfaceVariant)
            Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                OutlinedButton(enabled = !arbeitet && aktiv != null && (anzahl.toIntOrNull() ?: 0) in 1..1000, onClick = {
                    vorlage = vid
                    s.ausfuehren(scope, { arbeitet = it }) {
                        vorschau = s.api.post("/api/voucher", body(false)).texte("log").take(1)
                    }
                }) { Text("Vorschau") }
                Button(enabled = schreiben && !arbeitet && vorschau != null, onClick = { fragen = true }) { Text("Am Gateway erstellen") }
            }
            vorschau?.forEach { Text(it, style = MaterialTheme.typography.bodyMedium) }
            ergebnis?.let { e ->
                val codes = e.texte("codes")
                Card(Modifier.widthIn(max = 560.dp)) {
                    Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(6.dp)) {
                        Text("${codes.size} Voucher · ${e.s("dauer")}", style = MaterialTheme.typography.titleMedium, fontWeight = FontWeight.SemiBold)
                        codes.forEach { c ->
                            Text(code(c), fontFamily = FontFamily.Monospace, fontSize = 22.sp, fontWeight = FontWeight.Bold)
                            HorizontalDivider()
                        }
                        if (codes.isEmpty()) Text(e.texte("log").firstOrNull() ?: "")
                        Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                            OutlinedButton(enabled = codes.isNotEmpty(), onClick = {
                                clip.setText(AnnotatedString(codes.joinToString("\n") { code(it) }))
                                scope.launch { s.melden("Code(s) kopiert.") }
                            }) { Icon(Icons.Filled.ContentCopy, null); Text(" Kopieren") }
                            OutlinedButton(enabled = codes.isNotEmpty(), onClick = {
                                teilen(ctx, "WLAN-Voucher", buildString {
                                    append("Gast-WLAN – Voucher (${e.s("dauer")})\n")
                                    codes.forEach { append(code(it)).append('\n') }
                                    if (e.s("text").isNotEmpty()) append('\n').append(e.s("text"))
                                })
                            }) { Icon(Icons.Filled.Share, null); Text(" Teilen") }
                        }
                    }
                }
            }
        }
    }

    if (fragen) {
        Bestaetigen(
            "Voucher am Gateway erstellen?",
            (vorschau?.firstOrNull() ?: "") + "\n\nDie Voucher werden sofort am Gateway angelegt.",
            "Erstellen",
            onJa = {
                fragen = false
                s.ausfuehren(scope, { arbeitet = it }) {
                    val a = s.api.post("/api/voucher", body(true))
                    ergebnis = a
                    vorschau = null
                    s.meldenLog(a)
                }
            },
            onAbbrechen = { fragen = false },
        )
    }
}

@Composable
private fun VoucherListe(s: Sitzung) {
    val l = rememberLaden(s, s) { s.api.get("/api/voucher-liste") }
    var filter by rememberSaveable { mutableStateOf("unbenutzt") }
    Laden(l) { a ->
        val alle = a.liste("zeilen")
        val zeilen = alle.filter { filter == "alle" || it.s("status") == filter }
        Column(Modifier.fillMaxSize().verticalScroll(rememberScrollState()).padding(16.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
            Text(a.texte("log").firstOrNull() ?: "", color = MaterialTheme.colorScheme.onSurfaceVariant)
            Row(Modifier.horizontalScrollRow(), horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                listOf("unbenutzt", "in Benutzung", "voll belegt", "abgelaufen", "alle").forEach { f ->
                    FilterChip(selected = filter == f, onClick = { filter = f }, label = { Text(f) })
                }
            }
            zeilen.forEach { z ->
                Row(Modifier.fillMaxWidth().padding(vertical = 4.dp), verticalAlignment = Alignment.CenterVertically) {
                    Column(Modifier.weight(1f)) {
                        Text(code(z.s("code")), fontFamily = FontFamily.Monospace, fontWeight = FontWeight.SemiBold)
                        Text(listOf(z.s("name"), z.s("dauer"), z.s("vorlage")).filter { it.isNotEmpty() }.distinct().joinToString(" · "),
                            style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.onSurfaceVariant)
                    }
                    Marke(z.s("status"))
                }
                HorizontalDivider()
            }
            if (zeilen.isEmpty()) Text("Keine Voucher in dieser Ansicht.")
        }
    }
}

/** Voucher-Codes wie im Manager in zwei Fünfergruppen */
private fun code(c: String) = if (c.length == 10 && c.all { it.isDigit() }) c.substring(0, 5) + "-" + c.substring(5) else c

fun dauer(min: Int): String = when {
    min <= 0 -> "unbegrenzt"
    min % 1440 == 0 -> "${min / 1440} Tag(e)"
    min % 60 == 0 -> "${min / 60} Stunde(n)"
    else -> "$min Minuten"
}
