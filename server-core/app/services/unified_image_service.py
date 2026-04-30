"""
F.A.R.O. Unified Image Service - Centralized image processing pipeline
Handles compression, resizing, format conversion, and optimization for OCR and web display
"""

from __future__ import annotations

import io
import logging
import hashlib
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple
from dataclasses import dataclass
from enum import Enum

import boto3
from PIL import Image, ImageEnhance, ImageFilter
from fastapi import HTTPException
from botocore.exceptions import ClientError

from app.core.config import settings
from app.services.storage_service import _get_s3_client

logger = logging.getLogger(__name__)


class ImageFormat(Enum):
    """Supported image formats"""
    WEBP = "webp"
    JPEG = "jpeg"
    PNG = "png"


class ImagePurpose(Enum):
    """Image processing purposes"""
    OCR = "ocr"           # High quality for OCR processing
    STORAGE = "storage"   # Balanced quality for storage
    WEB = "web"          # Optimized for web display
    THUMBNAIL = "thumbnail"  # Small preview


@dataclass
class ImageProcessingConfig:
    """Configuration for image processing"""
    quality: int
    format: ImageFormat
    max_width: Optional[int] = None
    max_height: Optional[int] = None
    purpose: ImagePurpose = ImagePurpose.STORAGE
    watermark: bool = False
    optimize: bool = True


@dataclass
class ProcessedImage:
    """Result of image processing"""
    image_data: bytes
    format: ImageFormat
    width: int
    height: int
    file_size: int
    hash: str
    config: ImageProcessingConfig


@dataclass
class ImageVariant:
    """Single image variant"""
    size_name: str
    image_data: bytes
    format: ImageFormat
    width: int
    height: int
    file_size: int
    url: Optional[str] = None


