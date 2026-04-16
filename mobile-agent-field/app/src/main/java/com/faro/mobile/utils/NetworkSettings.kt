package com.faro.mobile.utils

import android.content.Context
import android.content.SharedPreferences
import com.google.gson.Gson
import com.google.gson.reflect.TypeToken

/**
 * Network settings for trusted SSIDs configuration.
 * Allows administrators to configure trusted WiFi networks.
 */
class NetworkSettings private constructor(context: Context) {
    
    private val prefs: SharedPreferences = context.getSharedPreferences(
        PREFS_NAME,
        Context.MODE_PRIVATE
    )
    
    companion object {
        private const val PREFS_NAME = "network_settings"
        private const val KEY_TRUSTED_SSIDS = "trusted_ssids"
        private const val KEY_SYNC_TTL_DAYS = "sync_ttl_days"
        private const val KEY_HEAVY_DATA_THRESHOLD_MB = "heavy_data_threshold_mb"
        
        @Volatile
        private var instance: NetworkSettings? = null
        
        fun getInstance(context: Context): NetworkSettings {
            return instance ?: synchronized(this) {
                instance ?: NetworkSettings(context.applicationContext).also { instance = it }
            }
        }
    }
    
    /**
     * Get list of trusted SSIDs.
     */
    fun getTrustedSsids(): List<String> {
        val json = prefs.getString(KEY_TRUSTED_SSIDS, null) ?: return getDefaultTrustedSsids()
        return try {
            val type = object : TypeToken<List<String>>() {}.type
            Gson().fromJson(json, type) ?: getDefaultTrustedSsids()
        } catch (e: Exception) {
            getDefaultTrustedSsids()
        }
    }
    
    /**
     * Set list of trusted SSIDs.
     */
    fun setTrustedSsids(ssids: List<String>) {
        val json = Gson().toJson(ssids)
        prefs.edit().putString(KEY_TRUSTED_SSIDS, json).apply()
    }
    
    /**
     * Add a trusted SSID.
     */
    fun addTrustedSsid(ssid: String) {
        val current = getTrustedSsids().toMutableList()
        if (ssid !in current) {
            current.add(ssid)
            setTrustedSsids(current)
        }
    }
    
    /**
     * Remove a trusted SSID.
     */
    fun removeTrustedSsid(ssid: String) {
        val current = getTrustedSsids().toMutableList()
        current.remove(ssid)
        setTrustedSsids(current)
    }
    
    /**
     * Get sync TTL in days.
     */
    fun getSyncTtlDays(): Long {
        return prefs.getLong(KEY_SYNC_TTL_DAYS, 7L)
    }
    
    /**
     * Set sync TTL in days.
     */
    fun setSyncTtlDays(days: Long) {
        prefs.edit().putLong(KEY_SYNC_TTL_DAYS, days).apply()
    }
    
    /**
     * Get heavy data threshold in MB.
     */
    fun getHeavyDataThresholdMb(): Long {
        return prefs.getLong(KEY_HEAVY_DATA_THRESHOLD_MB, 10L)
    }
    
    /**
     * Set heavy data threshold in MB.
     */
    fun setHeavyDataThresholdMb(thresholdMb: Long) {
        prefs.edit().putLong(KEY_HEAVY_DATA_THRESHOLD_MB, thresholdMb).apply()
    }
    
    /**
     * Reset all settings to defaults.
     */
    fun resetToDefaults() {
        prefs.edit().clear().apply()
    }
    
    /**
     * Get default trusted SSIDs.
     */
    private fun getDefaultTrustedSsids(): List<String> {
        return listOf("BMRS", "GOV", "POLICIA")
    }
}
