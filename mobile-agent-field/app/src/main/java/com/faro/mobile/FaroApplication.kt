package com.faro.mobile

import android.app.Application
import androidx.hilt.work.HiltWorkerFactory
import androidx.work.Configuration
import dagger.hilt.android.HiltAndroidApp
import timber.log.Timber
import javax.inject.Inject
import android.app.NotificationChannel
import android.app.NotificationManager
import android.os.Build
import androidx.core.app.NotificationManagerCompat

@HiltAndroidApp
class FaroApplication : Application(), Configuration.Provider {

    @Inject
    lateinit var workerFactory: HiltWorkerFactory

    override fun onCreate() {
        super.onCreate()
        
        // Initialize Timber for logging
        if (BuildConfig.DEBUG) {
            Timber.plant(Timber.DebugTree())
        }
        
        createNotificationChannels()
        Timber.d("F.A.R.O. Application initialized")
    }

    private fun createNotificationChannels() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            val monitoringChannel = NotificationChannel(
                MONITORING_CHANNEL_ID,
                "Monitoramento Tatico",
                NotificationManager.IMPORTANCE_LOW
            ).apply {
                description = "Notificacao persistente do rastro de geolocalizacao"
            }

            val criticalChannel = NotificationChannel(
                CRITICAL_ALERTS_CHANNEL_ID,
                "Alertas Criticos (INTERCEPT)",
                NotificationManager.IMPORTANCE_HIGH
            ).apply {
                description = "Alertas de alta prioridade e interceptacao criminal"
                enableVibration(true)
                vibrationPattern = longArrayOf(0, 500, 200, 500)
                setBypassDnd(true) // Attempt to bypass DND
            }

            val notificationManager = getSystemService(NotificationManager::class.java)
            notificationManager.createNotificationChannel(monitoringChannel)
            notificationManager.createNotificationChannel(criticalChannel)
            Timber.d("Notification channels created: Monitoring & Critical")
        }
    }

    companion object {
        const val MONITORING_CHANNEL_ID = "tactical_monitoring"
        const val CRITICAL_ALERTS_CHANNEL_ID = "critical_intercept_alerts"
    }

    override val workManagerConfiguration: Configuration
        get() = Configuration.Builder()
            .setWorkerFactory(workerFactory)
            .setMinimumLoggingLevel(android.util.Log.INFO)
            .build()
}
