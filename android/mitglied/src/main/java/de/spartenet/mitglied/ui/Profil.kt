package de.spartenet.mitglied.ui

import android.Manifest
import android.appwidget.AppWidgetManager
import android.content.ComponentName
import android.os.Build
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.clickable
import androidx.compose.material3.Checkbox
import androidx.compose.material3.Switch
import androidx.compose.ui.platform.LocalContext
import de.spartenet.mitglied.data.Speicher
import de.spartenet.mitglied.hintergrund.GeraeteWidget
import de.spartenet.mitglied.hintergrund.Hintergrund
import de.spartenet.mitglied.hintergrund.Meldungen
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.widthIn
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Delete
import androidx.compose.material.icons.filled.Lock
import androidx.compose.material.icons.filled.PersonAdd
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.Button
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.SegmentedButton
import androidx.compose.material3.SegmentedButtonDefaults
import androidx.compose.material3.SingleChoiceSegmentedButtonRow
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.KeyboardCapitalization
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.unit.dp
import de.spartenet.mitglied.data.Api
import de.spartenet.mitglied.data.b
import de.spartenet.mitglied.data.liste
import de.spartenet.mitglied.data.s
import de.spartenet.mitglied.data.texte
import org.json.JSONObject

/**
 * Profil: Vorname, Nachname und Parzelle sind gesperrt (ändert nur der Verein).
 * Änderbar: Mobilnummer, Telefon und E-Mail – eine neue E-Mail-Adresse gilt erst nach dem Code, der an sie geschickt wird.
 */
@Composable
fun ProfilKarte(
    api: Api, profil: JSONObject, erlaubt: JSONObject, aktion: (suspend () -> Unit) -> Unit, melden: (String) -> Unit,
    onEmail: (String) -> Unit, onGespeichert: () -> Unit,
) {
    val darf = erlaubt.b("profil")
    var mobil by remember(profil.toString()) { mutableStateOf(profil.s("mobil")) }
    var telefon by remember(profil.toString()) { mutableStateOf(profil.s("telefon")) }
    var email by remember(profil.toString()) { mutableStateOf(profil.s("email")) }
    var codeFragen by remember { mutableStateOf(false) }
    Karte("Mein Profil") {
        Gesperrt("Vorname", profil.s("vorname"))
        Gesperrt("Nachname", profil.s("nachname"))
        Gesperrt("Parzelle", profil.texte("parzellen").joinToString("\n"))
        HorizontalDivider(Modifier.padding(vertical = 4.dp))
        OutlinedTextField(
            mobil, { mobil = it.take(30) }, Modifier.fillMaxWidth(), label = { Text("Rufnummer (Mobil)") }, singleLine = true, enabled = darf,
            keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Phone),
        )
        OutlinedTextField(
            telefon, { telefon = it.take(30) }, Modifier.fillMaxWidth(), label = { Text("Telefon") }, singleLine = true, enabled = darf,
            keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Phone),
        )
        OutlinedTextField(
            email, { email = it.take(200) }, Modifier.fillMaxWidth(), label = { Text("E-Mail-Adresse") }, singleLine = true, enabled = darf,
            keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Email),
            supportingText = { Text("Eine neue Adresse bestätigen Sie mit einem Code, der an sie geschickt wird.") },
        )
        if (darf) {
            Button(onClick = {
                aktion {
                    val b = JSONObject().put("mobil", mobil.trim()).put("telefon", telefon.trim())
                    if (email.trim().lowercase() != profil.s("email").lowercase()) b.put("email", email.trim())
                    val r = api.post("/mein/profil", b)
                    melden(r.s("text"))
                    if (r.b("bestaetigen")) codeFragen = true else onGespeichert()
                }
            }) { Text("Speichern") }
        } else {
            Text("Änderungen bitte beim Verein melden.", style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.onSurfaceVariant)
        }
    }
    if (codeFragen) {
        CodeDialog(onAbbrechen = { codeFragen = false }) { code ->
            aktion {
                val r = api.post("/mein/profil_bestaetigen", JSONObject().put("code", code))
                codeFragen = false
                melden(r.s("text"))
                onEmail(r.s("email"))
            }
        }
    }
}

