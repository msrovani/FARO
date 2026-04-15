package com.faro.mobile.presentation.viewmodel

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.faro.mobile.data.session.SessionRepository
import com.faro.mobile.domain.repository.ObservationRepository
import dagger.hilt.android.lifecycle.HiltViewModel
import javax.inject.Inject
import kotlinx.coroutines.flow.SharingStarted
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.map
import kotlinx.coroutines.flow.stateIn

@HiltViewModel
class HomeViewModel @Inject constructor(
    observationRepository: ObservationRepository,
    sessionRepository: SessionRepository,
) : ViewModel() {
    val pendingSyncCount: StateFlow<Int> = observationRepository
        .getRecentObservations(limit = 100)
        .map { observations -> observations.count { it.syncStatus.name != "COMPLETED" } }
        .stateIn(
            scope = viewModelScope,
            started = SharingStarted.WhileSubscribed(5_000),
            initialValue = 0,
        )

    val unreadFeedbackCount: StateFlow<Int> = sessionRepository
        .unreadFeedbackCountFlow
        .stateIn(
            scope = viewModelScope,
            started = SharingStarted.WhileSubscribed(5_000),
            initialValue = 0,
        )
}
