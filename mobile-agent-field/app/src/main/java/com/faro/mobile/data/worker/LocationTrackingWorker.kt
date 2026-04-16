package com.faro.mobile.data.worker

import android.annotation.SuppressLint
import android.content.Context
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

            // 2. Capture Location
            val location = fusedLocationClient.getCurrentLocation(
                Priority.PRIORITY_HIGH_ACCURACY,
                null
            ).await()

            if (location != null) {
                val entity = AgentLocationEntity(
                    latitude = location.latitude,
                    longitude = location.longitude,
                    accuracy = location.accuracy.toDouble(),
                    recordedAt = Instant.now().toString(),
                    connectivityStatus = secureSyncManager.getNetworkType().name,
                    batteryLevel = null // Could add battery manager check later
                )

                // 3. Save to local buffer (Offline Replay support)
                agentLocationRepository.saveLocation(entity)
                Timber.d("Location saved to local buffer: ${location.latitude}, ${location.longitude}")

                // 4. Try Real-time sync if online
                if (secureSyncManager.canSync().let { it is com.faro.mobile.utils.SyncCheckResult.ALLOWED }) {
                    try {
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

            // 5. Check for pending backlog (Offline Replay)
            syncPendingBacklog()

            Result.success()
        } catch (e: Exception) {
            Timber.e(e, "Location tracking worker error")
            Result.retry()
        }
    }

    private suspend fun syncPendingBacklog() {
        val pending = agentLocationRepository.getPendingLocations()
        if (pending.isNotEmpty() && secureSyncManager.canSync().let { it is com.faro.mobile.utils.SyncCheckResult.ALLOWED }) {
            try {
                val batch = AgentLocationBatchSyncDto(
                    deviceId = sessionRepository.getDeviceId() ?: "unknown",
                    items = pending.map { 
                        AgentLocationUpdateDto(
                            location = LocationDto(it.latitude, it.longitude, it.accuracy),
                            recordedAt = it.recordedAt,
                            connectivityStatus = it.connectivityStatus,
                            batteryLevel = it.batteryLevel
                        )
                    }
                )
                faroMobileApi.syncLocationHistory(batch)
                pending.forEach { agentLocationRepository.markAsSynced(it) }
                Timber.d("Synced backlog of ${pending.size} locations")
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
