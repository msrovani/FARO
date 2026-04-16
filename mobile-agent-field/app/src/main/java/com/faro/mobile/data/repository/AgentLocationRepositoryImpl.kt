package com.faro.mobile.data.repository

import com.faro.mobile.data.local.dao.AgentLocationDao
import com.faro.mobile.data.local.entity.AgentLocationEntity
import com.faro.mobile.domain.model.SyncStatus
import com.faro.mobile.domain.repository.AgentLocationRepository
import kotlinx.coroutines.flow.Flow
import javax.inject.Inject

class AgentLocationRepositoryImpl @Inject constructor(
    private val dao: AgentLocationDao
) : AgentLocationRepository {

    override suspend fun saveLocation(location: AgentLocationEntity) {
        dao.insert(location)
    }

    override suspend fun getPendingLocations(): List<AgentLocationEntity> {
        return dao.getPendingLocations(SyncStatus.PENDING)
    }

    override suspend fun markAsSynced(location: AgentLocationEntity) {
        dao.updateSyncStatus(location.copy(syncStatus = SyncStatus.COMPLETED))
    }

    override suspend fun clearOldLogs() {
        dao.clearSyncedLocations()
    }

    override fun getPendingCountFlow(): Flow<Int> {
        return dao.getPendingCountFlow()
    }
}
