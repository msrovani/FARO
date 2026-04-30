package com.faro.mobile.utils

/**
 * Dynamic performance configuration based on hardware capabilities.
 * Provides optimal settings for different device categories.
 */
data class PerformanceConfig(
    val threadPoolSize: Int,
    val imageCompressionQuality: Int,
    val imageMaxWidth: Int,
    val imageMaxHeight: Int,
    val ocrUseGpu: Boolean,
    val ocrBatchSize: Int,
    val syncBatchSize: Int,
    val syncWifiBatchSize: Int,
    val cacheLimitMb: Int,
    val enableImageCaching: Boolean,
    val enableResponseCaching: Boolean
)

class PerformanceConfigManager(private val context: Context) {
    
    private val hardwareDetector = HardwareDetector(context)
    private val deviceClassifier = DeviceClassifier(context)
    
    private var cachedConfig: PerformanceConfig? = null
    
    /**
     * Get optimal performance configuration for the current device.
     * Caches the result to avoid repeated hardware detection.
     */
    fun getOptimalConfig(): PerformanceConfig {
        cachedConfig?.let { return it }
        
        val hardware = hardwareDetector.detectHardware()
        val category = deviceClassifier.classifyDevice(hardware)
        
        val config = when (category) {
            DeviceCategory.LOW_END -> createLowEndConfig()
            DeviceCategory.MID_RANGE -> createMidRangeConfig(hardware)
            DeviceCategory.HIGH_END -> createHighEndConfig(hardware)
        }
        
        cachedConfig = config
        return config
    }
    
    /**
     * Configuration for low-end devices (2GB RAM, 4 cores).
     * Conservative settings to ensure stability.
     */
    private fun createLowEndConfig(): PerformanceConfig {
        return PerformanceConfig(
            threadPoolSize = 2,
            imageCompressionQuality = 70,
            imageMaxWidth = 640,
            imageMaxHeight = 480,
            ocrUseGpu = false,
            ocrBatchSize = 2,
            syncBatchSize = 10,
            syncWifiBatchSize = 15,
            cacheLimitMb = 50,
            enableImageCaching = true,
            enableResponseCaching = true
        )
    }
    
    /**
     * Configuration for mid-range devices (4GB RAM, 8 cores).
     * Balanced settings for good performance.
     */
    private fun createMidRangeConfig(hardware: HardwareCapabilities): PerformanceConfig {
        val useGpu = hardware.gpuAvailable && hardware.apiLevel >= Build.VERSION_CODES.P
        
        return PerformanceConfig(
            threadPoolSize = 4,
            imageCompressionQuality = 80,
            imageMaxWidth = 800,
            imageMaxHeight = 600,
            ocrUseGpu = useGpu,
            ocrBatchSize = 4,
            syncBatchSize = 25,
            syncWifiBatchSize = 40,
            cacheLimitMb = 150,
            enableImageCaching = true,
            enableResponseCaching = true
        )
    }
    
    /**
     * Configuration for high-end devices (8GB+ RAM, 8+ cores, GPU).
     * Aggressive settings for maximum performance.
     */
    private fun createHighEndConfig(hardware: HardwareCapabilities): PerformanceConfig {
        val useGpu = hardware.gpuAvailable && hardware.apiLevel >= Build.VERSION_CODES.P
        
        return PerformanceConfig(
            threadPoolSize = 8,
            imageCompressionQuality = 85,
            imageMaxWidth = 1280,
            imageMaxHeight = 720,
            ocrUseGpu = useGpu,
            ocrBatchSize = 8,
            syncBatchSize = 50,
            syncWifiBatchSize = 75,
            cacheLimitMb = 300,
            enableImageCaching = true,
            enableResponseCaching = true
        )
    }
    
    /**
     * Clear cached configuration (useful for testing or after hardware changes).
     */
    fun clearCache() {
        cachedConfig = null
    }
    
    /**
     * Get current device category for logging/debugging.
     */
    fun getDeviceCategory(): String {
        val hardware = hardwareDetector.detectHardware()
        val category = deviceClassifier.classifyDevice(hardware)
        return category.name
    }
}
