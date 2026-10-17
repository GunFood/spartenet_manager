package de.spartenet.manager.ui

import android.os.Build
import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.darkColorScheme
import androidx.compose.material3.dynamicDarkColorScheme
import androidx.compose.material3.dynamicLightColorScheme
import androidx.compose.material3.lightColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext

private val Hell = lightColorScheme(
    primary = Color(0xFF2E7D32),
    onPrimary = Color.White,
    primaryContainer = Color(0xFFB9F0B4),
    onPrimaryContainer = Color(0xFF002204),
    secondary = Color(0xFF52634F),
    secondaryContainer = Color(0xFFD5E8CF),
    tertiary = Color(0xFF38656A),
    error = Color(0xFFBA1A1A),
    background = Color(0xFFF7FBF2),
    surface = Color(0xFFF7FBF2),
)

private val Dunkel = darkColorScheme(
    primary = Color(0xFF9DD49A),
    onPrimary = Color(0xFF00390C),
    primaryContainer = Color(0xFF145218),
    onPrimaryContainer = Color(0xFFB9F0B4),
    secondary = Color(0xFFB9CCB4),
    secondaryContainer = Color(0xFF3B4B38),
    tertiary = Color(0xFFA0CFD4),
    error = Color(0xFFFFB4AB),
    background = Color(0xFF10140F),
    surface = Color(0xFF10140F),
)

/** ansicht: "system", "hell" oder "dunkel" – wie im Manager */
@Composable
fun SparteNetTheme(ansicht: String, inhalt: @Composable () -> Unit) {
    val dunkel = when (ansicht) {
        "hell" -> false
        "dunkel" -> true
        else -> isSystemInDarkTheme()
    }
    val ctx = LocalContext.current
    val farben = when {
        Build.VERSION.SDK_INT >= Build.VERSION_CODES.S -> if (dunkel) dynamicDarkColorScheme(ctx) else dynamicLightColorScheme(ctx)
        dunkel -> Dunkel
        else -> Hell
    }
    MaterialTheme(colorScheme = farben, content = inhalt)
}
