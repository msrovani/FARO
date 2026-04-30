package com.faro.mobile.presentation.components

import androidx.compose.animation.*
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.faro.mobile.utils.TacticalAlertManager

@Composable
fun AlertCard(
    alertType: String,
    title: String,
    message: String,
    severity: String,
    onAcknowledge: () -> Unit,
    onDismiss: () -> Unit,
    onViewDetails: () -> Unit
) {
    val context = LocalContext.current
    val alertManager = remember { TacticalAlertManager(context) }
    
    // Trigger haptic feedback based on severity
    LaunchedEffect(severity) {
        when (severity.lowercase()) {
            "info" -> alertManager.triggerPhysicalAlert(TacticalAlertManager.AlertLevel.LOW)
            "warning" -> alertManager.triggerPhysicalAlert(TacticalAlertManager.AlertLevel.MEDIUM)
            "critical" -> alertManager.triggerPhysicalAlert(TacticalAlertManager.AlertLevel.CRITICAL)
            else -> alertManager.triggerPhysicalAlert(TacticalAlertManager.AlertLevel.MEDIUM)
        }
    }

    // Get colors and icons based on severity
    val (backgroundColor, iconColor, icon) = when (severity.lowercase()) {
        "info" -> Triple(
            Color(0xFFE3F2FD), // Blue
            Color(0xFF1976D2),
            Icons.Default.Info
        )
        "warning" -> Triple(
            Color(0xFFFFF59D), // Yellow
            Color(0xFFD97706),
            Icons.Default.Warning
        )
        "critical" -> Triple(
            Color(0xFFFEE2E2), // Red
            Color(0xFFDC2626),
            Icons.Default.Error
        )
        else -> Triple(
            Color(0xFFF3F4F6), // Gray
            Color(0xFF6B7280),
            Icons.Default.Notifications
        )
    }

    Card(
        modifier = Modifier
            .fillMaxWidth()
            .padding(horizontal = 16.dp, vertical = 8.dp)
            .clip(RoundedCornerShape(12.dp)),
        elevation = CardDefaults.cardElevation(defaultElevation = 6.dp)
    ) {
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .background(backgroundColor)
                .padding(16.dp)
        ) {
            // Header with icon and title
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Row(
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Icon(
                        imageVector = icon,
                        contentDescription = null,
                        tint = iconColor,
                        modifier = Modifier.size(24.dp)
                    )
                    Spacer(modifier = Modifier.width(12.dp))
                    Text(
                        text = alertType,
                        color = iconColor,
                        fontSize = 14.sp,
                        fontWeight = FontWeight.Bold,
                        modifier = Modifier.weight(1f)
                    )
                }
                
                // Dismiss button (large for one-handed use)
                IconButton(
                    onClick = onDismiss,
                    modifier = Modifier.size(48.dp)
                ) {
                    Icon(
                        imageVector = Icons.Default.Close,
                        contentDescription = "Dismiss",
                        tint = iconColor,
                        modifier = Modifier.size(24.dp)
                    )
                }
            }

            Spacer(modifier = Modifier.height(12.dp))

            // Alert title
            Text(
                text = title,
                color = Color.Black,
                fontSize = 16.sp,
                fontWeight = FontWeight.Bold,
                modifier = Modifier.fillMaxWidth()
            )

            Spacer(modifier = Modifier.height(8.dp))

            // Alert message
            Text(
                text = message,
                color = Color.Black.copy(alpha = 0.8f),
                fontSize = 14.sp,
                lineHeight = 20.sp,
                modifier = Modifier.fillMaxWidth()
            )

            Spacer(modifier = Modifier.height(16.dp))

            // Action buttons (large for one-handed use)
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.spacedBy(8.dp)
            ) {
                // Acknowledge button
                Button(
                    onClick = onAcknowledge,
                    modifier = Modifier
                        .weight(1f)
                        .height(56.dp), // Large touch target
                    colors = ButtonDefaults.buttonColors(
                        containerColor = Color(0xFF1976D2), // Blue
                        contentColor = Color.White
                    ),
                    shape = RoundedCornerShape(8.dp)
                ) {
                    Text(
                        text = "ACK",
                        fontSize = 16.sp,
                        fontWeight = FontWeight.Bold
                    )
                }

                // View Details button
                OutlinedButton(
                    onClick = onViewDetails,
                    modifier = Modifier
                        .weight(1f)
                        .height(56.dp), // Large touch target
                    colors = ButtonDefaults.outlinedButtonColors(
                        contentColor = iconColor
                    ),
                    border = ButtonDefaults.outlinedButtonBorder.copy(
                        width = 2.dp,
                        color = iconColor
                    ),
                    shape = RoundedCornerShape(8.dp)
                ) {
                    Text(
                        text = "DETALHES",
                        fontSize = 16.sp,
                        fontWeight = FontWeight.Bold
                    )
                }
            }
        }
    }
}

