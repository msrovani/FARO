package com.faro.mobile.presentation.screens

import androidx.compose.animation.*
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalConfiguration
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.ImeAction
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.hilt.navigation.compose.hiltViewModel
import com.faro.mobile.presentation.viewmodel.ApproachViewModel
import com.faro.mobile.utils.TacticalAlertManager

@Composable
fun ApproachScreen(
    viewModel: ApproachViewModel = hiltViewModel(),
    onApproachComplete: (Boolean, String) -> Unit
) {
    val context = LocalContext.current
    val configuration = LocalConfiguration.current
    val alertManager = remember { TacticalAlertManager(context) }
    
    // Get screen width for one-handed optimization
    val screenWidth = configuration.screenWidthDp
    val isCompactScreen = screenWidth < 400.dp
    
    val uiState by viewModel.uiState.collectAsState()
    val currentStep by viewModel.currentStep.collectAsState()

    // Auto-trigger haptic feedback on critical alerts
    LaunchedEffect(uiState.isCriticalAlert) {
        if (uiState.isCriticalAlert) {
            alertManager.triggerPhysicalAlert(TacticalAlertManager.AlertLevel.CRITICAL)
        }
    }

    Column(
        modifier = Modifier
            .fillMaxSize()
            .background(Color(0xFFF5F5F5))
            .padding(horizontal = 16.dp, vertical = 8.dp)
    ) {
        // Progress indicator
        ProgressIndicator(
            currentStep = currentStep,
            totalSteps = 4,
            modifier = Modifier.fillMaxWidth()
        )

        Spacer(modifier = Modifier.height(16.dp))

        // Main content based on current step
        when (currentStep) {
            1 -> PlateConfirmationStep(
                plateNumber = uiState.plateNumber,
                confidence = uiState.confidence,
                ocrImage = uiState.ocrImage,
                onConfirm = { viewModel.confirmPlate() },
                onRetry = { viewModel.retryOCR() },
                isCompactScreen = isCompactScreen
            )
            
            2 -> VehicleDetailsStep(
                vehicleDetails = uiState.vehicleDetails,
                onUpdateDetails = viewModel::updateVehicleDetails,
                isCompactScreen = isCompactScreen
            )
            
            3 -> SuspicionLevelStep(
                suspicionLevel = uiState.suspicionLevel,
                onUpdateLevel = viewModel::updateSuspicionLevel,
                isCompactScreen = isCompactScreen
            )
            
            4 -> ApproachConfirmationStep(
                wasApproached = uiState.wasApproached,
                approachOutcome = uiState.approachOutcome,
                notes = uiState.notes,
                onUpdateApproach = viewModel::updateApproachDetails,
                onComplete = { confirmed, outcome ->
                    onApproachComplete(confirmed, outcome)
                    viewModel.completeApproach()
                },
                isCompactScreen = isCompactScreen
            )
        }

        // Navigation buttons (large for one-handed use)
        NavigationButtons(
            currentStep = currentStep,
            totalSteps = 4,
            onPrevious = { if (currentStep > 1) viewModel.previousStep() },
            onNext = { if (currentStep < 4) viewModel.nextStep() },
            isCompactScreen = isCompactScreen
        )
    }
}

@Composable
private fun ProgressIndicator(
    currentStep: Int,
    totalSteps: Int,
    modifier: Modifier = Modifier
) {
    Row(
        modifier = modifier.fillMaxWidth(),
        horizontalArrangement = Arrangement.SpaceEvenly,
        verticalAlignment = Alignment.CenterVertically
    ) {
        repeat(totalSteps) { step ->
            Box(
                modifier = Modifier
                    .size(12.dp)
                    .background(
                        color = if (step < currentStep) Color(0xFF1976D2) else Color(0xFFE5E7EB),
                        shape = RoundedCornerShape(6.dp)
                    )
            ) {
                if (step < currentStep) {
                    Box(
                        modifier = Modifier
                            .size(8.dp)
                            .background(Color(0xFF1976D2), RoundedCornerShape(4.dp))
                            .align(Alignment.Center)
                    )
                }
            }
        }
    }
}

