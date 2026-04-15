package com.faro.mobile.data.local.entity

import androidx.room.Entity
import androidx.room.PrimaryKey
import androidx.room.TypeConverters
import com.faro.mobile.data.local.Converters
import java.time.Instant

@Entity(
    tableName = "plate_reads",
    primaryKeys = ["observationId", "id"]
)
@TypeConverters(Converters::class)
data class PlateReadEntity(
    val id: String,
    val observationId: String,
    val ocrRawText: String,
    val ocrConfidence: Float,
    val ocrEngine: String = "mlkit_v2",
    val imagePath: String? = null,
    val processedAt: Instant = Instant.now(),
    val processingTimeMs: Long? = null
)