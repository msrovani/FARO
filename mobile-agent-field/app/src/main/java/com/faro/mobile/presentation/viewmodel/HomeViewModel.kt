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
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import java.time.Duration
import java.time.Instant

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

    private val _showShiftRenewal = MutableStateFlow(false)
    val showShiftRenewal = _showShiftRenewal.asStateFlow()

    private val _minutesRemaining = MutableStateFlow<Long?>(null)
    val minutesRemaining = _minutesRemaining.asStateFlow()

    init {
        monitorShift()
    }

    private fun monitorShift() {
        viewModelScope.launch {
            while (true) {
                val session = sessionRepository.sessionFlow.first()
                val expiresAt = session.serviceExpiresAt?.let { Instant.parse(it) }
                
                if (expiresAt != null) {
                    val remaining = Duration.between(Instant.now(), expiresAt).toMinutes()
                    _minutesRemaining.value = remaining
                    
                    // Show renewal prompt if < 5 minutes remaining
                    if (remaining in 1..5) {
                        _showShiftRenewal.value = true
                    } else if (remaining <= 0) {
                        _showShiftRenewal.value = false
                        // Turn is over, we might want to set is_on_duty = false 
                        // but the server will handle it.
                    }
                }
                delay(60_000) // Check every minute
            }
        }
    }

    fun dismissRenewal() {
        _showShiftRenewal.value = false
    }

    fun renewShift(hours: Int) {
        viewModelScope.launch {
            val result = sessionRepository.renewShift(hours)
            if (result.isSuccess) {
                _showShiftRenewal.value = false
                // The monitorShift loop will naturally pick up the new expiry 
                // because it collects sessionFlow in each iteration.
            }
        }
    }
}
