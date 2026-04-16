package com.faro.mobile.utils

import android.content.Context

/**
 * UI optimization utilities for adaptive rendering and performance.
 * Implements UI optimizations based on device capabilities.
 */
class UiOptimizer(private val context: Context) {
    
    private val performanceConfigManager = PerformanceConfigManager(context)
    
    /**
     * Get optimal RecyclerView item cache size.
     */
    fun getRecyclerViewCacheSize(): Int {
        val config = performanceConfigManager.getOptimalConfig()
        
        return when {
            config.threadPoolSize <= 2 -> 10  // Low-end devices
            config.threadPoolSize <= 4 -> 20  // Mid-range devices
            else -> 30  // High-end devices
        }
    }
    
    /**
     * Check if image loading should use aggressive caching.
     */
    fun shouldUseAggressiveImageCaching(): Boolean {
        val config = performanceConfigManager.getOptimalConfig()
        return config.enableImageCaching
    }
    
    /**
     * Get optimal image loading placeholder strategy.
     */
    fun getImageLoadingStrategy(): ImageLoadingStrategy {
        val config = performanceConfigManager.getOptimalConfig()
        
        return when {
            config.threadPoolSize <= 2 -> ImageLoadingStrategy.CONSERVATIVE
            config.threadPoolSize <= 4 -> ImageLoadingStrategy.BALANCED
            else -> ImageLoadingStrategy.AGGRESSIVE
        }
    }
    
    /**
     * Get optimal animation duration multiplier.
     * Lower-end devices get longer durations to reduce jank.
     */
    fun getAnimationDurationMultiplier(): Float {
        val config = performanceConfigManager.getOptimalConfig()
        
        return when {
            config.threadPoolSize <= 2 -> 1.5f  // Slower animations on low-end
            config.threadPoolSize <= 4 -> 1.0f  // Normal animations on mid-range
            else -> 0.8f  // Faster animations on high-end
        }
    }
    
    /**
     * Check if complex animations should be disabled.
     */
    fun shouldDisableComplexAnimations(): Boolean {
        val config = performanceConfigManager.getOptimalConfig()
        return config.threadPoolSize <= 2
    }
    
    /**
     * Get optimal list item preload count.
     */
    fun getListItemPreloadCount(): Int {
        val config = performanceConfigManager.getOptimalConfig()
        
        return when {
            config.threadPoolSize <= 2 -> 3  // Low-end: preload fewer items
            config.threadPoolSize <= 4 -> 5  // Mid-range: moderate preload
            else -> 10  // High-end: aggressive preload
        }
    }
    
    /**
     * Check if hardware acceleration should be enabled.
     */
    fun shouldUseHardwareAcceleration(): Boolean {
        val hardware = HardwareDetector(context).detectHardware()
        return hardware.gpuAvailable
    }
}

enum class ImageLoadingStrategy {
    CONSERVATIVE,  // Minimal caching, lower quality placeholders
    BALANCED,      // Moderate caching, standard placeholders
    AGGRESSIVE     // Aggressive caching, high-quality placeholders
}
