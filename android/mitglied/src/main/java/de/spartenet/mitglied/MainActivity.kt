package de.spartenet.mitglied

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import de.spartenet.mitglied.data.Speicher
import de.spartenet.mitglied.ui.Anmeldung
import de.spartenet.mitglied.ui.MitgliedTheme
import de.spartenet.mitglied.ui.Uebersicht

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()
        val speicher = Speicher(this)
        setContent {
            var ansicht by remember { mutableStateOf(speicher.ansicht) }
            MitgliedTheme(ansicht) {
                var token by remember { mutableStateOf(speicher.token) }
                val t = token
                if (t == null) {
                    Anmeldung(speicher) { neu ->
                        speicher.token = neu
                        token = neu
                    }
                } else {
                    Uebersicht(speicher, t, ansicht, onAnsicht = { neu -> speicher.ansicht = neu; ansicht = neu }) {
                        speicher.token = null
                        token = null
                    }
                }
            }
        }
    }
}
