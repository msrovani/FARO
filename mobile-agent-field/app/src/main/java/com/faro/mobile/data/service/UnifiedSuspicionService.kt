package com.faro.mobile.data.service

import android.content.Context
import com.faro.mobile.domain.model.*
import com.faro.mobile.data.remote.SuspicionCaptureRequestDto
import com.faro.mobile.data.remote.SuspicionApproachRequestDto
import com.faro.mobile.data.remote.UnifiedSuspicionResponseDto
import com.faro.mobile.data.remote.SuspicionContextResponseDto
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import timber.log.Timber
import java.time.Instant
import java.util.*
import javax.inject.Inject
import javax.inject.Singleton

/**
 * Unified Suspicion Service for F.A.R.O.
 * Handles capture, approach, feedback, and context for vehicle suspicions
 */
@Singleton
class UnifiedSuspicionService @Inject constructor(
    private val context: Context,
    private val apiService: FaroMobileApi,
    private val sessionRepository: SessionRepository
) {
    
    companion object {
        private const val TAG = "UnifiedSuspicionService"
    }
    
    /**
     * Capture initial suspicion from field agent
     */
    suspend fun captureSuspicion(
        observationId: String,
        reason: SuspicionReason,
        level: SuspicionLevel,
        urgency: UrgencyLevel,
        notes: String? = null,
        evidenceUrls: List<String>? = null
    ): Result<UnifiedSuspicionReport> = withContext(Dispatchers.IO) {
        try {
            val request = SuspicionCaptureRequestDto(
                observationId = observationId,
                reason = reason.name.lowercase(),
                level = level.name.lowercase(),
                urgency = urgency.name.lowercase(),
                notes = notes,
                evidenceUrls = evidenceUrls
            )
            
            val response = apiService.captureSuspicion(request)
            
            if (response.isSuccessful && response.body() != null) {
                val suspicionResponse = response.body()!!
                val unifiedReport = convertToUnifiedReport(suspicionResponse)
                
                Timber.d(TAG, "Successfully captured suspicion: ${unifiedReport.id}")
                Result.success(unifiedReport)
            } else {
                val error = "Failed to capture suspicion: ${response.code()} ${response.message()}"
                Timber.e(TAG, error)
                Result.failure(Exception(error))
            }
            
        } catch (e: Exception) {
            Timber.e(e, "Exception during suspicion capture")
            Result.failure(e)
        }
    }
    
    /**
     * Confirm vehicle approach with detailed feedback
     */
    suspend fun confirmApproach(
        suspicionId: String,
        confirmedSuspicion: Boolean,
        approachLevel: Int, // 0-100
        hasIncident: Boolean,
        incidentType: IncidentType? = null,
        notes: String? = null,
        evidenceUrls: List<String>? = null
    ): Result<UnifiedSuspicionReport> = withContext(Dispatchers.IO) {
        try {
            val request = SuspicionApproachRequestDto(
                suspicionId = suspicionId,
                confirmedSuspicion = confirmedSuspicion,
                approachLevel = approachLevel,
                hasIncident = hasIncident,
                incidentType = incidentType?.name?.lowercase(),
                notes = notes,
                evidenceUrls = evidenceUrls
            )
            
            val response = apiService.confirmApproach(request)
            
            if (response.isSuccessful && response.body() != null) {
                val suspicionResponse = response.body()!!
                val unifiedReport = convertToUnifiedReport(suspicionResponse)
                
                Timber.d(TAG, "Successfully confirmed approach: ${unifiedReport.id}")
                Result.success(unifiedReport)
            } else {
                val error = "Failed to confirm approach: ${response.code()} ${response.message()}"
                Timber.e(TAG, error)
                Result.failure(Exception(error))
            }
            
        } catch (e: Exception) {
            Timber.e(e, "Exception during approach confirmation")
            Result.failure(e)
        }
    }
    
    /**
     * Get complete context for approaching a vehicle
     */
    suspend fun getSuspicionContext(observationId: String): Result<SuspicionContext> = withContext(Dispatchers.IO) {
        try {
            val response = apiService.getSuspicionContext(observationId)
            
            if (response.isSuccessful && response.body() != null) {
                val contextResponse = response.body()!!
                val context = convertToSuspicionContext(contextResponse)
                
                Timber.d(TAG, "Successfully retrieved suspicion context for: $observationId")
                Result.success(context)
            } else {
                val error = "Failed to get suspicion context: ${response.code()} ${response.message()}"
                Timber.e(TAG, error)
                Result.failure(Exception(error))
            }
            
        } catch (e: Exception) {
            Timber.e(e, "Exception during context retrieval")
            Result.failure(e)
        }
    }
    
    /**
     * Get suspicion history for a plate
     */
    suspend fun getSuspicionHistory(
        plateNumber: String,
        limit: Int = 10
    ): Result<List<UnifiedSuspicionReport>> = withContext(Dispatchers.IO) {
        try {
            val response = apiService.getSuspicionHistory(plateNumber, limit)
            
            if (response.isSuccessful && response.body() != null) {
                val historyResponse = response.body()!!
                val history = historyResponse.history.map { convertToUnifiedReport(it) }
                
                Timber.d(TAG, "Successfully retrieved suspicion history for: $plateNumber")
                Result.success(history)
            } else {
                val error = "Failed to get suspicion history: ${response.code()} ${response.message()}"
                Timber.e(TAG, error)
                Result.failure(Exception(error))
            }
            
        } catch (e: Exception) {
            Timber.e(e, "Exception during history retrieval")
            Result.failure(e)
        }
    }
    
    /**
     * Get suspicion details by ID
     */
    suspend fun getSuspicionById(suspicionId: String): Result<UnifiedSuspicionReport> = withContext(Dispatchers.IO) {
        try {
            val response = apiService.getSuspicion(suspicionId)
            
            if (response.isSuccessful && response.body() != null) {
                val suspicionResponse = response.body()!!
                val unifiedReport = convertToUnifiedReport(suspicionResponse)
                
                Timber.d(TAG, "Successfully retrieved suspicion: $suspicionId")
                Result.success(unifiedReport)
            } else {
                val error = "Failed to get suspicion: ${response.code()} ${response.message()}"
                Timber.e(TAG, error)
                Result.failure(Exception(error))
            }
            
        } catch (e: Exception) {
            Timber.e(e, "Exception during suspicion retrieval")
            Result.failure(e)
        }
    }
    
    /**
     * Get available suspicion reasons
     */
    suspend fun getSuspicionReasons(): Result<List<SuspicionReasonOption>> = withContext(Dispatchers.IO) {
        try {
            val response = apiService.getSuspicionReasons()
            
            if (response.isSuccessful && response.body() != null) {
                val reasons = response.body()!!.map { reason ->
                    SuspicionReasonOption(
                        value = reason.value,
                        label = reason.label
                    )
                }
                
                Result.success(reasons)
            } else {
                val error = "Failed to get suspicion reasons: ${response.code()}"
                Result.failure(Exception(error))
            }
            
        } catch (e: Exception) {
            Timber.e(e, "Exception during reasons retrieval")
            Result.failure(e)
        }
    }
    
    /**
     * Get available urgency levels
     */
    suspend fun getUrgencyLevels(): Result<List<UrgencyLevelOption>> = withContext(Dispatchers.IO) {
        try {
            val response = apiService.getUrgencyLevels()
            
            if (response.isSuccessful && response.body() != null) {
                val urgencies = response.body()!!.map { urgency ->
                    UrgencyLevelOption(
                        value = urgency.value,
                        label = urgency.label
                    )
                }
                
                Result.success(urgencies)
            } else {
                val error = "Failed to get urgency levels: ${response.code()}"
                Result.failure(Exception(error))
            }
            
        } catch (e: Exception) {
            Timber.e(e, "Exception during urgencies retrieval")
            Result.failure(e)
        }
    }
    
    /**
     * Get available incident types
     */
    suspend fun getIncidentTypes(): Result<List<IncidentTypeOption>> = withContext(Dispatchers.IO) {
        try {
            val response = apiService.getIncidentTypes()
            
            if (response.isSuccessful && response.body() != null) {
                val incidents = response.body()!!.map { incident ->
                    IncidentTypeOption(
                        value = incident.value,
                        label = incident.label
                    )
                }
                
                Result.success(incidents)
            } else {
                val error = "Failed to get incident types: ${response.code()}"
                Result.failure(Exception(error))
            }
            
        } catch (e: Exception) {
            Timber.e(e, "Exception during incident types retrieval")
            Result.failure(e)
        }
    }
    
    /**
     * Validate suspicion data before submission
     */
    fun validateSuspicionData(
        reason: SuspicionReason?,
        level: SuspicionLevel?,
        urgency: UrgencyLevel?,
        notes: String?
    ): ValidationResult {
        val errors = mutableListOf<String>()
        
        if (reason == null) {
            errors.add("Motivo da suspeição é obrigatório")
        }
        
        if (level == null) {
            errors.add("Nível da suspeição é obrigatório")
        }
        
        if (urgency == null) {
            errors.add("Nível de urgência é obrigatório")
        }
        
        if (notes != null && notes.length > 500) {
            errors.add("Notas não podem exceder 500 caracteres")
        }
        
        return ValidationResult(
            isValid = errors.isEmpty(),
            errors = errors
        )
    }
    
    /**
     * Validate approach data before submission
     */
    fun validateApproachData(
        approachLevel: Int,
        hasIncident: Boolean,
        notes: String?
    ): ValidationResult {
        val errors = mutableListOf<String>()
        
        if (approachLevel < 0 || approachLevel > 100) {
            errors.add("Nível de abordagem deve estar entre 0 e 100")
        }
        
        if (hasIncident && notes?.isBlank() == true) {
            errors.add("Notas são obrigatórias quando há ocorrência")
        }
        
        if (notes != null && notes.length > 1000) {
            errors.add("Notas não podem exceder 1000 caracteres")
        }
        
        return ValidationResult(
            isValid = errors.isEmpty(),
            errors = errors
        )
    }
    
    private fun convertToUnifiedReport(response: UnifiedSuspicionResponseDto): UnifiedSuspicionReport {
        return UnifiedSuspicionReport(
            id = response.id,
            observationId = response.observationId,
            agentId = response.agentId,
            initialReason = SuspicionReason.valueOf(response.initialReason.uppercase()),
            initialLevel = SuspicionLevel.valueOf(response.initialLevel.uppercase()),
            initialUrgency = UrgencyLevel.valueOf(response.initialUrgency.uppercase()),
            initialNotes = response.initialNotes,
            initialEvidence = emptyList(), // Would be populated if API returns evidence
            wasApproached = response.wasApproached,
            approachConfirmedSuspicion = response.approachConfirmedSuspicion,
            approachLevel = response.approachLevel,
            approachNotes = response.approachNotes,
            approachEvidence = emptyList(), // Would be populated if API returns evidence
            hasIncident = response.hasIncident,
            incidentType = response.incidentType?.let { IncidentType.valueOf(it.uppercase()) },
            incidentReport = null, // Would be populated if API returns incident report
            status = SuspicionStatus.valueOf(response.status.uppercase()),
            priority = response.priority,
            previousApproaches = emptyList(), // Would be populated if API returns history
            createdAt = Instant.parse(response.createdAt),
            updatedAt = Instant.parse(response.updatedAt),
            approachedAt = response.approachedAt?.let { Instant.parse(it) }
        )
    }
    
    private fun convertToSuspicionContext(response: SuspicionContextResponseDto): SuspicionContext {
        return SuspicionContext(
            currentSuspicion = response.currentSuspicion?.let { convertToUnifiedReport(it) },
            suspicionHistory = response.suspicionHistory.map { 
                // Convert history items to appropriate format
                mapOf("data" to it)
            },
            agentFeedback = response.agentFeedback.map {
                // Convert feedback items to appropriate format
                mapOf("data" to it)
            },
            recommendations = response.recommendations,
            plateNumber = response.plateNumber,
            generatedAt = Instant.parse(response.generatedAt)
        )
    }
}

