package com.faro.mobile.data.websocket

import android.util.Log
import com.faro.mobile.utils.TacticalAlertManager
import com.google.gson.Gson
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import javax.inject.Inject
import javax.inject.Singleton

/**
 * Handles INTERCEPT location-based alerts with tactical feedback.
 * 
 * Processes incoming WebSocket messages for INTERCEPT alerts and triggers
 * appropriate tactile and audible feedback based on severity and priority.
 */
@Singleton
class InterceptAlertHandler @Inject constructor(
    private val tacticalAlertManager: TacticalAlertManager
) {
    private val scope = CoroutineScope(Dispatchers.Main)
    private val gson = Gson()

    data class InterceptAlertData(
        val intercept_event_id: String,
        val plate_number: String,
        val observation_id: String,
        val location: LocationData,
        val intercept_score: Double,
        val recommendation: String, // "APPROACH", "MONITOR", "IGNORE"
        val priority_level: String, // "high", "medium", "low"
        val location_context: LocationContext,
        val target_agent: TargetAgent,
        val tactical_alert: TacticalAlert,
        val created_at: String
    )

    data class LocationData(
        val latitude: Double,
        val longitude: Double
    )

    data class LocationContext(
        val is_urban: Boolean,
        val location_name: String,
        val alert_radius_km: Double
    )

    data class TargetAgent(
        val agent_id: String,
        val full_name: String,
        val distance_km: Double
    )

    data class TacticalAlert(
        val alert_level: String, // "CRITICAL", "MEDIUM", "LOW"
        val vibration_pattern: List<Long>,
        val sound_type: String, // "ALARM", "NOTIFICATION"
        val urgency: String // "high", "medium"
    )

    /**
     * Process incoming INTERCEPT alert message.
     */
    fun handleInterceptAlert(message: String) {
        try {
            val alertData = parseAlertMessage(message)
            if (alertData == null) {
                Log.w(TAG, "Failed to parse INTERCEPT alert message")
                return
            }

            Log.i(TAG, "Processing INTERCEPT alert for plate ${alertData.plate_number} with priority ${alertData.priority_level}")
            
            // Trigger tactical feedback based on alert severity
            triggerTacticalFeedback(alertData)
            
        } catch (e: Exception) {
            Log.e(TAG, "Error processing INTERCEPT alert", e)
        }
    }

    /**
     * Parse WebSocket message into InterceptAlertData.
     */
    private fun parseAlertMessage(message: String): InterceptAlertData? {
        return try {
            // Parse the outer message structure
            val messageJson = gson.fromJson(message, Map::class.java) as Map<String, Any>
            
            // Extract data payload
            val dataPayload = messageJson["data"] as? Map<String, Any>
                ?: return null
            
            // Parse the alert data
            gson.fromJson(gson.toJson(dataPayload), InterceptAlertData::class.java)
        } catch (e: Exception) {
            Log.e(TAG, "Failed to parse alert message: $message", e)
            null
        }
    }

    /**
     * Trigger appropriate tactile and audible feedback.
     */
    private fun triggerTacticalFeedback(alertData: InterceptAlertData) {
        scope.launch {
            try {
                // Map alert level to tactical alert manager enum
                val alertLevel = when (alertData.tactical_alert.alert_level) {
                    "CRITICAL" -> TacticalAlertManager.AlertLevel.CRITICAL
                    "MEDIUM" -> TacticalAlertManager.AlertLevel.MEDIUM
                    "LOW" -> TacticalAlertManager.AlertLevel.LOW
                    else -> TacticalAlertManager.AlertLevel.MEDIUM
                }

                // Trigger the physical alert
                tacticalAlertManager.triggerPhysicalAlert(alertLevel)
                
                // Log the alert for audit purposes
                logAlertTriggered(alertData, alertLevel)
                
            } catch (e: Exception) {
                Log.e(TAG, "Failed to trigger tactical feedback", e)
            }
        }
    }

    /**
     * Log alert details for audit and debugging.
     */
    private fun logAlertTriggered(alertData: InterceptAlertData, alertLevel: TacticalAlertManager.AlertLevel) {
        Log.i(TAG, "INTERCEPT Alert Triggered: " +
            "Plate=${alertData.plate_number}, " +
            "Priority=${alertData.priority_level}, " +
            "Recommendation=${alertData.recommendation}, " +
            "Score=${alertData.intercept_score}, " +
            "Location=${alertData.location_context.location_name}, " +
            "Distance=${alertData.target_agent.distance_km}km, " +
            "AlertLevel=$alertLevel, " +
            "Urban=${alertData.location_context.is_urban}")
    }

    /**
     * Check if alert should trigger immediate feedback.
     * Only APPROACH and MONITOR recommendations trigger physical alerts.
     */
    private fun shouldTriggerFeedback(alertData: InterceptAlertData): Boolean {
        return alertData.recommendation in listOf("APPROACH", "MONITOR") &&
               alertData.priority_level in listOf("high", "medium")
    }

    /**
     * Get enhanced alert context for logging.
     */
    private fun getAlertContext(alertData: InterceptAlertData): String {
        return buildString {
            append("INTERCEPT Alert Context:\n")
            append("  Plate: ${alertData.plate_number}\n")
            append("  Recommendation: ${alertData.recommendation}\n")
            append("  Priority: ${alertData.priority_level}\n")
            append("  Score: ${(alertData.intercept_score * 100).toInt()}%\n")
            append("  Location: ${alertData.location_context.location_name}\n")
            append("  Urban: ${alertData.location_context.is_urban}\n")
            append("  Distance: ${alertData.target_agent.distance_km}km\n")
            append("  Alert Level: ${alertData.tactical_alert.alert_level}\n")
            append("  Sound Type: ${alertData.tactical_alert.sound_type}\n")
            append("  Vibration Pattern: ${alertData.tactical_alert.vibration_pattern.joinToString(", ")}")
        }
    }

    companion object {
        private const val TAG = "InterceptAlertHandler"
    }
}
