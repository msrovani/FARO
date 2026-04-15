package com.faro.mobile.data.local.dao

import androidx.room.Dao
import androidx.room.Insert
import androidx.room.OnConflictStrategy
import androidx.room.Query
import androidx.room.Update
import com.faro.mobile.data.local.entity.ObservationEntity
import kotlinx.coroutines.flow.Flow

@Dao
interface ObservationDao {
    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insert(observation: ObservationEntity)

    @Update
    suspend fun update(observation: ObservationEntity)

    @Query("SELECT * FROM observations WHERE id = :id")
    suspend fun getById(id: String): ObservationEntity?

    @Query("SELECT * FROM observations WHERE syncStatus IN ('PENDING', 'FAILED') ORDER BY createdAt ASC")
    suspend fun getPendingSync(): List<ObservationEntity>

    @Query("SELECT * FROM observations WHERE agentId = :agentId ORDER BY createdAt DESC")
    fun getByAgent(agentId: String): Flow<List<ObservationEntity>>

    @Query("SELECT * FROM observations ORDER BY createdAt DESC LIMIT :limit")
    fun getRecent(limit: Int = 50): Flow<List<ObservationEntity>>

    @Query("UPDATE observations SET syncStatus = :status, syncAttempts = syncAttempts + 1, syncedAt = :syncedAt, syncError = :error WHERE id = :id")
    suspend fun updateSyncStatus(id: String, status: String, syncedAt: java.time.Instant?, error: String?)
}
