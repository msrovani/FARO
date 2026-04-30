package com.faro.mobile.domain.usecase

import com.faro.mobile.domain.model.VehicleObservation
import com.faro.mobile.domain.repository.ObservationRepository
import kotlinx.coroutines.flow.Flow

class GetRecentObservationsUseCase(
    private val observationRepository: ObservationRepository
) {
    operator fun invoke(limit: Int = 50): Flow<List<VehicleObservation>> {
        return observationRepository.getRecentObservations(limit)
    }
}