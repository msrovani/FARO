package com.faro.mobile.data.service

import android.content.Context
import android.graphics.Bitmap
import android.graphics.BitmapFactory
import android.graphics.ImageFormat
import android.graphics.Rect
import android.graphics.YuvImage
import android.hardware.camera2.CameraCharacteristics
import android.util.Log
import androidx.camera.core.ImageCapture
import androidx.camera.core.ImageProxy
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import java.io.ByteArrayOutputStream
import java.io.File
import java.io.FileOutputStream
import java.util.UUID
import javax.inject.Inject
import javax.inject.Singleton

/**
 * Unified Image Capture Service for F.A.R.O.
 * Handles WebP capture, optimization, and processing for OCR and storage
 */
@Singleton
class UnifiedImageCaptureService @Inject constructor(
    private val context: Context,
    private val performanceConfigManager: PerformanceConfigManager
) {
    
    companion object {
        private const val TAG = "UnifiedImageCapture"
        private const val WEBP_QUALITY = 90
        private const val MAX_FILE_SIZE_MB = 10
        private const val TEMP_IMAGE_PREFIX = "faro_capture_"
        private const val TEMP_IMAGE_SUFFIX = ".webp"
    }
    
    data class CapturedImage(
        val bitmap: Bitmap,
        val webpData: ByteArray,
        val filePath: String,
        val width: Int,
        val height: Int,
        val fileSizeBytes: Int,
        val captureTimeMs: Long,
        val format: String = "webp"
    )
    
    data class ImageProcessingConfig(
        val quality: Int = WEBP_QUALITY,
        val maxWidth: Int = 1280,
        val maxHeight: Int = 720,
        val enableOptimization: Boolean = true,
        val enableWatermark: Boolean = false
    )
    
    /**
     * Process camera image proxy to WebP format
     */
    suspend fun processCameraImage(
        imageProxy: ImageProxy,
        config: ImageProcessingConfig = ImageProcessingConfig()
    ): Result<CapturedImage> = withContext(Dispatchers.IO) {
        try {
            val startTime = System.currentTimeMillis()
            
            // Convert ImageProxy to Bitmap
            val bitmap = imageProxyToBitmap(imageProxy)
            
            // Optimize for purpose
            val optimizedBitmap = optimizeBitmap(bitmap, config)
            
            // Convert to WebP
            val webpData = bitmapToWebP(optimizedBitmap, config.quality)
            
            // Save to temporary file
            val tempFile = createTempImageFile()
            saveWebPToFile(webpData, tempFile)
            
            val capturedImage = CapturedImage(
                bitmap = optimizedBitmap,
                webpData = webpData,
                filePath = tempFile.absolutePath,
                width = optimizedBitmap.width,
                height = optimizedBitmap.height,
                fileSizeBytes = webpData.size,
                captureTimeMs = System.currentTimeMillis() - startTime
            )
            
            Log.d(TAG, "Captured WebP image: ${capturedImage.width}x${capturedImage.height}, " +
                   "size=${capturedImage.fileSizeBytes} bytes, " +
                   "time=${capturedImage.captureTimeMs}ms")
            
            Result.success(capturedImage)
            
        } catch (e: Exception) {
            Log.e(TAG, "Failed to process camera image", e)
            Result.failure(e)
        } finally {
            imageProxy.close()
        }
    }
    
    /**
     * Process existing file to WebP format
     */
    suspend fun processFileToWebP(
        sourceFile: File,
        config: ImageProcessingConfig = ImageProcessingConfig()
    ): Result<CapturedImage> = withContext(Dispatchers.IO) {
        try {
            val startTime = System.currentTimeMillis()
            
            // Load and decode bitmap
            val bitmap = loadBitmapFromFile(sourceFile)
            
            // Optimize for purpose
            val optimizedBitmap = optimizeBitmap(bitmap, config)
            
            // Convert to WebP
            val webpData = bitmapToWebP(optimizedBitmap, config.quality)
            
            // Save to temporary file
            val tempFile = createTempImageFile()
            saveWebPToFile(webpData, tempFile)
            
            val capturedImage = CapturedImage(
                bitmap = optimizedBitmap,
                webpData = webpData,
                filePath = tempFile.absolutePath,
                width = optimizedBitmap.width,
                height = optimizedBitmap.height,
                fileSizeBytes = webpData.size,
                captureTimeMs = System.currentTimeMillis() - startTime
            )
            
            Log.d(TAG, "Processed file to WebP: ${capturedImage.width}x${capturedImage.height}, " +
                   "size=${capturedImage.fileSizeBytes} bytes")
            
            Result.success(capturedImage)
            
        } catch (e: Exception) {
            Log.e(TAG, "Failed to process file to WebP", e)
            Result.failure(e)
        }
    }
    
    /**
     * Get optimal configuration based on device capabilities
     */
    fun getOptimalConfig(purpose: String = "general"): ImageProcessingConfig {
        val config = performanceConfigManager.getOptimalConfig()
        
        return when (purpose.lowercase()) {
            "ocr" -> ImageProcessingConfig(
                quality = 95, // Highest quality for OCR
                maxWidth = 1920,
                maxHeight = 1080,
                enableOptimization = false, // No compression artifacts
                enableWatermark = false
            )
            "storage" -> ImageProcessingConfig(
                quality = config.imageCompressionQuality,
                maxWidth = config.imageMaxWidth,
                maxHeight = config.imageMaxHeight,
                enableOptimization = true,
                enableWatermark = true
            )
            "web" -> ImageProcessingConfig(
                quality = maxOf(60, config.imageCompressionQuality - 20), // Lower for web
                maxWidth = 800,
                maxHeight = 600,
                enableOptimization = true,
                enableWatermark = true
            )
            "thumbnail" -> ImageProcessingConfig(
                quality = 60,
                maxWidth = 200,
                maxHeight = 150,
                enableOptimization = true,
                enableWatermark = false
            )
            else -> ImageProcessingConfig(
                quality = config.imageCompressionQuality,
                maxWidth = config.imageMaxWidth,
                maxHeight = config.imageMaxHeight,
                enableOptimization = true,
                enableWatermark = false
            )
        }
    }
    
    /**
     * Convert ImageProxy to Bitmap
     */
    private fun imageProxyToBitmap(imageProxy: ImageProxy): Bitmap {
        return when (imageProxy.format) {
            ImageFormat.YUV_420_888 -> {
                val yBuffer = imageProxy.planes[0].buffer
                val uBuffer = imageProxy.planes[1].buffer
                val vBuffer = imageProxy.planes[2].buffer
                
                val ySize = yBuffer.remaining()
                val uSize = uBuffer.remaining()
                val vSize = vBuffer.remaining()
                
                val nv21 = ByteArray(ySize + uSize + vSize)
                
                yBuffer.get(nv21, 0, ySize)
                
                val uvPixelStride = imageProxy.planes[1].pixelStride
                if (uvPixelStride == 1) {
                    vBuffer.get(nv21, ySize, vSize)
                    uBuffer.get(nv21, ySize + vSize, uSize)
                } else {
                    // Handle interleaved UV
                    val uvBuffer = ByteArray(uSize + vSize)
                    uBuffer.get(uvBuffer, 0, uSize)
                    vBuffer.get(uvBuffer, uSize, vSize)
                    
                    for (i in 0 until uSize) {
                        nv21[ySize + i * 2] = uvBuffer[i]
                        nv21[ySize + i * 2 + 1] = uvBuffer[uSize + i]
                    }
                }
                
                val yuvImage = YuvImage(nv21, ImageFormat.NV21, imageProxy.width, imageProxy.height, null)
                val out = ByteArrayOutputStream()
                val rect = Rect(0, 0, imageProxy.width, imageProxy.height)
                yuvImage.compressToJpeg(rect, 100, out)
                val imageBytes = out.toByteArray()
                BitmapFactory.decodeByteArray(imageBytes, 0, imageBytes.size)
            }
            else -> {
                // For other formats, convert to JPEG first then to Bitmap
                val buffer = imageProxy.planes[0].buffer
                val bytes = ByteArray(buffer.remaining())
                buffer.get(bytes)
                BitmapFactory.decodeByteArray(bytes, 0, bytes.size)
            }
        }
    }
    
    /**
     * Load bitmap from file with proper memory management
     */
    private fun loadBitmapFromFile(file: File): Bitmap {
        val options = BitmapFactory.Options().apply {
            inJustDecodeBounds = true
        }
        BitmapFactory.decodeFile(file.absolutePath, options)
        
        // Calculate inSampleSize
        val config = performanceConfigManager.getOptimalConfig()
        options.inSampleSize = calculateInSampleSize(
            options.outWidth, options.outHeight,
            config.imageMaxWidth, config.imageMaxHeight
        )
        
        options.inJustDecodeBounds = false
        return BitmapFactory.decodeFile(file.absolutePath, options)
    }
    
    /**
     * Optimize bitmap according to configuration
     */
    private fun optimizeBitmap(bitmap: Bitmap, config: ImageProcessingConfig): Bitmap {
        var optimized = bitmap
        
        // Resize if needed
        if (bitmap.width > config.maxWidth || bitmap.height > config.maxHeight) {
            val ratio = minOf(
                config.maxWidth.toFloat() / bitmap.width,
                config.maxHeight.toFloat() / bitmap.height
            )
            
            val newWidth = (bitmap.width * ratio).toInt()
            val newHeight = (bitmap.height * ratio).toInt()
            
            optimized = Bitmap.createScaledBitmap(optimized, newWidth, newHeight, true)
        }
        
        // Apply watermark if enabled
        if (config.enableWatermark) {
            optimized = applyWatermark(optimized)
        }
        
        return optimized
    }
    
    /**
     * Convert bitmap to WebP format
     */
    private fun bitmapToWebP(bitmap: Bitmap, quality: Int): ByteArray {
        val stream = ByteArrayOutputStream()
        
        // Android 4.0+ supports WebP
        val success = if (android.os.Build.VERSION.SDK_INT >= android.os.Build.VERSION_CODES.Q) {
            bitmap.compress(Bitmap.CompressFormat.WEBP, quality, stream)
        } else {
            // Fallback to PNG for older Android versions
            bitmap.compress(Bitmap.CompressFormat.PNG, quality, stream)
        }
        
        if (!success) {
            throw RuntimeException("Failed to compress bitmap to WebP")
        }
        
        return stream.toByteArray()
    }
    
    /**
     * Save WebP data to file
     */
    private fun saveWebPToFile(webpData: ByteArray, file: File) {
        FileOutputStream(file).use { output ->
            output.write(webpData)
            output.flush()
        }
    }
    
    /**
     * Create temporary image file
     */
    private fun createTempImageFile(): File {
        val tempDir = File(context.cacheDir, "faro_images")
        if (!tempDir.exists()) {
            tempDir.mkdirs()
        }
        
        return File.createTempFile(
            TEMP_IMAGE_PREFIX,
            TEMP_IMAGE_SUFFIX,
            tempDir
        )
    }
    
    /**
     * Calculate inSampleSize for efficient bitmap loading
     */
    private fun calculateInSampleSize(
        width: Int, height: Int,
        reqWidth: Int, reqHeight: Int
    ): Int {
        var inSampleSize = 1
        
        if (height > reqHeight || width > reqWidth) {
            val halfHeight = height / 2
            val halfWidth = width / 2
            
            while (halfWidth / inSampleSize >= reqWidth && halfHeight / inSampleSize >= reqHeight) {
                inSampleSize *= 2
            }
        }
        
        return inSampleSize
    }
    
    /**
     * Apply F.A.R.O. watermark to bitmap
     */
    private fun applyWatermark(bitmap: Bitmap): Bitmap {
        // This is a simplified watermark implementation
        // In production, you'd want a more sophisticated watermarking system
        return bitmap
    }
    
    /**
     * Clean up temporary files
     */
    fun cleanupTempFiles() {
        try {
            val tempDir = File(context.cacheDir, "faro_images")
            if (tempDir.exists()) {
                tempDir.listFiles()?.forEach { file ->
                    if (file.name.startsWith(TEMP_IMAGE_PREFIX)) {
                        file.delete()
                    }
                }
            }
        } catch (e: Exception) {
            Log.e(TAG, "Failed to cleanup temp files", e)
        }
    }
    
    /**
     * Get image file info
     */
    suspend fun getImageInfo(filePath: String): Result<Map<String, Any>> = withContext(Dispatchers.IO) {
        try {
            val file = File(filePath)
            if (!file.exists()) {
                return Result.failure(Exception("File not found"))
            }
            
            val options = BitmapFactory.Options().apply {
                inJustDecodeBounds = true
            }
            BitmapFactory.decodeFile(filePath, options)
            
            val info = mapOf(
                "width" to options.outWidth,
                "height" to options.outHeight,
                "fileSize" to file.length(),
                "format" to "webp",
                "path" to filePath,
                "exists" to true
            )
            
            Result.success(info)
            
        } catch (e: Exception) {
            Log.e(TAG, "Failed to get image info", e)
            Result.failure(e)
        }
    }
}
