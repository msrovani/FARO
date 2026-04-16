package com.faro.mobile.utils

import android.content.Context
import java.time.Instant

/**
 * Secure sync manager that enforces network validation and sync policies.
 * Integrates with existing observation repository to control sync operations.
 */
class SecureSyncManager(private val context: Context) {
    
    private val networkValidator = NetworkValidator(context)
    private val syncPolicy = SyncPolicy(context)
    
    /**
     * Check if sync can proceed based on network conditions.
     */
    fun canSync(): SyncCheckResult {
        // Check if network is trusted
        if (networkValidator.shouldBlockSync()) {
            return SyncCheckResult.BLOCKED(
                reason = "Rede não confiável detectada",
                networkType = networkValidator.getNetworkType(),
                suggestion = "Use 4G ou WiFi institucional para sincronizar"
            )
        }
        
        // Check if network quality is sufficient
        if (syncPolicy.shouldDeferSync()) {
            return SyncCheckResult.DEFERRED(
                reason = "Qualidade de rede insuficiente",
                networkQuality = networkValidator.getNetworkQuality(),
                suggestion = "Aguarde melhor conexão ou mude de rede"
            )
        }
        
        return SyncCheckResult.ALLOWED(
            networkType = networkValidator.getNetworkType(),
            networkQuality = networkValidator.getNetworkQuality()
        )
    }
    
    /**
     * Check if specific data can be synced based on type, size, and age.
     */
    fun canSyncData(
        dataType: DataType,
        dataSizeMb: Long,
        createdAt: Instant
    ): SyncDataCheckResult {
        val decision = syncPolicy.canSyncData(dataType, dataSizeMb, createdAt)
        
        return when (decision) {
            is SyncDecision.ALLOWED -> SyncDataCheckResult.ALLOWED
            is SyncDecision.BLOCKED -> SyncDataCheckResult.BLOCKED(
                reason = decision.reason,
                suggestion = decision.suggestion
            )
        }
    }
    
    /**
     * Get recommended batch size for sync based on network.
     */
    fun getRecommendedBatchSize(): Int {
        return syncPolicy.getRecommendedBatchSize()
    }
    
    /**
     * Get sync priority for data based on type and age.
     */
    fun getSyncPriority(dataType: DataType, createdAt: Instant): Int {
        return syncPolicy.getSyncPriority(dataType, createdAt)
    }
    
    /**
     * Get network information for logging/debugging.
     */
    fun getNetworkInfo(): NetworkInfo {
        return NetworkInfo(
            type = networkValidator.getNetworkType(),
            quality = networkValidator.getNetworkQuality(),
            isTrusted = networkValidator.isNetworkTrusted(),
            canTransferHeavyData = networkValidator.canTransferHeavyData()
        )
    }
}

/**
 * Result of sync capability check.
 */
sealed class SyncCheckResult {
    data class ALLOWED(
        val networkType: NetworkType,
        val networkQuality: Int
    ) : SyncCheckResult()
    
    data class BLOCKED(
        val reason: String,
        val networkType: NetworkType,
        val suggestion: String
    ) : SyncCheckResult()
    
    data class DEFERRED(
        val reason: String,
        val networkQuality: Int,
        val suggestion: String
    ) : SyncCheckResult()
}

/**
 * Result of data sync capability check.
 */
sealed class SyncDataCheckResult {
    data object ALLOWED : SyncDataCheckResult()
    data class BLOCKED(
        val reason: String,
        val suggestion: String
    ) : SyncDataCheckResult()
}

/**
 * Network information for logging.
 */
data class NetworkInfo(
    val type: NetworkType,
    val quality: Int,
    val isTrusted: Boolean,
    val canTransferHeavyData: Boolean
)
