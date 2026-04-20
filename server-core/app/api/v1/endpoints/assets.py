"""
F.A.R.O. Assets API - Serve images and files from storage
Supports both MinIO/S3 and local storage fallback
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import FileResponse, Response
from botocore.exceptions import ClientError

from app.core.config import settings
from app.services.storage_service import _get_s3_client

logger = logging.getLogger(__name__)

router = APIRouter()


def _get_file_from_s3(bucket: str, key: str) -> tuple[bytes, str]:
    """Get file from S3/MinIO storage."""
    try:
        client = _get_s3_client()
        response = client.get_object(Bucket=bucket, Key=key)
        return response["Body"].read(), response.get("ContentType", "application/octet-stream")
    except ClientError as e:
        logger.error(f"Failed to get file from S3: {e}")
        raise HTTPException(status_code=404, detail="File not found in S3 storage")


def _get_file_from_local(key: str) -> tuple[bytes, str]:
    """Get file from local storage."""
    try:
        local_path = Path(settings.local_storage_path) / key
        if not local_path.exists():
            raise FileNotFoundError(f"File not found: {local_path}")
        
        with open(local_path, "rb") as f:
            content = f.read()
        
        # Determine content type based on extension
        content_type = "application/octet-stream"
        if local_path.suffix.lower() in [".jpg", ".jpeg"]:
            content_type = "image/jpeg"
        elif local_path.suffix.lower() == ".png":
            content_type = "image/png"
        elif local_path.suffix.lower() == ".gif":
            content_type = "image/gif"
        elif local_path.suffix.lower() in [".mp3", ".wav"]:
            content_type = "audio/mpeg"
        elif local_path.suffix.lower() == ".mp4":
            content_type = "video/mp4"
        
        return content, content_type
    except FileNotFoundError as e:
        logger.error(f"File not found in local storage: {e}")
        raise HTTPException(status_code=404, detail="File not found in local storage")
    except Exception as e:
        logger.error(f"Failed to get file from local storage: {e}")
        raise HTTPException(status_code=500, detail="Failed to read file from local storage")


@router.get("/assets/{bucket}/{path:path}")
async def get_asset(bucket: str, path: str, request: Request) -> Response:
    """
    Get asset from storage.
    
    Supports both S3/MinIO and local storage fallback.
    URL format: /api/v1/assets/{bucket}/{path}
    
    Examples:
    - S3: /api/v1/assets/faro-assets/observations/123/image/abc_plate.jpg
    - Local: /api/v1/assets/local/observations/123/image/abc_plate.jpg
    """
    try:
        # Determine storage backend based on bucket name
        if bucket == "local":
            # Use local storage
            content, content_type = _get_file_from_local(path)
        else:
            # Try S3/MinIO first, fallback to local
            try:
                content, content_type = _get_file_from_s3(bucket, path)
            except HTTPException:
                # Fallback to local storage if S3 fails
                logger.warning(f"S3 lookup failed, trying local storage for {path}")
                content, content_type = _get_file_from_local(path)
        
        # Set cache headers for better performance
        headers = {
            "Cache-Control": "public, max-age=3600",  # Cache for 1 hour
            "Content-Type": content_type,
        }
        
        return Response(content=content, headers=headers)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error serving asset: {e}")
        raise HTTPException(status_code=500, detail="Failed to serve asset")


@router.head("/assets/{bucket}/{path:path}")
async def head_asset(bucket: str, path: str) -> Response:
    """
    Check if asset exists without downloading it.
    Useful for preloading or checking availability.
    """
    try:
        if bucket == "local":
            local_path = Path(settings.local_storage_path) / path
            if not local_path.exists():
                raise HTTPException(status_code=404, detail="File not found")
        else:
            try:
                client = _get_s3_client()
                client.head_object(Bucket=bucket, Key=path)
            except ClientError:
                # Fallback to local storage
                local_path = Path(settings.local_storage_path) / path
                if not local_path.exists():
                    raise HTTPException(status_code=404, detail="File not found")
        
        return Response(status_code=200)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error checking asset existence: {e}")
        raise HTTPException(status_code=500, detail="Failed to check asset")
