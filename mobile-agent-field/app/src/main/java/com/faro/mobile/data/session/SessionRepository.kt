package com.faro.mobile.data.session

import com.faro.mobile.BuildConfig
import com.faro.mobile.data.remote.FaroMobileApi
import com.faro.mobile.data.remote.LoginRequestDto
import com.faro.mobile.data.remote.MarkFeedbackReadRequestDto
import com.faro.mobile.data.remote.PendingFeedbackDto
import com.faro.mobile.data.remote.RefreshTokenRequestDto
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.map
import timber.log.Timber
import java.time.Instant
import java.time.temporal.ChronoUnit
import com.faro.mobile.data.remote.ShiftRenewalRequest
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class SessionRepository @Inject constructor(
    private val api: FaroMobileApi,
    private val store: SessionStore,
) {
    val sessionFlow: Flow<SessionSnapshot> = store.sessionFlow
    val profilesFlow: Flow<List<SessionProfile>> = store.profilesFlow

    val unreadFeedbackCountFlow: Flow<Int> = store.pendingFeedbackFlow
        .map { feedback -> feedback.count { !it.isRead } }

    val pendingFeedbackFlow: Flow<List<PendingFeedbackDto>> = store.pendingFeedbackFlow

    suspend fun login(email: String, password: String, shiftDurationHours: Int? = null): Result<SessionSnapshot> {
        return runCatching {
            val response = api.login(
                LoginRequestDto(
                    identifier = email.trim(),
                    password = password,
                    deviceId = android.os.Build.ID.takeIf { it.isNotBlank() } ?: "android-device",
                    deviceModel = "${android.os.Build.MANUFACTURER} ${android.os.Build.MODEL}",
                    osVersion = "Android ${android.os.Build.VERSION.RELEASE}",
                    appVersion = BuildConfig.VERSION_NAME,
                    shiftDurationHours = shiftDurationHours
                )
            )
            val session = SessionSnapshot(
                accessToken = response.accessToken,
                refreshToken = response.refreshToken,
                tokenType = response.tokenType,
                expiresAtEpochSeconds = Instant.now().epochSecond + response.expiresIn,
                userId = response.user.id,
                userName = response.user.fullName,
                userEmail = response.user.email,
                userRole = response.user.role,
                userUnitName = response.user.unitName,
                userAgencyId = response.user.agencyId,
                userAgencyName = response.user.agencyName,
                serviceExpiresAt = response.serviceExpiresAt
            )
            store.saveSession(session)
            session
        }
    }

    suspend fun refreshTokenIfNeeded(): Boolean {
        val current = store.getSessionSnapshot() ?: return false
        if (!current.isAccessTokenExpired) return true

        return runCatching {
            val response = api.refresh(RefreshTokenRequestDto(current.refreshToken))
            val updated = current.copy(
                accessToken = response.accessToken,
                refreshToken = response.refreshToken,
                tokenType = response.tokenType,
                expiresAtEpochSeconds = Instant.now().epochSecond + response.expiresIn,
            )
            store.saveSession(updated)
            true
        }.getOrElse { error ->
            Timber.e(error, "Falha ao renovar token")
            false
        }
    }

    suspend fun logout() {
        runCatching { api.logout() }
            .onFailure { Timber.w(it, "Logout remoto falhou; limpando sessao local") }
        store.clearSession()
    }

    suspend fun logoutAll() {
        runCatching { api.logout() }
            .onFailure { Timber.w(it, "Logout remoto falhou; limpando perfis locais") }
        store.clearAllSessions()
    }

    suspend fun switchProfile(userId: String): Boolean {
        val switched = store.switchActiveProfile(userId)
        if (!switched) return false
        return refreshTokenIfNeeded()
    }

    suspend fun savePendingFeedback(items: List<PendingFeedbackDto>) {
        store.savePendingFeedback(items)
    }

    suspend fun markFeedbackRead(feedbackId: String) {
        runCatching {
            api.markFeedbackRead(
                feedbackId = feedbackId,
                request = MarkFeedbackReadRequestDto(readAt = Instant.now().toString())
            )
        }.onFailure { Timber.w(it, "Falha ao marcar feedback no servidor; aplicando leitura local") }
        store.markFeedbackRead(feedbackId)
    }

    suspend fun renewShift(hours: Int): Result<Boolean> {
        return runCatching {
            val response = api.renewDutyShift(ShiftRenewalRequest(hours))
            val current = store.getSessionSnapshot()
            if (current != null) {
                // Approximate client-side update for immediate UI feedback
                val newExpiry = Instant.now().plus(hours.toLong(), ChronoUnit.HOURS).toString()
                store.saveSession(current.copy(serviceExpiresAt = newExpiry))
            }
            true
        }
    }
}
