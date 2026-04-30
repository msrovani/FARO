package com.faro.mobile.di

import android.content.Context
import androidx.room.Room
import com.faro.mobile.data.local.FaroDatabase
import com.faro.mobile.data.local.dao.ObservationDao
import com.faro.mobile.data.local.dao.PlateReadDao
import com.faro.mobile.data.local.dao.SuspicionReportDao
import dagger.Module
import dagger.Provides
import dagger.hilt.InstallIn
import dagger.hilt.android.qualifiers.ApplicationContext
import dagger.hilt.components.SingletonComponent
import javax.inject.Singleton

@Module
@InstallIn(SingletonComponent::class)
object DatabaseModule {

    @Provides
    @Singleton
    fun provideDatabase(@ApplicationContext context: Context): FaroDatabase {
        return Room.databaseBuilder(
            context,
            FaroDatabase::class.java,
            FaroDatabase.DATABASE_NAME
        ).build()
    }

    @Provides
    @Singleton
    fun provideObservationDao(database: FaroDatabase): ObservationDao {
        return database.observationDao()
    }

    @Provides
    @Singleton
    fun providePlateReadDao(database: FaroDatabase): PlateReadDao {
        return database.plateReadDao()
    }

    @Provides
    @Singleton
    fun provideSuspicionReportDao(database: FaroDatabase): SuspicionReportDao {
        return database.suspicionReportDao()
    }
}