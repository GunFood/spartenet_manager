package de.spartenet.manager

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import de.spartenet.manager.data.Speicher
import de.spartenet.manager.ui.SparteNetTheme
import de.spartenet.manager.ui.Wurzel

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()
        val speicher = Speicher(this)
        setContent {
            var ansicht by remember { mutableStateOf(speicher.ansicht) }
            SparteNetTheme(ansicht) {
                Wurzel(speicher, ansicht) { neu ->
                    speicher.ansicht = neu
                    ansicht = neu
                }
            }
        }
    }
}
