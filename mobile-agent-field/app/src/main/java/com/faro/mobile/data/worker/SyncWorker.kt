package com.faro.mobile.data.worker

import com.faro.mobile.BuildConfig
import android.content.Context
import androidx.hilt.work.HiltWorker
import androidx.work.CoroutineWorker
import androidx.work.WorkerParameters
import com.faro.mobile.data.remote.FaroMobileApi
import com.faro.mobile.data.remote.SyncBatchRequestDto
import com.faro.mobile.data.remote.SyncItemDto
import com.faro.mobile.data.session.SessionRepository
import com.faro.mobile.domain.model.VehicleObservation
import com.faro.mobile.domain.model.SyncStatus
import com.faro.mobile.domain.repository.ObservationRepository
import dagger.assisted.Assisted
import dagger.assisted.AssistedInject
import okhttp3.MediaType.Companion.toMediaTypeOrNull
import okhttp3.MultipartBody
import okhttp3.RequestBody.Companion.asRequestBody
import okhttp3.RequestBody.Companion.toRequestBody
import timber.log.Timber
import java.io.File
import java.security.MessageDigest
import java.time.Instant
import java.util.Locale

@HiltWorker
class SyncWorker @AssistedInject constructor(
    @Assisted appContext: Context,
    @Assisted workerParams: WorkerParameters,
    private val observationRepository: ObservationRepository,
    private val faroMobileApi: FaroMobileApi,
    private val sessionRepository: SessionRepository,
) : CoroutineWorker(appContext, workerParams) {

    override suspend fun doWork(): Result {
        return try {
            Timber.d("Starting observation sync")
            sessionRepository.refreshTokenIfNeeded()

            val pendingObservations = observationRepository.getPendingSyncObservations()

            if (pendingObservations.isEmpty()) {
                Timber.d("No pending observations to sync")
                return Result.success()
            }

            Timber.d("Syncing ${pendingObservations.size} observations")

            val request = SyncBatchRequestDto(
                deviceId = pendingObservations.firstOrNull()?.deviceId ?: "unknown_device",
                appVersion = BuildConfig.VERSION_NAME,
                items = pendingObservations.map { observation ->
                    val payload = observation.toSyncPayload()
                    SyncItemDto(
                        entityType = "observation",
                        entityLocalId = observation.id,
                        operation = "create",
                        payload = payload,
                        payloadHash = payload.toStableHash(),
                        createdAtLocal = observation.observedAtLocal.toString()
                    )
                },
                clientTimestamp = Instant.now().toString()
            )

            val response = faroMobileApi.syncBatch(request)
            val resultsByLocalId = response.results.associateBy { it.entityLocalId }

            pendingObservations.forEach { observation ->
                val result = resultsByLocalId[observation.id]
                if (result != null && result.status.equals("completed", ignoreCase = true)) {
                    observationRepository.updateSyncStatus(
                        id = observation.id,
                        status = SyncStatus.COMPLETED
                    )
                    result.entityServerId?.let { serverId ->
                        uploadObservationAssetsIfAny(observation, serverId)
                    }
                } else {
                    observationRepository.updateSyncStatus(
                        id = observation.id,
                        status = SyncStatus.FAILED,
                        error = result?.error ?: "item nao confirmado no lote de sync"
                    )
                }
            }

            if (response.pendingFeedback.isNotEmpty()) {
                Timber.d("Sync returned ${response.pendingFeedback.size} pending feedback item(s)")
                sessionRepository.savePendingFeedback(response.pendingFeedback)
            }

            Timber.d("Sync completed successfully")
            if (response.failedCount > 0) Result.retry() else Result.success()

        } catch (e: Exception) {
            Timber.e(e, "Sync failed")
            Result.retry()
        }
    }

    private suspend fun uploadObservationAssetsIfAny(
        observation: VehicleObservation,
        serverObservationId: String,
    ) {
        val plateImagePath = observation.plateReads.firstOrNull()?.imagePath
        val suspicionImagePath = observation.suspicionReport?.imagePath
        val suspicionAudioPath = observation.suspicionReport?.audioPath

        val candidates = listOfNotNull(
            plateImagePath?.let { AssetCandidate(it, "image") },
            suspicionImagePath?.let { AssetCandidate(it, "image") },
            suspicionAudioPath?.let { AssetCandidate(it, "audio") },
        )

        for (candidate in candidates) {
            val file = File(candidate.path)
            if (!file.exists() || !file.isFile) {
                Timber.w("Asset path not found for sync upload: ${candidate.path}")
                continue
            }

            runCatching {
                val guessedMime = guessMimeType(file)
                val requestBody = file.asRequestBody(guessedMime.toMediaTypeOrNull())
                val part = MultipartBody.Part.createFormData("file", file.name, requestBody)
                val typeBody = candidate.assetType.toRequestBody("text/plain".toMediaTypeOrNull())
                faroMobileApi.uploadObservationAsset(
                    observationId = serverObservationId,
                    assetType = typeBody,
                    file = part
                )
            }.onSuccess { response ->
                Timber.d(
                    "Uploaded %s asset for observation %s -> %s/%s",
                    candidate.assetType,
                    serverObservationId,
                    response.storageBucket,
                    response.storageKey
                )
            }.onFailure { error ->
                Timber.w(
                    error,
                    "Failed to upload %s asset for observation %s",
                    candidate.assetType,
                    serverObservationId
                )
            }
        }
    }

    companion object {
        const val WORK_NAME = "observation_sync"
    }
}

