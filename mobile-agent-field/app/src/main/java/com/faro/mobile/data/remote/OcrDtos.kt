package com.faro.mobile.data.remote

import com.google.gson.annotations.SerializedName

/**
 * OCR Validation Request DTO
 */
data class OcrValidationRequestDto(
    @SerializedName("image_base64")
    val imageBase64: String,
    
    @SerializedName("mobile_ocr_text")
    val mobileOcrText: String? = null,
    
    @SerializedName("mobile_ocr_confidence")
    val mobileOcrConfidence: Float? = null,
    
    @SerializedName("device_id")
    val deviceId: String? = null
)

/**
 * OCR Validation Response DTO
 */
data class OcrValidationResponseDto(
    @SerializedName("plate_number")
    val plateNumber: String?,
    
    @SerializedName("confidence")
    val confidence: Float,
    
    @SerializedName("is_valid")
    val isValid: Boolean,
    
    @SerializedName("plate_format")
    val plateFormat: String?,
    
    @SerializedName("ocr_engine")
    val ocrEngine: String,
    
    @SerializedName("processing_time_ms")
    val processingTimeMs: Int,
    
    @SerializedName("mobile_comparison")
    val mobileComparison: MobileComparisonDto? = null
)

/**
 * Mobile Comparison DTO
 */
data class MobileComparisonDto(
    @SerializedName("mobile_text")
    val mobileText: String?,
    
    @SerializedName("mobile_confidence")
    val mobileConfidence: Float?,
    
    @SerializedName("match")
    val match: Boolean,
    
    @SerializedName("use_server_result")
    val useServerResult: Boolean
)
