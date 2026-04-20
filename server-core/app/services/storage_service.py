"""
S3-compatible storage service for FARO assets.
Supports both simple upload and progressive chunked upload with retry.

Fallback to local storage when MinIO is not available or disabled.
"""

from __future__ import annotations

import hashlib
import logging
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional
from uuid import uuid4

import boto3
from botocore.client import BaseClient
from botocore.exceptions import ClientError

from app.core.config import settings

logger = logging.getLogger(__name__)


@dataclass
class UploadedAsset:
    bucket: str
    key: str
    content_type: str
    size_bytes: int
    checksum_sha256: str


_s3_client: BaseClient | None = None
_s3_available: bool | None = None


def _check_s3_available() -> bool:
    """Check if S3/MinIO is available and configured."""
    global _s3_available
    if _s3_available is not None:
        return _s3_available
    
    if not settings.s3_enabled:
        _s3_available = False
        logger.info("S3/MinIO disabled in configuration, using local storage fallback")
        return False
    
    try:
        client = _get_s3_client()
        client.head_bucket(Bucket=settings.s3_bucket_name)
        _s3_available = True
        logger.info("S3/MinIO is available")
        return True
    except (ClientError, Exception) as e:
        _s3_available = False
        logger.warning(f"S3/MinIO not available, using local storage fallback: {e}")
        return False


def _get_s3_client() -> BaseClient:
    global _s3_client
    if _s3_client is None:
        _s3_client = boto3.client(
            "s3",
            endpoint_url=settings.s3_endpoint,
            aws_access_key_id=settings.s3_access_key,
            aws_secret_access_key=settings.s3_secret_key,
            region_name=settings.s3_region,
        )
    return _s3_client


def _ensure_local_storage_dir() -> Path:
    """Ensure local storage directory exists."""
    local_path = Path(settings.local_storage_path)
    local_path.mkdir(parents=True, exist_ok=True)
    return local_path


def _ensure_bucket_exists(client: BaseClient, bucket_name: str) -> None:
    try:
        client.head_bucket(Bucket=bucket_name)
    except ClientError:
        client.create_bucket(Bucket=bucket_name)


def _upload_local(
    *,
    observation_id: str,
    asset_type: str,
    original_filename: str,
    payload: bytes,
) -> UploadedAsset:
    """Upload asset to local filesystem as fallback."""
    local_path = _ensure_local_storage_dir()
    
    safe_name = original_filename.replace("\\", "_").replace("/", "_").replace(" ", "_")
    relative_path = f"observations/{observation_id}/{asset_type}/{uuid4()}_{safe_name}"
    full_path = local_path / relative_path
    
    # Ensure directory exists
    full_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Write file
    with open(full_path, "wb") as f:
        f.write(payload)
    
    checksum = hashlib.sha256(payload).hexdigest()
    
    logger.info(f"Uploaded asset to local storage: {relative_path}")
    
    return UploadedAsset(
        bucket="local",
        key=relative_path,
        content_type="application/octet-stream",
        size_bytes=len(payload),
        checksum_sha256=checksum,
    )


def upload_observation_asset_bytes(
    *,
    observation_id: str,
    asset_type: str,
    original_filename: str,
    content_type: str,
    payload: bytes,
) -> UploadedAsset:
    """Simple upload for small files or when progressive upload is disabled.
    
    Falls back to local storage if S3/MinIO is not available.
    """
    if _check_s3_available():
        # Use S3/MinIO
        client = _get_s3_client()
        bucket_name = settings.s3_bucket_name
        _ensure_bucket_exists(client, bucket_name)

        safe_name = original_filename.replace("\\", "_").replace("/", "_").replace(" ", "_")
        key = f"observations/{observation_id}/{asset_type}/{uuid4()}_{safe_name}"

        checksum = hashlib.sha256(payload).hexdigest()
        client.put_object(
            Bucket=bucket_name,
            Key=key,
            Body=payload,
            ContentType=content_type,
            Metadata={"sha256": checksum, "asset_type": asset_type},
        )
        return UploadedAsset(
            bucket=bucket_name,
            key=key,
            content_type=content_type,
            size_bytes=len(payload),
            checksum_sha256=checksum,
        )
    else:
        # Fallback to local storage
        return _upload_local(
            observation_id=observation_id,
            asset_type=asset_type,
            original_filename=original_filename,
            payload=payload,
        )