@Composable
private fun PlateConfirmationStep(
    plateNumber: String,
    confidence: Float,
    ocrImage: String?,
    onConfirm: () -> Unit,
    onRetry: () -> Unit,
    isCompactScreen: Boolean
) {
    Card(
        modifier = Modifier.fillMaxWidth(),
        elevation = CardDefaults.cardElevation(defaultElevation = 4.dp)
    ) {
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .padding(16.dp),
            horizontalAlignment = Alignment.CenterHorizontally
        ) {
            Text(
                text = "Confirmar Placa",
                fontSize = 18.sp,
                fontWeight = FontWeight.Bold,
                color = Color(0xFF1F2937),
                modifier = Modifier.padding(bottom = 16.dp)
            )

            // OCR result display
            ocrImage?.let { imageUrl ->
                Box(
                    modifier = Modifier
                        .size(120.dp)
                        .background(Color(0xFFF0F0F0), RoundedCornerShape(8.dp))
                        .padding(8.dp)
                ) {
                    // TODO: Load and display OCR image
                    Text(
                        text = "OCR\nImage",
                        fontSize = 12.sp,
                        color = Color.Gray,
                        textAlign = TextAlign.Center
                    )
                }
            }

            Spacer(modifier = Modifier.height(16.dp))

            // Plate number display
            Text(
                text = plateNumber,
                fontSize = if (isCompactScreen) 24.sp else 32.sp,
                fontWeight = FontWeight.Bold,
                fontFamily = androidx.compose.ui.text.font.FontFamily.Monospace,
                color = Color.Black,
                textAlign = TextAlign.Center,
                modifier = Modifier
                    .fillMaxWidth()
                    .background(Color(0xFFFFEB3B), RoundedCornerShape(8.dp))
                    .padding(16.dp)
            )

            Spacer(modifier = Modifier.height(8.dp))

            // Confidence indicator
            Text(
                text = "Confiança: ${(confidence * 100).toInt()}%",
                fontSize = 14.sp,
                color = if (confidence > 0.7f) Color(0xFF4CAF50) else Color(0xFFFF9800),
                modifier = Modifier.padding(bottom = 16.dp)
            )

            // Action buttons (large for one-handed use)
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.spacedBy(8.dp)
            ) {
                Button(
                    onClick = onRetry,
                    modifier = Modifier
                        .weight(1f)
                        .height(64.dp), // Large touch target
                    colors = ButtonDefaults.buttonColors(
                        containerColor = Color(0xFF6B7280),
                        contentColor = Color.White
                    )
                ) {
                    Icon(
                        imageVector = Icons.Default.Refresh,
                        contentDescription = "Refazer OCR",
                        modifier = Modifier.size(20.dp)
                    )
                }

                Button(
                    onClick = onConfirm,
                    modifier = Modifier
                        .weight(1f)
                        .height(64.dp), // Large touch target
                    colors = ButtonDefaults.buttonColors(
                        containerColor = Color(0xFF1976D2),
                        contentColor = Color.White
                    )
                ) {
                    Icon(
                        imageVector = Icons.Default.Check,
                        contentDescription = "Confirmar",
                        modifier = Modifier.size(20.dp)
                    )
                }
            }
        }
    }
}

@Composable
private fun VehicleDetailsStep(
    vehicleDetails: Map<String, String>,
    onUpdateDetails: (String, String) -> Unit,
    isCompactScreen: Boolean
) {
    Card(
        modifier = Modifier.fillMaxWidth(),
        elevation = CardDefaults.cardElevation(defaultElevation = 4.dp)
    ) {
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .padding(16.dp)
        ) {
            Text(
                text = "Detalhes do Veículo",
                fontSize = 18.sp,
                fontWeight = FontWeight.Bold,
                color = Color(0xFF1F2937),
                modifier = Modifier.padding(bottom = 16.dp)
            )

            // Vehicle detail fields
            val fields = listOf(
                "Cor" to (vehicleDetails["color"] ?: ""),
                "Modelo" to (vehicleDetails["model"] ?: ""),
                "Tipo" to (vehicleDetails["type"] ?: "")
            )

            fields.forEach { (label, value) ->
                Column(
                    modifier = Modifier.padding(bottom = 12.dp)
                ) {
                    Text(
                        text = label,
                        fontSize = 14.sp,
                        color = Color(0xFF6B7280),
                        modifier = Modifier.padding(bottom = 4.dp)
                    )

                    OutlinedTextField(
                        value = value,
                        onValueChange = { onUpdateDetails(label, it) },
                        modifier = Modifier.fillMaxWidth(),
                        keyboardOptions = KeyboardOptions(
                            imeAction = ImeAction.Next
                        ),
                        placeholder = { "Digite $label..." },
                        singleLine = true,
                        textStyle = androidx.compose.ui.text.TextStyle(
                            fontSize = if (isCompactScreen) 14.sp else 16.sp
                        )
                    )
                }
            }

            Spacer(modifier = Modifier.height(16.dp))

            // Next button (large for one-handed use)
            Button(
                onClick = { /* Trigger next step */ },
                modifier = Modifier
                    .fillMaxWidth()
                    .height(64.dp), // Large touch target
                colors = ButtonDefaults.buttonColors(
                    containerColor = Color(0xFF1976D2),
                    contentColor = Color.White
                )
            ) {
                Text(
                    text = "PRÓXIMO",
                    fontSize = 16.sp,
                    fontWeight = FontWeight.Bold
                )
            }
        }
    }
}

