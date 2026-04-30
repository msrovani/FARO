package com.faro.mobile.presentation.viewmodel

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.faro.mobile.data.remote.PendingFeedbackDto
import com.faro.mobile.data.session.SessionRepository
import com.faro.mobile.domain.model.SyncStatus
import com.faro.mobile.domain.repository.ObservationRepository
import dagger.hilt.android.lifecycle.HiltViewModel
import java.time.ZoneId
import java.time.format.DateTimeFormatter
import javax.inject.Inject
import kotlinx.coroutines.flow.SharingStarted
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.combine
import kotlinx.coroutines.flow.map
import kotlinx.coroutines.flow.stateIn
import kotlinx.coroutines.launch

@HiltViewModel
class HistoryViewModel @Inject constructor(
    observationRepository: ObservationRepository,
    private val sessionRepository: SessionRepository,
) : ViewModel() {
    val uiState: StateFlow<HistoryUiState> = combine(
        observationRepository.getRecentObservations(limit = 50).map { observations ->
            observations.map { observation ->
                HistoryObservationItem(
                    id = observation.id,
                    plate = observation.plateNumber,
                    timestamp = DateTimeFormatter.ofPattern("dd/MM HH:mm")
                        .withZone(ZoneId.systemDefault())
                        .format(observation.observedAtLocal),
                    isSynced = observation.syncStatus == SyncStatus.COMPLETED,
                    hasSuspicion = observation.suspicionReport != null,
                )
            }
        },
        sessionRepository.pendingFeedbackFlow,
    ) { observations, feedback ->
        HistoryUiState(
            observations = observations,
            feedback = feedback,
        )
    }.stateIn(
        scope = viewModelScope,
        started = SharingStarted.WhileSubscribed(5_000),
        initialValue = HistoryUiState(),
    )

    fun markFeedbackRead(feedbackId: String) {
        viewModelScope.launch {
            sessionRepository.markFeedbackRead(feedbackId)
        }
    }
}

data class HistoryUiState(
    val observations: List<HistoryObservationItem> = emptyList(),
    val feedback: List<PendingFeedbackDto> = emptyList(),
)

data class HistoryObservationItem(
    val id: String,
    val plate: String,
    val timestamp: String,
    val isSynced: Boolean,
    val hasSuspicion: Boolean,
)
