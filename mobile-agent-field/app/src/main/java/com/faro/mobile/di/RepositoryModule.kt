package com.faro.mobile.di

import com.faro.mobile.data.local.dao.ObservationDao
import com.faro.mobile.data.local.dao.PlateReadDao
import com.faro.mobile.data.local.dao.SuspicionReportDao
import com.faro.mobile.data.repository.ObservationRepositoryImpl
import com.faro.mobile.domain.repository.ObservationRepository
import dagger.Module
import dagger.Provides
import dagger.hilt.InstallIn
import dagger.hilt.components.SingletonComponent
import javax.inject.Singleton

@Module
@InstallIn(SingletonComponent::class)
object RepositoryModule {

    @Provides
    @Singleton
    fun provideObservationRepository(
        observationDao: ObservationDao,
        plateReadDao: PlateReadDao,
        suspicionReportDao: SuspicionReportDao
    ): ObservationRepository {
        return ObservationRepositoryImpl(
            observationDao,
            plateReadDao,
            suspicionReportDao
        )
    }
}