@Composable
private fun SuspicionLevelStep(
    suspicionLevel: Int,
    onUpdateLevel: (Int) -> Unit,
    isCompactScreen: Boolean
) {
    Card(
        modifier = Modifier.fillMaxWidth(),
        elevation = CardDefaults.cardElevation(defaultElevation = 4.dp)
    ) {
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .padding(16.dp),
            horizontalAlignment = Alignment.CenterHorizontally
        ) {
            Text(
                text = "Nível de Suspeição",
                fontSize = 18.sp,
                fontWeight = FontWeight.Bold,
                color = Color(0xFF1F2937),
                modifier = Modifier.padding(bottom = 16.dp)
            )

            // Large slider for one-handed use
            Column(
                modifier = Modifier.fillMaxWidth(),
                horizontalAlignment = Alignment.CenterHorizontally
            ) {
                Text(
                    text = "${suspicionLevel}%",
                    fontSize = if (isCompactScreen) 32.sp else 48.sp,
                    fontWeight = FontWeight.Bold,
                    color = when {
                        suspicionLevel < 30 -> Color(0xFF4CAF50) // Green
                        suspicionLevel < 70 -> Color(0xFFFF9800) // Orange
                        else -> Color(0xFFF44336) // Red
                    },
                    modifier = Modifier.padding(vertical = 16.dp)
                )

                // Visual scale
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceEvenly
                ) {
                    listOf(0, 25, 50, 75, 100).forEach { level ->
                        Box(
                            modifier = Modifier
                                .size(8.dp)
                                .background(
                                    color = if (level <= suspicionLevel) Color(0xFF1976D2) else Color(0xFFE5E7EB),
                                    shape = RoundedCornerShape(4.dp)
                                )
                        )
                    }
                }
            }

            Spacer(modifier = Modifier.height(16.dp))

            // Quick select buttons (large for one-handed use)
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.spacedBy(8.dp)
            ) {
                listOf(20, 50, 80).forEach { level ->
                    Button(
                        onClick = { onUpdateLevel(level) },
                        modifier = Modifier
                            .weight(1f)
                            .height(56.dp), // Large touch target
                        colors = ButtonDefaults.buttonColors(
                            containerColor = when {
                                level == 20 -> Color(0xFF4CAF50)
                                level == 50 -> Color(0xFFFF9800)
                                level == 80 -> Color(0xFFF44336)
                                else -> Color(0xFF6B7280)
                            },
                            contentColor = Color.White
                        )
                    ) {
                        Text(
                            text = "$level%",
                            fontSize = 14.sp,
                            fontWeight = FontWeight.Bold
                        )
                    }
                }
            }
        }
    }
}

