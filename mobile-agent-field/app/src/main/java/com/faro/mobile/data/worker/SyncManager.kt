package com.faro.mobile.data.worker

import android.content.Context
import androidx.work.Constraints
import androidx.work.ExistingPeriodicWorkPolicy
import androidx.work.NetworkType
import androidx.work.PeriodicWorkRequestBuilder
import androidx.work.WorkManager
import androidx.work.OneTimeWorkRequestBuilder
import com.faro.mobile.utils.NetworkValidator
import com.faro.mobile.utils.NetworkSettings
import dagger.hilt.android.qualifiers.ApplicationContext
import timber.log.Timber
import java.util.concurrent.TimeUnit
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class SyncManager @Inject constructor(
    @ApplicationContext private val context: Context,
    private val networkValidator: NetworkValidator,
    private val networkSettings: NetworkSettings
) {
    private val workManager = WorkManager.getInstance(context)

    /**
     * Schedule periodic sync with network validation.
     * Blocks sync on untrusted networks (public WiFi).
     */
    fun schedulePeriodicSync() {
        // Check network trust before scheduling
        if (!isNetworkAllowedForSync()) {
            Timber.w("Sync blocked: untrusted network")
            return
        }

        val constraints = Constraints.Builder()
            .setRequiredNetworkType(NetworkType.CONNECTED)
            .build()

        val syncWork = PeriodicWorkRequestBuilder<SyncWorker>(
            repeatInterval = 15, // 15 minutes
            repeatIntervalTimeUnit = TimeUnit.MINUTES
        )
            .setConstraints(constraints)
            .build()

        workManager.enqueueUniquePeriodicWork(
            SyncWorker.WORK_NAME,
            ExistingPeriodicWorkPolicy.KEEP,
            syncWork
        )
        
        Timber.d("Periodic sync scheduled")
    }

    /**
     * Schedule immediate sync with network validation.
     */
    fun scheduleImmediateSync() {
        // Always allow manual sync if network is connected
        // But log warning for untrusted
        if (!networkValidator.isNetworkTrusted()) {
            Timber.w("Manual sync on untrusted network")
        }

        val constraints = Constraints.Builder()
            .setRequiredNetworkType(NetworkType.CONNECTED)
            .build()

        val syncWork = OneTimeWorkRequestBuilder<SyncWorker>()
            .setConstraints(constraints)
            .build()

        workManager.enqueue(syncWork)
    }

    /**
     * Check if network is allowed for automatic sync.
     * Based on NetworkValidator 4G-first policy and settings.
     */
    private fun isNetworkAllowedForSync(): Boolean {
        return when {
            // Always allow on cellular (4G)
            networkValidator.is4G() -> {
                Timber.d("Sync allowed: 4G connection")
                true
            }
            // Allow on institutional WiFi
            networkValidator.isInstitutionalWifi() -> {
                Timber.d("Sync allowed: institutional WiFi")
                true
            }
            // Check if sync on public WiFi is enabled
            networkSettings.isPublicWifiSyncEnabled() -> {
                Timber.w("Sync allowed but non-recommended: public WiFi")
                true
            }
            // Block on public WiFi
            else -> {
                Timber.w("Sync blocked: public WiFi")
                false
            }
        }
    }

    /**
     * Cancel all scheduled syncs.
     */
    fun cancelSync() {
        workManager.cancelUniqueWork(SyncWorker.WORK_NAME)
        Timber.d("Periodic sync cancelled")
    }

    /**
     * Schedule periodic location tracking with battery-aware constraints.
     * Optimizes battery usage by:
     * - Only running when battery is not low
     * - Preferring unmetered network (Wi-Fi)
     * - Using adaptive interval based on battery level
     */
    fun scheduleLocationTracking() {
        val constraints = Constraints.Builder()
            .setRequiresBatteryNotLow(true)  // Don't run when battery is dying
            .setRequiresStorageNotLow(true)  // Don't run when storage is low
            .setRequiredNetworkType(NetworkType.UNMETERED)  // Prefer Wi-Fi
            .build()

        // Adaptive interval based on battery level would be handled by the worker itself
        // Default to 15 minutes for periodic tracking
        val locationWork = PeriodicWorkRequestBuilder<LocationTrackingWorker>(
            repeatInterval = 15, // 15 minutes
            repeatIntervalTimeUnit = TimeUnit.MINUTES
        )
            .setConstraints(constraints)
            .build()

        workManager.enqueueUniquePeriodicWork(
            LocationTrackingWorker.WORK_NAME,
            ExistingPeriodicWorkPolicy.KEEP,
            locationWork
        )
        
        Timber.d("Location tracking scheduled with battery constraints")
    }

    /**
     * Cancel location tracking.
     */
    fun cancelLocationTracking() {
        workManager.cancelUniqueWork(LocationTrackingWorker.WORK_NAME)
        Timber.d("Location tracking cancelled")
    }
}