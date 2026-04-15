package com.faro.mobile.presentation

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.ui.Modifier
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.rememberNavController
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

    val startDestination = if (authSession.isAuthenticated) "home" else "login"

    LaunchedEffect(authSession.isAuthenticated) {
        val currentRoute = navController.currentDestination?.route
        if (authSession.isAuthenticated && currentRoute == "login") {
            navController.navigate("home") {
                popUpTo("login") { inclusive = true }
            }
        } else if (!authSession.isAuthenticated && currentRoute != "login") {
            navController.navigate("login") {
                popUpTo(navController.graph.id) { inclusive = true }
            }
        }
    }

    NavHost(
        navController = navController,
        startDestination = startDestination
    ) {
        composable("login") {
            LoginScreen(
                uiState = loginState,
                savedProfiles = savedProfiles,
                onLogin = { email, password ->
                    authViewModel.login(email, password) {
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
                suspicionData = null, // Would be passed via ViewModel in real implementation
                observationId = observationId,
                onSubmit = { confirmedSuspicion, suspicionLevel, wasApproached, hasIncident, notes ->
                    // Submit approach confirmation
                    navController.popBackStack()
                },
                onCancel = { navController.popBackStack() }
            )
        }
    }
}
