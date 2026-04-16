"""
OCR Service for License Plate Recognition
Implements YOLOv11 + EasyOCR for Brazilian license plates
Supports both old format (LLL-NNNN) and Mercosur format (LLLNLNN)
"""

import asyncio
import re
import time
from pathlib import Path
from typing import Optional, Tuple
from dataclasses import dataclass
from PIL import Image
import numpy as np

from ultralytics import YOLO
import easyocr


def detect_gpu_device(device_preference: str = "auto") -> str:
    """
    Detect available GPU device for OCR processing.

    Args:
        device_preference: Preferred device ("auto", "cpu", "cuda", "mps")

    Returns:
        Device string to use ("cpu", "cuda", "mps")
    """
    if device_preference != "auto":
        return device_preference

    # Try CUDA (NVIDIA)
    try:
        import torch
        if torch.cuda.is_available():
            return "cuda"
    except ImportError:
        pass

    # Try MPS (Apple Silicon)
    try:
        import torch
        if hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
            return "mps"
    except (ImportError, AttributeError):
        pass

    # Fallback to CPU
    return "cpu"


@dataclass
class OcrResult:
    """Result of OCR processing"""
    plate_number: str
    confidence: float
    processing_time_ms: float
    ocr_engine: str = "yolov11_easyocr"
    plate_format: str = "unknown"  # "old" or "mercusor" or "unknown"


class OcrService:
    """
    OCR Service for license plate recognition
    Uses YOLOv11 for plate detection and EasyOCR for character recognition
    """

    # Brazilian license plate patterns
    OLD_PLATE_PATTERN = re.compile(r"^[A-Z]{3}[0-9]{4}$")
    MERCOSUR_PLATE_PATTERN = re.compile(r"^[A-Z]{3}[0-9][A-Z0-9][0-9]{2}$")

    def __init__(
        self,
        yolo_model_path: Optional[str] = None,
        easyocr_langs: list = None,
        device: str = "cpu"
    ):
        """
        Initialize OCR service

        Args:
            yolo_model_path: Path to YOLOv11 model file. If None, uses default
            easyocr_langs: List of languages for EasyOCR. Default ['en', 'pt']
            device: Device to run models on ('cpu', 'cuda', 'mps')
        """
        self.yolo_model_path = yolo_model_path
        self.easyocr_langs = easyocr_langs or ["en", "pt"]
        self.device = device

        self._plate_detector: Optional[YOLO] = None
        self._text_reader: Optional[easyocr.Reader] = None

    def _load_models(self):
        """Lazy load models on first use"""
        if self._plate_detector is None:
            # Load YOLOv11 for plate detection
            if self.yolo_model_path and Path(self.yolo_model_path).exists():
                self._plate_detector = YOLO(self.yolo_model_path)
            else:
                # Use default YOLOv11 model (will download on first run)
                self._plate_detector = YOLO("yolov11n.pt")
            
            # Set device
            self._plate_detector.to(self.device)

        if self._text_reader is None:
            # Load EasyOCR for text recognition
            self._text_reader = easyocr.Reader(
                self.easyocr_langs,
                gpu=self.device != "cpu",
                verbose=False
            )

    def process_image(
        self,
        image_path: str,
        confidence_threshold: float = 0.5
    ) -> Optional[OcrResult]:
        """
        Process an image to extract license plate

        Args:
            image_path: Path to image file
            confidence_threshold: Minimum confidence for plate detection

        Returns:
            OcrResult if successful, None otherwise
        """
        self._load_models()

        start_time = time.time()

        try:
            # Load image
            image = Image.open(image_path)
            image_np = np.array(image)

            # Step 1: Detect license plate with YOLO
            plate_results = self._plate_detector(
                image_np,
                conf=confidence_threshold,
                verbose=False
            )

            if not plate_results or not plate_results[0].boxes:
                return None

            # Get the bounding box of the detected plate
            boxes = plate_results[0].boxes
            best_box = boxes[0]  # Use the first detection

            # Crop the plate region
            x1, y1, x2, y2 = best_box.xyxy[0].cpu().numpy()
            plate_region = image_np[int(y1):int(y2), int(x1):int(x2)]

            # Step 2: OCR on the cropped plate
            ocr_results = self._text_reader.readtext(plate_region)

            if not ocr_results:
                return None

            # Get the best OCR result (highest confidence)
            best_ocr = max(ocr_results, key=lambda x: x[2])

            plate_text = best_ocr[0].upper().replace(" ", "").replace("-", "")
            ocr_confidence = float(best_ocr[2])

            # Validate plate format
            plate_format = self._validate_plate_format(plate_text)

            processing_time_ms = (time.time() - start_time) * 1000

            return OcrResult(
                plate_number=plate_text,
                confidence=ocr_confidence,
                processing_time_ms=processing_time_ms,
                plate_format=plate_format
            )

        except Exception as e:
            # Log error in production
            print(f"OCR processing error: {e}")
            return None

    def process_image_bytes(
        self,
        image_bytes: bytes,
        confidence_threshold: float = 0.5
    ) -> Optional[OcrResult]:
        """
        Process image bytes to extract license plate

        Args:
            image_bytes: Image data as bytes
            confidence_threshold: Minimum confidence for plate detection

        Returns:
            OcrResult if successful, None otherwise
        """
        self._load_models()

        try:
            # Load image from bytes
            image = Image.open(image_bytes)
            image_np = np.array(image)

            start_time = time.time()

            # Step 1: Detect license plate with YOLO
            plate_results = self._plate_detector(
                image_np,
                conf=confidence_threshold,
                verbose=False
            )

            if not plate_results or not plate_results[0].boxes:
                return None

            # Get the bounding box of the detected plate
            boxes = plate_results[0].boxes
            best_box = boxes[0]

            # Crop the plate region
            x1, y1, x2, y2 = best_box.xyxy[0].cpu().numpy()
            plate_region = image_np[int(y1):int(y2), int(x1):int(x2)]

            # Step 2: OCR on the cropped plate
            ocr_results = self._text_reader.readtext(plate_region)

            if not ocr_results:
                return None

            # Get the best OCR result
            best_ocr = max(ocr_results, key=lambda x: x[2])

            plate_text = best_ocr[0].upper().replace(" ", "").replace("-", "")
            ocr_confidence = float(best_ocr[2])

            # Validate plate format
            plate_format = self._validate_plate_format(plate_text)

            processing_time_ms = (time.time() - start_time) * 1000

            return OcrResult(
                plate_number=plate_text,
                confidence=ocr_confidence,
                processing_time_ms=processing_time_ms,
                plate_format=plate_format
            )

        except Exception as e:
            print(f"OCR processing error: {e}")
            return None

    def _validate_plate_format(self, plate_text: str) -> str:
        """
        Validate and identify Brazilian license plate format

        Args:
            plate_text: Plate text from OCR

        Returns:
            "old", "mercusor", or "unknown"
        """
        if self.OLD_PLATE_PATTERN.match(plate_text):
            return "old"
        elif self.MERCOSUR_PLATE_PATTERN.match(plate_text):
            return "mercusor"
        return "unknown"

    def validate_plate_number(self, plate_number: str) -> Tuple[bool, str]:
        """
        Validate a plate number format

        Args:
            plate_number: Plate number to validate

        Returns:
            (is_valid, format_type)
        """
        plate_clean = plate_number.upper().replace(" ", "").replace("-", "")
        
        if self.OLD_PLATE_PATTERN.match(plate_clean):
            return True, "old"
        elif self.MERCOSUR_PLATE_PATTERN.match(plate_clean):
            return True, "mercusor"
        
        return False, "unknown"


