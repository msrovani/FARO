package com.faro.mobile.data.remote

import com.google.gson.annotations.SerializedName

data class LoginRequestDto(
    // Can be CPF (11 digits) or email
    val identifier: String,
    val password: String,
    @SerializedName("device_id")
    val deviceId: String? = null,
    @SerializedName("device_model")
    val deviceModel: String? = null,
    @SerializedName("os_version")
    val osVersion: String? = null,
    @SerializedName("app_version")
    val appVersion: String? = null,
)

data class RefreshTokenRequestDto(
    @SerializedName("refresh_token")
    val refreshToken: String,
)

data class TokenResponseDto(
    @SerializedName("access_token")
    val accessToken: String,
    @SerializedName("refresh_token")
    val refreshToken: String,
    @SerializedName("token_type")
    val tokenType: String,
    @SerializedName("expires_in")
    val expiresIn: Long,
    val user: AuthUserDto,
)

data class AuthUserDto(
    val id: String,
    val email: String,
    @SerializedName("full_name")
    val fullName: String,
    val role: String,
    @SerializedName("agency_id")
    val agencyId: String? = null,
    @SerializedName("agency_name")
    val agencyName: String? = null,
    @SerializedName("unit_id")
    val unitId: String? = null,
    @SerializedName("unit_name")
    val unitName: String? = null,
)

data class BasicMessageResponseDto(
    val message: String
)
