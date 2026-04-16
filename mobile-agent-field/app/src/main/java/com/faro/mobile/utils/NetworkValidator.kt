package com.faro.mobile.utils

import android.content.Context
import android.net.ConnectivityManager
import android.net.NetworkCapabilities
import android.os.Build
import android.net.wifi.WifiManager
import java.util.concurrent.TimeUnit

/**
 * Network validation for secure data transmission.
 * Implements network validation and 4G-first policy for sensitive data.
 */
class NetworkValidator(private val context: Context) {
    
    private val wifiManager: WifiManager by lazy {
        context.applicationContext.getSystemService(Context.WIFI_SERVICE) as WifiManager
    }
    
    private val connectivityManager: ConnectivityManager by lazy {
        context.getSystemService(Context.CONNECTIVITY_SERVICE) as ConnectivityManager
    }
    
    /**
     * Check if current network is trusted.
     * Trusted networks: 4G, institutional WiFi
     */
    fun isNetworkTrusted(): Boolean {
        return when {
            is4G() -> true
            isInstitutionalWifi() -> true
            else -> false
        }
    }
    
    /**
     * Check if sync should be blocked based on network.
     */
    fun shouldBlockSync(): Boolean {
        return !isNetworkTrusted()
    }
    
    /**
     * Check if network is suitable for heavy data transfer (images, large files).
     * Only allowed on institutional WiFi or 4G.
     */
    fun canTransferHeavyData(): Boolean {
        return when {
            is4G() -> true
            isInstitutionalWifi() -> true
            else -> false
        }
    }
    
    /**
     * Check if current connection is 4G/cellular.
     */
    fun is4G(): Boolean {
        val network = connectivityManager.activeNetwork ?: return false
        val capabilities = connectivityManager.getNetworkCapabilities(network) ?: return false
        
        return capabilities.hasTransport(NetworkCapabilities.TRANSPORT_CELLULAR)
    }
    
    /**
     * Check if current connection is WiFi.
     */
    fun isWifi(): Boolean {
        val network = connectivityManager.activeNetwork ?: return false
        val capabilities = connectivityManager.getNetworkCapabilities(network) ?: return false
        
        return capabilities.hasTransport(NetworkCapabilities.TRANSPORT_WIFI)
    }
    
    /**
     * Check if current WiFi is institutional/trusted.
     * Trusted SSIDs: BMRS, GOV, POLICIA, or configured in app settings.
     */
    fun isInstitutionalWifi(): Boolean {
        if (!isWifi()) return false
        
        val ssid = getWifiSsid()
        if (ssid == null) return false
        
        val trustedSsids = getTrustedSsids()
        return trustedSsids.any { ssid.contains(it, ignoreCase = true) }
    }
    
    /**
     * Get current WiFi SSID.
     */
    private fun getWifiSsid(): String? {
        return if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.R) {
            wifiManager.currentConnection?.ssid?.removeSurrounding("\"")
        } else {
            @Suppress("DEPRECATION")
            wifiManager.connectionInfo?.ssid?.removeSurrounding("\"")
        }
    }
    
    /**
     * Get list of trusted SSIDs from app settings.
     * Can be configured by administrators.
     */
    private fun getTrustedSsids(): List<String> {
        return NetworkSettings.getInstance(context).getTrustedSsids()
    }
    
    /**
     * Get network type for logging/debugging.
     */
    fun getNetworkType(): NetworkType {
        return when {
            is4G() -> NetworkType.CELLULAR
            isInstitutionalWifi() -> NetworkType.INSTITUTIONAL_WIFI
            isWifi() -> NetworkType.PUBLIC_WIFI
            else -> NetworkType.UNKNOWN
        }
    }
    
    /**
     * Get network quality score (0-100).
     * Higher score = better connection.
     */
    fun getNetworkQuality(): Int {
        val network = connectivityManager.activeNetwork ?: return 0
        val capabilities = connectivityManager.getNetworkCapabilities(network) ?: return 0
        
        var score = 0
        
        // Transport type
        if (capabilities.hasTransport(NetworkCapabilities.TRANSPORT_ETHERNET)) score += 50
        else if (capabilities.hasTransport(NetworkCapabilities.TRANSPORT_WIFI)) score += 40
        else if (capabilities.hasTransport(NetworkCapabilities.TRANSPORT_CELLULAR)) score += 30
        
        // Capabilities
        if (capabilities.hasCapability(NetworkCapabilities.NET_CAPABILITY_INTERNET)) score += 20
        if (capabilities.hasCapability(NetworkCapabilities.NET_CAPABILITY_VALIDATED)) score += 15
        if (capabilities.hasCapability(NetworkCapabilities.NET_CAPABILITY_NOT_METERED)) score += 15
        
        return minOf(score, 100)
    }
}

enum class NetworkType {
    CELLULAR,
    INSTITUTIONAL_WIFI,
    PUBLIC_WIFI,
    UNKNOWN
}
