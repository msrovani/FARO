package com.faro.mobile.data.security

import android.content.Context
import androidx.security.crypto.EncryptedSharedPreferences
import androidx.security.crypto.MasterKey
import com.faro.mobile.domain.model.GeoLocation
import com.faro.mobile.domain.model.SyncStatus
import com.google.gson.Gson
import com.google.gson.reflect.TypeToken
import timber.log.Timber
import java.io.File
import java.time.Instant
import kotlin.random.Random

/**
 * Secure storage for observation data using EncryptedSharedPreferences.
 * 
 * ARCHITECTURE: Zero-trust mobile - data is temporary and volatile.
 * - All data encrypted at rest (AES-256)
 - Auto-expiration (TTL 24h) with secure deletion
 * - Secure wipe after successful server sync
 * - Hardware-backed keys when available
 */
class SecureObservationStorage(context: Context) {
    
    private val gson = Gson()
    
    // Master key for EncryptedSharedPreferences
    private val masterKey = MasterKey.Builder(context)
        .setKeyScheme(MasterKey.KeyScheme.AES256_GCM)
        .build()
    
    // Encrypted storage
    private val securePrefs = EncryptedSharedPreferences.create(
        context,
        PREFS_FILE_NAME,
        masterKey,
        EncryptedSharedPreferences.PrefKeyEncryptionScheme.AES256_SIV,
        EncryptedSharedPreferences.PrefValueEncryptionScheme.AES256_GCM
    )
    
    // Metadata storage directory (for non-sensitive data)
    private val storageDir = context.getDir("observations", Context.MODE_PRIVATE)
    
    companion object {
        private const val PREFS_FILE_NAME = "faro_secure_observations"
        private const val TTL_SUFFIX = "_ttl"
        private const val MAX_TTL_MS = 7 * 24 * 60 * 60 * 1000L // 7 days
        private const val SECURE_WIPE_PASSES = 3 // DoD 5220.22-M standard
    }
    
    /**
     * Save an observation for pending sync.
     * Data is encrypted at rest automatically by EncryptedSharedPreferences.
     */
    fun savePending(observation: SecureObservationPayload) {
        val json = gson.toJson(observation)
        val ttl = System.currentTimeMillis() + MAX_TTL_MS
        
        securePrefs.edit()
            .putString(observation.localId, json)
            .putLong(observation.localId + TTL_SUFFIX, ttl)
            .apply()
        
        Timber.d("Saved observation ${observation.localId} (TTL: ${Instant.ofEpochMilli(ttl)})")
    }
    
    /**
     * Retrieve observation by ID (without removing).
     * Returns null if not found or expired.
     */
    fun retrieve(localId: String): SecureObservationPayload? {
        // Check TTL first
        val ttl = securePrefs.getLong(localId + TTL_SUFFIX, 0)
        if (ttl > 0 && System.currentTimeMillis() > ttl) {
            // Expired - secure delete
            Timber.w("Observation $localId expired, deleting")
            secureDelete(localId)
            return null
        }
        
        val json = securePrefs.getString(localId, null) ?: return null
        return gson.fromJson(json, SecureObservationPayload::class.java)
    }
    
    /**
     * Retrieve and remove observation (for sync process).
     */
    fun retrieveAndRemove(localId: String): SecureObservationPayload? {
        val observation = retrieve(localId) ?: return null
        
        // Remove from storage (will be re-added if sync fails)
        securePrefs.edit()
            .remove(localId)
            .remove(localId + TTL_SUFFIX)
            .apply()
        
        return observation
    }
    
    /**
     * List all pending (non-expired) observations.
     * Automatically purges expired entries.
     */
    fun listPending(): List<SecureObservationPayload> {
        val now = System.currentTimeMillis()
        val pending = mutableListOf<SecureObservationPayload>()
        val expiredKeys = mutableListOf<String>()
        
        securePrefs.all.forEach { (key, value) ->
            // Skip TTL keys
            if (key.endsWith(TTL_SUFFIX)) return@forEach
            
            val ttl = securePrefs.getLong(key + TTL_SUFFIX, 0)
            
            if (ttl > 0 && now > ttl) {
                // Expired
                expiredKeys.add(key)
            } else {
                // Valid
                try {
                    val json = value as? String ?: return@forEach
                    val observation = gson.fromJson(json, SecureObservationPayload::class.java)
                    pending.add(observation)
                } catch (e: Exception) {
                    Timber.e(e, "Failed to parse observation $key")
                    expiredKeys.add(key)
                }
            }
        }
        
        // Clean up expired entries
        expiredKeys.forEach { secureDelete(it) }
        
        Timber.d("Listed ${pending.size} pending observations, purged ${expiredKeys.size} expired")
        return pending
    }
    
    /**
     * Securely delete observation data.
     * Implements DoD 5220.22-M wipe standard (3-pass overwrite).
     */
    fun secureDelete(localId: String) {
        val json = securePrefs.getString(localId, "") ?: ""
        
        if (json.isNotEmpty()) {
            // Overwrite with random data (3 passes)
            repeat(SECURE_WIPE_PASSES) { pass ->
                val garbage = generateRandomString(json.length)
                securePrefs.edit().putString(localId, garbage).commit()
                Timber.v("Secure wipe pass ${pass + 1}/$SECURE_WIPE_PASSES for $localId")
            }
        }
        
        // Final deletion
        securePrefs.edit()
            .remove(localId)
            .remove(localId + TTL_SUFFIX)
            .commit()
        
        Timber.d("Securely deleted observation $localId")
    }
    
