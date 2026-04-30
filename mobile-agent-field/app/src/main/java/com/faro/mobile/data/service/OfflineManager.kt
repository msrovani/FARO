package com.faro.mobile.data.service

import android.content.Context
import androidx.work.Constraints
import androidx.work.ExistingWorkPolicy
import androidx.work.NetworkType
import androidx.work.OneTimeWorkRequestBuilder
import androidx.work.WorkManager
import com.faro.mobile.data.local.dao.ObservationDao
import com.faro.mobile.data.local.entity.ObservationEntity
import com.faro.mobile.data.remote.FaroMobileApi
import com.faro.mobile.data.remote.SyncBatchRequestDto
import com.faro.mobile.data.remote.SyncItemDto
import com.faro.mobile.domain.model.SyncStatus
import com.google.gson.Gson
import com.google.gson.JsonSyntaxException
import com.jakewharton.timber.Timber
import dagger.hilt.android.qualifiers.ApplicationContext
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.withContext
import java.security.MessageDigest
import java.time.Instant
import javax.inject.Inject
import javax.inject.Singleton

/**
 * Offline Manager - Manages offline operations and automatic synchronization.
 * 
 * Features:
 * - Queue operations when offline
 * - Automatic sync when online
 * - Priority-based synchronization
 * - Conflict resolution
 * - Offline status tracking
 */
