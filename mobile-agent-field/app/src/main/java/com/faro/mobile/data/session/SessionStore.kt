package com.faro.mobile.data.session

import android.content.Context
import androidx.datastore.preferences.core.Preferences
import androidx.datastore.preferences.core.edit
import androidx.datastore.preferences.core.emptyPreferences
import androidx.datastore.preferences.core.longPreferencesKey
import androidx.datastore.preferences.core.stringPreferencesKey
import androidx.datastore.preferences.preferencesDataStore
import com.faro.mobile.data.remote.PendingFeedbackDto
import com.google.gson.Gson
import com.google.gson.reflect.TypeToken
import dagger.hilt.android.qualifiers.ApplicationContext
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.catch
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.flow.map
import timber.log.Timber
import java.io.IOException
import javax.inject.Inject
import javax.inject.Singleton

private val Context.sessionDataStore by preferencesDataStore(name = "faro_session")

@Singleton
class SessionStore @Inject constructor(
    @ApplicationContext private val context: Context
) {
    private val gson = Gson()
    private val profilesType = object : TypeToken<Map<String, SessionSnapshot>>() {}.type
    private val feedbackInboxesType = object : TypeToken<Map<String, List<PendingFeedbackDto>>>() {}.type

    private val profilesJsonKey = stringPreferencesKey("profiles_json")
    private val activeProfileUserIdKey = stringPreferencesKey("active_profile_user_id")
    private val feedbackInboxesJsonKey = stringPreferencesKey("feedback_inboxes_json")
    private val schemaVersionKey = longPreferencesKey("session_schema_version")
    private val schemaVersion = 2L

    private val stateFlow: Flow<PersistedState> = context.sessionDataStore.data
        .catch { exception ->
            if (exception is IOException) {
                Timber.e(exception, "Erro lendo SessionStore; usando preferencias vazias")
                emit(emptyPreferences())
            } else {
                throw exception
            }
        }
        .map { preferences -> preferences.toState() }

    val sessionFlow: Flow<SessionSnapshot> = stateFlow
        .map { state ->
            val activeUserId = state.activeProfileUserId
            if (activeUserId.isNullOrBlank()) {
                SessionSnapshot.anonymous()
            } else {
                state.profiles[activeUserId] ?: SessionSnapshot.anonymous()
            }
        }

    val profilesFlow: Flow<List<SessionProfile>> = stateFlow
        .map { state ->
            state.profiles.values
                .map { snapshot ->
                    SessionProfile(
                        userId = snapshot.userId,
                        userName = snapshot.userName,
                        userEmail = snapshot.userEmail,
                        userRole = snapshot.userRole,
                        userUnitName = snapshot.userUnitName,
                        userAgencyName = snapshot.userAgencyName,
                        serviceExpiresAt = snapshot.serviceExpiresAt,
                    )
                }
                .sortedBy { it.userName.lowercase() }
        }

    val pendingFeedbackFlow: Flow<List<PendingFeedbackDto>> = stateFlow.map { state ->
        val activeUserId = state.activeProfileUserId
        if (activeUserId.isNullOrBlank()) {
            emptyList()
        } else {
            state.feedbackInboxes[activeUserId] ?: emptyList()
        }
    }

    suspend fun saveSession(session: SessionSnapshot) {
        context.sessionDataStore.edit { preferences ->
            val state = preferences.toState()
            val updatedProfiles = state.profiles.toMutableMap().apply {
                this[session.userId] = session
            }
            preferences[profilesJsonKey] = gson.toJson(updatedProfiles)
            preferences[activeProfileUserIdKey] = session.userId
            preferences[schemaVersionKey] = schemaVersion
        }
    }

    suspend fun clearSession() {
        context.sessionDataStore.edit { preferences ->
            val state = preferences.toState()
            val activeUserId = state.activeProfileUserId
            if (activeUserId.isNullOrBlank()) {
                preferences.remove(activeProfileUserIdKey)
                return@edit
            }

            val updatedProfiles = state.profiles.toMutableMap().apply { remove(activeUserId) }
            val updatedFeedbackInboxes = state.feedbackInboxes.toMutableMap().apply { remove(activeUserId) }
            val nextActiveUserId = updatedProfiles.keys.firstOrNull()

            if (updatedProfiles.isEmpty()) {
                preferences.remove(profilesJsonKey)
            } else {
                preferences[profilesJsonKey] = gson.toJson(updatedProfiles)
            }
            if (updatedFeedbackInboxes.isEmpty()) {
                preferences.remove(feedbackInboxesJsonKey)
            } else {
                preferences[feedbackInboxesJsonKey] = gson.toJson(updatedFeedbackInboxes)
            }
            if (nextActiveUserId.isNullOrBlank()) {
                preferences.remove(activeProfileUserIdKey)
            } else {
                preferences[activeProfileUserIdKey] = nextActiveUserId
            }
            preferences[schemaVersionKey] = schemaVersion
        }
    }

    suspend fun clearAllSessions() {
        context.sessionDataStore.edit { preferences ->
            preferences.remove(profilesJsonKey)
            preferences.remove(activeProfileUserIdKey)
            preferences.remove(feedbackInboxesJsonKey)
            preferences[schemaVersionKey] = schemaVersion
        }
    }

    suspend fun switchActiveProfile(userId: String): Boolean {
        val profiles = stateFlow.first().profiles
        if (!profiles.containsKey(userId)) return false
        context.sessionDataStore.edit { preferences ->
            preferences[activeProfileUserIdKey] = userId
            preferences[schemaVersionKey] = schemaVersion
        }
        return true
    }

    suspend fun getSessionSnapshot(): SessionSnapshot? {
        val snapshot = sessionFlow.first()
        return if (snapshot.isAuthenticated) snapshot else null
    }

    suspend fun getAccessToken(): String? = getSessionSnapshot()?.accessToken

    suspend fun getRefreshToken(): String? = getSessionSnapshot()?.refreshToken

    suspend fun savePendingFeedback(items: List<PendingFeedbackDto>) {
        if (items.isEmpty()) return
        val state = stateFlow.first()
        val activeUserId = state.activeProfileUserId ?: return
        val merged = mergeFeedback(existing = state.feedbackInboxes[activeUserId] ?: emptyList(), incoming = items)
        context.sessionDataStore.edit { preferences ->
            val updatedInboxes = preferences.toState().feedbackInboxes.toMutableMap().apply {
                this[activeUserId] = merged
            }
            preferences[feedbackInboxesJsonKey] = gson.toJson(updatedInboxes)
            preferences[schemaVersionKey] = schemaVersion
        }
    }

    suspend fun markFeedbackRead(feedbackId: String) {
        val state = stateFlow.first()
        val activeUserId = state.activeProfileUserId ?: return
        val current = state.feedbackInboxes[activeUserId] ?: emptyList()
        val updated = current.map { item ->
            if (item.feedbackId == feedbackId) {
                item.copy(isRead = true, readAt = java.time.Instant.now().toString())
            } else {
                item
            }
        }
        context.sessionDataStore.edit { preferences ->
            val updatedInboxes = preferences.toState().feedbackInboxes.toMutableMap().apply {
                this[activeUserId] = updated
            }
            preferences[feedbackInboxesJsonKey] = gson.toJson(updatedInboxes)
            preferences[schemaVersionKey] = schemaVersion
        }
    }

    private fun mergeFeedback(
        existing: List<PendingFeedbackDto>,
        incoming: List<PendingFeedbackDto>
    ): List<PendingFeedbackDto> {
        val byId = linkedMapOf<String, PendingFeedbackDto>()
        existing.forEach { byId[it.feedbackId] = it }
        incoming.forEach { incomingItem ->
            val current = byId[incomingItem.feedbackId]
            byId[incomingItem.feedbackId] = when {
                current == null -> incomingItem
                current.isRead -> incomingItem.copy(isRead = true, readAt = current.readAt ?: incomingItem.readAt)
                else -> incomingItem
            }
        }
        return byId.values.sortedByDescending { it.sentAt }
    }

    private fun Preferences.toState(): PersistedState {
        val profiles = this[profilesJsonKey]
            ?.let { raw ->
                runCatching { gson.fromJson<Map<String, SessionSnapshot>>(raw, profilesType) }
                    .getOrElse {
                        Timber.e(it, "Falha ao desserializar perfis de sessao")
                        emptyMap()
                    }
            }
            ?: emptyMap()
        val feedbackInboxes = this[feedbackInboxesJsonKey]
            ?.let { raw ->
                runCatching { gson.fromJson<Map<String, List<PendingFeedbackDto>>>(raw, feedbackInboxesType) }
                    .getOrElse {
                        Timber.e(it, "Falha ao desserializar inboxes de feedback")
                        emptyMap()
                    }
            }
            ?: emptyMap()
        return PersistedState(
            profiles = profiles,
            activeProfileUserId = this[activeProfileUserIdKey],
            feedbackInboxes = feedbackInboxes,
        )
    }
}

