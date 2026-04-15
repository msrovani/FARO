package com.faro.mobile.data.local.dao

import androidx.room.Dao
import androidx.room.Insert
import androidx.room.OnConflictStrategy
import androidx.room.Query
import com.faro.mobile.data.local.entity.PlateReadEntity

@Dao
interface PlateReadDao {
    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insert(plateRead: PlateReadEntity)

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertAll(plateReads: List<PlateReadEntity>)

    @Query("SELECT * FROM plate_reads WHERE observationId = :observationId ORDER BY processedAt DESC")
    suspend fun getByObservationId(observationId: String): List<PlateReadEntity>
}