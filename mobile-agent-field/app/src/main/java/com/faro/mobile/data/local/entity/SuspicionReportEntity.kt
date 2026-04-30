package com.faro.mobile.data.local.entity

import androidx.room.Entity
import androidx.room.PrimaryKey
import androidx.room.TypeConverters
import com.faro.mobile.data.local.Converters
import java.time.Instant

@Entity(tableName = "suspicion_reports")
@TypeConverters(Converters::class)
data class SuspicionReportEntity(
    @PrimaryKey val id: String,
    val observationId: String,
    val reason: String, // SuspicionReason enum name
    val level: String, // SuspicionLevel enum name
    val urgency: String, // UrgencyLevel enum name
    val notes: String? = null,
    val imagePath: String? = null,
    val audioPath: String? = null,
    val audioDurationSeconds: Int? = null,
    val createdAt: Instant = Instant.now()
)