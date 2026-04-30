package com.faro.mobile.presentation.screens

import androidx.compose.animation.animateColorAsState
import androidx.compose.animation.core.tween
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.ExperimentalLayoutApi
import androidx.compose.foundation.layout.FlowRow
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxHeight
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.ArrowBack
import androidx.compose.material.icons.filled.CameraAlt
import androidx.compose.material.icons.filled.Check
import androidx.compose.material.icons.filled.CloudOff
import androidx.compose.material.icons.filled.ConfirmationNumber
import androidx.compose.material.icons.filled.LocationOn
import androidx.compose.material.icons.filled.Refresh
import androidx.compose.material.icons.filled.Save
import androidx.compose.material.icons.filled.Warning
import androidx.compose.material3.AssistChip
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.FilterChip
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.material3.TopAppBar
import androidx.compose.material3.TopAppBarDefaults
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableFloatStateOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.graphics.Color
import kotlinx.coroutines.delay
import androidx.compose.ui.hapticfeedback.HapticFeedbackType
import androidx.compose.ui.platform.LocalHapticFeedback
import androidx.compose.ui.text.input.KeyboardCapitalization
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.unit.dp
import com.faro.mobile.domain.model.SuspicionLevel
import com.faro.mobile.domain.model.SuspicionReason
import com.faro.mobile.domain.model.UrgencyLevel
import com.faro.mobile.presentation.components.CameraPreview

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun PlateCaptureScreen(
    onCaptureComplete: () -> Unit,
    onCancel: () -> Unit
) {
    var plateNumber by remember { mutableStateOf("") }
    var ocrSuggestion by remember { mutableStateOf("") }
    var ocrConfidence by remember { mutableFloatStateOf(0.0f) }
    var autoOcrEnabled by remember { mutableStateOf(true) }
    var autoOcrThreshold by remember { mutableFloatStateOf(0.85f) }
    var suspicionReason by remember { mutableStateOf<SuspicionReason?>(SuspicionReason.SUSPICIOUS_BEHAVIOR) }
    var suspicionLevel by remember { mutableStateOf(SuspicionLevel.MEDIUM) }
    var urgencyLevel by remember { mutableStateOf(UrgencyLevel.INTELLIGENCE) }
    var notes by remember { mutableStateOf("") }
    var alertFlashActive by remember { mutableStateOf(false) }
    
    val haptic = LocalHapticFeedback.current
    
    val flashColor by animateColorAsState(
        targetValue = if (alertFlashActive) Color.Red.copy(alpha = 0.5f) else Color.Transparent,
        animationSpec = tween(durationMillis = 300),
        label = "AlertFlash"
    )

    val triggerAlert: (Int) -> Unit = { level ->
        when (level) {
            1 -> { // Verde - Sucesso normal
                haptic.performHapticFeedback(HapticFeedbackType.TextHandleMove)
            }
            2 -> { // Laranja - Suspeição
                haptic.performHapticFeedback(HapticFeedbackType.LongPress)
            }
            3 -> { // Vermelha - Grave
                haptic.performHapticFeedback(HapticFeedbackType.LongPress)
                haptic.performHapticFeedback(HapticFeedbackType.LongPress)
            }
            4 -> { // Fatos Criminais - Intenso + Flash
                alertFlashActive = true
                haptic.performHapticFeedback(HapticFeedbackType.LongPress)
                // In a real app we would use Vibrator for pattern, here we simulate with repeated haptics
            }
        }
    }

    if (alertFlashActive) {
        LaunchedEffect(Unit) {
            delay(1000)
            alertFlashActive = false
        }
    }

    val onTextRecognized: (String, Float) -> Unit = { text, confidence ->
        ocrSuggestion = text
        ocrConfidence = confidence
        // Auto-accept OCR if enabled and confidence meets threshold
        if (autoOcrEnabled && confidence >= autoOcrThreshold) {
            if (plateNumber != text) {
                plateNumber = text
                // Simulate deep intelligence check feedback
                val simulatedRisk = if (text.endsWith("0")) 4 else if (text.contains("Z")) 3 else 1
                triggerAlert(simulatedRisk)
            }
        } else if (plateNumber.isBlank() && confidence > 0.6f) {
            // Fallback to lower threshold for suggestion
            plateNumber = text
            triggerAlert(1)
        }
    }

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("Registro Rápido") },
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
        },
        bottomBar = {
            Column(modifier = Modifier.padding(16.dp)) {
                Button(
                    onClick = onCaptureComplete,
                    modifier = Modifier.fillMaxWidth().height(56.dp),
                    enabled = plateNumber.length >= 7
                ) {
                    Icon(Icons.Default.Save, null, modifier = Modifier.size(24.dp))
                    Spacer(modifier = Modifier.width(8.dp))
                    Text("CONCLUIR LANÇAMENTO EXTERNO", style = MaterialTheme.typography.titleMedium)
                }
            }
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
            CameraGuideCard(onTextRecognized = onTextRecognized)

            OCRCard(
                suggestion = ocrSuggestion,
                confidence = ocrConfidence,
                onAccept = { plateNumber = ocrSuggestion },
                onRetry = {
                    ocrSuggestion = ""
                    ocrConfidence = 0.0f
                }
            )

            OutlinedTextField(
                value = plateNumber,
                onValueChange = { value ->
                    plateNumber = value.uppercase().replace(" ", "").take(7)
                },
                label = { Text("Placa confirmada") },
                supportingText = { Text("OCR sugere. O agente confirma ou corrige.") },
                leadingIcon = { Icon(Icons.Default.ConfirmationNumber, null) },
                keyboardOptions = KeyboardOptions(
                    keyboardType = KeyboardType.Ascii,
                    capitalization = KeyboardCapitalization.Characters
                ),
                modifier = Modifier.fillMaxWidth(),
                singleLine = true
            )

            LocationCard()
            SyncPreviewCard()
            FeedbackPreviewCard()

                onNotesChange = { notes = it }
            )
        }
        
        // Flash Overlay for high urgency / criminal facts
        Box(
            modifier = Modifier
                .fillMaxSize()
                .background(flashColor)
        )
    }
}