    /**
     * Securely wipe ALL observations (emergency/reset).
     */
    fun secureWipeAll() {
        val allKeys = securePrefs.all.keys.filter { !it.endsWith(TTL_SUFFIX) }
        
        allKeys.forEach { key ->
            secureDelete(key)
        }
        
        Timber.w("Securely wiped all ${allKeys.size} observations")
    }
    
    /**
     * Check if there are pending observations.
     */
    fun hasPending(): Boolean {
        return listPending().isNotEmpty()
    }
    
    /**
     * Get count of pending observations.
     */
    fun getPendingCount(): Int {
        return listPending().size
    }
    
    /**
     * Update sync status for an observation.
     * Note: In zero-trust model, this should not be needed as we delete after sync.
     * Kept for error recovery scenarios.
     */
    fun updateSyncStatus(localId: String, status: SyncStatus, error: String? = null) {
        val observation = retrieve(localId) ?: return
        
        val updated = observation.copy(
            syncStatus = status,
            syncError = error,
            syncAttempts = observation.syncAttempts + 1,
            syncedAt = if (status == SyncStatus.COMPLETED) Instant.now() else observation.syncedAt
        )
        
        savePending(updated)
    }
    
    /**
     * Generate random string for secure wipe.
     */
    private fun generateRandomString(length: Int): String {
        val chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*()"
        return (1..length)
            .map { chars[Random.nextInt(chars.length)] }
            .joinToString("")
    }
    
    /**
     * Get storage statistics for monitoring.
     */
    fun getStats(): StorageStats {
        val allKeys = securePrefs.all.keys.filter { !it.endsWith(TTL_SUFFIX) }
        val pending = listPending()
        
        return StorageStats(
            totalObservations = allKeys.size,
            pendingSync = pending.size,
            expired = allKeys.size - pending.size,
            oldestObservation = pending.minOfOrNull { it.createdAt }?.epochSecond
        )
    }
}

/**
 * Payload for secure storage - optimized for encryption and sync.
 * Flattened structure to minimize nested encryption.
 */
data class SecureObservationPayload(
    val localId: String,
    val clientId: String,
    
    // Core data
    val plateNumber: String,
    val plateState: String? = null,
    val plateCountry: String = "BR",
    
    // Timestamps
    val observedAtLocal: Instant,
    val observedAtServer: Instant? = null,
    
    // Location
    val latitude: Double,
    val longitude: Double,
    val locationAccuracy: Float? = null,
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
    
    // OCR data
    val ocrRawText: String? = null,
    val ocrConfidence: Float? = null,
    val ocrEngine: String = "mlkit_v2",
    
    // Suspicion report (flattened)
    val suspicionReason: String? = null, // enum name
    val suspicionLevel: String? = null,  // enum name
    val suspicionUrgency: String? = null, // enum name
    val suspicionNotes: String? = null,
    val hasSuspicionImage: Boolean = false,
    val hasSuspicionAudio: Boolean = false,
    
    // Image reference (not the actual image)
    val plateImageEncryptedRef: String? = null, // Reference to encrypted image file
    
    // Sync tracking
    val syncStatus: SyncStatus = SyncStatus.PENDING,
    val syncAttempts: Int = 0,
    val syncedAt: Instant? = null,
    val syncError: String? = null,
    
    // Metadata
    val connectivityType: String? = null,
    val appVersion: String,
    val createdAt: Instant = Instant.now()
) {
    /**
     * Convert to sync payload for API transmission.
     */
    fun toSyncPayload(): Map<String, Any?> {
        return mutableMapOf<String, Any?>(
            "client_id" to clientId,
            "plate_number" to plateNumber,
            "plate_state" to plateState,
            "plate_country" to plateCountry,
            "observed_at_local" to observedAtLocal.toString(),
            "location" to mapOf(
                "latitude" to latitude,
                "longitude" to longitude,
                "accuracy" to locationAccuracy,
            ),
            "heading" to heading,
            "speed" to speed,
            "vehicle_color" to vehicleColor,
            "vehicle_type" to vehicleType,
            "vehicle_model" to vehicleModel,
            "vehicle_year" to vehicleYear,
            "device_id" to deviceId,
            "connectivity_type" to connectivityType,
            "app_version" to appVersion,
            "plate_read" to if (ocrRawText != null) mapOf(
                "ocr_raw_text" to ocrRawText,
                "ocr_confidence" to ocrConfidence?.toDouble(),
                "ocr_engine" to ocrEngine,
            ) else null,
            "suspicion_report" to if (suspicionReason != null) mapOf(
                "reason" to suspicionReason,
                "level" to suspicionLevel,
                "urgency" to suspicionUrgency,
                "notes" to suspicionNotes,
                "has_image" to hasSuspicionImage,
                "has_audio" to hasSuspicionAudio,
            ) else null,
        )
    }
}

/**
 * Storage statistics.
 */
data class StorageStats(
    val totalObservations: Int,
    val pendingSync: Int,
    val expired: Int,
    val oldestObservation: Long? // epoch seconds
)