@Composable
private fun ApproachConfirmationStep(
    wasApproached: Boolean,
    approachOutcome: String,
    notes: String,
    onUpdateApproach: (Boolean, String, String) -> Unit,
    onComplete: (Boolean, String) -> Unit,
    isCompactScreen: Boolean
) {
    Card(
        modifier = Modifier.fillMaxWidth(),
        elevation = CardDefaults.cardElevation(defaultElevation = 4.dp)
    ) {
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .padding(16.dp)
        ) {
            Text(
                text = "Confirmação de Abordagem",
                fontSize = 18.sp,
                fontWeight = FontWeight.Bold,
                color = Color(0xFF1F2937),
                modifier = Modifier.padding(bottom = 16.dp)
            )

            // Was approached toggle (large for one-handed use)
            Row(
                modifier = Modifier.fillMaxWidth(),
                verticalAlignment = Alignment.CenterVertically
            ) {
                Text(
                    text = "Foi abordado?",
                    fontSize = 16.sp,
                    modifier = Modifier.weight(1f)
                )

                Switch(
                    checked = wasApproached,
                    onCheckedChange = { onUpdateApproach(it, approachOutcome, notes) },
                    modifier = Modifier.scale(1.2f) // Larger for one-handed use
                )
            }

            Spacer(modifier = Modifier.height(16.dp))

            // Approach outcome
            if (wasApproached) {
                Text(
                    text = "Resultado",
                    fontSize = 14.sp,
                    color = Color(0xFF6B7280),
                    modifier = Modifier.padding(bottom = 8.dp)
                )

                val outcomes = listOf("Abordado", "Não Encontrado", "Fuga", "Outro")
                
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.spacedBy(4.dp)
                ) {
                    outcomes.forEach { outcome ->
                        FilterChip(
                            onClick = { onUpdateApproach(wasApproached, outcome, notes) },
                            label = outcome,
                            selected = approachOutcome == outcome,
                            modifier = Modifier.weight(1f)
                        )
                    }
                }
            }

            Spacer(modifier = Modifier.height(16.dp))

            // Notes field
            OutlinedTextField(
                value = notes,
                onValueChange = { onUpdateApproach(wasApproached, approachOutcome, it) },
                modifier = Modifier
                    .fillMaxWidth()
                    .height(if (isCompactScreen) 120.dp else 160.dp),
                keyboardOptions = KeyboardOptions(
                    imeAction = ImeAction.Done
                ),
                placeholder = { "Observações da abordagem..." },
                textStyle = androidx.compose.ui.text.TextStyle(
                    fontSize = if (isCompactScreen) 14.sp else 16.sp
                )
            )

            Spacer(modifier = Modifier.height(16.dp))

            // Complete button (large for one-handed use)
            Button(
                onClick = { onComplete(wasApproached, approachOutcome) },
                modifier = Modifier
                    .fillMaxWidth()
                    .height(72.dp), // Extra large for final action
                colors = ButtonDefaults.buttonColors(
                    containerColor = Color(0xFF1976D2),
                    contentColor = Color.White
                ),
                enabled = wasApproached && approachOutcome.isNotEmpty()
            ) {
                Icon(
                    imageVector = Icons.Default.Check,
                    contentDescription = "Finalizar",
                    modifier = Modifier.size(24.dp)
                )
                Spacer(modifier = Modifier.width(8.dp))
                Text(
                    text = "FINALIZAR ABORDAGEM",
                    fontSize = 16.sp,
                    fontWeight = FontWeight.Bold
                )
            }
        }
    }
}

@Composable
private fun NavigationButtons(
    currentStep: Int,
    totalSteps: Int,
    onPrevious: () -> Unit,
    onNext: () -> Unit,
    isCompactScreen: Boolean
) {
    Row(
        modifier = Modifier.fillMaxWidth(),
        horizontalArrangement = Arrangement.spacedBy(8.dp)
    ) {
        Button(
            onClick = onPrevious,
            enabled = currentStep > 1,
            modifier = Modifier
                .weight(1f)
                .height(56.dp), // Large touch target
            colors = ButtonDefaults.buttonColors(
                containerColor = Color(0xFF6B7280),
                contentColor = Color.White
            )
        ) {
            Icon(
                imageVector = Icons.Default.ArrowBack,
                contentDescription = "Anterior",
                modifier = Modifier.size(20.dp)
            )
        }

        Button(
            onClick = onNext,
            enabled = currentStep < totalSteps,
            modifier = Modifier
                .weight(1f)
                .height(56.dp), // Large touch target
            colors = ButtonDefaults.buttonColors(
                containerColor = Color(0xFF1976D2),
                contentColor = Color.White
            )
        ) {
            Text(
                text = if (currentStep == totalSteps) "FINALIZAR" else "PRÓXIMO",
                fontSize = if (isCompactScreen) 14.sp else 16.sp,
                fontWeight = FontWeight.Bold
            )
        }
    }
}

@Composable
private fun FilterChip(
    onClick: () -> Unit,
    label: String,
    selected: Boolean,
    modifier: Modifier = Modifier
) {
    FilterChip(
        onClick = onClick,
        label = { Text(label, fontSize = 12.sp) },
        selected = selected,
        modifier = modifier.height(40.dp), // Larger for one-handed use
        colors = FilterChipDefaults.filterChipColors(
            selectedContainerColor = Color(0xFF1976D2),
            selectedLabelColor = Color.White,
            unselectedContainerColor = Color(0xFFE5E7EB),
            unselectedLabelColor = Color(0xFF6B7280)
        )
    )
}
