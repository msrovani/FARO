package com.faro.mobile.data.repository

import com.faro.mobile.data.local.dao.ObservationDao
import com.faro.mobile.data.local.dao.PlateReadDao
import com.faro.mobile.data.local.dao.SuspicionReportDao
import com.faro.mobile.data.local.entity.ObservationEntity
import com.faro.mobile.data.local.entity.PlateReadEntity
import com.faro.mobile.data.local.entity.SuspicionReportEntity
import com.faro.mobile.domain.model.GeoLocation
import com.faro.mobile.domain.model.InstantFeedback
import com.faro.mobile.domain.model.PlateRead
import com.faro.mobile.domain.model.SuspicionReport
import com.faro.mobile.domain.model.SyncStatus
import com.faro.mobile.domain.model.VehicleObservation
import com.faro.mobile.domain.repository.ObservationRepository
import com.google.gson.Gson
import com.google.gson.reflect.TypeToken
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.map
import java.time.Instant

private val gson = Gson()
private val metadataType = object : TypeToken<Map<String, String>>() {}.type

class ObservationRepositoryImpl(
    private val observationDao: ObservationDao,
    private val plateReadDao: PlateReadDao,
    private val suspicionReportDao: SuspicionReportDao
) : ObservationRepository {

    override suspend fun saveObservation(observation: VehicleObservation) {
        val entity = observation.toEntity()
        observationDao.insert(entity)

        // Save plate reads
        val plateReadEntities = observation.plateReads.map { it.toEntity(observation.id) }
        plateReadDao.insertAll(plateReadEntities)

        // Save suspicion report if exists
        observation.suspicionReport?.let { suspicion ->
            val suspicionEntity = suspicion.toEntity(observation.id)
            suspicionReportDao.insert(suspicionEntity)
        }
    }

    override suspend fun getObservationById(id: String): VehicleObservation? {
        val entity = observationDao.getById(id) ?: return null
        val plateReads = plateReadDao.getByObservationId(id).map { it.toDomain() }
        val suspicionReport = suspicionReportDao.getByObservationId(id)?.toDomain()

        return entity.toDomain(plateReads, suspicionReport)
    }

    override suspend fun getPendingSyncObservations(): List<VehicleObservation> {
        val entities = observationDao.getPendingSync()
        return entities.map { entity ->
            val plateReads = plateReadDao.getByObservationId(entity.id).map { it.toDomain() }
            val suspicionReport = suspicionReportDao.getByObservationId(entity.id)?.toDomain()
            entity.toDomain(plateReads, suspicionReport)
        }
    }

    override fun getObservationsByAgent(agentId: String): Flow<List<VehicleObservation>> {
        return observationDao.getByAgent(agentId).map { entities ->
            entities.map { entity ->
                val plateReads = plateReadDao.getByObservationId(entity.id).map { it.toDomain() }
                val suspicionReport = suspicionReportDao.getByObservationId(entity.id)?.toDomain()
                entity.toDomain(plateReads, suspicionReport)
            }
        }
    }

    override fun getRecentObservations(limit: Int): Flow<List<VehicleObservation>> {
        return observationDao.getRecent(limit).map { entities ->
            entities.map { entity ->
                val plateReads = plateReadDao.getByObservationId(entity.id).map { it.toDomain() }
                val suspicionReport = suspicionReportDao.getByObservationId(entity.id)?.toDomain()
                entity.toDomain(plateReads, suspicionReport)
            }
        }
    }

    override suspend fun updateSyncStatus(id: String, status: SyncStatus, error: String?) {
        val syncedAt = if (status == SyncStatus.COMPLETED) Instant.now() else null
        observationDao.updateSyncStatus(id, status.name, syncedAt, error)
    }
}

// Extension functions for mapping
private fun VehicleObservation.toEntity(): ObservationEntity {
    return ObservationEntity(
        id = id,
        clientId = clientId,
        plateNumber = plateNumber,
        plateState = plateState,
        plateCountry = plateCountry,
        observedAtLocal = observedAtLocal,
        observedAtServer = observedAtServer,
        latitude = location.latitude,
        longitude = location.longitude,
        locationAccuracy = location.accuracy,
        heading = heading,
        speed = speed,
        vehicleColor = vehicleColor,
        vehicleType = vehicleType,
        vehicleModel = vehicleModel,
        vehicleYear = vehicleYear,
        agentId = agentId,
        deviceId = deviceId,
        syncStatus = syncStatus.name,
        syncAttempts = syncAttempts,
        syncedAt = syncedAt,
        syncError = syncError,
        connectivityType = connectivityType,
        metadataSnapshot = metadataSnapshot?.let { gson.toJson(it) },
        createdAt = createdAt,
        updatedAt = updatedAt
    )
}