@Composable
fun CompactAlertCard(
    alertType: String,
    severity: String,
    onQuickAction: () -> Unit
) {
    val context = LocalContext.current
    val alertManager = remember { TacticalAlertManager(context) }
    
    // Trigger haptic feedback
    LaunchedEffect(Unit) {
        when (severity.lowercase()) {
            "info" -> alertManager.triggerPhysicalAlert(TacticalAlertManager.AlertLevel.LOW)
            "warning" -> alertManager.triggerPhysicalAlert(TacticalAlertManager.AlertLevel.MEDIUM)
            "critical" -> alertManager.triggerPhysicalAlert(TacticalAlertManager.AlertLevel.CRITICAL)
            else -> alertManager.triggerPhysicalAlert(TacticalAlertManager.AlertLevel.MEDIUM)
        }
    }

    val (backgroundColor, iconColor) = when (severity.lowercase()) {
        "info" -> Pair(Color(0xFFE3F2FD), Color(0xFF1976D2))
        "warning" -> Pair(Color(xFFFFF59D), Color(0xFFD97706))
        "critical" -> Pair(Color(0xFFFEE2E2), Color(0xFFDC2626))
        else -> Pair(Color(0xFFF3F4F6), Color(0xFF6B7280))
    }

    Card(
        modifier = Modifier
            .fillMaxWidth()
            .padding(horizontal = 16.dp, vertical = 4.dp)
            .clip(RoundedCornerShape(8.dp)),
        elevation = CardDefaults.cardElevation(defaultElevation = 4.dp)
    ) {
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .background(backgroundColor)
                .padding(12.dp),
            verticalAlignment = Alignment.CenterVertically,
            horizontalArrangement = Arrangement.SpaceBetween
        ) {
            Row(
                verticalAlignment = Alignment.CenterVertically,
                modifier = Modifier.weight(1f)
            ) {
                Box(
                    modifier = Modifier
                        .size(12.dp)
                        .background(iconColor, RoundedCornerShape(2.dp))
                )
                Spacer(modifier = Modifier.width(8.dp))
                Text(
                    text = alertType,
                    color = Color.Black,
                    fontSize = 12.sp,
                    fontWeight = FontWeight.Bold,
                    modifier = Modifier.weight(1f)
                )
            }

            // Quick action button (large for one-handed use)
            Button(
                onClick = onQuickAction,
                modifier = Modifier.size(48.dp),
                colors = ButtonDefaults.buttonColors(
                    containerColor = iconColor,
                    contentColor = Color.White
                ),
                shape = RoundedCornerShape(6.dp)
            ) {
                Icon(
                    imageVector = Icons.Default.ArrowForward,
                    contentDescription = "Action",
                    modifier = Modifier.size(20.dp)
                )
            }
        }
    }
}

@Composable
fun AlertIndicator(
    isActive: Boolean,
    alertCount: Int = 0
) {
    if (!isActive && alertCount == 0) return

    val (backgroundColor, pulseColor) = if (isActive) {
        Pair(Color(0xFFDC2626), Color(0xFFFF6B6B)) // Red with pulse
    } else {
        Pair(Color(0xFFFF9800), Color(0xFFFFA726)) // Orange with pulse
    }

    Box(
        modifier = Modifier
            .size(64.dp)
            .background(backgroundColor, RoundedCornerShape(32.dp))
    ) {
        if (isActive) {
            // Pulsing animation for active alerts
            LaunchedEffect(Unit) {
                // Trigger continuous vibration for critical alerts
                // This would be handled by the service
            }
        }

        Column(
            modifier = Modifier.fillMaxSize(),
            horizontalAlignment = Alignment.CenterHorizontally,
            verticalAlignment = Alignment.CenterVertically
        ) {
            if (alertCount > 0) {
                // Alert count badge
                Box(
                    modifier = Modifier
                        .size(24.dp)
                        .background(pulseColor, RoundedCornerShape(12.dp))
                ) {
                    Text(
                        text = if (alertCount > 99) "99+" else alertCount.toString(),
                        color = Color.White,
                        fontSize = 12.sp,
                        fontWeight = FontWeight.Bold,
                        textAlign = TextAlign.Center,
                        modifier = Modifier.fillMaxSize()
                    )
                }
            } else {
                // Active indicator
                Box(
                    modifier = Modifier
                        .size(8.dp)
                        .background(Color.White, RoundedCornerShape(4.dp))
                )
            }
        }
    }
}
