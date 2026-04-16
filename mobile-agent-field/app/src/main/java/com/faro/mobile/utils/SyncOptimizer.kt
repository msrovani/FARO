package com.faro.mobile.utils

import android.content.Context
import android.net.ConnectivityManager
import android.net.NetworkCapabilities
import android.os.Build
import kotlinx.coroutines.delay

/**
 * Sync optimization utilities for adaptive batch processing.
 * Implements adaptive sync based on connectivity and device capabilities.
 */
class SyncOptimizer(private val context: Context) {
    
    private val performanceConfigManager = PerformanceConfigManager(context)
    
    /**
     * Get optimal batch size for sync based on current connectivity.
     */
    fun getOptimalBatchSize(): Int {
        val config = performanceConfigManager.getOptimalConfig()
        
        return when (isWifiConnected()) {
            true -> config.syncWifiBatchSize
            false -> config.syncBatchSize
        }
    }
    
    /**
     * Get optimal compression level based on connectivity.
     * Returns compression quality (0-100).
     */
    fun getOptimalCompressionLevel(): Int {
        val config = performanceConfigManager.getOptimalConfig()
        
        return when (isWifiConnected()) {
            true -> config.imageCompressionQuality
            false -> maxOf(60, config.imageCompressionQuality - 10) // Higher compression on mobile
        }
    }
    
    /**
     * Check if device is connected to WiFi.
     */
    private fun isWifiConnected(): Boolean {
        val connectivityManager = context.getSystemService(Context.CONNECTIVITY_SERVICE) as ConnectivityManager
        
        return if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.M) {
            val network = connectivityManager.activeNetwork
            val capabilities = connectivityManager.getNetworkCapabilities(network)
            capabilities?.hasTransport(NetworkCapabilities.TRANSPORT_WIFI) == true
        } else {
            @Suppress("DEPRECATION")
            val networkInfo = connectivityManager.activeNetworkInfo
            networkInfo?.type == ConnectivityManager.TYPE_WIFI && networkInfo.isConnected
        }
    }
    
    /**
     * Calculate exponential backoff delay for retry logic.
     */
    fun calculateBackoffDelay(attempt: Int, baseDelayMs: Long = 1000): Long {
        val maxDelayMs = 30000L // 30 seconds max
        val delayMs = (baseDelayMs * (2.0.pow(attempt))).toLong()
        return minOf(delayMs, maxDelayMs)
    }
    
    /**
     * Check if sync should be performed based on connectivity and battery.
     */
    fun shouldSync(): Boolean {
        if (!isNetworkAvailable()) {
            return false
        }
        
        // Prefer WiFi for large syncs
        val batchSize = getOptimalBatchSize()
        if (batchSize > 20 && !isWifiConnected()) {
            return false
        }
        
        return true
    }
    
    /**
     * Check if network is available.
     */
    private fun isNetworkAvailable(): Boolean {
        val connectivityManager = context.getSystemService(Context.CONNECTIVITY_SERVICE) as ConnectivityManager
        
        return if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.M) {
            val network = connectivityManager.activeNetwork
            network != null
        } else {
            @Suppress("DEPRECATION")
            val networkInfo = connectivityManager.activeNetworkInfo
            networkInfo?.isConnected == true
        }
    }
    
    /**
     * Get sync priority based on data type and connectivity.
     * Higher priority = should sync first.
     */
    fun getSyncPriority(dataType: SyncDataType): Int {
        val isWifi = isWifiConnected()
        
        return when (dataType) {
            SyncDataType.OBSERVATION -> if (isWifi) 1 else 3 // High priority on WiFi
            SyncDataType.IMAGE -> if (isWifi) 2 else 4 // Medium priority on WiFi
            SyncDataType.AUDIO -> if (isWifi) 3 else 5 // Lower priority on WiFi
            SyncDataType.FEEDBACK -> 1 // Always high priority
        }
    }
}

enum class SyncDataType {
    OBSERVATION,
    IMAGE,
    AUDIO,
    FEEDBACK
}
