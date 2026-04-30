package com.faro.mobile.utils

import android.content.Context

/**
 * Storage optimization utilities for adaptive data management.
 * Implements storage optimizations based on device capabilities.
 */
class StorageOptimizer(private val context: Context) {
    
    private val performanceConfigManager = PerformanceConfigManager(context)
    
    /**
     * Get optimal database query page size.
     */
    fun getQueryPageSize(): Int {
        val config = performanceConfigManager.getOptimalConfig()
        
        return when {
            config.threadPoolSize <= 2 -> 20  // Low-end: smaller pages
            config.threadPoolSize <= 4 -> 50  // Mid-range: moderate pages
            else -> 100  // High-end: larger pages
        }
    }
    
    /**
     * Get optimal cache size for database queries.
     */
    fun getQueryCacheSize(): Int {
        val config = performanceConfigManager.getOptimalConfig()
        
        return when {
            config.threadPoolSize <= 2 -> 50  // Low-end: smaller cache
            config.threadPoolSize <= 4 -> 100  // Mid-range: moderate cache
            else -> 200  // High-end: larger cache
        }
    }
    
    /**
     * Get optimal data compression level for storage.
     * Returns compression level (0-9, where 9 is maximum compression).
     */
    fun getDataCompressionLevel(): Int {
        val config = performanceConfigManager.getOptimalConfig()
        
        return when {
            config.threadPoolSize <= 2 -> 6  // Low-end: higher compression
            config.threadPoolSize <= 4 -> 4  // Mid-range: moderate compression
            else -> 2  // High-end: lower compression (faster)
        }
    }
    
    /**
     * Get optimal TTL for cached data.
     */
    fun getCacheTtlMinutes(): Int {
        val config = performanceConfigManager.getOptimalConfig()
        
        return when {
            config.threadPoolSize <= 2 -> 30  // Low-end: shorter TTL
            config.threadPoolSize <= 4 -> 60  // Mid-range: moderate TTL
            else -> 120  // High-end: longer TTL
        }
    }
    
    /**
     * Get maximum number of items to keep in local storage.
     */
    fun getMaxLocalItems(): Int {
        val config = performanceConfigManager.getOptimalConfig()
        
        return when {
            config.threadPoolSize <= 2 -> 100  // Low-end: fewer items
            config.threadPoolSize <= 4 -> 250  // Mid-range: moderate items
            else -> 500  // High-end: more items
        }
    }
    
    /**
     * Check if data should be compressed before storage.
     */
    fun shouldCompressData(): Boolean {
        val hardware = HardwareDetector(context).detectHardware()
        // Compress if memory is limited
        return hardware.availableMemoryMb < 2048
    }
    
    /**
     * Get optimal batch size for database operations.
     */
    fun getDatabaseBatchSize(): Int {
        val config = performanceConfigManager.getOptimalConfig()
        
        return when {
            config.threadPoolSize <= 2 -> 10  // Low-end: smaller batches
            config.threadPoolSize <= 4 -> 25  // Mid-range: moderate batches
            else -> 50  // High-end: larger batches
        }
    }
    
    /**
     * Get optimal index usage strategy.
     */
    fun getIndexUsageStrategy(): IndexStrategy {
        val config = performanceConfigManager.getOptimalConfig()
        
        return when {
            config.threadPoolSize <= 2 -> IndexStrategy.MINIMAL  // Low-end: minimal indexes
            config.threadPoolSize <= 4 -> IndexStrategy.STANDARD  // Mid-range: standard indexes
            else -> IndexStrategy.AGGRESSIVE  // High-end: aggressive indexes
        }
    }
    
    /**
     * Get optimal WAL (Write-Ahead Logging) mode for database.
     */
    fun getWalMode(): WalMode {
        val config = performanceConfigManager.getOptimalConfig()
        
        return when {
            config.threadPoolSize <= 2 -> WalMode.DISABLED  // Low-end: disable WAL
            config.threadPoolSize <= 4 -> WalMode.NORMAL  // Mid-range: normal WAL
            else -> WalMode.FULL  // High-end: full WAL
        }
    }
}

enum class IndexStrategy {
    MINIMAL,    // Only essential indexes
    STANDARD,   // Standard set of indexes
    AGGRESSIVE  // Comprehensive indexing
}

enum class WalMode {
    DISABLED,   // WAL disabled (slower writes, less storage)
    NORMAL,     // Normal WAL mode
    FULL        // Full WAL mode (fastest writes, more storage)
}