@Composable
private fun Gesperrt(beschriftung: String, wert: String) {
    Row(verticalAlignment = Alignment.CenterVertically) {
        Column(Modifier.weight(1f)) {
            Text(beschriftung, style = MaterialTheme.typography.labelMedium, color = MaterialTheme.colorScheme.onSurfaceVariant)
            Text(wert.ifEmpty { "–" }, style = MaterialTheme.typography.bodyLarge)
        }
        Icon(Icons.Filled.Lock, "nur vom Verein änderbar", tint = MaterialTheme.colorScheme.onSurfaceVariant)
    }
}

@Composable
private fun CodeDialog(onAbbrechen: () -> Unit, onBestaetigen: (String) -> Unit) {
    var code by remember { mutableStateOf("") }
    AlertDialog(
        onDismissRequest = onAbbrechen,
        title = { Text("Neue E-Mail-Adresse bestätigen") },
        text = {
            Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                Text("Geben Sie den 6-stelligen Code ein, den wir an die neue Adresse geschickt haben.")
                OutlinedTextField(
                    code, { code = it.filter(Char::isDigit).take(6) }, Modifier.fillMaxWidth(), label = { Text("Code") }, singleLine = true,
                    keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.NumberPassword),
                )
            }
        },
        confirmButton = { TextButton(onClick = { onBestaetigen(code) }, enabled = code.length == 6) { Text("Bestätigen") } },
        dismissButton = { TextButton(onClick = onAbbrechen) { Text("Abbrechen") } },
    )
}

/** Personen der Parzelle – der Pächter kann weitere Personen (Mitpächter, Partner …) anlegen und entfernen */
@Composable
fun PersonenKarte(api: Api, p: JSONObject, erlaubt: JSONObject, aktion: (suspend () -> Unit) -> Unit, melden: (String) -> Unit, onGeaendert: () -> Unit) {
    val darf = erlaubt.b("personen") && p.b("haupt")
    var neu by remember { mutableStateOf(false) }
    var entfernen by remember { mutableStateOf<JSONObject?>(null) }
    Karte("Personen der Parzelle ${p.s("parzelle")}") {
        p.liste("personen").forEachIndexed { n, x ->
            if (n > 0) HorizontalDivider()
            Row(Modifier.fillMaxWidth().padding(vertical = 4.dp), verticalAlignment = Alignment.CenterVertically) {
                Column(Modifier.weight(1f)) {
                    Text("${x.s("vorname")} ${x.s("nachname")}".trim(), fontWeight = FontWeight.Medium)
                    Text(
                        listOf(if (x.b("haupt")) "Pächter" else "weitere Person", x.s("email")).filter { it.isNotEmpty() }.joinToString(" · "),
                        style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.onSurfaceVariant,
                    )
                }
                if (darf && !x.b("haupt")) IconButton(onClick = { entfernen = x }) { Icon(Icons.Filled.Delete, "Person entfernen") }
            }
        }
        if (darf) {
            OutlinedButton(onClick = { neu = true }) {
                Icon(Icons.Filled.PersonAdd, null)
                Text("Neues Mitglied in der Parzelle anlegen", Modifier.padding(start = 6.dp))
            }
        } else if (erlaubt.b("personen")) {
            Text("Weitere Personen kann der Pächter der Parzelle anlegen.", style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.onSurfaceVariant)
        }
    }
    if (neu) {
        PersonDialog(onAbbrechen = { neu = false }) { b ->
            aktion {
                val r = api.post("/mein/person_neu", b.put("id", p.s("id")))
                neu = false
                melden(r.s("text"))
                onGeaendert()
            }
        }
    }
    entfernen?.let { x ->
        AlertDialog(
            onDismissRequest = { entfernen = null },
            title = { Text("Person entfernen?") },
            text = { Text("${x.s("vorname")} ${x.s("nachname")} hat danach keinen Zugang mehr zum Mitgliederbereich dieser Parzelle.") },
            confirmButton = {
                TextButton(onClick = {
                    entfernen = null
                    aktion {
                        melden(api.post("/mein/person_entfernen", JSONObject().put("id", p.s("id")).put("email", x.s("email"))).s("text"))
                        onGeaendert()
                    }
                }) { Text("Entfernen") }
            },
            dismissButton = { TextButton(onClick = { entfernen = null }) { Text("Abbrechen") } },
        )
    }
}