def upload_observation_asset_progressive(
    *,
    observation_id: str,
    asset_type: str,
    original_filename: str,
    content_type: str,
    payload: bytes,
    upload_id: Optional[str] = None,
    chunk_index: int = 0,
) -> dict:
    """
    Progressive upload with chunking support.

    Args:
        observation_id: Observation ID
        asset_type: Type of asset (image/audio)
        original_filename: Original filename
        content_type: Content type
        payload: Chunk of data to upload
        upload_id: Existing upload ID for multipart upload
        chunk_index: Index of current chunk

    Returns:
        Dictionary with upload status and next action
    
    Note: Progressive upload requires S3/MinIO. Falls back to simple upload if not available.
    """
    if not settings.progressive_upload_enabled or not _check_s3_available():
        # Fallback to simple upload
        uploaded = upload_observation_asset_bytes(
            observation_id=observation_id,
            asset_type=asset_type,
            original_filename=original_filename,
            content_type=content_type,
            payload=payload,
        )
        return {
            "status": "completed",
            "asset": {
                "bucket": uploaded.bucket,
                "key": uploaded.key,
                "size_bytes": uploaded.size_bytes,
                "checksum_sha256": uploaded.checksum_sha256,
            },
        }

    client = _get_s3_client()
    bucket_name = settings.s3_bucket_name
    _ensure_bucket_exists(client, bucket_name)

    safe_name = original_filename.replace("\\", "_").replace("/", "_").replace(" ", "_")
    chunk_size_bytes = settings.progressive_upload_chunk_size_mb * 1024 * 1024

    # Initialize multipart upload if not exists
    if upload_id is None:
        key = f"observations/{observation_id}/{asset_type}/{uuid4()}_{safe_name}"
        response = client.create_multipart_upload(
            Bucket=bucket_name,
            Key=key,
            ContentType=content_type,
            Metadata={"asset_type": asset_type, "original_filename": original_filename},
        )
        upload_id = response["UploadId"]
        logger.info(f"Started multipart upload: {upload_id} for {key}")

        return {
            "status": "initialized",
            "upload_id": upload_id,
            "key": key,
            "chunk_size": chunk_size_bytes,
            "next_chunk_index": 0,
        }

    # Upload chunk
    key = f"observations/{observation_id}/{asset_type}/{safe_name}"
    part_number = chunk_index + 1

    try:
        response = client.upload_part(
            Bucket=bucket_name,
            Key=key,
            PartNumber=part_number,
            UploadId=upload_id,
            Body=payload,
        )

        return {
            "status": "chunk_uploaded",
            "upload_id": upload_id,
            "key": key,
            "chunk_index": chunk_index,
            "part_number": part_number,
            "etag": response["ETag"],
        }

    except ClientError as e:
        logger.error(f"Failed to upload chunk {chunk_index}: {e}")
        # Abort upload on error
        try:
            client.abort_multipart_upload(
                Bucket=bucket_name,
                Key=key,
                UploadId=upload_id,
            )
        except ClientError as e:
            logger.warning("Erro ao abortar multipart upload no cleanup: %s", e)
        raise


def complete_progressive_upload(
    *,
    upload_id: str,
    key: str,
    parts: list[dict],
) -> UploadedAsset:
    """
    Complete a multipart upload by combining all parts.

    Args:
        upload_id: Multipart upload ID
        key: Object key
        parts: List of part info with PartNumber and ETag

    Returns:
        UploadedAsset with final metadata
    """
    client = _get_s3_client()
    bucket_name = settings.s3_bucket_name

    # Complete multipart upload
    response = client.complete_multipart_upload(
        Bucket=bucket_name,
        Key=key,
        UploadId=upload_id,
        MultipartUpload={"Parts": parts},
    )

    # Get object metadata
    head_response = client.head_object(Bucket=bucket_name, Key=key)

    return UploadedAsset(
        bucket=bucket_name,
        key=key,
        content_type=head_response["ContentType"],
        size_bytes=head_response["ContentLength"],
        checksum_sha256=head_response.get("Metadata", {}).get("sha256", ""),
    )
