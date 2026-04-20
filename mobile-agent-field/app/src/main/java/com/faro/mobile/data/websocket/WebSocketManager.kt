package com.faro.mobile.data.websocket

import android.util.Log
import com.faro.mobile.data.session.SessionRepository
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.MutableSharedFlow
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.SharedFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asSharedFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.Response
import okhttp3.WebSocket
import okhttp3.WebSocketListener
import java.util.concurrent.TimeUnit
import javax.inject.Inject
import javax.inject.Singleton

/**
 * WebSocket manager for real-time push notifications.
 * Manages WebSocket connection lifecycle and message handling.
 */
@Singleton
class WebSocketManager @Inject constructor(
    private val sessionRepository: SessionRepository
) {
    private val scope = CoroutineScope(SupervisorJob() + Dispatchers.IO)
    
    private var webSocket: WebSocket? = null
    private var okHttpClient: OkHttpClient? = null
    
    private val _connectionState = MutableStateFlow<ConnectionState>(ConnectionState.Disconnected)
    val connectionState: StateFlow<ConnectionState> = _connectionState.asStateFlow()
    
    private val _notifications = MutableStateFlow<List<PushNotification>>(emptyList())
    val notifications: StateFlow<List<PushNotification>> = _notifications.asStateFlow()

    private val _immediateAlerts = MutableSharedFlow<PushNotification>(replay = 0)
    val immediateAlerts: SharedFlow<PushNotification> = _immediateAlerts.asSharedFlow()
    
    private var reconnectAttempts = 0
    private val maxReconnectAttempts = 5
    
    /**
     * Connect to WebSocket server for user-specific notifications.
     */
    fun connect(userId: String, baseUrl: String) {
        if (webSocket != null) {
            Log.d(TAG, "WebSocket already connected")
            return
        }
        
        val token = sessionRepository.getAccessToken()
        if (token.isNullOrBlank()) {
            Log.e(TAG, "No access token available for WebSocket connection")
            _connectionState.value = ConnectionState.Error("No access token")
            return
        }
        
        val url = "$baseUrl/ws/user/$userId?token=$token"
        
        okHttpClient = OkHttpClient.Builder()
            .connectTimeout(10, TimeUnit.SECONDS)
            .readTimeout(30, TimeUnit.SECONDS)
            .writeTimeout(30, TimeUnit.SECONDS)
            .pingInterval(20, TimeUnit.SECONDS)
            .build()
        
        val request = Request.Builder()
            .url(url)
            .build()
        
        webSocket = okHttpClient?.newWebSocket(request, object : WebSocketListener() {
            override fun onOpen(ws: WebSocket, response: Response) {
                Log.d(TAG, "WebSocket connected")
                _connectionState.value = ConnectionState.Connected
                reconnectAttempts = 0
            }
            
            override fun onMessage(ws: WebSocket, text: String) {
                Log.d(TAG, "WebSocket message received: $text")
                handleMessage(text)
            }
            
            override fun onClosing(ws: WebSocket, code: Int, reason: String) {
                Log.d(TAG, "WebSocket closing: $code - $reason")
            }
            
            override fun onClosed(ws: WebSocket, code: Int, reason: String) {
                Log.d(TAG, "WebSocket closed: $code - $reason")
                _connectionState.value = ConnectionState.Disconnected
                webSocket = null
                attemptReconnect(userId, baseUrl)
            }
            
            override fun onFailure(ws: WebSocket, t: Throwable, response: Response?) {
                Log.e(TAG, "WebSocket error", t)
                _connectionState.value = ConnectionState.Error(t.message ?: "Unknown error")
                webSocket = null
                attemptReconnect(userId, baseUrl)
            }
        })
    }
    
    /**
     * Disconnect WebSocket.
     */
    fun disconnect() {
        webSocket?.close(1000, "User disconnected")
        webSocket = null
        okHttpClient = null
        _connectionState.value = ConnectionState.Disconnected
        reconnectAttempts = 0
        Log.d(TAG, "WebSocket disconnected")
    }
    
    /**
     * Attempt to reconnect with exponential backoff.
     */
    private fun attemptReconnect(userId: String, baseUrl: String) {
        if (reconnectAttempts >= maxReconnectAttempts) {
            Log.e(TAG, "Max reconnect attempts reached")
            return
        }
        
        reconnectAttempts++
        val delayMs = (1000L * Math.pow(2.0, reconnectAttempts.toDouble())).toLong().coerceAtMost(30000)
        
        scope.launch {
            Log.d(TAG, "Attempting reconnect in ${delayMs}ms (attempt $reconnectAttempts/$maxReconnectAttempts)")
            delay(delayMs)
            connect(userId, baseUrl)
        }
    }
    
    /**
     * Handle incoming WebSocket message.
     */
    private fun handleMessage(text: String) {
        try {
            // Parse JSON message
            // For now, just log - implement proper parsing based on message structure
            when {
                text.contains("\"type\":\"connected\"") -> {
                    Log.d(TAG, "WebSocket connection confirmed")
                }
                text.contains("\"type\":\"feedback_received\"") -> {
                    Log.d(TAG, "Feedback notification received")
                    // Parse and add to notifications
                    val notification = parseFeedbackNotification(text)
                    notification?.let {
                        val current = _notifications.value.toMutableList()
                        current.add(0, it)
                        _notifications.value = current
                        
                        // Emit to immediate alerts if it's high priority or "intercept"
                        if (it.type == "criminal_alert" || it.message.contains("INTERCEPT", ignoreCase = true)) {
                            scope.launch { _immediateAlerts.emit(it) }
                        }
                    }
                }
                else -> {
                    Log.d(TAG, "Unknown message type: $text")
                }
            }
        } catch (e: Exception) {
            Log.e(TAG, "Error parsing WebSocket message", e)
        }
    }
    
    /**
     * Parse feedback notification from JSON.
     */
    private fun parseFeedbackNotification(text: String): PushNotification? {
        // Simplified parsing - implement proper JSON parsing
        return try {
            PushNotification(
                type = "feedback_received",
                title = extractField(text, "title") ?: "Novo Feedback",
                message = extractField(text, "message") ?: "",
                timestamp = System.currentTimeMillis()
            )
        } catch (e: Exception) {
            Log.e(TAG, "Error parsing feedback notification", e)
            null
        }
    }
    
    /**
     * Extract field from JSON string (simplified).
     */
    private fun extractField(text: String, fieldName: String): String? {
        val pattern = "\"$fieldName\"\\s*:\\s*\"([^\"]*)\"".toRegex()
        val match = pattern.find(text)
        return match?.groupValues?.get(1)
    }
    
    /**
     * Clear all notifications.
     */
    fun clearNotifications() {
        _notifications.value = emptyList()
    }
    
    /**
     * Mark notification as read.
     */
    fun markAsRead(notificationId: String) {
        val current = _notifications.value.toMutableList()
        val index = current.indexOfFirst { it.id == notificationId }
        if (index >= 0) {
            current[index] = current[index].copy(read = true)
            _notifications.value = current
        }
    }
    
    sealed class ConnectionState {
        data object Connected : ConnectionState()
        data object Disconnected : ConnectionState()
        data class Error(val message: String) : ConnectionState()
    }
    
    data class PushNotification(
        val id: String = java.util.UUID.randomUUID().toString(),
        val type: String,
        val title: String,
        val message: String,
        val timestamp: Long,
        val read: Boolean = false
    )
    
    companion object {
        private const val TAG = "WebSocketManager"
    }
}
