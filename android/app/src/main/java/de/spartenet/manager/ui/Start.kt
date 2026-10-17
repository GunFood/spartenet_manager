package de.spartenet.manager.ui

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.FlowRow
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.widthIn
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Add
import androidx.compose.material.icons.filled.Refresh
import androidx.compose.material3.AssistChip
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import de.spartenet.manager.data.d
import de.spartenet.manager.data.i
import de.spartenet.manager.data.o
import de.spartenet.manager.data.s
import de.spartenet.manager.data.texte
import de.spartenet.manager.data.geld

@Composable
fun Kopf(titel: String, unter: String? = null, aktionen: @Composable () -> Unit = {}) {
    Row(Modifier.fillMaxWidth().padding(start = 16.dp, end = 4.dp, top = 8.dp, bottom = 4.dp), verticalAlignment = Alignment.CenterVertically) {
        Column(Modifier.weight(1f)) {
            Text(titel, style = MaterialTheme.typography.headlineSmall, fontWeight = FontWeight.SemiBold)
            if (!unter.isNullOrEmpty()) Text(unter, style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.onSurfaceVariant)
        }
        aktionen()
    }
}

@Composable
private fun Zahl(wert: String, text: String) {
    Column {
        Text(wert, style = MaterialTheme.typography.headlineMedium, fontWeight = FontWeight.Bold)
        Text(text, style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.onSurfaceVariant)
    }
}

@Composable
fun StartSeite(s: Sitzung, erlaubt: List<Bereich>, breit: Boolean, gehe: (Bereich, String?) -> Unit) {
    val l = rememberLaden(s, s) { s.api.get("/api/app-uebersicht") }
    Column(Modifier.fillMaxSize()) {
        Kopf("Hallo ${s.name}", "SparteNet Manager ${s.version}") {
            IconButton(onClick = { l.laden() }) { Icon(Icons.Filled.Refresh, "Aktualisieren") }
        }
        Laden(l) { u ->
            val kw = if (breit) Modifier.widthIn(min = 260.dp, max = 360.dp) else Modifier.fillMaxWidth()
            Column(Modifier.fillMaxSize().verticalScroll(rememberScrollState()).padding(12.dp), verticalArrangement = Arrangement.spacedBy(12.dp)) {
                FlowRow(horizontalArrangement = Arrangement.spacedBy(12.dp), verticalArrangement = Arrangement.spacedBy(12.dp)) {
                    if (u.has("tickets")) {
                        val t = u.o("tickets")
                        Kachel("Anfragen", kw, onClick = { gehe(Bereich.TICKETS, null) }) {
                            Row(horizontalArrangement = Arrangement.spacedBy(20.dp)) {
                                Zahl("${t.i("offen")}", "offen")
                                Zahl("${t.i("neu")}", "neu")
                                Zahl("${t.i("meine")}", "für mich")
                                Zahl("${t.i("dringend")}", "dringend/hoch")
                            }
                        }
                    }
                    if (u.has("stoerungen")) {
                        val st = u.o("stoerungen")
                        val off = st.texte("offline")
                        Kachel("Geräte", kw, onClick = if (Bereich.STOERUNGEN in erlaubt) ({ gehe(Bereich.STOERUNGEN, null) }) else null) {
                            Column {
                                if (off.isEmpty()) Text("✔ Alle überwachten Geräte erreichbar", color = MaterialTheme.colorScheme.primary)
                                else Text("⚠ ${off.size} Gerät(e) offline: ${off.joinToString(", ")}", color = MaterialTheme.colorScheme.error)
                                val lp = st.s("letzte_pruefung")
                                Text(if (lp.isEmpty()) "Noch keine Prüfung (Überwachung unter System einschalten)" else "Letzte Prüfung: $lp",
                                    style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.onSurfaceVariant)
                            }
                        }
                    }
                    if (u.has("buchungen") || u.has("mitglieder")) {
                        Kachel("Parzellen", kw, onClick = if (Bereich.BUCHUNGEN in erlaubt) ({ gehe(Bereich.BUCHUNGEN, null) }) else null) {
                            Row(horizontalArrangement = Arrangement.spacedBy(24.dp)) {
                                if (u.has("buchungen")) Zahl("${u.i("buchungen")}", "gebucht")
                                if (u.has("mitglieder")) Zahl("${u.i("mitglieder")}", "Mitglieder")
                            }
                        }
                    }
                    if (u.has("laufzeiten")) {
                        val lz = u.o("laufzeiten")
                        Kachel("Laufzeiten", kw, onClick = if (Bereich.LAUFZEITEN in erlaubt) ({ gehe(Bereich.LAUFZEITEN, null) }) else null) {
                            Row(horizontalArrangement = Arrangement.spacedBy(20.dp)) {
                                Zahl("${lz.i("aktiv")}", "laufend")
                                Zahl("${lz.i("bald")}", "enden in 24 h")
                                Zahl("${lz.i("abgelaufen")}", "abgelaufen")
                                if (lz.i("offen") > 0) Zahl("${lz.i("offen")}", "am Gateway offen")
                            }
                        }
                    }
                    if (u.has("rechnungen")) {
                        val r = u.o("rechnungen")
                        Kachel("Rechnungen", kw, onClick = { gehe(Bereich.RECHNUNGEN, null) }) {
                            Row(horizontalArrangement = Arrangement.spacedBy(20.dp)) {
                                Zahl("${r.i("offen")}", "offen")
                                Zahl(geld(r.d("offen_betrag")), "ausstehend")
                                Zahl("${r.i("ueberfaellig")}", "überfällig")
                            }
                        }
                    }
                }
                Text("Schnell", style = MaterialTheme.typography.titleSmall, modifier = Modifier.padding(top = 8.dp))
                FlowRow(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                    if (s.darf("tickets", "schreiben"))
                        AssistChip(onClick = { gehe(Bereich.TICKETS, "neu") }, label = { Text("Neue Anfrage") }, leadingIcon = { Icon(Icons.Filled.Add, null) })
                    if (s.darf("mitglieder", "schreiben"))
                        AssistChip(onClick = { gehe(Bereich.MITGLIEDER, "neu") }, label = { Text("Mitglied anlegen") }, leadingIcon = { Icon(Icons.Filled.Add, null) })
                    if (Bereich.PARZELLE in erlaubt)
                        AssistChip(onClick = { gehe(Bereich.PARZELLE, null) }, label = { Text("WLAN einer Parzelle") }, leadingIcon = { Icon(Bereich.PARZELLE.icon, null) })
                    if (s.darf("voucher", "schreiben"))
                        AssistChip(onClick = { gehe(Bereich.VOUCHER, null) }, label = { Text("Gast-Voucher") }, leadingIcon = { Icon(Bereich.VOUCHER.icon, null) })
                }
                Text("Stand ${u.s("zeit")}", style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.onSurfaceVariant)
            }
        }
    }
}
