package com.faro.mobile.presentation.theme

import android.app.Activity
import android.os.Build
import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.runtime.SideEffect
import androidx.compose.ui.graphics.toArgb
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.platform.LocalView
import androidx.core.view.WindowCompat

// F.A.R.O. Color Scheme
private val FaroBlue = androidx.compose.ui.graphics.Color(0xFF0033A0)
private val FaroBlueDark = androidx.compose.ui.graphics.Color(0xFF002266)
private val FaroGold = androidx.compose.ui.graphics.Color(0xFFFFD700)

private val DarkColorScheme = darkColorScheme(
    primary = FaroBlue,
    onPrimary = androidx.compose.ui.graphics.Color.White,
    primaryContainer = FaroBlueDark,
    onPrimaryContainer = androidx.compose.ui.graphics.Color.White,
    secondary = FaroGold,
    onSecondary = androidx.compose.ui.graphics.Color.Black,
    secondaryContainer = FaroGold.copy(alpha = 0.2f),
    onSecondaryContainer = FaroGold,
)

private val LightColorScheme = lightColorScheme(
    primary = FaroBlue,
    onPrimary = androidx.compose.ui.graphics.Color.White,
    primaryContainer = FaroBlue.copy(alpha = 0.1f),
    onPrimaryContainer = FaroBlue,
    secondary = FaroGold,
    onSecondary = androidx.compose.ui.graphics.Color.Black,
    secondaryContainer = FaroGold.copy(alpha = 0.2f),
    onSecondaryContainer = FaroBlueDark,
)

@Composable
fun FAROTheme(
    darkTheme: Boolean = isSystemInDarkTheme(),
    dynamicColor: Boolean = false,
    content: @Composable () -> Unit
) {
    val colorScheme = when {
        dynamicColor && Build.VERSION.SDK_INT >= Build.VERSION_CODES.S -> {
            val context = LocalContext.current
            if (darkTheme) dynamicDarkColorScheme(context) else dynamicLightColorScheme(context)
        }
        darkTheme -> DarkColorScheme
        else -> LightColorScheme
    }
    val view = LocalView.current
    if (!view.isInEditMode) {
        SideEffect {
            val window = (view.context as Activity).window
            window.statusBarColor = colorScheme.primary.toArgb()
            WindowCompat.getInsetsController(window, view).isAppearanceLightStatusBars = false
        }
    }

    MaterialTheme(
        colorScheme = colorScheme,
        typography = Typography,
        content = content
    )
}
