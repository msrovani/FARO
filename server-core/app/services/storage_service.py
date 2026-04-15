"""
S3-compatible storage service for FARO assets.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass
from uuid import uuid4

import boto3
from botocore.client import BaseClient
from botocore.exceptions import ClientError

from app.core.config import settings


@dataclass
class UploadedAsset:
    bucket: str
    key: str
    content_type: str
    size_bytes: int
    checksum_sha256: str


_s3_client: BaseClient | None = None


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


def _ensure_bucket_exists(client: BaseClient, bucket_name: str) -> None:
    try:
        client.head_bucket(Bucket=bucket_name)
    except ClientError:
        client.create_bucket(Bucket=bucket_name)


def upload_observation_asset_bytes(
    *,
    observation_id: str,
    asset_type: str,
    original_filename: str,
    content_type: str,
    payload: bytes,
) -> UploadedAsset:
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
