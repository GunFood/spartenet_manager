package de.spartenet.mitglied.ui

import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.darkColorScheme
import androidx.compose.material3.lightColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.ui.graphics.Color

// Eigene Farbe (Blau wie die Kontakt-Seite), damit Mitglieder- und Manager-App nicht verwechselt werden
private val Hell = lightColorScheme(
    primary = Color(0xFF1F5FA8),
    onPrimary = Color.White,
    primaryContainer = Color(0xFFD5E3FF),
    onPrimaryContainer = Color(0xFF001B3C),
    secondary = Color(0xFF555F71),
    secondaryContainer = Color(0xFFD9E3F8),
    tertiary = Color(0xFF2E7D32),
    error = Color(0xFFBA1A1A),
    background = Color(0xFFF8F9FF),
    surface = Color(0xFFF8F9FF),
)

private val Dunkel = darkColorScheme(
    primary = Color(0xFFA7C8FF),
    onPrimary = Color(0xFF003062),
    primaryContainer = Color(0xFF0E4689),
    onPrimaryContainer = Color(0xFFD5E3FF),
    secondary = Color(0xFFBDC7DC),
    secondaryContainer = Color(0xFF3E4759),
    tertiary = Color(0xFF9DD49A),
    error = Color(0xFFFFB4AB),
    background = Color(0xFF111318),
    surface = Color(0xFF111318),
)

@Composable
fun MitgliedTheme(inhalt: @Composable () -> Unit) {
    MaterialTheme(colorScheme = if (isSystemInDarkTheme()) Dunkel else Hell, content = inhalt)
}
