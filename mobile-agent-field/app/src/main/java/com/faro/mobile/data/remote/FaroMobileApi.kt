package com.faro.mobile.data.remote

import okhttp3.MultipartBody
import okhttp3.RequestBody
import retrofit2.http.Body
import retrofit2.http.GET
import retrofit2.http.Multipart
import retrofit2.http.POST
import retrofit2.http.Part
import retrofit2.http.Path

interface FaroMobileApi {
    @POST("auth/login")
    suspend fun login(@Body request: LoginRequestDto): TokenResponseDto

    @POST("auth/refresh")
    suspend fun refresh(@Body request: RefreshTokenRequestDto): TokenResponseDto

    @POST("auth/logout")
    suspend fun logout(): BasicMessageResponseDto

    @POST("mobile/sync/batch")
    suspend fun syncBatch(@Body request: SyncBatchRequestDto): SyncBatchResponseDto

    @GET("mobile/plates/{plateNumber}/check-suspicion")
    suspend fun checkPlateSuspicion(
        @Path("plateNumber") plateNumber: String
    ): PlateSuspicionCheckResponseDto

    @POST("mobile/observations/{observationId}/approach-confirmation")
    suspend fun submitApproachConfirmation(
        @Path("observationId") observationId: String,
        @Body request: ApproachConfirmationRequestDto
    ): ApproachConfirmationResponseDto

    @POST("intelligence/feedback/{feedbackId}/read")
    suspend fun markFeedbackRead(
        @Path("feedbackId") feedbackId: String,
        @Body request: MarkFeedbackReadRequestDto
    ): BasicMessageResponseDto

    @Multipart
    @POST("mobile/observations/{observationId}/assets")
    suspend fun uploadObservationAsset(
        @Path("observationId") observationId: String,
        @Part("asset_type") assetType: RequestBody,
        @Part file: MultipartBody.Part
    ): UploadAssetResponseDto

    @Multipart
    @POST("mobile/observations/{observationId}/assets/progressive")
    suspend fun uploadObservationAssetProgressive(
        @Path("observationId") observationId: String,
        @Part("asset_type") assetType: RequestBody,
        @Part file: MultipartBody.Part,
        @Part("upload_id") uploadId: RequestBody?,
        @Part("chunk_index") chunkIndex: RequestBody,
        @Part("complete") complete: RequestBody,
        @Part("parts") parts: RequestBody?
    ): com.google.gson.JsonObject
}
