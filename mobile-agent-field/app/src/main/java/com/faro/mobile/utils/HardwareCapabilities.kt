package com.faro.mobile.utils

import android.app.ActivityManager
import android.content.Context
import android.opengl.GLES20
import android.os.Build
import java.io.BufferedReader
import java.io.FileReader

/**
 * Hardware capabilities detection for Android devices.
 * Provides automatic hardware detection for optimization purposes.
 */
data class HardwareCapabilities(
    val cpuCores: Int,
    val totalMemoryMb: Long,
    val availableMemoryMb: Long,
    val gpuAvailable: Boolean,
    val gpuRenderer: String?,
    val gpuVersion: String?,
    val deviceType: DeviceType,
    val apiLevel: Int,
    val architecture: String
)

enum class DeviceType {
    PHONE,
    TABLET,
    UNKNOWN
}

class HardwareDetector(private val context: Context) {
    
    fun detectHardware(): HardwareCapabilities {
        val cpuCores = detectCpuCores()
        val memoryInfo = detectMemoryInfo()
        val gpuInfo = detectGpuInfo()
        val deviceType = detectDeviceType()
        val apiLevel = Build.VERSION.SDK_INT
        val architecture = detectArchitecture()
        
        return HardwareCapabilities(
            cpuCores = cpuCores,
            totalMemoryMb = memoryInfo.first,
            availableMemoryMb = memoryInfo.second,
            gpuAvailable = gpuInfo.first,
            gpuRenderer = gpuInfo.second,
            gpuVersion = gpuInfo.third,
            deviceType = deviceType,
            apiLevel = apiLevel,
            architecture = architecture
        )
    }
    
    private fun detectCpuCores(): Int {
        return Runtime.getRuntime().availableProcessors()
    }
    
    private fun detectMemoryInfo(): Pair<Long, Long> {
        val activityManager = context.getSystemService(Context.ACTIVITY_SERVICE) as ActivityManager
        val memoryInfo = ActivityManager.MemoryInfo()
        activityManager.getMemoryInfo(memoryInfo)
        
        val totalMemoryMb = memoryInfo.totalMem / (1024 * 1024)
        val availableMemoryMb = memoryInfo.availMem / (1024 * 1024)
        
        return Pair(totalMemoryMb, availableMemoryMb)
    }
    
    private fun detectGpuInfo(): Triple<Boolean, String?, String?> {
        val glRenderer = StringBuilder()
        val glVersion = StringBuilder()
        
        try {
            // Try to get GPU info from OpenGL
            GLES20.glGetString(GLES20.GL_RENDERER)?.let { glRenderer.append(it) }
            GLES20.glGetString(GLES20.GL_VERSION)?.let { glVersion.append(it) }
            
            val renderer = glRenderer.toString().takeIf { it.isNotEmpty() }
            val version = glVersion.toString().takeIf { it.isNotEmpty() }
            
            return Triple(
                renderer != null,
                renderer,
                version
            )
        } catch (e: Exception) {
            // Fallback to reading from system files
            return detectGpuFromSystem()
        }
    }
    
    private fun detectGpuFromSystem(): Triple<Boolean, String?, String?> {
        try {
            val gpuFile = "/proc/gpuinfo"
            val file = FileReader(gpuFile)
            val reader = BufferedReader(file)
            
            val lines = reader.readLines()
            reader.close()
            
            val renderer = lines.firstOrNull { it.contains("renderer", ignoreCase = true) }?.split(":")?.getOrNull(1)?.trim()
            val version = lines.firstOrNull { it.contains("version", ignoreCase = true) }?.split(":")?.getOrNull(1)?.trim()
            
            return Triple(
                renderer != null || version != null,
                renderer,
                version
            )
        } catch (e: Exception) {
            return Triple(false, null, null)
        }
    }
    
    private fun detectDeviceType(): DeviceType {
        val configuration = context.resources.configuration
        val (screenLayout, screenLayoutSize) = Pair(configuration.screenLayout and configuration.SCREENLAYOUT_SIZE_MASK, 0)
        
        return when {
            screenLayoutSize >= configuration.SCREENLAYOUT_SIZE_LARGE -> DeviceType.TABLET
            else -> DeviceType.PHONE
        }
    }
    
    private fun detectArchitecture(): String {
        return when (Build.SUPPORTED_ABIS.firstOrNull()) {
            "armeabi-v7a" -> "ARMv7"
            "arm64-v8a" -> "ARM64"
            "x86" -> "x86"
            "x86_64" -> "x86_64"
            else -> "Unknown"
        }
    }
}

/**
 * Device category based on hardware capabilities.
 */
enum class DeviceCategory {
    LOW_END,    // 2GB RAM, 4 cores
    MID_RANGE,  // 4GB RAM, 8 cores
    HIGH_END    // 8GB+ RAM, 8+ cores, GPU
}

class DeviceClassifier(private val context: Context) {
    
    fun classifyDevice(hardware: HardwareCapabilities): DeviceCategory {
        val totalMemoryGb = hardware.totalMemoryMb / 1024
        val cpuCores = hardware.cpuCores
        val hasGpu = hardware.gpuAvailable
        
        return when {
            totalMemoryGb >= 8 && cpuCores >= 8 && hasGpu -> DeviceCategory.HIGH_END
            totalMemoryGb >= 4 && cpuCores >= 4 -> DeviceCategory.MID_RANGE
            else -> DeviceCategory.LOW_END
        }
    }
}