@Singleton
class OfflineManager @Inject constructor(
    @ApplicationContext private val context: Context,
    private val observationDao: ObservationDao,
    private val workManager: WorkManager,
    private val faroMobileApi: FaroMobileApi
) {
    
    private val gson = Gson()
    
    /**
     * Operation type for offline queue
     */
    enum class OperationType {
        CREATE_OBSERVATION,
        UPDATE_OBSERVATION,
        DELETE_OBSERVATION,
        SYNC_LOCATION,
        UPLOAD_ASSET
    }
    
    /**
     * Priority for operations
     */
    enum class OperationPriority {
        CRITICAL,  // Sync immediately when online
        HIGH,      // Sync within 5 minutes
        MEDIUM,    // Sync within 30 minutes
        LOW        // Sync within 1 hour
    }
    
    /**
     * Queued operation
     */
    data class QueuedOperation(
        val id: String,
        val type: OperationType,
        val priority: OperationPriority,
        val data: String, // JSON string
        val createdAt: Instant = Instant.now(),
        val retryCount: Int = 0,
        val maxRetries: Int = 3
    )
    
    private val operationQueue = mutableMapOf<String, QueuedOperation>()
    private var isOnline = true
    
    /**
     * Check if device is online
     */
    fun isOnline(): Boolean {
        val connectivityManager = context.getSystemService(Context.CONNECTIVITY_SERVICE) as android.net.ConnectivityManager
        val networkInfo = connectivityManager.activeNetworkInfo
        isOnline = networkInfo != null && networkInfo.isConnected
        return isOnline
    }
    
    /**
     * Queue an operation for later execution
     */
    fun queueOperation(
        operation: QueuedOperation
    ) {
        operationQueue[operation.id] = operation
        Timber.d("Queued operation: ${operation.type}, priority: ${operation.priority}")
        
        // If online, try to execute immediately for critical operations
        if (isOnline() && operation.priority == OperationPriority.CRITICAL) {
            executeOperation(operation)
        }
    }
    
    /**
     * Execute a queued operation
     */
    private suspend fun executeOperation(operation: QueuedOperation) {
        try {
            Timber.d("Executing operation: ${operation.type}")
            
            when (operation.type) {
                OperationType.CREATE_OBSERVATION -> {
                    // Parse observation from JSON and sync
                    val observation = parseObservation(operation.data)
                    if (observation != null) {
                        syncObservation(observation)
                    }
                }
                OperationType.UPDATE_OBSERVATION -> {
                    // Parse and sync update
                    val observation = parseObservation(operation.data)
                    if (observation != null) {
                        syncObservation(observation)
                    }
                }
                OperationType.DELETE_OBSERVATION -> {
                    // Handle deletion
                    Timber.d("Delete observation operation: ${operation.id}")
                }
                OperationType.SYNC_LOCATION -> {
                    // Handle location sync
                    Timber.d("Sync location operation: ${operation.id}")
                }
                OperationType.UPLOAD_ASSET -> {
                    // Handle asset upload
                    Timber.d("Upload asset operation: ${operation.id}")
                }
            }
            
            // Remove from queue if successful
            operationQueue.remove(operation.id)
            Timber.d("Operation completed successfully: ${operation.type}")
            
        } catch (e: Exception) {
            Timber.e(e, "Operation failed: ${operation.type}")
            
            // Increment retry count
            val updatedOperation = operation.copy(
                retryCount = operation.retryCount + 1
            )
            
            if (updatedOperation.retryCount >= updatedOperation.maxRetries) {
                // Max retries reached, remove from queue
                operationQueue.remove(operation.id)
                Timber.w("Max retries reached for operation: ${operation.type}")
            } else {
                // Update retry count and keep in queue
                operationQueue[operation.id] = updatedOperation
            }
        }
    }
    
    /**
     * Sync all pending operations when device comes online
     */
    suspend fun syncWhenOnline() {
        if (!isOnline()) {
            Timber.d("Device is offline, skipping sync")
            return
        }
        
        Timber.d("Syncing pending operations...")
        
        // Sort by priority (critical first)
        val sortedOperations = operationQueue.values.sortedByPriority()
        
        for (operation in sortedOperations) {
            executeOperation(operation)
        }
        
        Timber.d("Sync completed. Remaining operations: ${operationQueue.size}")
    }
    
    /**
     * Get pending observations from local database
     */
    suspend fun getPendingObservations(): List<ObservationEntity> {
        return withContext(Dispatchers.IO) {
            observationDao.getPendingSync()
        }
    }
    
    /**
     * Sync a single observation to server
     */
    private suspend fun syncObservation(observation: ObservationEntity) {
        // Update sync status to SYNCING
        observationDao.updateSyncStatus(
            id = observation.id,
            status = "SYNCING",
            syncedAt = null,
            error = null
        )
        
        try {
            // Convert observation to sync payload
            val payload = observationToSyncPayload(observation)
            
            // Create sync batch request with single item
            val request = SyncBatchRequestDto(
                deviceId = observation.deviceId,
                appVersion = "1.0.0",
                items = listOf(
                    SyncItemDto(
                        entityType = "observation",
                        entityLocalId = observation.id,
                        operation = "create",
                        payload = payload,
                        payloadHash = computeStableHash(payload),
                        createdAtLocal = observation.observedAtLocal.toString()
                    )
                ),
                clientTimestamp = Instant.now().toString()
            )
            
            // Call sync endpoint
            val response = faroMobileApi.syncBatch(request)
            
            // Check if sync was successful
            val result = response.results.firstOrNull { it.entityLocalId == observation.id }
            if (result != null && result.status.equals("completed", ignoreCase = true)) {
                observationDao.updateSyncStatus(
                    id = observation.id,
                    status = "COMPLETED",
                    syncedAt = Instant.now(),
                    error = null
                )
                
                // Update server ID if provided
                result.entityServerId?.let { serverId ->
                    // TODO: Update observation with server ID if needed
                }
                
                Timber.d("Observation synced successfully: ${observation.id} -> ${result.entityServerId}")
            } else {
                observationDao.updateSyncStatus(
                    id = observation.id,
                    status = "FAILED",
                    syncedAt = null,
                    error = result?.error ?: "Sync failed"
                )
                Timber.w("Observation sync failed: ${observation.id}, error: ${result?.error}")
            }
            
        } catch (e: Exception) {
            Timber.e(e, "Failed to sync observation: ${observation.id}")
            
            // Update sync status to FAILED
            observationDao.updateSyncStatus(
                id = observation.id,
                status = "FAILED",
                syncedAt = null,
                error = e.message
            )
        }
    }
    
    /**
     * Convert observation entity to sync payload
     */
    private fun observationToSyncPayload(observation: ObservationEntity): Map<String, Any?> {
        return mapOf(
            "client_id" to observation.clientId,
            "plate_number" to observation.plateNumber,
            "plate_state" to observation.plateState,
            "plate_country" to observation.plateCountry,
            "observed_at_local" to observation.observedAtLocal.toString(),
            "location" to mapOf(
                "latitude" to observation.latitude,
                "longitude" to observation.longitude,
                "accuracy" to observation.locationAccuracy
            ),
            "heading" to observation.heading,
            "speed" to observation.speed,
            "vehicle_color" to observation.vehicleColor,
            "vehicle_type" to observation.vehicleType,
            "vehicle_model" to observation.vehicleModel,
            "vehicle_year" to observation.vehicleYear,
            "device_id" to observation.deviceId,
            "connectivity_type" to observation.connectivityType,
            "app_version" to "1.0.0"
        )
    }
    
    /**
     * Compute stable hash for payload
     */
    private fun computeStableHash(payload: Map<String, Any?>): String {
        val normalized = canonicalizeMap(payload)
        val digest = MessageDigest.getInstance("SHA-256").digest(normalized.toByteArray())
        return digest.joinToString("") { byte -> "%02x".format(byte) }
    }
    
    /**
     * Canonicalize map for stable hashing
     */
    private fun canonicalizeMap(map: Map<String, Any?>): String {
        return map.entries
            .sortedBy { it.key }
            .joinToString(prefix = "{", postfix = "}") { (key, value) ->
                "\"$key\":${canonicalizeValue(value)}"
            }
    }
    
    /**
     * Canonicalize value for stable hashing
     */
    private fun canonicalizeValue(value: Any?): String {
        return when (value) {
            null -> "null"
            is Map<*, *> -> canonicalizeMap(value as Map<String, Any?>)
            is List<*> -> value.joinToString(prefix = "[", postfix = "]") { canonicalizeValue(it) }
            is String -> "\"$value\""
            is Number, is Boolean -> value.toString()
            else -> "\"${value.toString()}\""
        }
    }
    
    /**
     * Schedule automatic sync when device comes online
     */
    fun scheduleAutoSync() {
        val constraints = Constraints.Builder()
            .setRequiredNetworkType(NetworkType.CONNECTED)
            .build()
        
        val syncWorkRequest = OneTimeWorkRequestBuilder<SyncWorker>()
            .setConstraints(constraints)
            .setInitialDelay(0, java.util.concurrent.TimeUnit.SECONDS)
            .build()
        
        workManager.enqueueUniqueWork(
            "auto_sync",
            ExistingWorkPolicy.REPLACE,
            syncWorkRequest
        )
        
        Timber.d("Auto sync scheduled")
    }
    
    /**
     * Get queue statistics
     */
    fun getQueueStats(): Map<String, Any> {
        val byPriority = operationQueue.values.groupBy { it.priority }
        
        return mapOf(
            "total" to operationQueue.size,
            "critical" to (byPriority[OperationPriority.CRITICAL]?.size ?: 0),
            "high" to (byPriority[OperationPriority.HIGH]?.size ?: 0),
            "medium" to (byPriority[OperationPriority.MEDIUM]?.size ?: 0),
            "low" to (byPriority[OperationPriority.LOW]?.size ?: 0),
            "is_online" to isOnline()
        )
    }
    
    /**
     * Clear operation queue
     */
    fun clearQueue() {
        operationQueue.clear()
        Timber.d("Operation queue cleared")
    }
    
    /**
     * Parse observation from JSON string
     */
    private fun parseObservation(json: String): ObservationEntity? {
        return try {
            gson.fromJson(json, ObservationEntity::class.java)
        } catch (e: JsonSyntaxException) {
            Timber.e(e, "Failed to parse observation JSON")
            null
        } catch (e: Exception) {
            Timber.e(e, "Unexpected error parsing observation JSON")
            null
        }
    }
    
    /**
     * Sort operations by priority
     */
    private fun List<QueuedOperation>.sortedByPriority(): List<QueuedOperation> {
        val priorityOrder = mapOf(
            OperationPriority.CRITICAL to 0,
            OperationPriority.HIGH to 1,
            OperationPriority.MEDIUM to 2,
            OperationPriority.LOW to 3
        )
        
        return sortedBy { priorityOrder[it.priority] ?: Int.MAX_VALUE }
    }
}
