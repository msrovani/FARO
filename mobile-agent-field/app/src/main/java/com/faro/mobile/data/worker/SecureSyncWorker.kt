package com.faro.mobile.data.worker

import android.content.Context
import androidx.hilt.work.HiltWorker
import androidx.work.CoroutineWorker
import androidx.work.WorkerParameters
import com.faro.mobile.BuildConfig
import com.faro.mobile.data.remote.FaroMobileApi
import com.faro.mobile.data.remote.SyncBatchRequestDto
import com.faro.mobile.data.remote.SyncItemDto
import com.faro.mobile.data.security.SecureImageStorage
import com.faro.mobile.data.security.SecureObservationStorage
import com.faro.mobile.data.session.SessionRepository
import dagger.assisted.Assisted
import dagger.assisted.AssistedInject
import okhttp3.MediaType.Companion.toMediaTypeOrNull
import okhttp3.MultipartBody
import okhttp3.RequestBody.Companion.toRequestBody
import timber.log.Timber
import java.security.MessageDigest
import java.time.Instant
import java.util.Locale

/**
 * Secure sync worker implementing zero-trust mobile architecture.
 * 
 * SECURITY PRINCIPLES:
 * - Data encrypted at rest in local storage
 * - Decrypted only in memory for transmission
 * - Secure deletion (DoD 5220.22-M) after server confirmation
 * - TTL-based auto-destruction (24h)
 * 
 * FLOW:
 * 1. Read encrypted observations from secure storage
 * 2. Decrypt in memory
 * 3. Send to server via HTTPS/TLS 1.3
 * 4. Receive confirmation + server IDs
 * 5. Upload associated images (encrypted → decrypt → upload)
 * 6. Securely delete local data after confirmation
 * 7. Process server feedback
 */
