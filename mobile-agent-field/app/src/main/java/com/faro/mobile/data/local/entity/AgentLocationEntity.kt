package com.faro.mobile.data.local.entity

import androidx.room.Entity
import androidx.room.PrimaryKey
import com.faro.mobile.domain.model.SyncStatus

@Entity(tableName = "agent_locations")
data class AgentLocationEntity(
    @PrimaryKey(autoGenerate = true)
    val id: Long = 0,
    val latitude: Double,
    val longitude: Double,
    val accuracy: Double,
    val recordedAt: String,
    val connectivityStatus: String?,
    val batteryLevel: Float?,
    val syncStatus: SyncStatus = SyncStatus.PENDING
)
