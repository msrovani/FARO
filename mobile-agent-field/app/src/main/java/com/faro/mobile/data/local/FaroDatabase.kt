package com.faro.mobile.data.local

import androidx.room.Database
import androidx.room.RoomDatabase
import androidx.room.TypeConverters
import com.faro.mobile.data.local.dao.ObservationDao
import com.faro.mobile.data.local.dao.PlateReadDao
import com.faro.mobile.data.local.dao.SuspicionReportDao
import com.faro.mobile.data.local.entity.ObservationEntity
import com.faro.mobile.data.local.entity.PlateReadEntity
import com.faro.mobile.data.local.entity.SuspicionReportEntity

@Database(
    entities = [
        ObservationEntity::class,
        PlateReadEntity::class,
        SuspicionReportEntity::class
    ],
    version = 1,
    exportSchema = false
)
@TypeConverters(Converters::class)
abstract class FaroDatabase : RoomDatabase() {
    abstract fun observationDao(): ObservationDao
    abstract fun plateReadDao(): PlateReadDao
    abstract fun suspicionReportDao(): SuspicionReportDao

    companion object {
        const val DATABASE_NAME = "faro_database"
    }
}