// Data classes for unified models
data class UnifiedSuspicionReport(
    val id: String,
    val observationId: String,
    val agentId: String,
    val initialReason: SuspicionReason,
    val initialLevel: SuspicionLevel,
    val initialUrgency: UrgencyLevel,
    val initialNotes: String?,
    val initialEvidence: List<Evidence>,
    val wasApproached: Boolean,
    val approachConfirmedSuspicion: Boolean,
    val approachLevel: Int,
    val approachNotes: String?,
    val approachEvidence: List<Evidence>,
    val hasIncident: Boolean,
    val incidentType: IncidentType?,
    val incidentReport: String?,
    val status: SuspicionStatus,
    val priority: Int,
    val previousApproaches: List<ApproachHistory>,
    val createdAt: Instant,
    val updatedAt: Instant,
    val approachedAt: Instant?
)

data class Evidence(
    val id: String = UUID.randomUUID().toString(),
    val type: String = "image",
    val url: String = "",
    val description: String = "",
    val timestamp: Instant = Instant.now(),
    val metadata: Map<String, Any> = emptyMap()
)

data class ApproachHistory(
    val id: String = UUID.randomUUID().toString(),
    val agentId: String,
    val agentName: String,
    val approachTime: Instant,
    val confirmedSuspicion: Boolean,
    val approachLevel: Int,
    val hasIncident: Boolean,
    val incidentType: IncidentType?,
    val notes: String = "",
    val evidence: List<Evidence> = emptyList()
)

data class SuspicionContext(
    val currentSuspicion: UnifiedSuspicionReport?,
    val suspicionHistory: List<Map<String, Any>>,
    val agentFeedback: List<Map<String, Any>>,
    val recommendations: List<Map<String, Any>>,
    val plateNumber: String,
    val generatedAt: Instant
)

data class SuspicionReasonOption(
    val value: String,
    val label: String
)

data class UrgencyLevelOption(
    val value: String,
    val label: String
)

data class IncidentTypeOption(
    val value: String,
    val label: String
)

data class ValidationResult(
    val isValid: Boolean,
    val errors: List<String>
)

// Additional enums for unified system
enum class SuspicionStatus {
    PENDING_APPROACH,
    APPROACHED,
    CONFIRMED,
    FALSE_POSITIVE,
    RESOLVED
}

enum class IncidentType {
    TRAFFIC_VIOLATION,
    ARREST,
    WARNING,
    SEARCH,
    CITATION,
    OTHER
}
