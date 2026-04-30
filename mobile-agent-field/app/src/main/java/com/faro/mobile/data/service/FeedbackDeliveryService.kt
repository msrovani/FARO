package com.faro.mobile.data.service

import com.faro.mobile.data.remote.FaroMobileApi
import com.faro.mobile.data.remote.MarkFeedbackReadRequestDto
import com.jakewharton.timber.Timber
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import java.time.Instant
import javax.inject.Inject
import javax.inject.Singleton

/**
 * Feedback Delivery Service - Manages feedback delivery confirmation (ACK).
 * 
 * Features:
 * - Automatic ACK when feedback is received
 * - Retry mechanism for failed ACKs
 * - Cache of unacknowledged feedbacks
 * - Delivery status tracking
 * - Ordered delivery based on timestamp
 */
@Singleton
class FeedbackDeliveryService @Inject constructor(
    private val faroMobileApi: FaroMobileApi
) {
    
    /**
     * Delivery status
     */
    enum class DeliveryStatus {
        PENDING,      // Not yet acknowledged
        ACK_SENT,      // ACK sent, waiting for confirmation
        DELIVERED,     // Delivery confirmed
        FAILED         // Delivery failed
    }
    
    /**
     * Feedback delivery record
     */
    data class FeedbackDeliveryRecord(
        val feedbackId: String,
        val status: DeliveryStatus,
        val receivedAt: Instant,
        val ackSentAt: Instant? = null,
        val confirmedAt: Instant? = null,
        val retryCount: Int = 0,
        val maxRetries: Int = 3
    )
    
    private val deliveryRecords = mutableMapOf<String, FeedbackDeliveryRecord>()
    private val maxCacheSize = 100
    
    /**
     * Process received feedback and send ACK
     */
    suspend fun processFeedback(feedbackId: String): Boolean {
        Timber.d("Processing feedback: $feedbackId")
        
        // Check if already processed
        val existing = deliveryRecords[feedbackId]
        if (existing != null && existing.status == DeliveryStatus.DELIVERED) {
            Timber.d("Feedback $feedbackId already delivered")
            return true
        }
        
        // Create delivery record
        val record = FeedbackDeliveryRecord(
            feedbackId = feedbackId,
            status = DeliveryStatus.PENDING,
            receivedAt = Instant.now()
        )
        deliveryRecords[feedbackId] = record
        
        // Send ACK
        return sendAck(feedbackId)
    }
    
    /**
     * Send ACK for feedback
     */
    private suspend fun sendAck(feedbackId: String): Boolean = withContext(Dispatchers.IO) {
        try {
            Timber.d("Sending ACK for feedback: $feedbackId")
            
            val request = MarkFeedbackReadRequestDto(
                read_at = Instant.now().toString()
            )
            
            faroMobileApi.markFeedbackRead(feedbackId, request)
            
            // Update record status
            val record = deliveryRecords[feedbackId]
            if (record != null) {
                deliveryRecords[feedbackId] = record.copy(
                    status = DeliveryStatus.ACK_SENT,
                    ackSentAt = Instant.now()
                )
            }
            
            Timber.d("ACK sent successfully for feedback: $feedbackId")
            true
            
        } catch (e: Exception) {
            Timber.e(e, "Failed to send ACK for feedback: $feedbackId")
            
            // Update record status
            val record = deliveryRecords[feedbackId]
            if (record != null) {
                val updatedRecord = record.copy(
                    status = DeliveryStatus.FAILED,
                    retryCount = record.retryCount + 1
                )
                
                if (updatedRecord.retryCount >= updatedRecord.maxRetries) {
                    // Max retries reached, keep as failed
                    deliveryRecords[feedbackId] = updatedRecord
                } else {
                    // Keep as pending for retry
                    deliveryRecords[feedbackId] = updatedRecord.copy(status = DeliveryStatus.PENDING)
                }
            }
            
            false
        }
    }
    
    /**
     * Mark feedback as delivered (confirmed by server)
     */
    fun markAsDelivered(feedbackId: String) {
        val record = deliveryRecords[feedbackId]
        if (record != null) {
            deliveryRecords[feedbackId] = record.copy(
                status = DeliveryStatus.DELIVERED,
                confirmedAt = Instant.now()
            )
            Timber.d("Feedback $feedbackId marked as delivered")
        }
    }
    
    /**
     * Retry pending ACKs
     */
    suspend fun retryPendingAcks(): Int {
        val pendingRecords = deliveryRecords.values
            .filter { it.status == DeliveryStatus.PENDING && it.retryCount < it.maxRetries }
        
        Timber.d("Retrying ${pendingRecords.size} pending ACKs")
        
        var successCount = 0
        for (record in pendingRecords) {
            if (sendAck(record.feedbackId)) {
                successCount++
            }
        }
        
        return successCount
    }
    
    /**
     * Get delivery statistics
     */
    fun getDeliveryStats(): Map<String, Any> {
        val byStatus = deliveryRecords.values.groupBy { it.status }
        
        return mapOf(
            "total" to deliveryRecords.size,
            "pending" to (byStatus[DeliveryStatus.PENDING]?.size ?: 0),
            "ack_sent" to (byStatus[DeliveryStatus.ACK_SENT]?.size ?: 0),
            "delivered" to (byStatus[DeliveryStatus.DELIVERED]?.size ?: 0),
            "failed" to (byStatus[DeliveryStatus.FAILED]?.size ?: 0)
        )
    }
    
    /**
     * Get unacknowledged feedbacks ordered by timestamp
     */
    fun getUnacknowledgedFeedbacks(): List<FeedbackDeliveryRecord> {
        return deliveryRecords.values
            .filter { it.status == DeliveryStatus.PENDING || it.status == DeliveryStatus.FAILED }
            .sortedBy { it.receivedAt }
    }
    
    /**
     * Clear delivery records
     */
    fun clearRecords() {
        deliveryRecords.clear()
        Timber.d("Delivery records cleared")
    }
    
    /**
     * Clear old records (older than 24 hours)
     */
    fun clearOldRecords() {
        val cutoff = Instant.now().minusSeconds(24 * 60 * 60)
        val toRemove = deliveryRecords.values
            .filter { it.receivedAt.isBefore(cutoff) }
            .map { it.feedbackId }
        
        toRemove.forEach { deliveryRecords.remove(it) }
        
        Timber.d("Cleared ${toRemove.size} old delivery records")
    }
    
    /**
     * Limit cache size
     */
    private fun limitCacheSize() {
        if (deliveryRecords.size > maxCacheSize) {
            val toRemove = deliveryRecords.entries
                .sortedBy { it.value.receivedAt }
                .take(deliveryRecords.size - maxCacheSize)
                .map { it.key }
            
            toRemove.forEach { deliveryRecords.remove(it) }
        }
    }
}