@Composable
private fun CameraGuideCard(
    onTextRecognized: (String, Float) -> Unit
) {
    Card(
        modifier = Modifier.fillMaxWidth(),
        colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surfaceVariant)
    ) {
        Column(modifier = Modifier.padding(16.dp)) {
            Row(verticalAlignment = Alignment.CenterVertically) {
                Icon(Icons.Default.CameraAlt, null, tint = MaterialTheme.colorScheme.primary)
                Spacer(modifier = Modifier.width(8.dp))
                Text("Captura assistida", style = MaterialTheme.typography.titleMedium)
            }
            Spacer(modifier = Modifier.height(12.dp))
            CameraPreview(
                onTextRecognized = onTextRecognized,
                modifier = Modifier
                    .fillMaxWidth()
                    .height(200.dp)
            )
        }
    }
}

@Composable
private fun OCRCard(
    suggestion: String,
    confidence: Float,
    onAccept: () -> Unit,
    onRetry: () -> Unit
) {
    Card(
        modifier = Modifier.fillMaxWidth(),
        colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.primaryContainer)
    ) {
        Column(modifier = Modifier.padding(16.dp)) {
            Text("Leitura assistida", style = MaterialTheme.typography.titleMedium)
            Spacer(modifier = Modifier.height(8.dp))
            Text(
                text = suggestion,
                style = MaterialTheme.typography.headlineMedium,
                color = MaterialTheme.colorScheme.primary
            )
            Spacer(modifier = Modifier.height(4.dp))
            Text("Confiança OCR: ${(confidence * 100).toInt()}%", style = MaterialTheme.typography.bodyMedium)
            Spacer(modifier = Modifier.height(12.dp))
            Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                OutlinedButton(onClick = onRetry, modifier = Modifier.weight(1f)) {
                    Icon(Icons.Default.Refresh, null)
                    Spacer(modifier = Modifier.width(4.dp))
                    Text("Nova leitura")
                }
                Button(onClick = onAccept, modifier = Modifier.weight(1f)) {
                    Icon(Icons.Default.Check, null)
                    Spacer(modifier = Modifier.width(4.dp))
                    Text("Aceitar OCR")
                }
            }
        }
    }
}

@Composable
private fun LocationCard() {
    Card(modifier = Modifier.fillMaxWidth()) {
        Column(modifier = Modifier.padding(16.dp)) {
            Text("Contexto coletado", style = MaterialTheme.typography.titleMedium)
            Spacer(modifier = Modifier.height(12.dp))
            Row(verticalAlignment = Alignment.CenterVertically) {
                Icon(Icons.Default.LocationOn, null, tint = MaterialTheme.colorScheme.primary)
                Spacer(modifier = Modifier.width(8.dp))
                Column {
                    Text("-23.550520, -46.633308")
                    Text("Precisão 8 m • Heading 210° • 32 km/h", style = MaterialTheme.typography.bodySmall)
                }
            }
            Spacer(modifier = Modifier.height(8.dp))
            Text("Equipe RP-1201 • Dispositivo FARO-DEVICE-07 • Rede instável", style = MaterialTheme.typography.bodySmall)
        }
    }
}

