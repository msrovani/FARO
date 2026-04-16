package com.faro.mobile.data.service

import android.app.Notification
import android.app.PendingIntent
import android.app.Service
import android.content.Intent
import android.os.IBinder
import androidx.core.app.NotificationCompat
import com.faro.mobile.FaroApplication
import com.faro.mobile.R
import com.faro.mobile.data.local.entity.AgentLocationEntity
import com.faro.mobile.data.remote.AgentLocationUpdateDto
import com.faro.mobile.data.remote.FaroMobileApi
import com.faro.mobile.data.remote.LocationDto
import com.faro.mobile.data.session.SessionRepository
import com.faro.mobile.data.websocket.WebSocketManager
import com.faro.mobile.domain.repository.AgentLocationRepository
import com.faro.mobile.presentation.MainActivity
import com.faro.mobile.utils.SecureSyncManager
import com.faro.mobile.utils.TacticalAlertManager
import com.google.android.gms.location.*
import dagger.hilt.android.AndroidEntryPoint
import kotlinx.coroutines.*
import kotlinx.coroutines.flow.launchIn
import kotlinx.coroutines.flow.onEach
import timber.log.Timber
import java.time.Instant
import javax.inject.Inject

@AndroidEntryPoint
class TacticalMonitoringService : Service() {

    @Inject lateinit var sessionRepository: SessionRepository
    @Inject lateinit var webSocketManager: WebSocketManager
    @Inject lateinit var faroMobileApi: FaroMobileApi
    @Inject lateinit var agentLocationRepository: AgentLocationRepository
    @Inject lateinit var alertManager: TacticalAlertManager

    private val serviceScope = CoroutineScope(SupervisorJob() + Dispatchers.IO)
    private var locationClient: FusedLocationProviderClient? = null
    private lateinit var secureSyncManager: SecureSyncManager

    private val locationCallback = object : LocationCallback() {
        override fun onLocationResult(result: LocationResult) {
            super.onLocationResult(result)
            result.lastLocation?.let { location ->
                handleLocationUpdate(location)
            }
        }
    }

    override fun onCreate() {
        super.onCreate()
        secureSyncManager = SecureSyncManager(this)
        locationClient = LocationServices.getFusedLocationProviderClient(this)
    }

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        if (intent?.action == ACTION_STOP_SERVICE) {
            stopSelf()
            return START_NOT_STICKY
        }

        startForeground(NOTIFICATION_ID, createMonitoringNotification())
        
        // Start persistent features
        startLocationUpdates()
        connectWebSocket()
        observeNotifications()

