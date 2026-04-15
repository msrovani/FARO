package com.faro.mobile.presentation.screens

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import com.faro.mobile.data.remote.PlateSuspicionCheckResponseDto

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun ApproachFormScreen(
    plateNumber: String,
    suspicionData: PlateSuspicionCheckResponseDto?,
    observationId: String,
    onSubmit: (
        confirmedSuspicion: Boolean,
        suspicionLevel: Int,
        wasApproached: Boolean,
        hasIncident: Boolean,
        notes: String
    ) -> Unit,
    onCancel: () -> Unit,
) {
    var confirmedSuspicion by remember { mutableStateOf(false) }
    var suspicionLevel by remember { mutableIntStateOf(50) }
    var wasApproached by remember { mutableStateOf(false) }
    var hasIncident by remember { mutableStateOf(false) }
    var notes by remember { mutableStateOf("") }
    var isSubmitting by remember { mutableStateOf(false) }

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("Confirmação de Abordagem") },
                navigationIcon = {
                    IconButton(onClick = onCancel) {
                        Icon(Icons.Default.ArrowBack, contentDescription = "Voltar")
                    }
                },
                colors = TopAppBarDefaults.topAppBarColors(
                    containerColor = MaterialTheme.colorScheme.primary,
                    titleContentColor = MaterialTheme.colorScheme.onPrimary,
                    navigationIconContentColor = MaterialTheme.colorScheme.onPrimary
                )
            )
        }
    ) { padding ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(padding)
                .verticalScroll(rememberScrollState())
                .padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(16.dp)
        ) {
            // Plate header
            Card(
                modifier = Modifier.fillMaxWidth(),
                colors = CardDefaults.cardColors(
                    containerColor = MaterialTheme.colorScheme.primaryContainer
                )
            ) {
                Column(
                    modifier = Modifier.padding(16.dp),
                    horizontalAlignment = Alignment.CenterHorizontally
                ) {
                    Text(
                        text = plateNumber,
                        style = MaterialTheme.typography.headlineMedium,
                        fontWeight = FontWeight.Bold,
                        color = MaterialTheme.colorScheme.primary
                    )
                    Text(
                        text = "Veículo Suspeito",
                        style = MaterialTheme.typography.titleMedium,
                        color = MaterialTheme.colorScheme.error
                    )
                }
            }

            // Suspicion info from server
            if (suspicionData != null && suspicionData.isSuspect) {
                Card(
                    modifier = Modifier.fillMaxWidth(),
                    colors = CardDefaults.cardColors(
                        containerColor = when (suspicionData.alertLevel) {
                            "critical" -> MaterialTheme.colorScheme.errorContainer
                            "warning" -> MaterialTheme.colorScheme.tertiaryContainer
                            else -> MaterialTheme.colorScheme.secondaryContainer
                        }
                    )
                ) {
                    Column(modifier = Modifier.padding(16.dp)) {
                        Text(
                            text = suspicionData.alertTitle ?: "Alerta de Suspeita",
                            style = MaterialTheme.typography.titleMedium,
                            fontWeight = FontWeight.Bold
                        )
                        Spacer(modifier = Modifier.height(8.dp))
                        Text(
                            text = suspicionData.alertMessage ?: "",
                            style = MaterialTheme.typography.bodyMedium
                        )
                        suspicionData.suspicionReason?.let { reason ->
                            Spacer(modifier = Modifier.height(4.dp))
                            Text(
                                text = "Motivo: $reason",
                                style = MaterialTheme.typography.bodySmall
                            )
                        }
                        suspicionData.firstSuspicionAgentName?.let { agent ->
                            Spacer(modifier = Modifier.height(4.dp))
                            Text(
                                text = "Suspeita original por: $agent",
                                style = MaterialTheme.typography.bodySmall
                            )
                        }
                    }
                }
            }

            // Suspicion confirmation switch
            Card(modifier = Modifier.fillMaxWidth()) {
                Column(modifier = Modifier.padding(16.dp)) {
                    Text(
                        text = "Confirmação da Suspeita",
                        style = MaterialTheme.typography.titleMedium,
                        fontWeight = FontWeight.Bold
                    )
                    Spacer(modifier = Modifier.height(8.dp))
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        verticalAlignment = Alignment.CenterVertically,
                        horizontalArrangement = Arrangement.SpaceBetween
                    ) {
                        Text("Suspeita confirmada na abordagem?")
                        Switch(
                            checked = confirmedSuspicion,
                            onCheckedChange = { confirmedSuspicion = it }
                        )
                    }
                }
            }

            // Suspicion level slider (only show if suspicion confirmed)
            if (confirmedSuspicion) {
                Card(modifier = Modifier.fillMaxWidth()) {
                    Column(modifier = Modifier.padding(16.dp)) {
                        Text(
                            text = "Nível de Suspeição",
                            style = MaterialTheme.typography.titleMedium,
                            fontWeight = FontWeight.Bold
                        )
                        Spacer(modifier = Modifier.height(8.dp))
                        Text(
                            text = "$suspicionLevel%",
                            style = MaterialTheme.typography.headlineMedium,
                            color = when {
                                suspicionLevel >= 70 -> MaterialTheme.colorScheme.error
                                suspicionLevel >= 40 -> MaterialTheme.colorScheme.tertiary
                                else -> MaterialTheme.colorScheme.primary
                            }
                        )
                        Slider(
                            value = suspicionLevel.toFloat(),
                            onValueChange = { suspicionLevel = it.toInt() },
                            valueRange = 0f..100f,
                            steps = 9,
                            modifier = Modifier.fillMaxWidth()
                        )
                        Row(
                            modifier = Modifier.fillMaxWidth(),
                            horizontalArrangement = Arrangement.SpaceBetween
                        ) {
                            Text("Baixa", style = MaterialTheme.typography.bodySmall)
                            Text("Média", style = MaterialTheme.typography.bodySmall)
                            Text("Alta", style = MaterialTheme.typography.bodySmall)
                        }
                    }
                }
            }

            // Approach confirmation switch
            Card(modifier = Modifier.fillMaxWidth()) {
                Column(modifier = Modifier.padding(16.dp)) {
                    Text(
                        text = "Abordagem",
                        style = MaterialTheme.typography.titleMedium,
                        fontWeight = FontWeight.Bold
                    )
                    Spacer(modifier = Modifier.height(8.dp))
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        verticalAlignment = Alignment.CenterVertically,
                        horizontalArrangement = Arrangement.SpaceBetween
                    ) {
                        Text("Veículo foi abordado?")
                        Switch(
                            checked = wasApproached,
                            onCheckedChange = { wasApproached = it }
                        )
                    }
                }
            }

            // Incident switch
            Card(modifier = Modifier.fillMaxWidth()) {
                Column(modifier = Modifier.padding(16.dp)) {
                    Text(
                        text = "Ocorrência",
                        style = MaterialTheme.typography.titleMedium,
                        fontWeight = FontWeight.Bold
                    )
                    Spacer(modifier = Modifier.height(8.dp))
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        verticalAlignment = Alignment.CenterVertically,
                        horizontalArrangement = Arrangement.SpaceBetween
                    ) {
                        Text("Gerar ocorrência?")
                        Switch(
                            checked = hasIncident,
                            onCheckedChange = { hasIncident = it }
                        )
                    }
                }
            }

            // Notes field
            OutlinedTextField(
                value = notes,
                onValueChange = { notes = it },
                label = { Text("Observações da Abordagem") },
                placeholder = { Text("Descreva o que foi observado...") },
                modifier = Modifier.fillMaxWidth(),
                minLines = 3,
                maxLines = 5
            )

            // Submit button
            Button(
                onClick = {
                    isSubmitting = true
                    onSubmit(
                        confirmedSuspicion,
                        suspicionLevel,
                        wasApproached,
                        hasIncident,
                        notes
                    )
                },
                modifier = Modifier.fillMaxWidth(),
                enabled = !isSubmitting && notes.isNotBlank(),
                colors = ButtonDefaults.buttonColors(
                    containerColor = if (confirmedSuspicion) 
                        MaterialTheme.colorScheme.error 
                    else 
                        MaterialTheme.colorScheme.primary
                )
            ) {
                if (isSubmitting) {
                    CircularProgressIndicator(
                        modifier = Modifier.size(20.dp),
                        strokeWidth = 2.dp,
                        color = MaterialTheme.colorScheme.onPrimary
                    )
                } else {
                    Icon(Icons.Default.Check, null)
                    Spacer(modifier = Modifier.width(8.dp))
                    Text("Enviar Confirmação")
                }
            }

            // Cancel button
            OutlinedButton(
                onClick = onCancel,
                modifier = Modifier.fillMaxWidth()
            ) {
                Text("Cancelar")
            }
        }
    }
}
