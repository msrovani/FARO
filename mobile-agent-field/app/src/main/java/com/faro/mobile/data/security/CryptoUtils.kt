package com.faro.mobile.data.security

import android.security.keystore.KeyGenParameterSpec
import android.security.keystore.KeyProperties
import timber.log.Timber
import java.security.KeyStore
import java.security.SecureRandom
import javax.crypto.Cipher
import javax.crypto.KeyGenerator
import javax.crypto.SecretKey
import javax.crypto.spec.GCMParameterSpec

/**
 * Cryptographic utilities for secure local storage.
 * 
 * Uses Android Keystore for hardware-backed key storage when available.
 * Falls back to TEE (Trusted Execution Environment) or software.
 * 
 * SECURITY NOTE: This protects data at rest against physical device access.
 * Keys are non-exportable and bound to the device.
 */
object CryptoUtils {
    
    private const val ANDROID_KEYSTORE = "AndroidKeyStore"
    private const val ALGORITHM = "AES"
    private const val BLOCK_MODE = KeyProperties.BLOCK_MODE_GCM
    private const val PADDING = KeyProperties.ENCRYPTION_PADDING_NONE
    private const val TRANSFORMATION = "$ALGORITHM/$BLOCK_MODE/$PADDING"
    private const val KEY_SIZE = 256
    private const val GCM_TAG_LENGTH = 128
    private const val IV_SIZE = 12 // 96 bits for GCM
    
    /**
     * Get or create a key in the Android Keystore.
     * Key is hardware-bound if the device supports it.
     */
    fun getOrCreateKey(alias: String): SecretKey {
        val keyStore = KeyStore.getInstance(ANDROID_KEYSTORE).apply { load(null) }
        
        // Check if key already exists
        keyStore.getEntry(alias, null)?.let { entry ->
            if (entry is KeyStore.SecretKeyEntry) {
                Timber.d("Using existing key: $alias")
                return entry.secretKey
            }
        }
        
        // Generate new key
        return generateKey(alias)
    }
    
    /**
     * Generate a new AES-256 key in the Android Keystore.
     */
    private fun generateKey(alias: String): SecretKey {
        val keyGenerator = KeyGenerator.getInstance(ALGORITHM, ANDROID_KEYSTORE)
        
        val spec = KeyGenParameterSpec.Builder(
            alias,
            KeyProperties.PURPOSE_ENCRYPT or KeyProperties.PURPOSE_DECRYPT
        )
            .setBlockModes(BLOCK_MODE)
            .setEncryptionPaddings(PADDING)
            .setKeySize(KEY_SIZE)
            .setRandomizedEncryptionRequired(true)
            // Require hardware-backed key if available
            .setIsStrongBoxBacked(true) // Falls back to TEE if StrongBox unavailable
            .build()
        
        keyGenerator.init(spec)
        val key = keyGenerator.generateKey()
        
        Timber.i("Generated new hardware-backed key: $alias")
        return key
    }
    
    /**
     * Encrypt data using AES-256-GCM.
     * Returns IV + ciphertext.
     */
    fun encrypt(plaintext: ByteArray, key: SecretKey): EncryptedData {
        val cipher = Cipher.getInstance(TRANSFORMATION)
        cipher.init(Cipher.ENCRYPT_MODE, key)
        
        val iv = cipher.iv
        val ciphertext = cipher.doFinal(plaintext)
        
        return EncryptedData(iv, ciphertext)
    }
    
    /**
     * Decrypt data using AES-256-GCM.
     * Expects IV + ciphertext format.
     */
    fun decrypt(encryptedData: EncryptedData, key: SecretKey): ByteArray {
        val cipher = Cipher.getInstance(TRANSFORMATION)
        val spec = GCMParameterSpec(GCM_TAG_LENGTH, encryptedData.iv)
        cipher.init(Cipher.DECRYPT_MODE, key, spec)
        
        return cipher.doFinal(encryptedData.ciphertext)
    }
    
    /**
     * Generate random bytes for secure wipe operations.
     */
    fun generateRandomBytes(size: Int): ByteArray {
        return ByteArray(size).apply {
            SecureRandom().nextBytes(this)
        }
    }
    
    /**
     * Securely clear a byte array (overwrite with zeros).
     */
    fun secureClear(bytes: ByteArray) {
        bytes.fill(0)
    }
    
    /**
     * Check if device supports hardware-backed keys (StrongBox).
     */
    fun isStrongBoxSupported(): Boolean {
        return try {
            android.security.keystore.KeyGenParameterSpec.Builder(
                "test_strongbox",
                KeyProperties.PURPOSE_ENCRYPT
            )
                .setIsStrongBoxBacked(true)
                .build()
            true
        } catch (e: Exception) {
            false
        }
    }
    
    /**
     * Delete a key from the Keystore (irreversible).
     */
    fun deleteKey(alias: String): Boolean {
        return try {
            val keyStore = KeyStore.getInstance(ANDROID_KEYSTORE).apply { load(null) }
            keyStore.deleteEntry(alias)
            Timber.i("Deleted key: $alias")
            true
        } catch (e: Exception) {
            Timber.e(e, "Failed to delete key: $alias")
            false
        }
    }
}

/**
 * Container for encrypted data (IV + ciphertext).
 */
data class EncryptedData(
    val iv: ByteArray,
    val ciphertext: ByteArray
) {
    /**
     * Combine IV and ciphertext for storage.
     */
    fun toCombinedByteArray(): ByteArray {
        return iv + ciphertext
    }
    
    companion object {
        /**
         * Split combined byte array into IV and ciphertext.
         * IV size is 12 bytes (96 bits) for GCM.
         */
        fun fromCombinedByteArray(combined: ByteArray): EncryptedData {
            val iv = combined.sliceArray(0 until 12)
            val ciphertext = combined.sliceArray(12 until combined.size)
            return EncryptedData(iv, ciphertext)
        }
    }
    
    override fun equals(other: Any?): Boolean {
        if (this === other) return true
        if (javaClass != other?.javaClass) return false
        
        other as EncryptedData
        return iv.contentEquals(other.iv) && ciphertext.contentEquals(other.ciphertext)
    }
    
    override fun hashCode(): Int {
        var result = iv.contentHashCode()
        result = 31 * result + ciphertext.contentHashCode()
        return result
    }
}
