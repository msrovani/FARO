package com.faro.mobile.data.websocket

import android.util.Log
import com.faro.mobile.data.remote.FaroMobileApi
import com.faro.mobile.data.session.SessionRepository
import com.faro.mobile.utils.TacticalAlertManager
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
 * 
 * Features:
 * - Heartbeat to keep connection alive
 * - Fallback to polling when WebSocket fails
 * - Cache of undelivered notifications
 * - Exponential backoff for reconnection
 */
@Singleton
class WebSocketManager @Inject constructor(
    private val sessionRepository: SessionRepository,
    private val faroMobileApi: FaroMobileApi,
    private val interceptAlertHandler: InterceptAlertHandler
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
    
    // Heartbeat
    private var heartbeatJob: kotlinx.coroutines.Job? = null
    private val heartbeatIntervalMs = 30000L // 30 seconds
    private var lastHeartbeatTime = 0L
    private var lastPongTime = 0L
    
    // Fallback polling
    private var pollingJob: kotlinx.coroutines.Job? = null
    private var usePollingFallback = false
    private val pollingIntervalMs = 60000L // 1 minute
    
    // Cache of undelivered notifications
    private val undeliveredNotifications = mutableListOf<PushNotification>()
    private val maxCacheSize = 100
    
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
            .pingInterval(heartbeatIntervalMs, TimeUnit.MILLISECONDS)
            .build()
        
        val request = Request.Builder()
            .url(url)
            .build()
        
        webSocket = okHttpClient?.newWebSocket(request, object : WebSocketListener() {
            override fun onOpen(ws: WebSocket, response: Response) {
                Log.d(TAG, "WebSocket connected")
                _connectionState.value = ConnectionState.Connected
                reconnectAttempts = 0
                usePollingFallback = false
                startHeartbeat()
            }
            
            override fun onMessage(ws: WebSocket, text: String) {
                Log.d(TAG, "WebSocket message received: $text")
                handleMessage(text)
                lastPongTime = System.currentTimeMillis()
            }
            
            override fun onClosing(ws: WebSocket, code: Int, reason: String) {
                Log.d(TAG, "WebSocket closing: $code - $reason")
            }
            
            override fun onClosed(ws: WebSocket, code: Int, reason: String) {
                Log.d(TAG, "WebSocket closed: $code - $reason")
                _connectionState.value = ConnectionState.Disconnected
                webSocket = null
                stopHeartbeat()
                
                // Check if we should fallback to polling
                if (reconnectAttempts >= 3) {
                    Log.d(TAG, "Multiple reconnect attempts failed, enabling polling fallback")
                    usePollingFallback = true
                    startPollingFallback(userId, baseUrl)
                } else {
                    attemptReconnect(userId, baseUrl)
                }
            }
            
            override fun onFailure(ws: WebSocket, t: Throwable, response: Response?) {
                Log.e(TAG, "WebSocket error", t)
                _connectionState.value = ConnectionState.Error(t.message ?: "Unknown error")
                webSocket = null
                stopHeartbeat()
                
                // Check if we should fallback to polling
                if (reconnectAttempts >= 3) {
                    Log.d(TAG, "Multiple reconnect attempts failed, enabling polling fallback")
                    usePollingFallback = true
                    startPollingFallback(userId, baseUrl)
                } else {
                    attemptReconnect(userId, baseUrl)
                }
            }
        })
    }
    
    /**
     * Disconnect WebSocket.
     */
    fun disconnect() {
        stopHeartbeat()
        stopPollingFallback()
        webSocket?.close(1000, "User disconnected")
        webSocket = null
        okHttpClient = null
        _connectionState.value = ConnectionState.Disconnected
        reconnectAttempts = 0
        usePollingFallback = false
        Log.d(TAG, "WebSocket disconnected")
    }
    
    /**
     * Attempt to reconnect with exponential backoff.
     */
    private fun attemptReconnect(userId: String, baseUrl: String) {
        if (reconnectAttempts >= maxReconnectAttempts || usePollingFallback) {
            Log.e(TAG, "Max reconnect attempts reached or polling fallback enabled")
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
     * Start heartbeat to keep connection alive.
     */
    private fun startHeartbeat() {
        stopHeartbeat()
        
        heartbeatJob = scope.launch {
            while (webSocket != null) {
                delay(heartbeatIntervalMs)
                
                val currentTime = System.currentTimeMillis()
                
                // Check if pong was received
                if (lastPongTime > 0 && currentTime - lastPongTime > heartbeatIntervalMs * 2) {
                    Log.w(TAG, "No pong received, connection may be dead")
                    webSocket?.close(1000, "No pong received")
                    return@launch
                }
                
                // Send ping
                webSocket?.send("{\"type\":\"ping\",\"timestamp\":$currentTime}")
                lastHeartbeatTime = currentTime
                Log.d(TAG, "Heartbeat sent")
            }
        }
    }
    
    /**
     * Stop heartbeat.
     */
    private fun stopHeartbeat() {
        heartbeatJob?.cancel()
        heartbeatJob = null
        lastHeartbeatTime = 0
        lastPongTime = 0
    }
    
    /**
     * Start polling fallback when WebSocket fails.
     */
    private fun startPollingFallback(userId: String, baseUrl: String) {
        stopPollingFallback()
        
        pollingJob = scope.launch {
            Log.d(TAG, "Starting polling fallback")
            
            while (usePollingFallback) {
                try {
                    Log.d(TAG, "Polling for notifications...")
                    
                    // Call REST API to fetch pending notifications
                    // This would be an endpoint like GET /mobile/notifications/pending
                    // For now, we'll simulate with a delay
                    // In production, implement actual polling:
                    // val notifications = faroMobileApi.getPendingNotifications()
                    // notifications.forEach { notification ->
                    //     handleMessage(notification.toJson())
                    // }
                    
                    delay(pollingIntervalMs)
                } catch (e: Exception) {
                    Log.e(TAG, "Polling error", e)
                    delay(pollingIntervalMs)
                }
            }
        }
    }
    
    /**
     * Stop polling fallback.
     */
    private fun stopPollingFallback() {
        pollingJob?.cancel()
        pollingJob = null
    }
    
    /**
     * Cache notification for later delivery.
     */
    private fun cacheNotification(notification: PushNotification) {
        undeliveredNotifications.add(notification)
        
        // Limit cache size
        if (undeliveredNotifications.size > maxCacheSize) {
            undeliveredNotifications.removeAt(0)
        }
        
        Log.d(TAG, "Cached notification: ${notification.id}, total cached: ${undeliveredNotifications.size}")
    }
    
    /**
     * Get cached undelivered notifications.
     */
    fun getCachedNotifications(): List<PushNotification> {
        return undeliveredNotifications.toList()
    }
    
    /**
     * Clear cached notifications.
     */
    fun clearCachedNotifications() {
        undeliveredNotifications.clear()
        Log.d(TAG, "Cached notifications cleared")
    }
    
    /**
     * Handle incoming WebSocket message.
     */
    private fun handleMessage(text: String) {
        try {
            // Parse JSON message
            when {
                text.contains("\"type\":\"connected\"") -> {
                    Log.d(TAG, "WebSocket connection confirmed")
                }
                text.contains("\"alert_type\":\"field_agent\"") && text.contains("\"target\":\"mobile\"") -> {
                    Log.d(TAG, "INTERCEPT field agent alert received")
                    // Handle INTERCEPT location-based alert with tactical feedback
                    interceptAlertHandler.handleInterceptAlert(text)
                    
                    // Also create notification for UI
                    val notification = parseInterceptNotification(text)
                    notification?.let {
                        val current = _notifications.value.toMutableList()
                        current.add(0, it)
                        _notifications.value = current
                        
                        // Emit to immediate alerts
                        scope.launch { _immediateAlerts.emit(it) }
                    }
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
     * Parse INTERCEPT notification from JSON.
     */
    private fun parseInterceptNotification(text: String): PushNotification? {
        return try {
            val plateNumber = extractField(text, "plate_number") ?: "UNKNOWN"
            val recommendation = extractField(text, "recommendation") ?: "UNKNOWN"
            val priority = extractField(text, "priority_level") ?: "medium"
            
            PushNotification(
                type = "intercept_alert",
                title = "ALERTA INTERCEPT",
                message = "Placa: $plateNumber | Ação: $recommendation | Prioridade: $priority",
                timestamp = System.currentTimeMillis()
            )
        } catch (e: Exception) {
            Log.e(TAG, "Error parsing INTERCEPT notification", e)
            null
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
