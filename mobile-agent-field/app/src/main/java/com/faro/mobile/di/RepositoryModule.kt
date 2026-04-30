package com.faro.mobile.di

import com.faro.mobile.data.local.dao.AgentLocationDao
import com.faro.mobile.data.repository.ObservationRepositoryImpl
import com.faro.mobile.data.repository.AgentLocationRepositoryImpl
import com.faro.mobile.domain.repository.ObservationRepository
import com.faro.mobile.domain.repository.AgentLocationRepository
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

    @Provides
    @Singleton
    fun provideAgentLocationRepository(
        agentLocationDao: AgentLocationDao
    ): AgentLocationRepository {
        return AgentLocationRepositoryImpl(agentLocationDao)
    }
}