@Composable
private fun PersonDialog(onAbbrechen: () -> Unit, onAnlegen: (JSONObject) -> Unit) {
    var vorname by remember { mutableStateOf("") }
    var nachname by remember { mutableStateOf("") }
    var email by remember { mutableStateOf("") }
    var mobil by remember { mutableStateOf("") }
    var telefon by remember { mutableStateOf("") }
    val ok = vorname.isNotBlank() && nachname.isNotBlank() && Regex("^[^@\\s]+@[^@\\s]+\\.[A-Za-z]{2,}$").matches(email.trim())
    AlertDialog(
        onDismissRequest = onAbbrechen,
        title = { Text("Neues Mitglied in der Parzelle") },
        text = {
            Column(Modifier.widthIn(min = 280.dp), verticalArrangement = Arrangement.spacedBy(6.dp)) {
                Text("Die Person meldet sich mit ihrer E-Mail-Adresse und einem Einmalcode an und bekommt eine Info per E-Mail.",
                    style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.onSurfaceVariant)
                val cap = KeyboardOptions(capitalization = KeyboardCapitalization.Words)
                OutlinedTextField(vorname, { vorname = it.take(120) }, Modifier.fillMaxWidth(), label = { Text("Vorname") }, singleLine = true, keyboardOptions = cap)
                OutlinedTextField(nachname, { nachname = it.take(120) }, Modifier.fillMaxWidth(), label = { Text("Nachname") }, singleLine = true, keyboardOptions = cap)
                OutlinedTextField(email, { email = it.take(200) }, Modifier.fillMaxWidth(), label = { Text("E-Mail-Adresse") }, singleLine = true,
                    keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Email))
                OutlinedTextField(mobil, { mobil = it.take(30) }, Modifier.fillMaxWidth(), label = { Text("Rufnummer (Mobil, optional)") }, singleLine = true,
                    keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Phone))
                OutlinedTextField(telefon, { telefon = it.take(30) }, Modifier.fillMaxWidth(), label = { Text("Telefon (optional)") }, singleLine = true,
                    keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Phone))
            }
        },
        confirmButton = {
            TextButton(onClick = {
                onAnlegen(JSONObject().put("vorname", vorname.trim()).put("nachname", nachname.trim()).put("email", email.trim())
                    .put("mobil", mobil.trim()).put("telefon", telefon.trim()))
            }, enabled = ok) { Text("Anlegen") }
        },
        dismissButton = { TextButton(onClick = onAbbrechen) { Text("Abbrechen") } },
    )
}

/** Ansicht wählen – mit den Symbolen aus dem Manager: ◐ System, ☀ Hell, ☾ Dunkel */
@Composable
fun AnsichtKarte(ansicht: String, onAnsicht: (String) -> Unit) {
    Karte("Ansicht") {
        SingleChoiceSegmentedButtonRow(Modifier.fillMaxWidth()) {
            ANSICHTEN.forEachIndexed { i, (k, symbol, text) ->
                SegmentedButton(selected = ansicht == k, onClick = { onAnsicht(k) }, shape = SegmentedButtonDefaults.itemShape(i, ANSICHTEN.size)) {
                    Text("$symbol $text")
                }
            }
        }
    }
}

/**
 * Benachrichtigungen auf dem Handy: ein/aus, welche Arten, wie oft nachgesehen wird; Android 13+ fragt einmal nach der Erlaubnis.
 * Die App sieht selbst beim Manager nach (kein Firebase) – Meldungen kommen daher mit bis zu der eingestellten Verzögerung.
 */
