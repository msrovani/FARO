package com.faro.mobile.presentation.screens

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyRow
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.text.input.PasswordVisualTransformation
import androidx.compose.ui.unit.dp
import com.faro.mobile.data.session.SessionProfile
import com.faro.mobile.presentation.viewmodel.LoginUiState

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun LoginScreen(
    uiState: LoginUiState,
    savedProfiles: List<SessionProfile>,
    onLogin: (identifier: String, password: String) -> Unit,
    onUseSavedProfile: (profileUserId: String) -> Unit,
) {
    var identifier by remember { mutableStateOf("") }
    var password by remember { mutableStateOf("") }
    
    // Helper to detect if identifier is CPF (11 digits) or email
    fun isCPF(value: String): Boolean {
        val digitsOnly = value.replace(".", "").replace("-", "").replace(" ", "")
        return digitsOnly.length == 11 && digitsOnly.all { it.isDigit() }
    }
    
    val labelText = if (isCPF(identifier)) "CPF" else "CPF ou E-mail"
    val isValidIdentifier = identifier.isNotBlank() && (isCPF(identifier) || identifier.contains("@"))

    Scaffold { padding ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(padding)
                .padding(32.dp),
            verticalArrangement = Arrangement.Center,
            horizontalAlignment = Alignment.CenterHorizontally
        ) {
            // Logo
            Icon(
                imageVector = Icons.Default.Security,
                contentDescription = "F.A.R.O.",
                modifier = Modifier.size(80.dp),
                tint = MaterialTheme.colorScheme.primary
            )
            
            Spacer(modifier = Modifier.height(16.dp))
            
            Text(
                "F.A.R.O.",
                style = MaterialTheme.typography.headlineLarge,
                color = MaterialTheme.colorScheme.primary
            )
            
            Text(
                "Agente de Campo",
                style = MaterialTheme.typography.titleMedium
            )
            
            Spacer(modifier = Modifier.height(32.dp))

            if (savedProfiles.isNotEmpty()) {
                Text(
                    "Perfis salvos neste aparelho",
                    style = MaterialTheme.typography.titleSmall
                )
                Spacer(modifier = Modifier.height(8.dp))
                LazyRow(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                    items(savedProfiles, key = { it.userId }) { profile ->
                        AssistChip(
                            onClick = { onUseSavedProfile(profile.userId) },
                            label = {
                                Text("${profile.userName} (${profile.userRole})")
                            }
                        )
                    }
                }
                Spacer(modifier = Modifier.height(16.dp))
            }
             
            // Identifier (CPF or Email)
            OutlinedTextField(
                value = identifier,
                onValueChange = { identifier = it },
                label = { Text(labelText) },
                leadingIcon = { 
                    Icon(
                        if (isCPF(identifier)) Icons.Default.Person else Icons.Default.Email, 
                        null
                    ) 
                },
                keyboardOptions = KeyboardOptions(
                    keyboardType = if (isCPF(identifier)) KeyboardType.Number else KeyboardType.Email
                ),
                modifier = Modifier.fillMaxWidth(),
                singleLine = true,
                supportingText = if (identifier.isNotEmpty()) {
                    { 
                        Text(
                            if (isCPF(identifier)) "CPF detectado" else "E-mail"
                        ) 
                    }
                } else null
            )
            
            Spacer(modifier = Modifier.height(16.dp))
            
            // Password
            OutlinedTextField(
                value = password,
                onValueChange = { password = it },
                label = { Text("Senha") },
                leadingIcon = { Icon(Icons.Default.Lock, null) },
                visualTransformation = PasswordVisualTransformation(),
                keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Password),
                modifier = Modifier.fillMaxWidth(),
                singleLine = true
            )
            
            Spacer(modifier = Modifier.height(8.dp))
            
            // Error
            uiState.errorMessage?.let {
                Text(
                    it,
                    color = MaterialTheme.colorScheme.error,
                    style = MaterialTheme.typography.bodySmall
                )
                Spacer(modifier = Modifier.height(8.dp))
            }
            
            // Login Button
            Button(
                onClick = {
                    // Clean CPF if needed (remove formatting)
                    val cleanIdentifier = if (isCPF(identifier)) {
                        identifier.replace(".", "").replace("-", "").replace(" ", "")
                    } else {
                        identifier
                    }
                    onLogin(cleanIdentifier, password)
                },
                modifier = Modifier.fillMaxWidth(),
                enabled = isValidIdentifier && password.isNotBlank() && !uiState.isLoading
            ) {
                if (uiState.isLoading) {
                    CircularProgressIndicator(
                        modifier = Modifier.size(20.dp),
                        strokeWidth = 2.dp
                    )
                } else {
                    Text("Entrar")
                }
            }
            
            Spacer(modifier = Modifier.height(16.dp))
            
            Text(
                "Versão 1.0.0",
                style = MaterialTheme.typography.bodySmall,
                color = MaterialTheme.colorScheme.onSurfaceVariant
            )
        }
    }
}