@HiltWorker
class SecureSyncWorker @AssistedInject constructor(
    @Assisted appContext: Context,
    @Assisted workerParams: WorkerParameters,
    private val observationStorage: SecureObservationStorage,
    private val imageStorage: SecureImageStorage,
    private val faroMobileApi: FaroMobileApi,
    private val sessionRepository: SessionRepository,
) : CoroutineWorker(appContext, workerParams) {

    override suspend fun doWork(): Result {
        return try {
            Timber.d("Starting secure sync")
            
            // Refresh token if needed
            sessionRepository.refreshTokenIfNeeded()
            
            // Get pending observations
            val pending = observationStorage.listPending()
            
            if (pending.isEmpty()) {
                Timber.d("No pending observations to sync")
                return Result.success()
            }
            
            Timber.d("Syncing ${pending.size} observations securely")
            
            // Prepare batch
            val items = pending.map { observation ->
                val payload = observation.toSyncPayload()
                SyncItemDto(
                    entityType = "observation",
                    entityLocalId = observation.localId,
                    operation = "create",
                    payload = payload,
                    payloadHash = payload.toStableHash(),
                    createdAtLocal = observation.observedAtLocal.toString()
                )
            }
            
            val request = SyncBatchRequestDto(
                deviceId = pending.firstOrNull()?.deviceId ?: "unknown",
                appVersion = BuildConfig.VERSION_NAME,
                items = items,
                clientTimestamp = Instant.now().toString()
            )
            
            // Send to server
            val response = faroMobileApi.syncBatch(request)
            
            // Process results
            var successCount = 0
            var failCount = 0
            
            response.results.forEach { result ->
                when (result.status.lowercase(Locale.ROOT)) {
                    "completed", "success" -> {
                        // CRITICAL: Server confirmed receipt - now secure delete
                        result.entityServerId?.let { serverId ->
                            handleSuccessfulSync(result.entityLocalId, serverId)
                            successCount++
                        } ?: run {
                            // No server ID - treat as partial failure
                            Timber.w("No server ID for ${result.entityLocalId}")
                            failCount++
                        }
                    }
                    else -> {
                        // Sync failed - keep for retry
                        Timber.w("Sync failed for ${result.entityLocalId}: ${result.error}")
                        failCount++
                    }
                }
            }
            
            // Process feedback from server
            if (response.pendingFeedback.isNotEmpty()) {
                Timber.d("Received ${response.pendingFeedback.size} feedback items")
                sessionRepository.savePendingFeedback(response.pendingFeedback)
            }
            
            Timber.d("Secure sync completed: $successCount success, $failCount failed")
            
            // Retry if any failed
            if (failCount > 0) Result.retry() else Result.success()
            
        } catch (e: Exception) {
            Timber.e(e, "Secure sync failed")
            Result.retry()
        }
    }
    
    /**
     * Handle successful sync - upload assets and securely delete.
     * This is the CRITICAL security point where local data is eliminated.
     */
    private suspend fun handleSuccessfulSync(localId: String, serverId: String) {
        Timber.d("Handling successful sync for $localId -> server ID: $serverId")
        
        try {
            // Step 1: Upload associated images (if any)
            uploadImagesIfAny(localId, serverId)
            
            // Step 2: Securely delete all local data
            secureDeleteObservation(localId)
            
            Timber.i("Successfully synced and deleted observation $localId")
            
        } catch (e: Exception) {
            Timber.e(e, "Error in post-sync cleanup for $localId")
            // Don't throw - we've already synced, just log
        }
    }
    
    /**
     * Upload images associated with observation.
     * Images are decrypted in memory, uploaded, then cleared from memory.
     */
    private suspend fun uploadImagesIfAny(localId: String, serverId: String) {
        // Check for plate image
        val observation = observationStorage.retrieve(localId)
        val hasPlateImage = observation?.plateImageEncryptedRef != null
        
        if (hasPlateImage && imageStorage.exists(localId)) {
            uploadImageSecure(localId, serverId, "plate_image")
        }
        
        // Check for suspicion images (if implemented)
        // val suspicionImageId = "${localId}_suspicion"
        // if (imageStorage.exists(suspicionImageId)) {
        //     uploadImageSecure(suspicionImageId, serverId, "suspicion_image")
        // }
    }
    
    /**
     * Upload single image securely.
     * Decrypts to memory, uploads, clears memory.
     */
    private suspend fun uploadImageSecure(
        localImageId: String,
        serverObservationId: String,
        assetType: String
    ) {
        // Decrypt to memory
        val imageBytes = imageStorage.retrieveForUpload(localImageId)
        if (imageBytes == null) {
            Timber.w("Image not found for upload: $localImageId")
            return
        }
        
        try {
            // Prepare multipart upload
            val mimeType = "image/jpeg".toMediaTypeOrNull()
            val requestBody = imageBytes.toRequestBody(mimeType)
            val filePart = MultipartBody.Part.createFormData(
                "file",
                "$localImageId.jpg",
                requestBody
            )
            val typePart = assetType.toRequestBody("text/plain".toMediaTypeOrNull())
            
            // Upload
            val response = faroMobileApi.uploadObservationAsset(
                observationId = serverObservationId,
                assetType = typePart,
                file = filePart
            )
            
            Timber.d("Uploaded $assetType for $serverObservationId -> ${response.storageBucket}/${response.storageKey}")
            
        } catch (e: Exception) {
            Timber.e(e, "Failed to upload image $localImageId for observation $serverObservationId")
            // Don't rethrow - we'll keep the image for retry
            throw e
        } finally {
            // CRITICAL: Clear decrypted data from memory
            imageBytes.fill(0)
            Timber.v("Cleared image bytes from memory for $localImageId")
        }
    }
    
    /**
     * Securely delete observation and all associated data.
     * Implements secure wipe per DoD 5220.22-M standard.
     */
    private fun secureDeleteObservation(localId: String) {
        Timber.d("Initiating secure deletion for observation $localId")
        
        // Step 1: Delete encrypted image
        imageStorage.secureDelete(localId)
        
        // Step 2: Delete encrypted observation data
        observationStorage.secureDelete(localId)
        
        // Step 3: Force garbage collection hint
        System.gc()
        
        Timber.d("Secure deletion completed for observation $localId")
    }
    
    companion object {
        const val WORK_NAME = "secure_observation_sync"
    }
}

/**
 * Calculate stable hash for payload integrity verification.
 * Used to detect tampering during sync.
 */
private fun Map<String, Any?>.toStableHash(): String {
    val normalized = canonicalize(this)
    val digest = MessageDigest.getInstance("SHA-256").digest(normalized.toByteArray())
    return digest.joinToString("") { "%02x".format(it) }
}

private fun canonicalize(value: Any?): String {
    return when (value) {
        null -> "null"
        is Map<*, *> -> value.entries
            .sortedBy { it.key?.toString() ?: "" }
            .joinToString(prefix = "{", postfix = "}") { (k, v) ->
                "\"${k?.toString() ?: ""}\":${canonicalize(v)}"
            }
        is List<*> -> value.joinToString(prefix = "[", postfix = "]") { canonicalize(it) }
        is String -> "\"$value\""
        is Number, is Boolean -> value.toString()
        else -> "\"${value.toString()}\""
    }
}
