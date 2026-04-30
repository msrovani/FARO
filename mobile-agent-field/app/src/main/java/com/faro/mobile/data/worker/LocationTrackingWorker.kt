package com.faro.mobile.data.worker

import android.annotation.SuppressLint
import android.content.Context
import android.os.BatteryManager
import androidx.hilt.work.HiltWorker
import androidx.work.CoroutineWorker
import androidx.work.WorkerParameters
import com.faro.mobile.data.local.entity.AgentLocationEntity
import com.faro.mobile.data.remote.AgentLocationBatchSyncDto
import com.faro.mobile.data.remote.AgentLocationUpdateDto
import com.faro.mobile.data.remote.FaroMobileApi
import com.faro.mobile.data.remote.LocationDto
import com.faro.mobile.data.session.SessionRepository
import com.faro.mobile.domain.repository.AgentLocationRepository
import com.faro.mobile.utils.SecureSyncManager
import com.google.android.gms.location.LocationServices
import com.google.android.gms.location.Priority
import dagger.assisted.Assisted
import dagger.assisted.AssistedInject
import kotlinx.coroutines.ensureActive
import timber.log.Timber
import java.time.Instant
import kotlinx.coroutines.tasks.await

@HiltWorker
class LocationTrackingWorker @AssistedInject constructor(
    @Assisted appContext: Context,
    @Assisted workerParams: WorkerParameters,
    private val agentLocationRepository: AgentLocationRepository,
    private val faroMobileApi: FaroMobileApi,
    private val sessionRepository: SessionRepository,
) : CoroutineWorker(appContext, workerParams) {

    private val fusedLocationClient = LocationServices.getFusedLocationProviderClient(appContext)
    private val secureSyncManager = SecureSyncManager(appContext)
    private val batteryManager = appContext.getSystemService(Context.BATTERY_SERVICE) as BatteryManager

    private fun getCurrentBatteryLevel(): Float {
        val batteryLevel = batteryManager.getIntProperty(BatteryManager.BATTERY_PROPERTY_CAPACITY)
        return batteryLevel.toFloat()
    }

    /**
     * Select location priority based on battery level to optimize battery usage.
     * - High accuracy (>50% battery): GPS + Wi-Fi + Cell + Sensors
     * - Balanced accuracy (20-50%): Wi-Fi + Cell (rarely GPS)
     * - Low power (<20%): Cell towers only
     */
    private fun getPriorityBasedOnBattery(): Priority {
        val batteryLevel = getCurrentBatteryLevel()
        return when {
            batteryLevel > 50 -> {
                Timber.d("Using HIGH_ACCURACY priority (battery: $batteryLevel%)")
                Priority.PRIORITY_HIGH_ACCURACY
            }
            batteryLevel > 20 -> {
                Timber.d("Using BALANCED_POWER_ACCURACY priority (battery: $batteryLevel%)")
                Priority.PRIORITY_BALANCED_POWER_ACCURACY
            }
            else -> {
                Timber.d("Using LOW_POWER priority (battery: $batteryLevel%)")
                Priority.PRIORITY_LOW_POWER
            }
        }
    }

    /**
     * Check if battery is too low for heavy operations.
     * Returns true if battery level is sufficient for location tracking.
     */
    private fun isBatterySufficientForTracking(): Boolean {
        val batteryLevel = getCurrentBatteryLevel()
        val isCharging = batteryManager.isCharging
        
        // Allow tracking if charging or battery > 15%
        val sufficient = isCharging || batteryLevel > 15
        
        if (!sufficient) {
            Timber.w("Battery too low for location tracking: $batteryLevel% (charging: $isCharging)")
        }
        
        return sufficient
    }

    @SuppressLint("MissingPermission")
    override suspend fun doWork(): Result {
        return try {
            Timber.d("Starting tactical location capture")

            // 1. Verify session and duty status
            val session = sessionRepository.getSession() ?: return Result.success() // No session, stop tracking
            
            // Check if shift is still valid
            val expiresAt = session.serviceExpiresAt?.let { Instant.parse(it) }
            if (expiresAt != null && Instant.now().isAfter(expiresAt)) {
                Timber.i("Shift expired. Stopping tracking.")
                // Here we could trigger a renewal notification
                return Result.success()
            }

            // 2. Check battery level before heavy operations
            if (!isBatterySufficientForTracking()) {
                Timber.i("Battery too low, skipping location capture")
                return Result.success()
            }

            // 3. Capture Location with battery-aware priority
            ensureActive() // Check for cancellation
            val location = fusedLocationClient.getCurrentLocation(
                getPriorityBasedOnBattery(),
                null
            ).await()

            if (location != null) {
                ensureActive() // Check for cancellation
                val entity = AgentLocationEntity(
                    latitude = location.latitude,
                    longitude = location.longitude,
                    accuracy = location.accuracy.toDouble(),
                    recordedAt = Instant.now().toString(),
                    connectivityStatus = secureSyncManager.getNetworkType().name,
                    batteryLevel = getCurrentBatteryLevel()
                )

                // 4. Save to local buffer (Offline Replay support)
                agentLocationRepository.saveLocation(entity)
                Timber.d("Location saved to local buffer: ${location.latitude}, ${location.longitude}")

                // 5. Try Real-time sync if online and battery is sufficient
                if (secureSyncManager.canSync().let { it is com.faro.mobile.utils.SyncCheckResult.ALLOWED }) {
                    try {
                        ensureActive() // Check for cancellation
                        faroMobileApi.updateCurrentLocation(
                            AgentLocationUpdateDto(
                                location = LocationDto(location.latitude, location.longitude, location.accuracy.toDouble()),
                                recordedAt = entity.recordedAt,
                                connectivityStatus = entity.connectivityStatus,
                                batteryLevel = entity.batteryLevel
                            )
                        )
                        agentLocationRepository.markAsSynced(entity)
                        Timber.d("Live location synced to server")
                    } catch (e: Exception) {
                        Timber.w("Failed to sync live location, will retry in batch: ${e.message}")
                    }
                }
            }

            // 6. Check for pending backlog (Offline Replay) - only if battery is sufficient
            if (isBatterySufficientForTracking()) {
                syncPendingBacklog()
            } else {
                Timber.d("Skipping backlog sync due to low battery")
            }

            Result.success()
        } catch (e: Exception) {
            Timber.e(e, "Location tracking worker error")
            Result.retry()
        }
    }

    private suspend fun syncPendingBacklog() {
        ensureActive() // Check for cancellation
        val pending = agentLocationRepository.getPendingLocations()
        if (pending.isNotEmpty() && secureSyncManager.canSync().let { it is com.faro.mobile.utils.SyncCheckResult.ALLOWED }) {
            try {
                // Limit batch size to reduce network load when battery is low
                val batteryLevel = getCurrentBatteryLevel()
                val batchSize = if (batteryLevel < 30) {
                    Timber.d("Limiting batch size due to low battery: $batteryLevel%")
                    minOf(pending.size, 10)
                } else {
                    pending.size
                }
                
                val batchToSync = pending.take(batchSize)
                
                ensureActive() // Check for cancellation
                val batch = AgentLocationBatchSyncDto(
                    deviceId = sessionRepository.getDeviceId() ?: "unknown",
                    items = batchToSync.map { 
                        AgentLocationUpdateDto(
                            location = LocationDto(it.latitude, it.longitude, it.accuracy),
                            recordedAt = it.recordedAt,
                            connectivityStatus = it.connectivityStatus,
                            batteryLevel = it.batteryLevel
                        )
                    }
                )
                faroMobileApi.syncLocationHistory(batch)
                batchToSync.forEach { agentLocationRepository.markAsSynced(it) }
                Timber.d("Synced backlog of ${batchToSync.size} locations (total pending: ${pending.size})")
                agentLocationRepository.clearOldLogs()
            } catch (e: Exception) {
                Timber.w("Failed to sync backlog: ${e.message}")
            }
        }
    }

    companion object {
        const val WORK_NAME = "tactical_location_tracking"
    }
}
