package com.faro.mobile.utils

import android.content.Context
import android.graphics.Bitmap
import android.graphics.BitmapFactory
import android.os.Build
import java.io.File

/**
 * OCR optimization utilities for adaptive image processing.
 * Implements adaptive OCR based on device capabilities and GPU availability.
 */
class OcrOptimizer(private val context: Context) {
    
    private val performanceConfigManager = PerformanceConfigManager(context)
    
    /**
     * Get optimal batch size for OCR processing.
     */
    fun getOptimalBatchSize(): Int {
        val config = performanceConfigManager.getOptimalConfig()
        return config.ocrBatchSize
    }
    
    /**
     * Check if GPU acceleration should be used for OCR.
     */
    fun shouldUseGpu(): Boolean {
        val config = performanceConfigManager.getOptimalConfig()
        return config.ocrUseGpu
    }
    
    /**
     * Optimize image for OCR processing.
     * Resizes and compresses image according to device capabilities.
     */
    fun optimizeImageForOcr(imageFile: File): Bitmap? {
        val config = performanceConfigManager.getOptimalConfig()
        
        // Decode image with inSampleSize to reduce memory usage
        val options = BitmapFactory.Options().apply {
            inJustDecodeBounds = true
        }
        BitmapFactory.decodeFile(imageFile.absolutePath, options)
        
        // Calculate inSampleSize
        options.inSampleSize = calculateInSampleSize(
            options.outWidth,
            options.outHeight,
            config.imageMaxWidth,
            config.imageMaxHeight
        )
        
        options.inJustDecodeBounds = false
        val bitmap = BitmapFactory.decodeFile(imageFile.absolutePath, options)
        
        // Further resize if needed
        return if (bitmap != null && (bitmap.width > config.imageMaxWidth || bitmap.height > config.imageMaxHeight)) {
            Bitmap.createScaledBitmap(
                bitmap,
                config.imageMaxWidth,
                config.imageMaxHeight,
                true
            )
        } else {
            bitmap
        }
    }
    
    /**
     * Calculate inSampleSize for efficient bitmap decoding.
     */
    private fun calculateInSampleSize(
        width: Int,
        height: Int,
        reqWidth: Int,
        reqHeight: Int
    ): Int {
        var inSampleSize = 1
        
        if (height > reqHeight || width > reqWidth) {
            val halfHeight = height / 2
            val halfWidth = width / 2
            
            while (halfHeight / inSampleSize >= reqHeight && halfWidth / inSampleSize >= reqWidth) {
                inSampleSize *= 2
            }
        }
        
        return inSampleSize
    }
    
    /**
     * Get optimal image compression quality for OCR.
     */
    fun getOptimalCompressionQuality(): Int {
        val config = performanceConfigManager.getOptimalConfig()
        return config.imageCompressionQuality
    }
    
    /**
     * Check if on-device OCR should be used or fallback to server.
     * Returns true if device has sufficient capability for on-device OCR.
     */
    fun shouldUseOnDeviceOcr(): Boolean {
        val hardware = HardwareDetector(context).detectHardware()
        val config = performanceConfigManager.getOptimalConfig()
        
        // Use on-device OCR if:
        // - Device has GPU and API level >= P (for NNAPI)
        // - Device has at least 4GB RAM
        // - Device has at least 4 CPU cores
        return config.ocrUseGpu && 
               hardware.totalMemoryMb >= 4096 && 
               hardware.cpuCores >= 4
    }
    
    /**
     * Get OCR thread pool size for parallel processing.
     */
    fun getOcrThreadPoolSize(): Int {
        val config = performanceConfigManager.getOptimalConfig()
        return config.threadPoolSize
    }
    
    /**
     * Pre-compress image before OCR to reduce processing time.
     */
    fun preCompressImage(imageFile: File): File {
        val config = performanceConfigManager.getOptimalConfig()
        
        // This is a placeholder for actual image compression logic
        // In a real implementation, you would use a library like Glide or Coil
        // to compress the image before OCR processing
        
        return imageFile
    }
    
    /**
     * Get cache size for OCR models.
     */
    fun getOcrModelCacheSize(): Long {
        val config = performanceConfigManager.getOptimalConfig()
        return (config.cacheLimitMb * 1024 * 1024).toLong()
    }
}
