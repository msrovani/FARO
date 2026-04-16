package com.faro.mobile.data.local

import androidx.room.Database
import androidx.room.RoomDatabase
import androidx.room.TypeConverters
import com.faro.mobile.data.local.dao.ObservationDao
import com.faro.mobile.data.local.dao.PlateReadDao
import com.faro.mobile.data.local.dao.SuspicionReportDao
import com.faro.mobile.data.local.dao.AgentLocationDao
import com.faro.mobile.data.local.entity.ObservationEntity
import com.faro.mobile.data.local.entity.PlateReadEntity
import com.faro.mobile.data.local.entity.SuspicionReportEntity
import com.faro.mobile.data.local.entity.AgentLocationEntity

@Database(
    entities = [
        ObservationEntity::class,
        PlateReadEntity::class,
        SuspicionReportEntity::class,
        AgentLocationEntity::class
    ],
    version = 2,
    exportSchema = false
)
@TypeConverters(Converters::class)
abstract class FaroDatabase : RoomDatabase() {
    abstract fun observationDao(): ObservationDao
    abstract fun plateReadDao(): PlateReadDao
    abstract fun suspicionReportDao(): SuspicionReportDao
    abstract fun agentLocationDao(): AgentLocationDao

    companion object {
        const val DATABASE_NAME = "faro_database"
    }
}