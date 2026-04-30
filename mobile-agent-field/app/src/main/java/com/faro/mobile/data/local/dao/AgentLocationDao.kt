package com.faro.mobile.data.local.dao

import androidx.room.*
import com.faro.mobile.data.local.entity.AgentLocationEntity
import com.faro.mobile.domain.model.SyncStatus
import kotlinx.coroutines.flow.Flow

@Dao
interface AgentLocationDao {
    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insert(location: AgentLocationEntity)

    @Query("SELECT * FROM agent_locations WHERE syncStatus = :status ORDER BY recordedAt ASC")
    suspend fun getPendingLocations(status: SyncStatus = SyncStatus.PENDING): List<AgentLocationEntity>

    @Update
    suspend fun updateSyncStatus(location: AgentLocationEntity)

    @Query("DELETE FROM agent_locations WHERE syncStatus = 'COMPLETED'")
    suspend fun clearSyncedLocations()
    
    @Query("SELECT COUNT(*) FROM agent_locations WHERE syncStatus = 'PENDING'")
    fun getPendingCountFlow(): Flow<Int>
}
