"""
F.A.R.O. Images API - Unified image processing endpoints
Handles image processing, optimization, and variant generation
"""

from __future__ import annotations

import logging
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from app.services.unified_image_service import (
    UnifiedImageService,
    ImagePurpose,
    ImageProcessingConfig,
    ImageFormat
)

logger = logging.getLogger(__name__)

router = APIRouter()


class ImageProcessingRequest(BaseModel):
    """Request model for image processing."""
    purpose: str = Field(..., description="Processing purpose: ocr, storage, web, thumbnail")
    quality: Optional[int] = Field(None, ge=1, le=100, description="Compression quality (1-100)")
    format: Optional[str] = Field(None, description="Output format: webp, jpeg, png")
    max_width: Optional[int] = Field(None, gt=0, description="Maximum width")
    max_height: Optional[int] = Field(None, gt=0, description="Maximum height")
    watermark: Optional[bool] = Field(None, description="Apply watermark")
    optimize: Optional[bool] = Field(None, description="Optimize for size")


class ImageProcessingResponse(BaseModel):
    """Response model for image processing."""
    success: bool
    width: int
    height: int
    format: str
    file_size: int
    hash: str
    config: Dict[str, Any]


class ImageVariantResponse(BaseModel):
    """Response model for image variants."""
    size_name: str
    width: int
    height: int
    format: str
    file_size: int
    url: Optional[str] = None


class ImageVariantsResponse(BaseModel):
    """Response model for multiple image variants."""
    success: bool
    variants: List[ImageVariantResponse]
    urls: Dict[str, str]


def get_image_service() -> UnifiedImageService:
    """Dependency injection for image service."""
    return UnifiedImageService()


