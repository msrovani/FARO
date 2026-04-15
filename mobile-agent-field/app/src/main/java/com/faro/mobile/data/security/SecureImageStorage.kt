package com.faro.mobile.data.security

import android.content.Context
import android.graphics.Bitmap
import android.graphics.BitmapFactory
import android.graphics.Matrix
import android.media.ExifInterface
import timber.log.Timber
import java.io.ByteArrayOutputStream
import java.io.File
import java.io.FileOutputStream
import kotlin.math.min

/**
 * Secure storage for images with compression and encryption.
 * 
 * ARCHITECTURE PRINCIPLES:
 * - Low resolution but auditable (800x600 max)
 * - AES-256 encryption at rest
 * - Secure deletion after server confirmation
 * - No high-res images on device
 */
class SecureImageStorage(context: Context) {
    
    private val key = CryptoUtils.getOrCreateKey(KEY_ALIAS)
    private val storageDir = context.getDir("secure_images", Context.MODE_PRIVATE)
    
    companion object {
        private const val KEY_ALIAS = "faro_image_key"
        
        // Resolution constraints - AUDITABLE but low-res
        const val MAX_WIDTH = 800
        const val MAX_HEIGHT = 600
        const val COMPRESS_QUALITY = 85 // JPEG quality
        
        // Security
        private const val SECURE_WIPE_PASSES = 3
        
        // Format
        private const val EXTENSION = ".enc"
    }
    
    /**
     * Save image from Bitmap with compression and encryption.
     * 
     * FLOW:
     * 1. Compress to audit resolution (800x600 max)
     * 2. Encode to JPEG
     * 3. Encrypt with AES-256-GCM
     * 4. Save to secure storage
     */
    fun saveImage(bitmap: Bitmap, id: String): File {
        // Step 1: Compress to audit resolution
        val compressed = compressToAuditSize(bitmap)
        
        // Step 2: Encode to JPEG
        val stream = ByteArrayOutputStream()
        compressed.compress(Bitmap.CompressFormat.JPEG, COMPRESS_QUALITY, stream)
        val jpegBytes = stream.toByteArray()
        
        // Step 3: Encrypt
        val encrypted = CryptoUtils.encrypt(jpegBytes, key)
        
        // Step 4: Save to file (IV + ciphertext)
        val file = File(storageDir, "$id$EXTENSION")
        file.writeBytes(encrypted.toCombinedByteArray())
        
        // Clear sensitive data from memory
        CryptoUtils.secureClear(jpegBytes)
        stream.reset()
        
        Timber.d("Saved encrypted image $id (${file.length()} bytes)")
        return file
    }
    
    /**
     * Save image from file path (handles rotation from EXIF).
     */
    fun saveImageFromFile(sourcePath: String, id: String): File? {
        return try {
            // Read and rotate based on EXIF
            val bitmap = loadBitmapWithRotation(sourcePath) ?: return null
            
            val result = saveImage(bitmap, id)
            
            // Clear from memory
            bitmap.recycle()
            
            result
        } catch (e: Exception) {
            Timber.e(e, "Failed to save image from file: $sourcePath")
            null
        }
    }
    
    /**
     * Retrieve image for upload (decrypts to memory only).
     * Returns JPEG bytes ready for upload.
     */
    fun retrieveForUpload(id: String): ByteArray? {
        val file = File(storageDir, "$id$EXTENSION")
        if (!file.exists()) {
            Timber.w("Encrypted image not found: $id")
            return null
        }
        
        return try {
            // Read encrypted file
            val combined = file.readBytes()
            val encrypted = EncryptedData.fromCombinedByteArray(combined)
            
            // Decrypt to memory
            val decrypted = CryptoUtils.decrypt(encrypted, key)
            
            Timber.d("Retrieved image $id for upload (${decrypted.size} bytes)")
            decrypted
        } catch (e: Exception) {
            Timber.e(e, "Failed to decrypt image: $id")
            null
        }
    }
    
    /**
     * Retrieve image as Bitmap (for display only).
     * Use sparingly - decrypts to memory.
     */
    fun retrieveAsBitmap(id: String): Bitmap? {
        val jpegBytes = retrieveForUpload(id) ?: return null
        
        return try {
            BitmapFactory.decodeByteArray(jpegBytes, 0, jpegBytes.size)
        } finally {
            // Clear from memory
            CryptoUtils.secureClear(jpegBytes)
        }
    }
    
    /**
     * Check if encrypted image exists.
     */
    fun exists(id: String): Boolean {
        return File(storageDir, "$id$EXTENSION").exists()
    }
    
    /**
     * Get encrypted file size.
     */
    fun getSize(id: String): Long {
        return File(storageDir, "$id$EXTENSION").length()
    }
    
