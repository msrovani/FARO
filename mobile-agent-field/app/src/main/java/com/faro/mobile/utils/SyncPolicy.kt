package com.faro.mobile.utils

import android.content.Context
import java.time.Instant
import java.time.temporal.ChronoUnit

/**
 * Sync policy for secure data transmission.
 * Implements 4G-first policy and TTL enforcement.
 */
class SyncPolicy(private val context: Context) {
    
    private val networkValidator = NetworkValidator(context)
    private val networkSettings = NetworkSettings.getInstance(context)
    
    /**
     * Check if data can be synced based on network and age.
     */
    fun canSyncData(dataType: DataType, dataSizeMb: Long, createdAt: Instant): SyncDecision {
        val ageDays = ChronoUnit.DAYS.between(createdAt, Instant.now())
        val ttlDays = networkSettings.getSyncTtlDays()
        val thresholdMb = networkSettings.getHeavyDataThresholdMb()
        
        // Data older than TTL requires 4G
        if (ageDays >= ttlDays) {
            if (!networkValidator.is4G()) {
                return SyncDecision.BLOCKED(
                    reason = "Dados com mais de $ttlDays dias requerem conexão 4G",
                    suggestion = "Use 4G para sincronizar dados antigos"
                )
            }
        }
        
        // Heavy data requires trusted network
        if (dataSizeMb >= thresholdMb) {
            if (!networkValidator.canTransferHeavyData()) {
                return SyncDecision.BLOCKED(
                    reason = "Transferência de dados pesados requer WiFi institucional ou 4G",
                    suggestion = "Conecte-se a WiFi institucional ou use 4G"
                )
            }
        }
        
        // Sensitive data requires trusted network
        if (dataType.isSensitive()) {
            if (!networkValidator.isNetworkTrusted()) {
                return SyncDecision.BLOCKED(
                    reason = "Dados sensíveis requerem rede confiável",
                    suggestion = "Use 4G ou WiFi institucional"
                )
            }
        }
        
        return SyncDecision.ALLOWED
    }
    
    /**
     * Get sync priority based on data type and age.
     */
    fun getSyncPriority(dataType: DataType, createdAt: Instant): Int {
        val ageDays = ChronoUnit.DAYS.between(createdAt, Instant.now())
        val ttlDays = networkSettings.getSyncTtlDays()
        
        // Base priority by data type
        val basePriority = when (dataType) {
            DataType.OBSERVATION -> 100
            DataType.IMAGE -> 80
            DataType.AUDIO -> 60
            DataType.FEEDBACK -> 120
            DataType.OTHER -> 40
        }
        
        // Increase priority for older data (closer to TTL)
        val agePriority = (ageDays / ttlDays * 20).toInt()
        
        return basePriority + agePriority
    }
    
    /**
     * Get recommended sync batch size based on network.
     */
    fun getRecommendedBatchSize(): Int {
        return when (networkValidator.getNetworkType()) {
            NetworkType.CELLULAR -> 25
            NetworkType.INSTITUTIONAL_WIFI -> 50
            NetworkType.PUBLIC_WIFI -> 0 // Blocked
            NetworkType.UNKNOWN -> 0
        }
    }
    
    /**
     * Check if sync should be deferred based on network quality.
     */
    fun shouldDeferSync(): Boolean {
        val quality = networkValidator.getNetworkQuality()
        return quality < 30 // Poor network quality
    }
}

/**
 * Data type classification for sync policy.
 */
enum class DataType(val isSensitive: Boolean) {
    OBSERVATION(true),
    IMAGE(true),
    AUDIO(true),
    FEEDBACK(false),
    OTHER(false)
}

/**
 * Decision result for sync operation.
 */
sealed class SyncDecision {
    data class ALLOWED(val reason: String? = null) : SyncDecision()
    data class BLOCKED(val reason: String, val suggestion: String) : SyncDecision()
}
