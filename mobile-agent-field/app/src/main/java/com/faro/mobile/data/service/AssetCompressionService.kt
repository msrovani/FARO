package com.faro.mobile.data.service

import android.content.Context
import android.graphics.Bitmap
import android.graphics.BitmapFactory
import android.graphics.Matrix
import androidx.exifinterface.media.ExifInterface
import com.jakewharton.timber.Timber
import dagger.hilt.android.qualifiers.ApplicationContext
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import java.io.ByteArrayOutputStream
import java.io.File
import java.io.FileOutputStream
import javax.inject.Inject
import javax.inject.Singleton

/**
 * Asset Compression Service - Compresses images before upload to reduce data usage.
 * 
 * Features:
 * - JPEG/WebP compression with configurable quality
 * - Automatic EXIF rotation correction
 * - Adaptive quality based on network conditions
 * - Size estimation before compression
 * - Progressive upload support
 */
@Singleton
class AssetCompressionService @Inject constructor(
    @ApplicationContext private val context: Context
) {
    
    /**
     * Compression result
     */
    data class CompressionResult(
        val compressedFile: File,
        val originalSizeBytes: Long,
        val compressedSizeBytes: Long,
        val compressionRatio: Float,
        val quality: Int,
        val format: String
    )
    
    /**
     * Compression format
     */
    enum class CompressionFormat(val mimeType: String, val extension: String) {
        JPEG("image/jpeg", "jpg"),
        WEBP("image/webp", "webp")
    }
    
    /**
     * Default quality levels
     */
    enum class QualityLevel(val value: Int) {
        HIGH(90),
        MEDIUM(80),
        LOW(70),
        VERY_LOW(60)
    }
    
    /**
     * Compress image file
     */
    suspend fun compressImage(
        inputFile: File,
        outputFile: File? = null,
        quality: QualityLevel = QualityLevel.MEDIUM,
        format: CompressionFormat = CompressionFormat.WEBP,
        maxWidth: Int = 1920,
        maxHeight: Int = 1080
    ): CompressionResult = withContext(Dispatchers.IO) {
        val startTime = System.currentTimeMillis()
        val originalSize = inputFile.length()
        
        Timber.d("Compressing image: ${inputFile.name}, original size: ${originalSize / 1024}KB")
        
        // Decode bitmap with sampling
        val options = BitmapFactory.Options().apply {
            inJustDecodeBounds = true
        }
        BitmapFactory.decodeFile(inputFile.absolutePath, options)
        
        // Calculate inSampleSize
        options.inSampleSize = calculateInSampleSize(options, maxWidth, maxHeight)
        options.inJustDecodeBounds = false
        
        val bitmap = BitmapFactory.decodeFile(inputFile.absolutePath, options)
        
        // Handle EXIF rotation
        val rotatedBitmap = fixExifRotation(inputFile, bitmap)
        
        // Compress
        val outputStream = ByteArrayOutputStream()
        val compressFormat = when (format) {
            CompressionFormat.JPEG -> Bitmap.CompressFormat.JPEG
            CompressionFormat.WEBP -> Bitmap.CompressFormat.WEBP_LOSSY
        }
        
        rotatedBitmap.compress(compressFormat, quality.value, outputStream)
        
        // Write to file
        val output = outputFile ?: File(inputFile.parent, "${inputFile.nameWithoutExtension}_compressed.${format.extension}")
        FileOutputStream(output).use { it.write(outputStream.toByteArray()) }
        
        val compressedSize = output.length()
        val compressionRatio = (1f - (compressedSize.toFloat() / originalSize.toFloat())) * 100f
        
        // Clean up
        rotatedBitmap.recycle()
        if (rotatedBitmap != bitmap) {
            bitmap.recycle()
        }
        
        val duration = System.currentTimeMillis() - startTime
        Timber.d("Compression completed in ${duration}ms: ${originalSize / 1024}KB -> ${compressedSize / 1024}KB (${compressionRatio.toInt()}% reduction)")
        
        CompressionResult(
            compressedFile = output,
            originalSizeBytes = originalSize,
            compressedSizeBytes = compressedSize,
            compressionRatio = compressionRatio,
            quality = quality.value,
            format = format.extension
        )
    }
    
    /**
     * Compress bitmap directly
     */
    suspend fun compressBitmap(
        bitmap: Bitmap,
        quality: QualityLevel = QualityLevel.MEDIUM,
        format: CompressionFormat = CompressionFormat.WEBP,
        maxWidth: Int = 1920,
        maxHeight: Int = 1080
    ): ByteArray = withContext(Dispatchers.IO) {
        // Scale if needed
        val scaledBitmap = scaleBitmap(bitmap, maxWidth, maxHeight)
        
        // Compress
        val outputStream = ByteArrayOutputStream()
        val compressFormat = when (format) {
            CompressionFormat.JPEG -> Bitmap.CompressFormat.JPEG
            CompressionFormat.WEBP -> Bitmap.CompressFormat.WEBP_LOSSY
        }
        
        scaledBitmap.compress(compressFormat, quality.value, outputStream)
        
        // Clean up
        if (scaledBitmap != bitmap) {
            scaledBitmap.recycle()
        }
        
        outputStream.toByteArray()
    }
    
    /**
     * Get optimal quality based on network conditions
     */
    fun getOptimalQuality(networkQuality: String, batteryLevel: Float): QualityLevel {
        return when {
            batteryLevel < 0.2f -> QualityLevel.LOW
            networkQuality == "2g" || networkQuality == "3g" -> QualityLevel.LOW
            networkQuality == "4g" -> QualityLevel.MEDIUM
            networkQuality == "wifi" -> QualityLevel.HIGH
            else -> QualityLevel.MEDIUM
        }
    }
    
    /**
     * Estimate compressed size without actual compression
     */
    fun estimateCompressedSize(
        originalSizeBytes: Long,
        quality: QualityLevel,
        format: CompressionFormat
    ): Long {
        // Rough estimation based on format and quality
        val qualityFactor = quality.value / 100f
        val formatFactor = when (format) {
            CompressionFormat.WEBP -> 0.7f // WebP is more efficient
            CompressionFormat.JPEG -> 1.0f
        }
        
        return (originalSizeBytes * qualityFactor * formatFactor).toLong()
    }
    
    /**
     * Calculate inSampleSize for efficient decoding
     */
    private fun calculateInSampleSize(
        options: BitmapFactory.Options,
        reqWidth: Int,
        reqHeight: Int
    ): Int {
        val height = options.outHeight
        val width = options.outWidth
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
     * Fix EXIF rotation
     */
    private fun fixExifRotation(imageFile: File, bitmap: Bitmap): Bitmap {
        try {
            val exif = ExifInterface(imageFile.absolutePath)
            val orientation = exif.getAttributeInt(
                ExifInterface.TAG_ORIENTATION,
                ExifInterface.ORIENTATION_NORMAL
            )
            
            return when (orientation) {
                ExifInterface.ORIENTATION_ROTATE_90 -> rotateBitmap(bitmap, 90f)
                ExifInterface.ORIENTATION_ROTATE_180 -> rotateBitmap(bitmap, 180f)
                ExifInterface.ORIENTATION_ROTATE_270 -> rotateBitmap(bitmap, 270f)
                ExifInterface.ORIENTATION_FLIP_HORIZONTAL -> flipBitmap(bitmap, horizontal = true, vertical = false)
                ExifInterface.ORIENTATION_FLIP_VERTICAL -> flipBitmap(bitmap, horizontal = false, vertical = true)
                else -> bitmap
            }
        } catch (e: Exception) {
            Timber.w(e, "Failed to fix EXIF rotation")
            return bitmap
        }
    }
    
    /**
     * Rotate bitmap
     */
    private fun rotateBitmap(bitmap: Bitmap, degrees: Float): Bitmap {
        val matrix = Matrix()
        matrix.postRotate(degrees)
        
        val rotated = Bitmap.createBitmap(
            bitmap, 0, 0, bitmap.width, bitmap.height, matrix, true
        )
        
        if (rotated != bitmap) {
            bitmap.recycle()
        }
        
        return rotated
    }
    
    /**
     * Flip bitmap
     */
    private fun flipBitmap(bitmap: Bitmap, horizontal: Boolean, vertical: Boolean): Bitmap {
        val matrix = Matrix()
        matrix.postScale(
            if (horizontal) -1f else 1f,
            if (vertical) -1f else 1f,
            bitmap.width / 2f,
            bitmap.height / 2f
        )
        
        val flipped = Bitmap.createBitmap(
            bitmap, 0, 0, bitmap.width, bitmap.height, matrix, true
        )
        
        if (flipped != bitmap) {
            bitmap.recycle()
        }
        
        return flipped
    }
    
    /**
     * Scale bitmap to max dimensions
     */
    private fun scaleBitmap(bitmap: Bitmap, maxWidth: Int, maxHeight: Int): Bitmap {
        val width = bitmap.width
        val height = bitmap.height
        
        if (width <= maxWidth && height <= maxHeight) {
            return bitmap
        }
        
        val scale = minOf(maxWidth.toFloat() / width, maxHeight.toFloat() / height)
        val newWidth = (width * scale).toInt()
        val newHeight = (height * scale).toInt()
        
        val scaled = Bitmap.createScaledBitmap(bitmap, newWidth, newHeight, true)
        
        if (scaled != bitmap) {
            bitmap.recycle()
        }
        
        return scaled
    }
}