@Composable
fun BenachrichtigungKarte(speicher: Speicher, melden: (String) -> Unit) {
    val ctx = LocalContext.current
    var an by remember { mutableStateOf(speicher.meldungenAn && Meldungen.erlaubt(ctx)) }
    var arten by remember { mutableStateOf(speicher.meldungArten) }
    var intervall by remember { mutableStateOf(speicher.intervall) }
    fun einschalten(wert: Boolean) {
        an = wert
        speicher.meldungenAn = wert
        Hintergrund.planen(ctx)
        if (wert) {
            Meldungen.kanalAnlegen(ctx)
            Hintergrund.jetzt(ctx)
        }
    }
    val erlaubnis = rememberLauncherForActivityResult(ActivityResultContracts.RequestPermission()) { ok ->
        if (ok) einschalten(true) else melden("Ohne Erlaubnis kann die App keine Benachrichtigungen zeigen (Android-Einstellungen → Apps → SparteNet Mitglied).")
    }
    Karte("Benachrichtigungen") {
        Row(verticalAlignment = Alignment.CenterVertically) {
            Text("Benachrichtigungen auf diesem Handy", Modifier.weight(1f))
            Switch(checked = an, onCheckedChange = { neu ->
                if (neu && Build.VERSION.SDK_INT >= 33 && !Meldungen.erlaubt(ctx)) erlaubnis.launch(Manifest.permission.POST_NOTIFICATIONS) else einschalten(neu)
            })
        }
        if (an) {
            Speicher.MELDUNG_ARTEN.forEach { (k, text) ->
                Row(Modifier.fillMaxWidth().clickable {
                    arten = if (k in arten) arten - k else arten + k
                    speicher.meldungArten = arten
                }, verticalAlignment = Alignment.CenterVertically) {
                    Checkbox(checked = k in arten, onCheckedChange = { c ->
                        arten = if (c) arten + k else arten - k
                        speicher.meldungArten = arten
                    })
                    Text(text)
                }
            }
            Text("Nachsehen alle", style = MaterialTheme.typography.labelLarge)
            SingleChoiceSegmentedButtonRow(Modifier.fillMaxWidth()) {
                val wahl = listOf(15, 30, 60)
                wahl.forEachIndexed { i, m ->
                    SegmentedButton(selected = intervall == m, onClick = {
                        intervall = m
                        speicher.intervall = m
                        Hintergrund.planen(ctx)
                    }, shape = SegmentedButtonDefaults.itemShape(i, wahl.size)) { Text("$m Min.") }
                }
            }
            Text(
                "Die App sieht in diesem Abstand beim Verein nach und meldet nur Neues. Android kann das bei Energiesparen etwas verzögern.",
                style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.onSurfaceVariant,
            )
            OutlinedButton(onClick = {
                Meldungen.senden(ctx, "test", "SparteNet Mitglied", "So sehen Benachrichtigungen aus. ✔")
            }) { Text("Test-Benachrichtigung") }
        }
    }
}

/** Widget „Meine Geräte“ auf den Startbildschirm legen */
@Composable
fun WidgetKarte() {
    val ctx = LocalContext.current
    Karte("Widget „Meine Geräte“") {
        Text(
            "Zeigt auf dem Startbildschirm Ihren Tarif mit „x von y Geräten“ und die Geräte im WLAN der Parzelle – aktualisiert sich von selbst.",
            style = MaterialTheme.typography.bodyMedium,
        )
        val am = AppWidgetManager.getInstance(ctx)
        if (am.isRequestPinAppWidgetSupported) {
            Button(onClick = { am.requestPinAppWidget(ComponentName(ctx, GeraeteWidget::class.java), null, null) }) { Text("Widget hinzufügen") }
        } else {
            Text(
                "Lange auf eine freie Stelle des Startbildschirms tippen → „Widgets“ → „SparteNet Mitglied“ → „Meine Geräte“.",
                style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.onSurfaceVariant,
            )
        }
    }
}
