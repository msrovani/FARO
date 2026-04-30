package com.faro.mobile.data.local.dao

import androidx.room.Dao
import androidx.room.Insert
import androidx.room.OnConflictStrategy
import androidx.room.Query
import com.faro.mobile.data.local.entity.SuspicionReportEntity

@Dao
interface SuspicionReportDao {
    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insert(suspicionReport: SuspicionReportEntity)

    @Query("SELECT * FROM suspicion_reports WHERE observationId = :observationId")
    suspend fun getByObservationId(observationId: String): SuspicionReportEntity?
}