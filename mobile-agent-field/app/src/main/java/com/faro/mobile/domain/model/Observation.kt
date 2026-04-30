package com.faro.mobile.domain.model

import java.time.Instant
import java.util.UUID

/**
 * Domain model for Vehicle Observation
 * Core business entity for F.A.R.O.
 */
data class VehicleObservation(
    val id: String = UUID.randomUUID().toString(),
    val clientId: String, // For offline-first idempotency
    val plateNumber: String,
    val plateState: String? = null,
    val plateCountry: String = "BR",
    
    // Timestamps
    val observedAtLocal: Instant,
    val observedAtServer: Instant? = null,
    
    // Location
    val location: GeoLocation,
    val heading: Float? = null,
    val speed: Float? = null,
    
    // Vehicle details
    val vehicleColor: String? = null,
    val vehicleType: String? = null,
    val vehicleModel: String? = null,
    val vehicleYear: Int? = null,
    
    // References
    val agentId: String,
    val deviceId: String,
    
    // Sync status
    val syncStatus: SyncStatus = SyncStatus.PENDING,
    val syncAttempts: Int = 0,
    val syncedAt: Instant? = null,
    val syncError: String? = null,
    
    // Metadata
    val connectivityType: String? = null,
    val metadataSnapshot: Map<String, String>? = null,
    
    val createdAt: Instant = Instant.now(),
    val updatedAt: Instant = Instant.now(),
    
    // Relations
    val plateReads: List<PlateRead> = emptyList(),
    val suspicionReport: SuspicionReport? = null,
    val instantFeedback: InstantFeedback? = null
)

data class GeoLocation(
    val latitude: Double,
    val longitude: Double,
    val accuracy: Float? = null
)

data class PlateRead(
    val id: String = UUID.randomUUID().toString(),
    val observationId: String,
    val ocrRawText: String,
    val ocrConfidence: Float,
    val ocrEngine: String = "mlkit_v2",
    val imagePath: String? = null,
    val processedAt: Instant = Instant.now(),
    val processingTimeMs: Long? = null
)

data class SuspicionReport(
    val id: String = UUID.randomUUID().toString(),
    val observationId: String,
    val reason: SuspicionReason,
    val level: SuspicionLevel,
    val urgency: UrgencyLevel,
    val notes: String? = null,
    val imagePath: String? = null,
    val audioPath: String? = null,
    val audioDurationSeconds: Int? = null,
    val createdAt: Instant = Instant.now()
)

data class InstantFeedback(
    val hasAlert: Boolean = false,
    val alertLevel: String? = null,
    val alertTitle: String? = null,
    val alertMessage: String? = null,
    val previousObservationsCount: Int = 0,
    val isMonitored: Boolean = false,
    val intelligenceInterest: Boolean = false,
    val guidance: String? = null
)

enum class SyncStatus {
    PENDING,
    SYNCING,
    COMPLETED,
    FAILED
}

enum class SuspicionLevel {
    LOW, MEDIUM, HIGH
}

enum class UrgencyLevel {
    MONITOR, INTELLIGENCE, APPROACH
}

enum class SuspicionReason {
    STOLEN_VEHICLE,
    SUSPICIOUS_BEHAVIOR,
    WANTED_PLATE,
    UNUSUAL_HOURS,
    KNOWN_ASSOCIATE,
    DRUG_TRAFFICKING,
    WEAPONS,
    GANG_ACTIVITY,
    OTHER
}

enum class UserRole {
    FIELD_AGENT,
    INTELLIGENCE,
    SUPERVISOR,
    ADMIN
}
