package com.faro.mobile.domain.repository

import com.faro.mobile.domain.model.SyncStatus
import com.faro.mobile.domain.model.VehicleObservation
import kotlinx.coroutines.flow.Flow

interface ObservationRepository {
    suspend fun saveObservation(observation: VehicleObservation)
    suspend fun getObservationById(id: String): VehicleObservation?
    suspend fun getPendingSyncObservations(): List<VehicleObservation>
    fun getObservationsByAgent(agentId: String): Flow<List<VehicleObservation>>
    fun getRecentObservations(limit: Int): Flow<List<VehicleObservation>>
    suspend fun updateSyncStatus(id: String, status: SyncStatus, error: String? = null)
}