private fun VehicleObservation.toSyncPayload(): Map<String, Any?> {
    val payload = mutableMapOf<String, Any?>(
        "client_id" to clientId,
        "plate_number" to plateNumber,
        "plate_state" to plateState,
        "plate_country" to plateCountry,
        "observed_at_local" to observedAtLocal.toString(),
        "location" to mapOf(
            "latitude" to location.latitude,
            "longitude" to location.longitude,
            "accuracy" to location.accuracy,
        ),
        "heading" to heading,
        "speed" to speed,
        "vehicle_color" to vehicleColor,
        "vehicle_type" to vehicleType,
        "vehicle_model" to vehicleModel,
        "vehicle_year" to vehicleYear,
        "device_id" to deviceId,
        "connectivity_type" to connectivityType,
        "app_version" to BuildConfig.VERSION_NAME,
    )

    val read = plateReads.firstOrNull()
    if (read != null) {
        payload["plate_read"] = mapOf(
            "ocr_raw_text" to read.ocrRawText,
            "ocr_confidence" to read.ocrConfidence.toDouble(),
            "ocr_engine" to read.ocrEngine,
            "image_width" to null,
            "image_height" to null,
            "processing_time_ms" to read.processingTimeMs?.toInt(),
        )
    }

    return payload
}

private fun Map<String, Any?>.toStableHash(): String {
    val normalized = canonicalizeAny(this)
    val digest = MessageDigest.getInstance("SHA-256").digest(normalized.toByteArray())
    return digest.joinToString(separator = "") { byte -> "%02x".format(byte) }
}

private fun canonicalizeAny(value: Any?): String {
    return when (value) {
        null -> "null"
        is Map<*, *> -> value.entries
            .sortedBy { it.key?.toString() ?: "" }
            .joinToString(prefix = "{", postfix = "}") { (key, nested) ->
                "\"${key?.toString() ?: ""}\":${canonicalizeAny(nested)}"
            }
        is List<*> -> value.joinToString(prefix = "[", postfix = "]") { canonicalizeAny(it) }
        is String -> "\"$value\""
        is Number, is Boolean -> value.toString()
        else -> "\"${value.toString()}\""
    }
}

private data class AssetCandidate(
    val path: String,
    val assetType: String,
)

private fun guessMimeType(file: File): String {
    val extension = file.extension.lowercase(Locale.ROOT)
    return when (extension) {
        "jpg", "jpeg" -> "image/jpeg"
        "png" -> "image/png"
        "webp" -> "image/webp"
        "heic" -> "image/heic"
        "aac" -> "audio/aac"
        "m4a" -> "audio/mp4"
        "wav" -> "audio/wav"
        "ogg", "opus" -> "audio/ogg"
        "mp3" -> "audio/mpeg"
        else -> "application/octet-stream"
    }
}
