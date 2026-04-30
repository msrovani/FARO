package com.faro.mobile.presentation

import android.content.Intent
import android.os.Bundle
import com.faro.mobile.data.service.TacticalMonitoringService
import java.time.Instant
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.animation.*
import androidx.compose.animation.core.*
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.rememberNavController
import com.faro.mobile.data.websocket.WebSocketManager
import com.faro.mobile.presentation.screens.ApproachFormScreen
import com.faro.mobile.presentation.screens.HistoryScreen
import com.faro.mobile.presentation.screens.HomeScreen
import com.faro.mobile.presentation.screens.LoginScreen
import com.faro.mobile.presentation.screens.PlateCaptureScreen
import com.faro.mobile.presentation.theme.FAROTheme
import com.faro.mobile.presentation.viewmodel.AuthViewModel
import com.faro.mobile.presentation.viewmodel.HomeViewModel
import dagger.hilt.android.AndroidEntryPoint

@AndroidEntryPoint
class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()
        setContent {
            FAROTheme {
                Surface(
                    modifier = Modifier.fillMaxSize(),
                    color = MaterialTheme.colorScheme.background
                ) {
                    FARONavigation()
                }
            }
        }
    }
}

@Composable
fun FARONavigation() {
    val navController = rememberNavController()
    val authViewModel: AuthViewModel = hiltViewModel()
    val homeViewModel: HomeViewModel = hiltViewModel()

    val authSession by authViewModel.sessionState.collectAsStateWithLifecycle()
    val savedProfiles by authViewModel.profilesState.collectAsStateWithLifecycle()
    val loginState by authViewModel.uiState.collectAsStateWithLifecycle()
    val pendingSync by homeViewModel.pendingSyncCount.collectAsStateWithLifecycle()
    val unreadFeedback by homeViewModel.unreadFeedbackCount.collectAsStateWithLifecycle()
    val showShiftRenewal by homeViewModel.showShiftRenewal.collectAsStateWithLifecycle()
    val minutesRemaining by homeViewModel.minutesRemaining.collectAsStateWithLifecycle()

    // 🚨 Critical Alert Overlay State
    val webSocketManager = hiltViewModel<com.faro.mobile.presentation.viewmodel.WebSocketViewModel>().webSocketManager
    val immediateAlert by webSocketManager.immediateAlerts.collectAsState(initial = null)
    var activeAlert by remember { mutableStateOf<WebSocketManager.PushNotification?>(null) }
    
    LaunchedEffect(immediateAlert) {
        if (immediateAlert != null) {
            activeAlert = immediateAlert
        }
    }

    val startDestination = if (authSession.isAuthenticated) "home" else "login"

    LaunchedEffect(authSession.isAuthenticated, authSession.serviceExpiresAt) {
        val currentRoute = navController.currentDestination?.route
        
        // 1. Navigation Logic
        if (authSession.isAuthenticated && currentRoute == "login") {
            navController.navigate("home") {
                popUpTo("login") { inclusive = true }
            }
        } else if (!authSession.isAuthenticated && currentRoute != "login") {
            navController.navigate("login") {
                popUpTo(navController.graph.id) { inclusive = true }
            }
        }

        // 2. Tactical Service Lifecycle
        val context = navController.context
        val expiresAt = authSession.serviceExpiresAt?.let { 
            try { Instant.parse(it) } catch (e: java.time.format.DateTimeParseException) { null } 
        }
        val isOnDuty = authSession.isAuthenticated && expiresAt != null && Instant.now().isBefore(expiresAt)

        if (isOnDuty) {
            val serviceIntent = Intent(context, TacticalMonitoringService::class.java)
            context.startForegroundService(serviceIntent)
        } else {
            val serviceIntent = Intent(context, TacticalMonitoringService::class.java)
            context.stopService(serviceIntent)
        }
    }

    Box(modifier = Modifier.fillMaxSize()) {
        NavHost(
            navController = navController,
            startDestination = startDestination
        ) {
            composable("login") {
                LoginScreen(
                    uiState = loginState,
                    savedProfiles = savedProfiles,
                    onLogin = { email, password, duration ->
                        authViewModel.login(email, password, duration) {
                            navController.navigate("home") {
                                popUpTo("login") { inclusive = true }
                            }
                        }
                    },
                    onUseSavedProfile = { profileUserId ->
                        authViewModel.switchProfile(
                            userId = profileUserId,
                            onSuccess = {
                                navController.navigate("home") {
                                    popUpTo("login") { inclusive = true }
                                }
                            },
                            onFailure = { /* erro já refletido no estado de login */ }
                        )
                    },
                )
            }
            composable("home") {
                HomeScreen(
                    onRegisterVehicle = { navController.navigate("capture") },
                    onViewHistory = { navController.navigate("history") },
                    onViewFeedback = { navController.navigate("history") },
                    pendingSync = pendingSync,
                    unreadFeedback = unreadFeedback,
                    operatorName = authSession.userName.ifBlank { "Operador" },
                    agencyName = authSession.userAgencyName,
                    unitName = authSession.userUnitName,
                    onLogout = {
                        authViewModel.logout {
                            navController.navigate("login") {
                                popUpTo(navController.graph.id) { inclusive = true }
                            }
                        }
                    },
                    showShiftRenewal = showShiftRenewal,
                    minutesRemaining = minutesRemaining,
                    onRenewShift = { hours -> homeViewModel.renewShift(hours) },
                    onDismissRenewal = { homeViewModel.dismissRenewal() }
                )
            }
            composable("capture") {
                PlateCaptureScreen(
                    onCaptureComplete = { navController.popBackStack() },
                    onCancel = { navController.popBackStack() }
                )
            }
            composable("history") {
                HistoryScreen(
                    onBack = { navController.popBackStack() }
                )
            }
            composable("approach/{observationId}/{plateNumber}") { backStackEntry ->
                val observationId = backStackEntry.arguments?.getString("observationId") ?: ""
                val plateNumber = backStackEntry.arguments?.getString("plateNumber") ?: ""
                ApproachFormScreen(
                    plateNumber = plateNumber,
                    suspicionData = null,
                    observationId = observationId,
                    onSubmit = { confirmedSuspicion, suspicionLevel, wasApproached, hasIncident, notes ->
                        navController.popBackStack()
                    },
                    onCancel = { navController.popBackStack() }
                )
            }
        }

        // 🚨 Critical Alert Overlay
        AnimatedVisibility(
            visible = activeAlert != null,
            enter = fadeIn() + slideInVertically(),
            exit = fadeOut() + slideOutVertically()
        ) {
            activeAlert?.let { alert ->
                CriticalAlertOverlay(
                    notification = alert,
                    onDismiss = { activeAlert = null }
                )
            }
        }
    }
}

