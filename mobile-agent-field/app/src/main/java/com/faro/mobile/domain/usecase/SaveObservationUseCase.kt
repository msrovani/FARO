package com.faro.mobile.domain.usecase

import com.faro.mobile.domain.model.VehicleObservation
import com.faro.mobile.domain.repository.ObservationRepository

class SaveObservationUseCase(
    private val observationRepository: ObservationRepository
) {
    suspend operator fun invoke(observation: VehicleObservation) {
        observationRepository.saveObservation(observation)
    }
}