        return START_STICKY
    }

    private fun startLocationUpdates() {
        val request = LocationRequest.Builder(Priority.PRIORITY_HIGH_ACCURACY, 30000L) // 30s
            .setMinUpdateIntervalMillis(15000L)
            .build()

        try {
            locationClient?.requestLocationUpdates(request, locationCallback, mainLooper)
            Timber.i("Tactical location updates started (30s interval)")
        } catch (e: SecurityException) {
            Timber.e(e, "Missing location permissions for tactical service")
        }
    }

    private fun connectWebSocket() {
        serviceScope.launch {
            val session = sessionRepository.getSession()
            val userId = session?.userId ?: return@launch
            
            // Use the base URL from build config, converting http to ws
            val baseUrl = com.faro.mobile.BuildConfig.API_BASE_URL
            val wsUrl = baseUrl.replace("http://", "ws://").replace("https://", "wss://")
            
            webSocketManager.connect(userId, wsUrl)
        }
    }

    private fun observeNotifications() {
        webSocketManager.notifications
            .onEach { notifications ->
                notifications.filter { !it.read }.forEach { notification ->
                    showSystemNotification(notification)
                    webSocketManager.markAsRead(notification.id)
                }
            }
            .launchIn(serviceScope)
    }

    private fun handleLocationUpdate(location: android.location.Location) {
        serviceScope.launch {
            val entity = AgentLocationEntity(
                latitude = location.latitude,
                longitude = location.longitude,
                accuracy = location.accuracy.toDouble(),
                recordedAt = Instant.now().toString(),
                connectivityStatus = secureSyncManager.getNetworkType().name,
                batteryLevel = null
            )
            
            agentLocationRepository.saveLocation(entity)

            // Try real-time sync
            if (secureSyncManager.canSync().let { it is com.faro.mobile.utils.SyncCheckResult.ALLOWED }) {
                try {
                    faroMobileApi.updateCurrentLocation(
                        AgentLocationUpdateDto(
                            location = LocationDto(location.latitude, location.longitude, location.accuracy.toDouble()),
                            recordedAt = entity.recordedAt,
                            connectivityStatus = entity.connectivityStatus,
                            batteryLevel = null
                        )
                    )
                    agentLocationRepository.markAsSynced(entity)
                } catch (e: Exception) {
                    Timber.w("Failed to sync live location: ${e.message}")
                }
            }
        }
    }

    private fun showSystemNotification(push: WebSocketManager.PushNotification) {
        val isCritical = push.type == "criminal_alert" || push.message.contains("INTERCEPT", ignoreCase = true)
        if (isCritical) {
            alertManager.triggerPhysicalAlert(TacticalAlertManager.AlertLevel.CRITICAL)
        }
        val channelId = if (isCritical) {
            FaroApplication.CRITICAL_ALERTS_CHANNEL_ID
        } else {
            FaroApplication.MONITORING_CHANNEL_ID
        }

        val intent = Intent(this, MainActivity::class.java).apply {
            flags = Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TASK
        }
        val pendingIntent = PendingIntent.getActivity(this, 0, intent, PendingIntent.FLAG_IMMUTABLE)

        val notification = NotificationCompat.Builder(this, channelId)
            .setSmallIcon(R.drawable.ic_notification)
            .setContentTitle(push.title)
            .setContentText(push.message)
            .setPriority(if (isCritical) NotificationCompat.PRIORITY_MAX else NotificationCompat.PRIORITY_DEFAULT)
            .setCategory(if (isCritical) NotificationCompat.CATEGORY_ALARM else NotificationCompat.CATEGORY_MESSAGE)
            .setContentIntent(pendingIntent)
            .setAutoCancel(true)
            .setVisibility(NotificationCompat.VISIBILITY_PUBLIC)
            .apply {
                if (isCritical) {
                    setVibrate(longArrayOf(0, 500, 200, 500, 200, 500))
                    setFullScreenIntent(pendingIntent, true) // Show over lockscreen
                    // Sound is handled by channel
                }
            }
            .build()

        val notificationManager = getSystemService(NOTIFICATION_SERVICE) as android.app.NotificationManager
        notificationManager.notify(push.id.hashCode(), notification)
    }

    private fun createMonitoringNotification(): Notification {
        val stopIntent = Intent(this, TacticalMonitoringService::class.java).apply {
            action = ACTION_STOP_SERVICE
        }
        val stopPendingIntent = PendingIntent.getService(this, 0, stopIntent, PendingIntent.FLAG_IMMUTABLE)

        val intent = Intent(this, MainActivity::class.java)
        val pendingIntent = PendingIntent.getActivity(this, 0, intent, PendingIntent.FLAG_IMMUTABLE)

        return NotificationCompat.Builder(this, FaroApplication.MONITORING_CHANNEL_ID)
            .setContentTitle("F.A.R.O. - Em Servico")
            .setContentText("Monitoramento tatico ativo. Recebendo alertas em tempo real.")
            .setSmallIcon(R.drawable.ic_tactical_monitor)
            .setOngoing(true)
            .setContentIntent(pendingIntent)
            .addAction(0, "Sair de Servico", stopPendingIntent)
            .build()
    }

    override fun onDestroy() {
        super.onDestroy()
        locationClient?.removeLocationUpdates(locationCallback)
        webSocketManager.disconnect()
        serviceScope.cancel()
        Timber.i("Tactical monitoring service stopped")
    }

    override fun onBind(intent: Intent?): IBinder? = null

    companion object {
        const val NOTIFICATION_ID = 1001
        const val ACTION_STOP_SERVICE = "STOP_TACTICAL_MONITORING"
    }
}
