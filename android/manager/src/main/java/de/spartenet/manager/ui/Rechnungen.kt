package de.spartenet.manager.ui

import android.content.ActivityNotFoundException
import android.content.Context
import android.content.Intent
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.PictureAsPdf
import androidx.compose.material.icons.filled.Refresh
import androidx.compose.material3.FilterChip
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.ListItem
import androidx.compose.material3.MaterialTheme
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
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.core.content.FileProvider
import de.spartenet.manager.data.Datei
import de.spartenet.manager.data.d
import de.spartenet.manager.data.geld
import de.spartenet.manager.data.liste
import de.spartenet.manager.data.o
import de.spartenet.manager.data.s
import de.spartenet.manager.data.texte
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import java.io.File

private val R_FILTER = listOf("" to "Alle", "offen" to "Offen", "teilweise" to "Teilweise", "bezahlt" to "Bezahlt", "storniert" to "Storniert")

@Composable
fun RechnungenSeite(s: Sitzung) {
    var jahr by rememberSaveable { mutableStateOf("") }
    var status by rememberSaveable { mutableStateOf("offen") }
    var arbeitet by remember { mutableStateOf(false) }
    val scope = rememberCoroutineScope()
    val ctx = LocalContext.current
    val l = rememberLaden(s, jahr, status) {
        s.api.get("/api/rechnungen", buildMap { if (jahr.isNotEmpty()) put("jahr", jahr); if (status.isNotEmpty()) put("status", status) })
    }

    Column(Modifier.fillMaxSize()) {
        Kopf("Rechnungen", l.daten?.texte("log")?.firstOrNull()) {
            IconButton(onClick = { l.laden() }) { Icon(Icons.Filled.Refresh, "Aktualisieren") }
        }
        Row(Modifier.fillMaxWidth().horizontalScrollRow().padding(horizontal = 12.dp), horizontalArrangement = Arrangement.spacedBy(8.dp)) {
            R_FILTER.forEach { (k, t) -> FilterChip(selected = status == k, onClick = { status = k }, label = { Text(t) }) }
        }
        val jahre = l.daten?.texte("jahre") ?: emptyList()
        if (jahre.isNotEmpty()) {
            Row(Modifier.fillMaxWidth().horizontalScrollRow().padding(horizontal = 12.dp), horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                FilterChip(selected = jahr.isEmpty(), onClick = { jahr = "" }, label = { Text("alle Jahre") })
                jahre.forEach { j -> FilterChip(selected = jahr == j, onClick = { jahr = j }, label = { Text(j) }) }
            }
        }
        Laden(l) { a ->
            val sum = a.o("summe")
            val zeilen = a.liste("zeilen")
            Column(Modifier.fillMaxSize()) {
                Row(Modifier.fillMaxWidth().padding(horizontal = 16.dp, vertical = 8.dp), horizontalArrangement = Arrangement.spacedBy(16.dp)) {
                    Text("Summe ${geld(sum.d("brutto"))}")
                    Text("bezahlt ${geld(sum.d("bezahlt"))}", color = MaterialTheme.colorScheme.primary)
                    Text("offen ${geld(sum.d("offen"))}", color = if (sum.d("offen") > 0) MaterialTheme.colorScheme.error else MaterialTheme.colorScheme.onSurface)
                }
                if (zeilen.isEmpty()) Leer("Keine Rechnungen in dieser Ansicht.")
                else LazyColumn(Modifier.fillMaxSize()) {
                    items(zeilen, key = { it.s("id") }) { z ->
                        ListItem(
                            overlineContent = { Text("${z.s("nr")} · ${z.s("datum")} · fällig ${z.s("faellig")}") },
                            headlineContent = { Text(z.s("name").ifEmpty { "–" }) },
                            supportingContent = {
                                Text(listOf("${z.s("sparte")} ${z.s("parzelle")}".trim(), z.s("tarif"), if (z.s("versendet").isNotEmpty()) "versendet" else "")
                                    .filter { it.isNotEmpty() }.joinToString(" · "))
                            },
                            trailingContent = {
                                Row(verticalAlignment = Alignment.CenterVertically) {
                                    Column(horizontalAlignment = Alignment.End) {
                                        Text(geld(z.d("brutto")), fontWeight = FontWeight.SemiBold)
                                        Marke(statusRechnung(z.s("status")))
                                    }
                                    IconButton(enabled = !arbeitet, onClick = {
                                        s.ausfuehren(scope, { arbeitet = it }) {
                                            val dat = s.api.datei("/api/rechnung-pdf", mapOf("id" to z.s("id")))
                                            pdfOeffnen(ctx, dat, "Rechnung_${z.s("nr")}.pdf")
                                        }
                                    }) { Icon(Icons.Filled.PictureAsPdf, "PDF öffnen") }
                                }
                            },
                        )
                        HorizontalDivider()
                    }
                }
            }
        }
    }
}

private fun statusRechnung(st: String) = when (st) {
    "teilweise" -> "teilweise bezahlt"; else -> st
}

/** PDF im Cache ablegen und mit einer PDF-App öffnen (ohne Speicher-Berechtigung) */
suspend fun pdfOeffnen(ctx: Context, dat: Datei, name: String) {
    val sicher = name.replace(Regex("[^A-Za-z0-9._-]"), "_")
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
        ctx.startActivity(Intent.createChooser(teilen, name))
    }
}
