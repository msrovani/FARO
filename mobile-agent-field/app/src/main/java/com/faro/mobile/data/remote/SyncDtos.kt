package com.faro.mobile.data.remote

import com.google.gson.annotations.SerializedName

data class SyncBatchRequestDto(
    @SerializedName("device_id")
    val deviceId: String,
    @SerializedName("app_version")
    val appVersion: String,
    val items: List<SyncItemDto>,
    @SerializedName("client_timestamp")
    val clientTimestamp: String
)

data class SyncItemDto(
    @SerializedName("entity_type")
    val entityType: String,
    @SerializedName("entity_local_id")
    val entityLocalId: String,
    val operation: String,
    val payload: Map<String, Any?>,
    @SerializedName("payload_hash")
    val payloadHash: String?,
    @SerializedName("created_at_local")
    val createdAtLocal: String
)

data class SyncBatchResponseDto(
    @SerializedName("processed_count")
    val processedCount: Int,
    @SerializedName("success_count")
    val successCount: Int,
    @SerializedName("failed_count")
    val failedCount: Int,
    val results: List<SyncResultDto>,
    @SerializedName("server_timestamp")
    val serverTimestamp: String,
    @SerializedName("pending_feedback")
    val pendingFeedback: List<PendingFeedbackDto> = emptyList()
)

data class SyncResultDto(
    @SerializedName("entity_local_id")
    val entityLocalId: String,
    @SerializedName("entity_server_id")
    val entityServerId: String? = null,
    val status: String,
    val error: String? = null,
    @SerializedName("synced_at")
    val syncedAt: String? = null
)

data class LoginRequestDto(
    @SerializedName("device_id")
    val deviceId: String? = null,
    val deviceModel: String? = null,
    val osVersion: String? = null,
    val appVersion: String? = null,
    @SerializedName("shift_duration_hours")
    val shiftDurationHours: Int? = null,
)

data class PendingFeedbackDto(
    @SerializedName("feedback_id")
    val feedbackId: String,
    @SerializedName("observation_id")
    val observationId: String,
    @SerializedName("plate_number")
    val plateNumber: String,
    @SerializedName("feedback_type")
    val feedbackType: String,
    val title: String,
    val message: String,
    @SerializedName("recommended_action")
    val recommendedAction: String? = null,
    @SerializedName("sent_at")
    val sentAt: String,
    @SerializedName("is_read")
    val isRead: Boolean,
    @SerializedName("read_at")
    val readAt: String? = null,
    @SerializedName("reviewer_name")
    val reviewerName: String,
)

data class MarkFeedbackReadRequestDto(
    @SerializedName("read_at")
    val readAt: String
)

data class AgentLocationBatchSyncDto(
    @SerializedName("items")
    val items: List<AgentLocationUpdateDto>,
    @SerializedName("device_id")
    val deviceId: String,
)

data class ShiftRenewalRequest(
    @SerializedName("shift_duration_hours")
    val shiftDurationHours: Int,
)

data class UploadAssetResponseDto(
    @SerializedName("asset_id")
    val assetId: String,
    @SerializedName("observation_id")
    val observationId: String,
    @SerializedName("asset_type")
    val assetType: String,
    @SerializedName("storage_bucket")
    val storageBucket: String,
    @SerializedName("storage_key")
    val storageKey: String,
    @SerializedName("content_type")
    val contentType: String,
    @SerializedName("size_bytes")
    val sizeBytes: Long,
    @SerializedName("checksum_sha256")
    val checksumSha256: String,
)

// Plate suspicion check (post-OCR alert)
data class PlateSuspicionCheckResponseDto(
    @SerializedName("plate_number")
    val plateNumber: String,
    @SerializedName("is_suspect")
    val isSuspect: Boolean,
    @SerializedName("alert_level")
    val alertLevel: String? = null,  // "info", "warning", "critical"
    @SerializedName("alert_title")
    val alertTitle: String? = null,
    @SerializedName("alert_message")
    val alertMessage: String? = null,
    @SerializedName("suspicion_reason")
    val suspicionReason: String? = null,
    @SerializedName("suspicion_level")
    val suspicionLevel: String? = null,
    @SerializedName("previous_observations_count")
    val previousObservationsCount: Int = 0,
    @SerializedName("is_monitored")
    val isMonitored: Boolean = false,
    @SerializedName("intelligence_interest")
    val intelligenceInterest: Boolean = false,
    @SerializedName("has_active_watchlist")
    val hasActiveWatchlist: Boolean = false,
    @SerializedName("watchlist_category")
    val watchlistCategory: String? = null,
    @SerializedName("guidance")
    val guidance: String? = null,
    @SerializedName("requires_approach_confirmation")
    val requiresApproachConfirmation: Boolean = false,
    @SerializedName("first_suspicion_agent_name")
    val firstSuspicionAgentName: String? = null,
    @SerializedName("first_suspicion_observation_id")
    val firstSuspicionObservationId: String? = null,
    @SerializedName("first_suspicion_at")
    val firstSuspicionAt: String? = null,
)

// Approach confirmation (field form submission)
data class ApproachConfirmationRequestDto(
    @SerializedName("confirmed_suspicion")
    val confirmedSuspicion: Boolean,
    @SerializedName("approach_outcome")
    val approachOutcome: String = "approached",
    val notes: String? = null,
    @SerializedName("approached_at_local")
    val approachedAtLocal: String,
    val location: LocationDto? = null,
    // Additional fields for the slider and switches
    @SerializedName("suspicion_level_slider")
    val suspicionLevelSlider: Int? = null,  // 0-100
    @SerializedName("was_approached")
    val wasApproached: Boolean = true,
    @SerializedName("has_incident")
    val hasIncident: Boolean = false,
    @SerializedName("street_direction")
    val streetDirection: String? = null,
)

data class LocationDto(
    val latitude: Double,
    val longitude: Double,
    val accuracy: Float? = null,
)

data class ApproachConfirmationResponseDto(
    @SerializedName("observation_id")
    val observationId: String,
    @SerializedName("plate_number")
    val plateNumber: String,
    @SerializedName("confirmed_suspicion")
    val confirmedSuspicion: Boolean,
    @SerializedName("approach_outcome")
    val approachOutcome: String,
    @SerializedName("notified_original_agent")
    val notifiedOriginalAgent: Boolean,
    @SerializedName("original_agent_id")
    val originalAgentId: String? = null,
    @SerializedName("original_agent_name")
    val originalAgentName: String? = null,
    @SerializedName("feedback_event_id")
    val feedbackEventId: String? = null,
    @SerializedName("processed_at")
    val processedAt: String,
)
