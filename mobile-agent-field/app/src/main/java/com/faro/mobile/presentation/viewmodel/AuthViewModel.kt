package com.faro.mobile.presentation.viewmodel

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.faro.mobile.data.session.SessionRepository
import com.faro.mobile.data.session.SessionSnapshot
import dagger.hilt.android.lifecycle.HiltViewModel
import javax.inject.Inject
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.stateIn
import kotlinx.coroutines.launch
import kotlinx.coroutines.flow.SharingStarted

@HiltViewModel
class AuthViewModel @Inject constructor(
    private val sessionRepository: SessionRepository,
) : ViewModel() {
    val sessionState = sessionRepository.sessionFlow
        .stateIn(
            scope = viewModelScope,
            started = SharingStarted.WhileSubscribed(5_000),
            initialValue = SessionSnapshot.anonymous(),
        )
    val profilesState = sessionRepository.profilesFlow
        .stateIn(
            scope = viewModelScope,
            started = SharingStarted.WhileSubscribed(5_000),
            initialValue = emptyList(),
        )

    private val _uiState = MutableStateFlow(LoginUiState())
    val uiState: StateFlow<LoginUiState> = _uiState.asStateFlow()

    init {
        viewModelScope.launch {
            sessionRepository.refreshTokenIfNeeded()
        }
    }

    fun login(email: String, password: String, onSuccess: () -> Unit) {
        viewModelScope.launch {
            _uiState.value = _uiState.value.copy(isLoading = true, errorMessage = null)
            val result = sessionRepository.login(email, password)
            result
                .onSuccess {
                    _uiState.value = _uiState.value.copy(isLoading = false, errorMessage = null)
                    onSuccess()
                }
                .onFailure { error ->
                    _uiState.value = _uiState.value.copy(
                        isLoading = false,
                        errorMessage = error.message ?: "Falha no login. Verifique credenciais e conectividade.",
                    )
                }
        }
    }

    fun logout(onComplete: () -> Unit) {
        viewModelScope.launch {
            sessionRepository.logout()
            onComplete()
        }
    }

    fun switchProfile(userId: String, onSuccess: () -> Unit, onFailure: (String) -> Unit) {
        viewModelScope.launch {
            _uiState.value = _uiState.value.copy(isLoading = true, errorMessage = null)
            val switched = sessionRepository.switchProfile(userId)
            if (switched) {
                _uiState.value = _uiState.value.copy(isLoading = false, errorMessage = null)
                onSuccess()
            } else {
                _uiState.value = _uiState.value.copy(isLoading = false)
                onFailure("Nao foi possivel alternar para o perfil selecionado.")
            }
        }
    }
}

data class LoginUiState(
    val isLoading: Boolean = false,
    val errorMessage: String? = null,
)
