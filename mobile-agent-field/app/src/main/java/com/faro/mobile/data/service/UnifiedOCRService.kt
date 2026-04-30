package com.faro.mobile.data.service

import android.content.Context
import android.graphics.Bitmap
import android.util.Base64
import com.faro.mobile.data.remote.FaroMobileApi
import com.faro.mobile.data.remote.OcrValidationRequestDto
import com.faro.mobile.data.remote.OcrValidationResponseDto
import com.jakewharton.timber.Timber
import dagger.hilt.android.qualifiers.ApplicationContext
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import java.io.ByteArrayOutputStream
import java.security.MessageDigest
import javax.inject.Inject
import javax.inject.Singleton

/**
 * Unified OCR Service - Intelligent OCR processing with edge computing and server fallback.
 * 
 * Features:
 * - Edge OCR as primary (ML Kit)
 * - Server OCR as fallback
 * - Local cache of OCR results
 * - Adaptive decision based on device capability, network, and battery
 * - Metrics and monitoring
 */
@Singleton
class UnifiedOCRService @Inject constructor(
    @ApplicationContext private val context: Context,
    private val edgeOCRService: EdgeOCRService,
    private val faroMobileApi: FaroMobileApi
) {
    
    /**
     * Result of unified OCR processing
     */
    data class UnifiedOCRResult(
        val plateNumber: String?,
        val confidence: Float,
        val processingTimeMs: Long,
        val source: OCRSource,
        val deviceCapability: EdgeOCRService.DeviceCapability,
        val cached: Boolean
    )
    
    /**
     * Source of OCR result
     */
    enum class OCRSource {
        EDGE_LOCAL,      // Processed locally with ML Kit
        SERVER_FALLBACK, // Processed on server
        CACHE            // Retrieved from local cache
    }
    
    /**
     * Cache entry for OCR results
     */
    private data class OCRCacheEntry(
        val plateNumber: String?,
        val confidence: Float,
        val timestamp: Long
    )
    
    private val ocrCache = mutableMapOf<String, OCRCacheEntry>()
    private val cacheTtlMs = 5 * 60 * 1000L // 5 minutes
    
    /**
     * Process image with unified OCR strategy
     * 
     * Strategy:
     * 1. Check cache first
     * 2. Try edge OCR if device capable
     * 3. Fallback to server OCR if edge fails or not capable
     */
    suspend fun processImage(
        bitmap: Bitmap,
        networkQuality: String = "unknown",
        batteryLevel: Float = 1.0f,
        forceServer: Boolean = false
    ): UnifiedOCRResult = withContext(Dispatchers.IO) {
        val startTime = System.currentTimeMillis()
        val imageHash = computeImageHash(bitmap)
        
        Timber.d("Unified OCR: Starting processing, hash=$imageHash, network=$networkQuality, battery=$batteryLevel")
        
        // 1. Check cache
        val cachedResult = getCachedResult(imageHash)
        if (cachedResult != null) {
            Timber.d("Unified OCR: Cache hit, plate=${cachedResult.plateNumber}")
            return@withContext UnifiedOCRResult(
                plateNumber = cachedResult.plateNumber,
                confidence = cachedResult.confidence,
                processingTimeMs = System.currentTimeMillis() - startTime,
                source = OCRSource.CACHE,
                deviceCapability = edgeOCRService.detectDeviceCapability(),
                cached = true
            )
        }
        
        // 2. Decide processing strategy
        val shouldUseEdge = if (forceServer) {
            false
        } else {
            edgeOCRService.shouldUseLocalOCR(networkQuality, batteryLevel)
        }
        
        Timber.d("Unified OCR: Should use edge=$shouldUseEdge")
        
        // 3. Process with selected strategy
        val result = if (shouldUseEdge) {
            processWithEdge(bitmap)
        } else {
            processWithServer(bitmap)
        }
        
        // 4. Cache successful results
        if (result.plateNumber != null && result.confidence >= 0.5f) {
            cacheResult(imageHash, result.plateNumber, result.confidence)
        }
        
        val processingTime = System.currentTimeMillis() - startTime
        Timber.d("Unified OCR: Completed in ${processingTime}ms, source=${result.source}, plate=${result.plateNumber}")
        
        UnifiedOCRResult(
            plateNumber = result.plateNumber,
            confidence = result.confidence,
            processingTimeMs = processingTime,
            source = result.source,
            deviceCapability = result.deviceCapability,
            cached = false
        )
    }
    
    /**
     * Process image with edge OCR (ML Kit)
     */
    private suspend fun processWithEdge(bitmap: Bitmap): UnifiedOCRResult {
        val edgeResult = edgeOCRService.processImageLocally(bitmap)
        
        return if (edgeResult.plateNumber != null && edgeResult.confidence >= 0.5f) {
            // Edge OCR successful
            UnifiedOCRResult(
                plateNumber = edgeResult.plateNumber,
                confidence = edgeResult.confidence,
                processingTimeMs = edgeResult.processingTimeMs,
                source = OCRSource.EDGE_LOCAL,
                deviceCapability = edgeResult.deviceCapability,
                cached = false
            )
        } else {
            // Edge OCR failed or low confidence, fallback to server
            Timber.w("Edge OCR failed or low confidence, falling back to server")
            processWithServer(bitmap)
        }
    }
    
    /**
     * Process image with server OCR (fallback)
     */
    private suspend fun processWithServer(
        bitmap: Bitmap,
        mobileOcrText: String? = null,
        mobileOcrConfidence: Float? = null
    ): UnifiedOCRResult {
        Timber.d("Processing with server OCR (fallback)")
        
        val startTime = System.currentTimeMillis()
        
        return try {
            // Convert bitmap to base64
            val imageBase64 = bitmapToBase64(bitmap)
            
            // Create OCR validation request
            val request = OcrValidationRequestDto(
                imageBase64 = imageBase64,
                mobileOcrText = mobileOcrText,
                mobileOcrConfidence = mobileOcrConfidence,
                deviceId = "device_001" // TODO: Get actual device ID
            )
            
            // Call server OCR endpoint
            val response = faroMobileApi.validateOcr(request)
            
            val processingTimeMs = (System.currentTimeMillis() - startTime).toInt()
            
            // Check if server OCR succeeded
            if (response.isValid && response.plateNumber != null) {
                // Use server result if valid
                Timber.d("Server OCR successful: ${response.plateNumber} (confidence: ${response.confidence})")
                
                UnifiedOCRResult(
                    plateNumber = response.plateNumber,
                    confidence = response.confidence,
                    processingTimeMs = processingTimeMs,
                    source = OCRSource.SERVER_FALLBACK,
                    deviceCapability = edgeOCRService.detectDeviceCapability(),
                    cached = false
                )
            } else {
                // Server OCR failed, return null
                Timber.w("Server OCR failed or invalid result")
                
                UnifiedOCRResult(
                    plateNumber = null,
                    confidence = 0f,
                    processingTimeMs = processingTimeMs,
                    source = OCRSource.SERVER_FALLBACK,
                    deviceCapability = edgeOCRService.detectDeviceCapability(),
                    cached = false
                )
            }
            
        } catch (e: Exception) {
            Timber.e(e, "Server OCR call failed")
            
            val processingTimeMs = (System.currentTimeMillis() - startTime).toInt()
            
            // Return null on error
            UnifiedOCRResult(
                plateNumber = null,
                confidence = 0f,
                processingTimeMs = processingTimeMs,
                source = OCRSource.SERVER_FALLBACK,
                deviceCapability = edgeOCRService.detectDeviceCapability(),
                cached = false
            )
        }
    }
    
    /**
     * Convert bitmap to base64 string
     */
    private fun bitmapToBase64(bitmap: Bitmap): String {
        val outputStream = ByteArrayOutputStream()
        bitmap.compress(Bitmap.CompressFormat.JPEG, 90, outputStream)
        val byteArray = outputStream.toByteArray()
        return Base64.encodeToString(byteArray, Base64.NO_WRAP)
    }
    
    /**
     * Get cached result for image hash
     */
    private fun getCachedResult(imageHash: String): OCRCacheEntry? {
        val entry = ocrCache[imageHash] ?: return null
        
        // Check if cache entry is still valid
        if (System.currentTimeMillis() - entry.timestamp > cacheTtlMs) {
            ocrCache.remove(imageHash)
            return null
        }
        
        return entry
    }
    
    /**
     * Cache OCR result
     */
    private fun cacheResult(imageHash: String, plateNumber: String, confidence: Float) {
        ocrCache[imageHash] = OCRCacheEntry(
            plateNumber = plateNumber,
            confidence = confidence,
            timestamp = System.currentTimeMillis()
        )
        
        // Limit cache size
        if (ocrCache.size > 100) {
            val oldestKey = ocrCache.keys.first()
            ocrCache.remove(oldestKey)
        }
        
        Timber.d("Cached OCR result: hash=$imageHash, plate=$plateNumber, confidence=$confidence")
    }
    
    /**
     * Clear OCR cache
     */
    fun clearCache() {
        ocrCache.clear()
        Timber.d("OCR cache cleared")
    }
    
    /**
     * Get cache statistics
     */
    fun getCacheStats(): Map<String, Any> {
        return mapOf(
            "size" to ocrCache.size,
            "max_size" to 100,
            "ttl_minutes" to (cacheTtlMs / 1000 / 60)
        )
    }
    
    /**
     * Compute hash of image for caching
     */
    private fun computeImageHash(bitmap: Bitmap): String {
        val digest = MessageDigest.getInstance("SHA-256")
        
        // Simple hash based on dimensions and first few pixels
        // In production, use full image hash
        val width = bitmap.width
        val height = bitmap.height
        
        val pixels = IntArray(10)
        bitmap.getPixels(pixels, 0, 1, 0, 0, 10, 1)
        
        val input = StringBuilder()
        input.append(width).append(height)
        pixels.forEach { input.append(it) }
        
        val hashBytes = digest.digest(input.toString().toByteArray())
        return hashBytes.joinToString("") { "%02x".format(it) }
    }
}
