package com.faro.mobile.data.service

import android.content.Context
import com.google.mlkit.vision.text.TextRecognition
import com.google.mlkit.vision.text.TextRecognitionOptions
import com.google.mlkit.vision.text.latin.TextRecognizerOptions
import com.jakewharton.timber.Timber
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import java.io.IOException
import java.io.File
import java.io.FileOutputStream

/**
 * Edge OCR Service - Local OCR processing with intelligent model caching.
 * 
 * Features:
 * - Local ML Kit text recognition
 * - Model caching to reduce startup time
 * - Device capability detection
 * - Fallback to server when needed
 * - Performance monitoring
 */
class EdgeOCRService(private val context: Context) {
    
    private val textRecognizer by lazy {
        TextRecognition.getClient(TextRecognizerOptions.DEFAULT_OPTIONS)
    }
    
    private val modelCacheDir by lazy {
        File(context.cacheDir, "ocr_models").apply { mkdirs() }
    }
    
    /**
     * Device capability level for OCR processing
     */
    enum class DeviceCapability {
        HIGH,    // Can process locally with high accuracy
        MEDIUM,  // Can process locally with moderate accuracy
        LOW,     // Should use server-side OCR
        UNKNOWN  // Capability not detected
    }
    
    /**
     * Result of OCR processing
     */
    data class OCRResult(
        val plateNumber: String?,
        val confidence: Float,
        val processingTimeMs: Long,
        val processedLocally: Boolean,
        val deviceCapability: DeviceCapability
    )
    
    /**
     * Detect device capability for OCR processing
     */
    fun detectDeviceCapability(): DeviceCapability {
        val activityManager = context.getSystemService(Context.ACTIVITY_SERVICE) as android.app.ActivityManager
        val memoryInfo = android.app.ActivityManager.MemoryInfo()
        activityManager.getMemoryInfo(memoryInfo)
        
        val totalMemoryMB = memoryInfo.totalMem / (1024 * 1024)
        val availableMemoryMB = memoryInfo.availMem / (1024 * 1024)
        
        return when {
            totalMemoryMB >= 4096 && availableMemoryMB >= 2048 -> DeviceCapability.HIGH
            totalMemoryMB >= 2048 && availableMemoryMB >= 1024 -> DeviceCapability.MEDIUM
            else -> DeviceCapability.LOW
        }
    }
    
    /**
     * Process image locally using ML Kit
     */
    suspend fun processImageLocally(bitmap: Bitmap): OCRResult = withContext(Dispatchers.IO) {
        val startTime = System.currentTimeMillis()
        val capability = detectDeviceCapability()
        
        try {
            // Check if device is capable of local processing
            if (capability == DeviceCapability.LOW) {
                Timber.d("Device capability LOW, skipping local OCR")
                return@withContext OCRResult(
                    plateNumber = null,
                    confidence = 0f,
                    processingTimeMs = System.currentTimeMillis() - startTime,
                    processedLocally = false,
                    deviceCapability = capability
                )
            }
            
            // Process image with ML Kit
            val inputImage = com.google.mlkit.vision.common.InputImage.fromBitmap(bitmap, 0)
            val result = textRecognizer.process(inputImage)
            
            val text = result.text
            val plateNumber = extractPlateNumber(text)
            val confidence = calculateConfidence(text, plateNumber)
            
            val processingTime = System.currentTimeMillis() - startTime
            
            Timber.d("Local OCR completed in ${processingTime}ms, plate: $plateNumber, confidence: $confidence")
            
            OCRResult(
                plateNumber = plateNumber,
                confidence = confidence,
                processingTimeMs = processingTime,
                processedLocally = true,
                deviceCapability = capability
            )
        } catch (e: IOException) {
            Timber.e(e, "Local OCR processing failed - I/O error")
            OCRResult(
                plateNumber = null,
                confidence = 0f,
                processingTimeMs = System.currentTimeMillis() - startTime,
                processedLocally = false,
                deviceCapability = capability
            )
        } catch (e: Exception) {
            Timber.e(e, "Local OCR processing failed - unexpected error")
            OCRResult(
                plateNumber = null,
                confidence = 0f,
                processingTimeMs = System.currentTimeMillis() - startTime,
                processedLocally = false,
                deviceCapability = capability
            )
        }
    }
    
    /**
     * Extract plate number from OCR text
     */
    private fun extractPlateNumber(text: String): String? {
        // Brazilian plate pattern: ABC-1234 or ABC1D23 (Mercosul)
        val platePattern = Regex("[A-Z]{3}[0-9][A-Z0-9][0-9]{2}")
        val match = platePattern.find(text.uppercase())
        
        return if (match != null) {
            match.value
        } else {
            // Try old pattern: ABC-1234
            val oldPattern = Regex("[A-Z]{3}-[0-9]{4}")
            val oldMatch = oldPattern.find(text.uppercase())
            oldMatch?.value?.replace("-", "")
        }
    }
    
    /**
     * Calculate confidence score for OCR result
     */
    private fun calculateConfidence(text: String, plateNumber: String?): Float {
        if (plateNumber == null) return 0f
        
        // Base confidence based on text length and format
        var confidence = 0.5f
        
        // Bonus for correct format
        if (plateNumber.matches(Regex("[A-Z]{3}[0-9][A-Z0-9][0-9]{2}"))) {
            confidence += 0.3f
        }
        
        // Bonus for text length (longer text = more context)
        if (text.length >= 10) {
            confidence += 0.1f
        }
        
        // Bonus for uppercase letters
        if (text == text.uppercase()) {
            confidence += 0.1f
        }
        
        return confidence.coerceAtMost(1.0f)
    }
    
    /**
     * Cache model data for faster startup
     */
    suspend fun cacheModelData(): Boolean = withContext(Dispatchers.IO) {
        try {
            // ML Kit automatically handles model caching
            // This is a placeholder for future custom model caching
            Timber.d("Model caching not needed for ML Kit (handled automatically)")
            true
        } catch (e: Exception) {
            Timber.e(e, "Failed to cache model data")
            false
        }
    }
    
    /**
     * Clear cached model data
     */
    fun clearModelCache() {
        try {
            modelCacheDir.deleteRecursively()
            Timber.d("Model cache cleared")
        } catch (e: Exception) {
            Timber.e(e, "Failed to clear model cache")
        }
    }
    
    /**
     * Get cache size in bytes
     */
    fun getCacheSize(): Long {
        return modelCacheDir.walkTopDown()
            .filter { it.isFile }
            .map { it.length() }
            .sum()
    }
    
    /**
     * Check if local OCR should be used based on conditions
     */
    fun shouldUseLocalOCR(
        networkQuality: String,
        batteryLevel: Float,
        forceLocal: Boolean = false
    ): Boolean {
        if (forceLocal) return true
        
        val capability = detectDeviceCapability()
        
        // Don't use local if device capability is low
        if (capability == DeviceCapability.LOW) return false
        
        // Use local if network is poor
        if (networkQuality == "3g" || networkQuality == "2g") return true
        
        // Use local if battery is low (local processing is more efficient)
        if (batteryLevel < 0.2f) return true
        
        // Use local if device capability is high
        if (capability == DeviceCapability.HIGH) return true
        
        return false
    }
}
