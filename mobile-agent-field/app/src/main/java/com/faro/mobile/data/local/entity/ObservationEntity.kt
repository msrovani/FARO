package com.faro.mobile.data.local.entity

import androidx.room.Entity
import androidx.room.PrimaryKey
import androidx.room.TypeConverters
import com.faro.mobile.data.local.Converters
import java.time.Instant

@Entity(tableName = "observations")
@TypeConverters(Converters::class)
data class ObservationEntity(
    @PrimaryKey val id: String,
    val clientId: String,
    val plateNumber: String,
    val plateState: String? = null,
    val plateCountry: String = "BR",

    val observedAtLocal: Instant,
    val observedAtServer: Instant? = null,

    val latitude: Double,
    val longitude: Double,
    val locationAccuracy: Float? = null,
    val heading: Float? = null,
    val speed: Float? = null,

    val vehicleColor: String? = null,
    val vehicleType: String? = null,
    val vehicleModel: String? = null,
    val vehicleYear: Int? = null,

    val agentId: String,
    val deviceId: String,

    val syncStatus: String = "PENDING",
    val syncAttempts: Int = 0,
    val syncedAt: Instant? = null,
    val syncError: String? = null,

    val connectivityType: String? = null,
    val metadataSnapshot: String? = null, // JSON string

    val createdAt: Instant = Instant.now(),
    val updatedAt: Instant = Instant.now()
)