class AsyncOcrService:
    """
    Async wrapper for OCR service using ProcessPoolExecutor.
    Provides async methods for CPU-bound OCR operations.
    """
    
    def __init__(self, ocr_service: OcrService):
        self._ocr_service = ocr_service
    
    async def process_image_async(
        self,
        image_path: str,
        confidence_threshold: float = 0.5
    ) -> Optional[OcrResult]:
        """
        Async wrapper for process_image using ProcessPoolExecutor.
        
        Args:
            image_path: Path to image file
            confidence_threshold: Minimum confidence for plate detection
            
        Returns:
            OcrResult if successful, None otherwise
        """
        from app.utils.process_pool import run_in_process_pool
        
        return await run_in_process_pool(
            self._ocr_service.process_image,
            image_path,
            confidence_threshold,
            task_type="ocr_processing",
            enable_monitoring=True,
            enable_circuit_breaker=True,
        )
    
    async def process_image_bytes_async(
        self,
        image_bytes: bytes,
        confidence_threshold: float = 0.5
    ) -> Optional[OcrResult]:
        """
        Async wrapper for process_image_bytes using ProcessPoolExecutor.
        
        Args:
            image_bytes: Image data as bytes
            confidence_threshold: Minimum confidence for plate detection
            
        Returns:
            OcrResult if successful, None otherwise
        """
        from app.utils.process_pool import run_in_process_pool
        
        return await run_in_process_pool(
            self._ocr_service.process_image_bytes,
            image_bytes,
            confidence_threshold
        )
    
    async def process_batch_async(
        self,
        image_paths: list[str],
        confidence_threshold: float = 0.5
    ) -> list[Optional[OcrResult]]:
        """
        Process multiple images in parallel using ProcessPoolExecutor.
        
        Args:
            image_paths: List of image file paths
            confidence_threshold: Minimum confidence for plate detection
            
        Returns:
            List of OcrResult (or None if failed)
        """
        from app.utils.process_pool import run_batch_in_process_pool
        
        args_list = [(path, confidence_threshold) for path in image_paths]
        return await run_batch_in_process_pool(
            self._ocr_service.process_image,
            args_list,
            task_type="ocr_batch",
            enable_monitoring=True,
        )


# Singleton instance for dependency injection
_ocr_service: Optional[OcrService] = None
_async_ocr_service: Optional[AsyncOcrService] = None


def get_ocr_service(
    yolo_model_path: Optional[str] = None,
    device: Optional[str] = None,
) -> OcrService:
    """
    Get or create OCR service singleton

    Args:
        yolo_model_path: Path to YOLO model
        device: Device to run on. If None, auto-detects GPU

    Returns:
        OcrService instance
    """
    global _ocr_service
    if _ocr_service is None:
        # Auto-detect GPU if device not specified
        if device is None:
            try:
                from app.core.config import settings
                device = detect_gpu_device(settings.ocr_device)
            except ImportError:
                device = detect_gpu_device("auto")
        
        _ocr_service = OcrService(
            yolo_model_path=yolo_model_path,
            device=device
        )
    return _ocr_service


def get_async_ocr_service(
    yolo_model_path: Optional[str] = None,
    device: Optional[str] = None,
) -> AsyncOcrService:
    """
    Get or create async OCR service wrapper singleton

    Args:
        yolo_model_path: Path to YOLO model
        device: Device to run on. If None, auto-detects GPU

    Returns:
        AsyncOcrService instance
    """
    global _async_ocr_service
    if _async_ocr_service is None:
        sync_service = get_ocr_service(yolo_model_path, device)
        _async_ocr_service = AsyncOcrService(sync_service)
    return _async_ocr_service