class UnifiedImageService:
    """Unified image processing service for F.A.R.O."""
    
    # Default configurations for different purposes
    CONFIGS = {
        ImagePurpose.OCR: ImageProcessingConfig(
            quality=90,
            format=ImageFormat.WEBP,
            max_width=1920,
            max_height=1080,
            purpose=ImagePurpose.OCR,
            watermark=False,
            optimize=False
        ),
        ImagePurpose.STORAGE: ImageProcessingConfig(
            quality=80,
            format=ImageFormat.WEBP,
            max_width=1280,
            max_height=720,
            purpose=ImagePurpose.STORAGE,
            watermark=True,
            optimize=True
        ),
        ImagePurpose.WEB: ImageProcessingConfig(
            quality=75,
            format=ImageFormat.JPEG,
            max_width=800,
            max_height=600,
            purpose=ImagePurpose.WEB,
            watermark=True,
            optimize=True
        ),
        ImagePurpose.THUMBNAIL: ImageProcessingConfig(
            quality=60,
            format=ImageFormat.JPEG,
            max_width=200,
            max_height=150,
            purpose=ImagePurpose.THUMBNAIL,
            watermark=False,
            optimize=True
        )
    }
    
    def __init__(self):
        self.s3_client = _get_s3_client()
        self.default_bucket = "faro-assets"
    
    async def process_image(
        self,
        source_data: bytes,
        source_format: Optional[str] = None,
        purpose: ImagePurpose = ImagePurpose.STORAGE,
        custom_config: Optional[ImageProcessingConfig] = None
    ) -> ProcessedImage:
        """
        Process a single image with specified purpose.
        
        Args:
            source_data: Raw image data
            source_format: Source format (auto-detected if None)
            purpose: Processing purpose
            custom_config: Override default config
            
        Returns:
            ProcessedImage: Processed image data
        """
        try:
            config = custom_config or self.CONFIGS[purpose]
            
            # Load image
            image = self._load_image(source_data, source_format)
            
            # Apply processing pipeline
            processed_image = await self._process_pipeline(image, config)
            
            # Generate hash
            image_hash = self._generate_hash(processed_image.image_data)
            
            logger.info(f"Processed image: {processed_image.width}x{processed_image.height}, "
                       f"format={processed_image.format.value}, "
                       f"size={processed_image.file_size} bytes, "
                       f"hash={image_hash[:8]}")
            
            return processed_image
            
        except Exception as e:
            logger.error(f"Failed to process image: {e}")
            raise HTTPException(status_code=500, detail=f"Image processing failed: {str(e)}")
    
    async def generate_variants(
        self,
        source_data: bytes,
        source_format: Optional[str] = None,
        variants: Optional[List[ImagePurpose]] = None
    ) -> List[ImageVariant]:
        """
        Generate multiple image variants for different purposes.
        
        Args:
            source_data: Raw image data
            source_format: Source format
            variants: List of variants to generate
            
        Returns:
            List[ImageVariant]: Generated variants
        """
        if variants is None:
            variants = [ImagePurpose.STORAGE, ImagePurpose.WEB, ImagePurpose.THUMBNAIL]
        
        processed_variants = []
        
        for purpose in variants:
            try:
                processed = await self.process_image(source_data, source_format, purpose)
                
                variant = ImageVariant(
                    size_name=purpose.value,
                    image_data=processed.image_data,
                    format=processed.format,
                    width=processed.width,
                    height=processed.height,
                    file_size=processed.file_size
                )
                
                processed_variants.append(variant)
                
            except Exception as e:
                logger.warning(f"Failed to generate {purpose.value} variant: {e}")
                continue
        
        return processed_variants
    
    async def upload_processed_variants(
        self,
        observation_id: str,
        variants: List[ImageVariant],
        bucket: Optional[str] = None
    ) -> Dict[str, str]:
        """
        Upload processed variants to storage.
        
        Args:
            observation_id: Observation ID for file naming
            variants: List of variants to upload
            bucket: Storage bucket (default: faro-assets)
            
        Returns:
            Dict mapping variant names to storage URLs
        """
        bucket = bucket or self.default_bucket
        urls = {}
        
        for variant in variants:
            try:
                # Generate file path
                file_path = f"observations/{observation_id}/images/{variant.size_name}.{variant.format.value}"
                
                # Upload to S3
                await self._upload_to_s3(
                    bucket=bucket,
                    key=file_path,
                    data=variant.image_data,
                    content_type=self._get_content_type(variant.format)
                )
                
                # Generate URL
                url = f"/api/v1/assets/{bucket}/{file_path}"
                urls[variant.size_name] = url
                
                logger.info(f"Uploaded variant {variant.size_name}: {file_path}")
                
            except Exception as e:
                logger.error(f"Failed to upload variant {variant.size_name}: {e}")
                continue
        
        return urls
    
    def _load_image(self, data: bytes, format_hint: Optional[str] = None) -> Image.Image:
        """Load image from bytes with format detection."""
        try:
            image = Image.open(io.BytesIO(data))
            
            # Convert to RGB if necessary (for JPEG compatibility)
            if image.mode in ('RGBA', 'LA', 'P'):
                if image.mode == 'P' and 'transparency' in image.info:
                    image = image.convert('RGBA')
                    background = Image.new('RGB', image.size, (255, 255, 255))
                    background.paste(image, mask=image.split()[-1])
                    image = background
                else:
                    image = image.convert('RGB')
            
            return image
            
        except Exception as e:
            logger.error(f"Failed to load image: {e}")
            raise ValueError(f"Invalid image data: {str(e)}")
    
    async def _process_pipeline(self, image: Image.Image, config: ImageProcessingConfig) -> ProcessedImage:
        """Apply processing pipeline to image."""
        processed_image = image
        
        # Resize if needed
        if config.max_width or config.max_height:
            processed_image = self._resize_image(processed_image, config.max_width, config.max_height)
        
        # Apply enhancements based on purpose
        if config.purpose == ImagePurpose.OCR:
            processed_image = self._enhance_for_ocr(processed_image)
        elif config.purpose == ImagePurpose.WEB:
            processed_image = self._enhance_for_web(processed_image)
        
        # Apply watermark
        if config.watermark:
            processed_image = self._apply_watermark(processed_image)
        
        # Convert to target format
        output_format = config.format.value.upper()
        if output_format == 'JPG':
            output_format = 'JPEG'
        
        # Save to bytes
        output = io.BytesIO()
        
        save_kwargs = {
            'format': output_format,
            'quality': config.quality,
            'optimize': config.optimize
        }
        
        if output_format == 'JPEG':
            save_kwargs['progressive'] = True
        elif output_format == 'PNG':
            save_kwargs['compress_level'] = 6
        
        processed_image.save(output, **save_kwargs)
        image_data = output.getvalue()
        
        return ProcessedImage(
            image_data=image_data,
            format=config.format,
            width=processed_image.width,
            height=processed_image.height,
            file_size=len(image_data),
            hash="",  # Will be set by caller
            config=config
        )
    
    def _resize_image(self, image: Image.Image, max_width: Optional[int], max_height: Optional[int]) -> Image.Image:
        """Resize image maintaining aspect ratio."""
        if not max_width and not max_height:
            return image
        
        # Calculate new dimensions
        width, height = image.size
        
        if max_width and width > max_width:
            height = int(height * max_width / width)
            width = max_width
        
        if max_height and height > max_height:
            width = int(width * max_height / height)
            height = max_height
        
        # Resize with high quality
        return image.resize((width, height), Image.Resampling.LANCZOS)
    
    def _enhance_for_ocr(self, image: Image.Image) -> Image.Image:
        """Enhance image for better OCR results."""
        # Convert to grayscale
        if image.mode != 'L':
            image = image.convert('L')
        
        # Apply contrast enhancement
        enhancer = ImageEnhance.Contrast(image)
        image = enhancer.enhance(1.5)
        
        # Apply sharpening
        image = image.filter(ImageFilter.SHARPEN)
        
        return image
    
    def _enhance_for_web(self, image: Image.Image) -> Image.Image:
        """Enhance image for web display."""
        # Slight contrast boost
        enhancer = ImageEnhance.Contrast(image)
        image = enhancer.enhance(1.1)
        
        # Slight sharpening
        image = image.filter(ImageFilter.UnsharpMask(radius=1, percent=120, threshold=3))
        
        return image
    
    def _apply_watermark(self, image: Image.Image) -> Image.Image:
        """Apply F.A.R.O. watermark to image."""
        # Create watermark text
        from PIL import ImageDraw, ImageFont
        
        # Simple text watermark
        draw = ImageDraw.Draw(image)
        
        # Try to load a font, fallback to default
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 20)
        except:
            font = ImageFont.load_default()
        
        # Add watermark in bottom right corner
        text = "F.A.R.O."
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        margin = 10
        x = image.width - text_width - margin
        y = image.height - text_height - margin
        
        # Semi-transparent background
        overlay = Image.new('RGBA', image.size, (0, 0, 0, 0))
        draw_overlay = ImageDraw.Draw(overlay)
        
        # Background rectangle
        draw_overlay.rectangle(
            [x - 5, y - 5, x + text_width + 5, y + text_height + 5],
            fill=(0, 0, 0, 128)
        )
        
        # Text
        draw_overlay.text((x, y), text, font=font, fill=(255, 255, 255, 200))
        
        # Composite watermark
        if image.mode != 'RGBA':
            image = image.convert('RGBA')
        
        return Image.alpha_composite(image, overlay)
    
    def _generate_hash(self, data: bytes) -> str:
        """Generate SHA-256 hash of image data."""
        return hashlib.sha256(data).hexdigest()
    
    def _get_content_type(self, format: ImageFormat) -> str:
        """Get MIME type for image format."""
        content_types = {
            ImageFormat.WEBP: "image/webp",
            ImageFormat.JPEG: "image/jpeg",
            ImageFormat.PNG: "image/png"
        }
        return content_types.get(format, "application/octet-stream")
    
    async def _upload_to_s3(self, bucket: str, key: str, data: bytes, content_type: str) -> None:
        """Upload data to S3 storage."""
        try:
            self.s3_client.put_object(
                Bucket=bucket,
                Key=key,
                Body=data,
                ContentType=content_type,
                CacheControl="public, max-age=3600"
            )
        except ClientError as e:
            logger.error(f"Failed to upload to S3: {e}")
            raise HTTPException(status_code=500, detail=f"Storage upload failed: {str(e)}")
    
    async def get_image_info(self, image_data: bytes) -> Dict[str, Any]:
        """Extract metadata from image."""
        try:
            image = Image.open(io.BytesIO(image_data))
            
            return {
                "width": image.width,
                "height": image.height,
                "format": image.format,
                "mode": image.mode,
                "size_bytes": len(image_data),
                "has_transparency": image.mode in ('RGBA', 'LA') or 'transparency' in image.info
            }
        except Exception as e:
            logger.error(f"Failed to extract image info: {e}")
            return {"error": str(e)}


# Singleton instance
unified_image_service = UnifiedImageService()
