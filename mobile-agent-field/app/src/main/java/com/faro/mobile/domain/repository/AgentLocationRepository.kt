package com.faro.mobile.domain.repository

import com.faro.mobile.data.local.entity.AgentLocationEntity
import com.faro.mobile.domain.model.SyncStatus
import kotlinx.coroutines.flow.Flow

interface AgentLocationRepository {
    suspend fun saveLocation(location: AgentLocationEntity)
    suspend fun getPendingLocations(): List<AgentLocationEntity>
    suspend fun markAsSynced(location: AgentLocationEntity)
    suspend fun clearOldLogs()
    fun getPendingCountFlow(): Flow<Int>
}