private fun PlateRead.toEntity(observationId: String): PlateReadEntity {
    return PlateReadEntity(
        id = id,
        observationId = observationId,
        ocrRawText = ocrRawText,
        ocrConfidence = ocrConfidence,
        ocrEngine = ocrEngine,
        imagePath = imagePath,
        processedAt = processedAt,
        processingTimeMs = processingTimeMs
    )
}

private fun SuspicionReport.toEntity(observationId: String): SuspicionReportEntity {
    return SuspicionReportEntity(
        id = id,
        observationId = observationId,
        reason = reason.name,
        level = level.name,
        urgency = urgency.name,
        notes = notes,
        imagePath = imagePath,
        audioPath = audioPath,
        audioDurationSeconds = audioDurationSeconds,
        createdAt = createdAt
    )
}

private fun ObservationEntity.toDomain(
    plateReads: List<PlateRead>,
    suspicionReport: SuspicionReport?
): VehicleObservation {
    return VehicleObservation(
        id = id,
        clientId = clientId,
        plateNumber = plateNumber,
        plateState = plateState,
        plateCountry = plateCountry,
        observedAtLocal = observedAtLocal,
        observedAtServer = observedAtServer,
        location = GeoLocation(latitude, longitude, locationAccuracy),
        heading = heading,
        speed = speed,
        vehicleColor = vehicleColor,
        vehicleType = vehicleType,
        vehicleModel = vehicleModel,
        vehicleYear = vehicleYear,
        agentId = agentId,
        deviceId = deviceId,
        syncStatus = SyncStatus.valueOf(syncStatus),
        syncAttempts = syncAttempts,
        syncedAt = syncedAt,
        syncError = syncError,
        connectivityType = connectivityType,
        metadataSnapshot = metadataSnapshot?.let {
            runCatching { gson.fromJson<Map<String, String>>(it, metadataType) }.getOrNull()
        },
        createdAt = createdAt,
        updatedAt = updatedAt,
        plateReads = plateReads,
        suspicionReport = suspicionReport,
        instantFeedback = metadataSnapshot?.let(::decodeInstantFeedback)
    )
}

private fun PlateReadEntity.toDomain(): PlateRead {
    return PlateRead(
        id = id,
        observationId = observationId,
        ocrRawText = ocrRawText,
        ocrConfidence = ocrConfidence,
        ocrEngine = ocrEngine,
        imagePath = imagePath,
        processedAt = processedAt,
        processingTimeMs = processingTimeMs
    )
}

private fun SuspicionReportEntity.toDomain(): SuspicionReport {
    return SuspicionReport(
        id = id,
        observationId = observationId,
        reason = com.faro.mobile.domain.model.SuspicionReason.valueOf(reason),
        level = com.faro.mobile.domain.model.SuspicionLevel.valueOf(level),
        urgency = com.faro.mobile.domain.model.UrgencyLevel.valueOf(urgency),
        notes = notes,
        imagePath = imagePath,
        audioPath = audioPath,
        audioDurationSeconds = audioDurationSeconds,
        createdAt = createdAt
    )
}

private fun decodeInstantFeedback(metadataJson: String): InstantFeedback? {
    val metadata = runCatching {
        Gson().fromJson<Map<String, String>>(metadataJson, object : TypeToken<Map<String, String>>() {}.type)
    }.getOrNull() ?: return null

    val hasAlert = metadata["has_alert"]?.toBooleanStrictOrNull() ?: false
    val hasSignal = hasAlert ||
        !metadata["alert_level"].isNullOrBlank() ||
        !metadata["alert_title"].isNullOrBlank() ||
        !metadata["alert_message"].isNullOrBlank() ||
        !metadata["guidance"].isNullOrBlank()
    if (!hasSignal) return null

    return InstantFeedback(
        hasAlert = hasAlert,
        alertLevel = metadata["alert_level"],
        alertTitle = metadata["alert_title"],
        alertMessage = metadata["alert_message"],
        previousObservationsCount = metadata["previous_observations_count"]?.toIntOrNull() ?: 0,
        isMonitored = metadata["is_monitored"]?.toBooleanStrictOrNull() ?: false,
        intelligenceInterest = metadata["intelligence_interest"]?.toBooleanStrictOrNull() ?: false,
        guidance = metadata["guidance"]
    )
}