@Composable
private fun SyncPreviewCard() {
    Card(
        modifier = Modifier.fillMaxWidth(),
        colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.errorContainer)
    ) {
        Row(
            modifier = Modifier.padding(16.dp),
            verticalAlignment = Alignment.CenterVertically
        ) {
            Icon(Icons.Default.CloudOff, null, tint = MaterialTheme.colorScheme.onErrorContainer)
            Spacer(modifier = Modifier.width(8.dp))
            Column {
                Text("Sincronização", style = MaterialTheme.typography.titleSmall)
                Text("Registro será salvo localmente e reenviado quando houver conectividade.", style = MaterialTheme.typography.bodySmall)
            }
        }
    }
}

@Composable
private fun FeedbackPreviewCard() {
    Card(
        modifier = Modifier.fillMaxWidth(),
        colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.secondaryContainer)
    ) {
        Column(modifier = Modifier.padding(16.dp)) {
            Text("Retorno imediato", style = MaterialTheme.typography.titleMedium)
            Spacer(modifier = Modifier.height(8.dp))
            AssistChip(
                onClick = {},
                label = { Text("Moderado • recorrência recente na área") },
                leadingIcon = { Icon(Icons.Default.Warning, null, modifier = Modifier.size(18.dp)) }
            )
            Spacer(modifier = Modifier.height(8.dp))
            Text(
                "Se confirmado, priorizar registro estruturado e observação qualificada.",
                style = MaterialTheme.typography.bodySmall
            )
        }
    }
}

@OptIn(ExperimentalLayoutApi::class)
@Composable
private fun StructuredSuspicionCard(
    selectedReason: SuspicionReason?,
    selectedLevel: SuspicionLevel,
    selectedUrgency: UrgencyLevel,
    notes: String,
    onReasonChange: (SuspicionReason) -> Unit,
    onLevelChange: (SuspicionLevel) -> Unit,
    onUrgencyChange: (UrgencyLevel) -> Unit,
    onNotesChange: (String) -> Unit
) {
    Card(modifier = Modifier.fillMaxWidth()) {
        Column(modifier = Modifier.padding(16.dp)) {
            Text("Suspeição estruturada", style = MaterialTheme.typography.titleMedium)
            Spacer(modifier = Modifier.height(12.dp))
            Text("Motivo principal", style = MaterialTheme.typography.labelLarge)
            Spacer(modifier = Modifier.height(8.dp))
            FlowRow(
                horizontalArrangement = Arrangement.spacedBy(8.dp),
                verticalArrangement = Arrangement.spacedBy(8.dp)
            ) {
                SuspicionReason.entries.forEach { reason ->
                    FilterChip(
                        selected = selectedReason == reason,
                        onClick = { onReasonChange(reason) },
                        label = { Text(reason.name.lowercase().replace("_", " ")) }
                    )
                }
            }
            Spacer(modifier = Modifier.height(12.dp))
            Text("Grau de suspeição", style = MaterialTheme.typography.labelLarge)
            Spacer(modifier = Modifier.height(8.dp))
            FlowRow(
                horizontalArrangement = Arrangement.spacedBy(8.dp),
                verticalArrangement = Arrangement.spacedBy(8.dp)
            ) {
                SuspicionLevel.entries.forEach { level ->
                    FilterChip(
                        selected = selectedLevel == level,
                        onClick = { onLevelChange(level) },
                        label = { Text(level.name.lowercase()) }
                    )
                }
            }
            Spacer(modifier = Modifier.height(12.dp))
            Text("Urgência", style = MaterialTheme.typography.labelLarge)
            Spacer(modifier = Modifier.height(8.dp))
            FlowRow(
                horizontalArrangement = Arrangement.spacedBy(8.dp),
                verticalArrangement = Arrangement.spacedBy(8.dp)
            ) {
                UrgencyLevel.entries.forEach { urgency ->
                    FilterChip(
                        selected = selectedUrgency == urgency,
                        onClick = { onUrgencyChange(urgency) },
                        label = { Text(urgency.name.lowercase()) }
                    )
                }
            }
            Spacer(modifier = Modifier.height(12.dp))
            OutlinedTextField(
                value = notes,
                onValueChange = onNotesChange,
                modifier = Modifier.fillMaxWidth(),
                label = { Text("Observação curta") },
                placeholder = { Text("Ex.: reduziu ao avistar viatura e mudou corredor") }
            )
        }
    }
}
