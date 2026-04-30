package com.faro.mobile.utils

import android.content.Context
import android.media.AudioAttributes
import android.media.RingtoneManager
import android.os.Build
import android.os.VibrationEffect
import android.os.Vibrator
import android.os.VibratorManager
import dagger.hilt.android.qualifiers.ApplicationContext
import timber.log.Timber
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class TacticalAlertManager @Inject constructor(
    @ApplicationContext private val context: Context
) {
    private val vibrator: Vibrator? = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S) {
        val vibratorManager = context.getSystemService(Context.VIBRATOR_MANAGER_SERVICE) as VibratorManager
        vibratorManager.defaultVibrator
    } else {
        @Suppress("DEPRECATION")
        context.getSystemService(Context.VIBRATOR_SERVICE) as Vibrator
    }

    enum class AlertLevel {
        LOW,      // Pulso único curto
        MEDIUM,   // Pulso duplo
        CRITICAL  // Alerta persistente (INTERCEPT)
    }

    fun triggerPhysicalAlert(level: AlertLevel) {
        when (level) {
            AlertLevel.LOW -> playLowAlert()
            AlertLevel.MEDIUM -> playMediumAlert()
            AlertLevel.CRITICAL -> playCriticalAlert()
        }
    }

    private fun playLowAlert() {
        val pattern = longArrayOf(0, 100)
        vibrate(pattern, -1)
    }

    private fun playMediumAlert() {
        val pattern = longArrayOf(0, 300, 100, 300)
        vibrate(pattern, -1)
    }

    private fun playCriticalAlert() {
        val pattern = longArrayOf(0, 500, 200, 500, 200, 500, 200, 500)
        vibrate(pattern, -1)
        playAlarmSound()
        Timber.i("CRITICAL tactical alert triggered - INTERCEPT APPROACH")
    }

    private fun vibrate(pattern: LongArray, repeat: Int) {
        if (vibrator == null || !vibrator.hasVibrator()) return

        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            vibrator.vibrate(VibrationEffect.createWaveform(pattern, repeat))
        } else {
            @Suppress("DEPRECATION")
            vibrator.vibrate(pattern, repeat)
        }
    }

    private fun playAlarmSound() {
        try {
            val alert = RingtoneManager.getDefaultUri(RingtoneManager.TYPE_ALARM)
            val ringtone = RingtoneManager.getRingtone(context, alert)
            
            // For bypassing silent/DND as requested, we'd need more complex Audio attributes
            // but for now we use the standard alarm stream
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.LOLLIPOP) {
                ringtone.audioAttributes = AudioAttributes.Builder()
                    .setUsage(AudioAttributes.USAGE_ALARM)
                    .setContentType(AudioAttributes.CONTENT_TYPE_SONIFICATION)
                    .build()
            }
            ringtone.play()
        } catch (e: SecurityException) {
            Timber.e(e, "Permission denied for ringtone playback")
            // Fallback to notification sound
            try {
                val notification = RingtoneManager.getDefaultUri(RingtoneManager.TYPE_NOTIFICATION)
                val r = RingtoneManager.getRingtone(context, notification)
                r.play()
            } catch (e2: SecurityException) {
                Timber.e(e2, "Permission denied for notification sound")
            }
        } catch (e: IllegalArgumentException) {
            Timber.e(e, "Invalid ringtone URI")
            // Fallback to notification sound
            try {
                val notification = RingtoneManager.getDefaultUri(RingtoneManager.TYPE_NOTIFICATION)
                val r = RingtoneManager.getRingtone(context, notification)
                r.play()
            } catch (e2: Exception) {
                Timber.e(e2, "Failed to play fallback sound")
            }
        }
    }
}
