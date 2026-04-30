package com.faro.mobile.presentation.components

import android.Manifest
import android.util.Log
import androidx.camera.core.CameraSelector
import androidx.camera.core.ImageAnalysis
import androidx.camera.core.ImageCapture
import androidx.camera.core.Preview
import androidx.camera.lifecycle.ProcessCameraProvider
import androidx.camera.view.PreviewView
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.runtime.Composable
import androidx.compose.runtime.DisposableEffect
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.platform.LocalLifecycleOwner
import androidx.compose.ui.viewinterop.AndroidView
import androidx.core.content.ContextCompat
import com.faro.mobile.data.service.UnifiedOCRService
import com.google.accompanist.permissions.ExperimentalPermissionsApi
import com.google.accompanist.permissions.isGranted
import com.google.accompanist.permissions.rememberPermissionState
import java.util.concurrent.Executors

private const val TAG = "CameraPreview"
private const val OCR_FRAME_INTERVAL_MS = 300L
private const val OCR_RESULT_DEDUP_WINDOW_MS = 1500L

private class OcrDispatchState {
    var isFrameProcessing: Boolean = false
    var lastFrameProcessedAt: Long = 0L
    var lastPlateDispatched: String? = null
    var lastPlateDispatchedAt: Long = 0L
}

@OptIn(ExperimentalPermissionsApi::class)
@Composable
fun CameraPreview(
    onTextRecognized: (String, Float) -> Unit,
    unifiedOCRService: UnifiedOCRService,
    modifier: Modifier = Modifier
) {
    val context = LocalContext.current
    val lifecycleOwner = LocalLifecycleOwner.current

    val cameraPermissionState = rememberPermissionState(Manifest.permission.CAMERA)

    var cameraProvider by remember { mutableStateOf<ProcessCameraProvider?>(null) }
    var imageCapture by remember { mutableStateOf<ImageCapture?>(null) }

    val cameraExecutor = remember { Executors.newSingleThreadExecutor() }
    val ocrDispatchState = remember { OcrDispatchState() }

    LaunchedEffect(Unit) {
        cameraPermissionState.launchPermissionRequest()
    }

    if (cameraPermissionState.status.isGranted) {
        Box(modifier = modifier) {
            AndroidView(
                factory = { ctx ->
                    val previewView = PreviewView(ctx).apply {
                        scaleType = PreviewView.ScaleType.FILL_CENTER
                    }

                    // Initialize camera
                    val cameraProviderFuture = ProcessCameraProvider.getInstance(ctx)
                    cameraProviderFuture.addListener({
                        try {
                            val provider = cameraProviderFuture.get()
                            cameraProvider = provider

                            // Preview
                            val preview = Preview.Builder().build().also {
                                it.setSurfaceProvider(previewView.surfaceProvider)
                            }

                            // Image capture
                            imageCapture = ImageCapture.Builder().build()

                            // Image analysis for OCR
                            val imageAnalyzer = ImageAnalysis.Builder()
                                .setBackpressureStrategy(ImageAnalysis.STRATEGY_KEEP_ONLY_LATEST)
                                .build()
                                .also { analysis ->
                                    analysis.setAnalyzer(cameraExecutor) { imageProxy ->
                                        val now = System.currentTimeMillis()
                                        if (
                                            ocrDispatchState.isFrameProcessing ||
                                            now - ocrDispatchState.lastFrameProcessedAt < OCR_FRAME_INTERVAL_MS
                                        ) {
                                            imageProxy.close()
                                            return@setAnalyzer
                                        }
                                        ocrDispatchState.isFrameProcessing = true
                                        ocrDispatchState.lastFrameProcessedAt = now
                                        processImageForOCR(
                                            imageProxy = imageProxy,
                                            unifiedOCRService = unifiedOCRService,
                                            onTextRecognized = onTextRecognized,
                                            dispatchState = ocrDispatchState,
                                            context = ctx
                                        )
                                    }
                                }

                            // Select back camera
                            val cameraSelector = CameraSelector.DEFAULT_BACK_CAMERA

                            // Bind to lifecycle
                            provider.unbindAll()
                            provider.bindToLifecycle(
                                lifecycleOwner,
                                cameraSelector,
                                preview,
                                imageCapture,
                                imageAnalyzer
                            )

                        } catch (e: Exception) {
                            Log.e(TAG, "Camera initialization failed", e)
                        }
                    }, ContextCompat.getMainExecutor(ctx))

                    previewView
                },
                modifier = Modifier.fillMaxSize()
            )
        }
    } else {
        // Permission not granted
        Box(
            modifier = modifier.fillMaxSize(),
            contentAlignment = Alignment.Center
        ) {
            androidx.compose.material3.Text("Camera permission required")
        }
    }

    DisposableEffect(Unit) {
        onDispose {
            cameraProvider?.unbindAll()
            cameraExecutor.shutdown()
        }
    }
}

private fun processImageForOCR(
    imageProxy: androidx.camera.core.ImageProxy,
    unifiedOCRService: UnifiedOCRService,
    onTextRecognized: (String, Float) -> Unit,
    dispatchState: OcrDispatchState,
    context: Context
) {
    val mediaImage = imageProxy.image
    if (mediaImage != null) {
        // Convert ImageProxy to Bitmap for processing
        val bitmap = imageProxyToBitmap(imageProxy)
        if (bitmap != null) {
            kotlinx.coroutines.GlobalScope.launch(kotlinx.coroutines.Dispatchers.IO) {
                val result = unifiedOCRService.processImage(
                    bitmap = bitmap,
                    networkQuality = "unknown", // Would come from network monitor
                    batteryLevel = 0.5f, // Would come from battery monitor
                    forceServer = false
                )
                
                if (result.plateNumber != null && result.confidence > 0.5f) {
                    val now = System.currentTimeMillis()
                    val isDuplicateWithinWindow =
                        dispatchState.lastPlateDispatched == result.plateNumber &&
                            (now - dispatchState.lastPlateDispatchedAt) < OCR_RESULT_DEDUP_WINDOW_MS
                    if (!isDuplicateWithinWindow) {
                        dispatchState.lastPlateDispatched = result.plateNumber
                        dispatchState.lastPlateDispatchedAt = now
                        withContext(kotlinx.coroutines.Dispatchers.Main) {
                            onTextRecognized(result.plateNumber, result.confidence)
                        }
                    }
                }
                
                dispatchState.isFrameProcessing = false
                imageProxy.close()
            }
        } else {
            dispatchState.isFrameProcessing = false
            imageProxy.close()
        }
    } else {
        dispatchState.isFrameProcessing = false
        imageProxy.close()
    }
}

/**
 * Convert ImageProxy to Bitmap for local OCR processing
 */
private fun imageProxyToBitmap(imageProxy: androidx.camera.core.ImageProxy): android.graphics.Bitmap? {
    val buffer = imageProxy.planes[0].buffer
    val bytes = ByteArray(buffer.remaining())
    buffer.get(bytes)
    
    val bitmap = android.graphics.BitmapFactory.decodeByteArray(bytes, 0, bytes.size)
    
    // Rotate bitmap if needed
    val rotation = imageProxy.imageInfo.rotationDegrees.toFloat()
    if (rotation != 0f) {
        val matrix = android.graphics.Matrix()
        matrix.postRotate(rotation)
        val rotatedBitmap = android.graphics.Bitmap.createBitmap(
            bitmap, 0, 0, bitmap.width, bitmap.height, matrix, true
        )
        bitmap.recycle()
        return rotatedBitmap
    }
    
    return bitmap
}
