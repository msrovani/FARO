package com.faro.mobile.di

import com.faro.mobile.domain.repository.ObservationRepository
import com.faro.mobile.domain.usecase.GetRecentObservationsUseCase
import com.faro.mobile.domain.usecase.SaveObservationUseCase
import dagger.Module
import dagger.Provides
import dagger.hilt.InstallIn
import dagger.hilt.components.SingletonComponent
import javax.inject.Singleton

@Module
@InstallIn(SingletonComponent::class)
object UseCaseModule {

    @Provides
    @Singleton
    fun provideSaveObservationUseCase(
        observationRepository: ObservationRepository
    ): SaveObservationUseCase {
        return SaveObservationUseCase(observationRepository)
    }

    @Provides
    @Singleton
    fun provideGetRecentObservationsUseCase(
        observationRepository: ObservationRepository
    ): GetRecentObservationsUseCase {
        return GetRecentObservationsUseCase(observationRepository)
    }
}