@router.post("/process", response_model=ImageProcessingResponse)
async def process_image(
    file: UploadFile = File(...),
    purpose: str = Form(...),
    quality: Optional[int] = Form(None),
    format: Optional[str] = Form(None),
    max_width: Optional[int] = Form(None),
    max_height: Optional[int] = Form(None),
    watermark: Optional[bool] = Form(None),
    optimize: Optional[bool] = Form(None),
    service: UnifiedImageService = Depends(get_image_service)
):
    """
    Process a single image with specified parameters.
    
    Args:
        file: Image file to process
        purpose: Processing purpose (ocr, storage, web, thumbnail)
        quality: Compression quality (1-100)
        format: Output format (webp, jpeg, png)
        max_width: Maximum width
        max_height: Maximum height
        watermark: Apply watermark
        optimize: Optimize for size
        
    Returns:
        ImageProcessingResponse: Processed image information
    """
    try:
        # Validate purpose
        try:
            image_purpose = ImagePurpose(purpose.lower())
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid purpose. Must be one of: {[p.value for p in ImagePurpose]}"
            )
        
        # Create custom config if parameters provided
        custom_config = None
        if any([quality, format, max_width, max_height, watermark is not None, optimize is not None]):
            # Validate format
            image_format = None
            if format:
                try:
                    image_format = ImageFormat(format.lower())
                except ValueError:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Invalid format. Must be one of: {[f.value for f in ImageFormat]}"
                    )
            
            custom_config = ImageProcessingConfig(
                quality=quality or service.CONFIGS[image_purpose].quality,
                format=image_format or service.CONFIGS[image_purpose].format,
                max_width=max_width,
                max_height=max_height,
                purpose=image_purpose,
                watermark=watermark if watermark is not None else service.CONFIGS[image_purpose].watermark,
                optimize=optimize if optimize is not None else service.CONFIGS[image_purpose].optimize
            )
        
        # Read file data
        file_data = await file.read()
        if not file_data:
            raise HTTPException(status_code=400, detail="No file data provided")
        
        # Process image
        processed = await service.process_image(
            source_data=file_data,
            source_format=file.content_type,
            purpose=image_purpose,
            custom_config=custom_config
        )
        
        return ImageProcessingResponse(
            success=True,
            width=processed.width,
            height=processed.height,
            format=processed.format.value,
            file_size=processed.file_size,
            hash=processed.hash,
            config={
                "quality": processed.config.quality,
                "format": processed.config.format.value,
                "max_width": processed.config.max_width,
                "max_height": processed.config.max_height,
                "purpose": processed.config.purpose.value,
                "watermark": processed.config.watermark,
                "optimize": processed.config.optimize
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Image processing failed: {e}")
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")


@router.post("/variants", response_model=ImageVariantsResponse)
async def generate_variants(
    file: UploadFile = File(...),
    variants: str = Form("storage,web,thumbnail"),
    service: UnifiedImageService = Depends(get_image_service)
):
    """
    Generate multiple image variants for different purposes.
    
    Args:
        file: Image file to process
        variants: Comma-separated list of variants (ocr,storage,web,thumbnail)
        
    Returns:
        ImageVariantsResponse: Generated variants information
    """
    try:
        # Parse variants
        variant_names = [v.strip().lower() for v in variants.split(",")]
        image_variants = []
        
        for variant_name in variant_names:
            try:
                image_variants.append(ImagePurpose(variant_name))
            except ValueError:
                logger.warning(f"Skipping invalid variant: {variant_name}")
        
        if not image_variants:
            raise HTTPException(
                status_code=400,
                detail=f"No valid variants provided. Must be from: {[p.value for p in ImagePurpose]}"
            )
        
        # Read file data
        file_data = await file.read()
        if not file_data:
            raise HTTPException(status_code=400, detail="No file data provided")
        
        # Generate variants
        generated_variants = await service.generate_variants(
            source_data=file_data,
            source_format=file.content_type,
            variants=image_variants
        )
        
        # Convert to response format
        variant_responses = []
        for variant in generated_variants:
            variant_responses.append(ImageVariantResponse(
                size_name=variant.size_name,
                width=variant.width,
                height=variant.height,
                format=variant.format.value,
                file_size=variant.file_size,
                url=variant.url
            ))
        
        return ImageVariantsResponse(
            success=True,
            variants=variant_responses,
            urls={v.size_name: v.url for v in generated_variants if v.url}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Variant generation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Variant generation failed: {str(e)}")


@router.post("/upload-variants")
async def upload_variants(
    file: UploadFile = File(...),
    observation_id: str = Form(...),
    variants: str = Form("storage,web,thumbnail"),
    bucket: Optional[str] = Form(None),
    service: UnifiedImageService = Depends(get_image_service)
):
    """
    Generate and upload image variants to storage.
    
    Args:
        file: Image file to process
        observation_id: Observation ID for file naming
        variants: Comma-separated list of variants
        bucket: Storage bucket (default: faro-assets)
        
    Returns:
        Dict with upload URLs
    """
    try:
        # Parse variants
        variant_names = [v.strip().lower() for v in variants.split(",")]
        image_variants = []
        
        for variant_name in variant_names:
            try:
                image_variants.append(ImagePurpose(variant_name))
            except ValueError:
                logger.warning(f"Skipping invalid variant: {variant_name}")
        
        if not image_variants:
            raise HTTPException(
                status_code=400,
                detail=f"No valid variants provided. Must be from: {[p.value for p in ImagePurpose]}"
            )
        
        # Read file data
        file_data = await file.read()
        if not file_data:
            raise HTTPException(status_code=400, detail="No file data provided")
        
        # Generate variants
        generated_variants = await service.generate_variants(
            source_data=file_data,
            source_format=file.content_type,
            variants=image_variants
        )
        
        # Upload variants
        urls = await service.upload_processed_variants(
            observation_id=observation_id,
            variants=generated_variants,
            bucket=bucket
        )
        
        return {
            "success": True,
            "observation_id": observation_id,
            "uploaded_variants": len(urls),
            "urls": urls
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Variant upload failed: {e}")
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@router.get("/info")
async def get_image_info(
    file: UploadFile = File(...),
    service: UnifiedImageService = Depends(get_image_service)
):
    """
    Extract metadata from uploaded image.
    
    Args:
        file: Image file to analyze
        
    Returns:
        Dict with image metadata
    """
    try:
        # Read file data
        file_data = await file.read()
        if not file_data:
            raise HTTPException(status_code=400, detail="No file data provided")
        
        # Extract info
        info = await service.get_image_info(file_data)
        
        return {
            "success": True,
            "filename": file.filename,
            "content_type": file.content_type,
            "size_bytes": len(file_data),
            "metadata": info
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Image info extraction failed: {e}")
        raise HTTPException(status_code=500, detail=f"Info extraction failed: {str(e)}")


@router.get("/formats")
async def get_supported_formats():
    """
    Get supported image formats and purposes.
    
    Returns:
        Dict with supported formats and purposes
    """
    return {
        "formats": [f.value for f in ImageFormat],
        "purposes": [p.value for p in ImagePurpose],
        "default_configs": {
            purpose.value: {
                "quality": config.quality,
                "format": config.format.value,
                "max_width": config.max_width,
                "max_height": config.max_height,
                "watermark": config.watermark,
                "optimize": config.optimize
            }
            for purpose, config in UnifiedImageService.CONFIGS.items()
        }
    }


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "unified-image-service",
        "version": "1.0.0"
    }