    /**
     * Securely delete image.
     * Implements DoD 5220.22-M standard (3-pass overwrite).
     */
    fun secureDelete(id: String) {
        val file = File(storageDir, "$id$EXTENSION")
        if (!file.exists()) return
        
        try {
            val size = file.length()
            
            // Overwrite with random data (3 passes)
            repeat(SECURE_WIPE_PASSES) { pass ->
                val garbage = CryptoUtils.generateRandomBytes(size.toInt())
                FileOutputStream(file).use { it.write(garbage) }
                file.sync() // Ensure written to disk
                Timber.v("Secure wipe image $id pass ${pass + 1}/$SECURE_WIPE_PASSES")
            }
            
            // Delete
            file.delete()
            
            Timber.d("Securely deleted image $id")
        } catch (e: Exception) {
            Timber.e(e, "Failed to securely delete image: $id")
            // Fallback: try normal delete
            file.delete()
        }
    }
    
    /**
     * Securely delete all images (emergency wipe).
     */
    fun secureDeleteAll() {
        storageDir.listFiles()?.forEach { file ->
            val id = file.nameWithoutExtension
            secureDelete(id)
        }
    }
    
    /**
     * Compress bitmap to audit size.
     * Maintains aspect ratio, fits within MAX_WIDTH x MAX_HEIGHT.
     * 
     * AUDIT REQUIREMENTS:
     * - Sufficient for human visual identification
     * - Sufficient for OCR reprocessing
     * - Not high-res (security/privacy)
     */
    private fun compressToAuditSize(bitmap: Bitmap): Bitmap {
        val width = bitmap.width
        val height = bitmap.height
        
        // Calculate scale factor
        val scale = minOf(
            MAX_WIDTH.toFloat() / width,
            MAX_HEIGHT.toFloat() / height,
            1.0f // Don't upscale
        )
        
        // If already small enough, return as-is
        if (scale >= 1.0f) return bitmap
        
        val newWidth = (width * scale).toInt()
        val newHeight = (height * scale).toInt()
        
        return Bitmap.createScaledBitmap(bitmap, newWidth, newHeight, true)
    }
    
    /**
     * Load bitmap with EXIF rotation correction.
     */
    private fun loadBitmapWithRotation(path: String): Bitmap? {
        // Decode bounds first
        val options = BitmapFactory.Options().apply {
            inJustDecodeBounds = true
        }
        BitmapFactory.decodeFile(path, options)
        
        // Calculate sample size to avoid OOM
        options.inSampleSize = calculateInSampleSize(options, MAX_WIDTH * 2, MAX_HEIGHT * 2)
        options.inJustDecodeBounds = false
        
        // Decode bitmap
        val bitmap = BitmapFactory.decodeFile(path, options) ?: return null
        
        // Read EXIF rotation
        val rotation = try {
            val exif = ExifInterface(path)
            when (exif.getAttributeInt(ExifInterface.TAG_ORIENTATION, ExifInterface.ORIENTATION_NORMAL)) {
                ExifInterface.ORIENTATION_ROTATE_90 -> 90
                ExifInterface.ORIENTATION_ROTATE_180 -> 180
                ExifInterface.ORIENTATION_ROTATE_270 -> 270
                else -> 0
            }
        } catch (e: Exception) {
            0
        }
        
        // Apply rotation if needed
        return if (rotation != 0) {
            val matrix = Matrix().apply { postRotate(rotation.toFloat()) }
            Bitmap.createBitmap(bitmap, 0, 0, bitmap.width, bitmap.height, matrix, true)
                .also { bitmap.recycle() } // Recycle original
        } else {
            bitmap
        }
    }
    
    /**
     * Calculate sample size for BitmapFactory.
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
            
            while ((halfHeight / inSampleSize) >= reqHeight &&
                   (halfWidth / inSampleSize) >= reqWidth) {
                inSampleSize *= 2
            }
        }
        
        return inSampleSize
    }
    
    /**
     * Get storage statistics.
     */
    fun getStats(): ImageStorageStats {
        val files = storageDir.listFiles() ?: emptyArray()
        val totalSize = files.sumOf { it.length() }
        val count = files.count { it.extension == EXTENSION.removePrefix(".") }
        
        return ImageStorageStats(
            encryptedImageCount = count,
            totalEncryptedBytes = totalSize,
            averageImageSize = if (count > 0) totalSize / count else 0
        )
    }
}

/**
 * Storage statistics for images.
 */
data class ImageStorageStats(
    val encryptedImageCount: Int,
    val totalEncryptedBytes: Long,
    val averageImageSize: Long
)