private data class PersistedState(
    val profiles: Map<String, SessionSnapshot>,
    val activeProfileUserId: String?,
    val feedbackInboxes: Map<String, List<PendingFeedbackDto>>,
)

data class SessionProfile(
    val userId: String,
    val userName: String,
    val userEmail: String,
    val userRole: String,
    val userUnitName: String? = null,
    val userAgencyName: String? = null,
    val serviceExpiresAt: String? = null,
)

data class SessionSnapshot(
    val accessToken: String,
    val refreshToken: String,
    val tokenType: String,
    val expiresAtEpochSeconds: Long,
    val userId: String,
    val userName: String,
    val userEmail: String,
    val userRole: String,
    val userUnitName: String? = null,
    val userAgencyId: String? = null,
    val userAgencyName: String? = null,
    val serviceExpiresAt: String? = null,
) {
    val isAuthenticated: Boolean
        get() = accessToken.isNotBlank() && refreshToken.isNotBlank()

    val isAccessTokenExpired: Boolean
        get() = java.time.Instant.now().epochSecond >= expiresAtEpochSeconds

    companion object {
        fun anonymous(): SessionSnapshot = SessionSnapshot(
            accessToken = "",
            refreshToken = "",
            tokenType = "bearer",
            expiresAtEpochSeconds = 0L,
            userId = "",
            userName = "",
            userEmail = "",
            userRole = "",
            userUnitName = null,
        )
    }
}