@Composable
fun CriticalAlertOverlay(
    notification: WebSocketManager.PushNotification,
    onDismiss: () -> Unit
) {
    Box(
        modifier = Modifier
            .fillMaxSize()
            .background(Color.Black.copy(alpha = 0.7f))
            .padding(24.dp),
        contentAlignment = Alignment.Center
    ) {
        Card(
            colors = CardDefaults.cardColors(
                containerColor = Color(0xFFB00020), // Deep red for critical
                contentColor = Color.White
            ),
            elevation = CardDefaults.cardElevation(defaultElevation = 12.dp),
            modifier = Modifier.fillMaxWidth()
        ) {
            Column(
                modifier = Modifier.padding(24.dp),
                horizontalAlignment = Alignment.CenterHorizontally
            ) {
                Text(
                    text = "🚨 ALERTA CRÍTICO 🚨",
                    fontSize = 24.sp,
                    fontWeight = FontWeight.Bold,
                    textAlign = TextAlign.Center
                )
                Spacer(modifier = Modifier.height(16.dp))
                Text(
                    text = notification.title,
                    fontSize = 20.sp,
                    fontWeight = FontWeight.SemiBold,
                    textAlign = TextAlign.Center
                )
                Spacer(modifier = Modifier.height(8.dp))
                Text(
                    text = notification.message,
                    fontSize = 16.sp,
                    textAlign = TextAlign.Center
                )
                Spacer(modifier = Modifier.height(24.dp))
                Button(
                    onClick = onDismiss,
                    colors = ButtonDefaults.buttonColors(
                        containerColor = Color.White,
                        contentColor = Color(0xFFB00020)
                    ),
                    modifier = Modifier.fillMaxWidth()
                ) {
                    Text("CIENTE", fontWeight = FontWeight.Bold)
                }
            }
        }
    }
}
