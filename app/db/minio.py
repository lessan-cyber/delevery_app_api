from miniopy_async import Minio
from miniopy_async.error import S3Error
from fastapi import UploadFile, HTTPException, status
from ..config import settings as s
from ..utils import log 
from PIL import Image,  UnidentifiedImageError
import uuid
from io import BytesIO

minio_client = Minio(
    f"{s.minio_endpoint}:{s.minio_port}",
    access_key=s.minio_access_key,
    secret_key=s.minio_secret_key,
    secure=s.minio_use_ssl
)

async def verify_minio_connection():
    """Verify if the connection to MinIO is established."""
    try:
        buckets = await minio_client.list_buckets()
        if not buckets:
            log.info("No buckets found")            
        else:
            log.info(f"Successfully connected to MinIO Buckets")              
    except S3Error as e:
        log.info(f"Failed to connect to MinIO: {e}")

async def upload_file(file: UploadFile, bucket_name: str, object_name: str):
    """Upload a file to MinIO asynchronously.

    Args:
        file (UploadFile): The file to upload.
        bucket_name (str): The bucket name.
        object_name (str): The object name (path in bucket).

    Returns:
        str: The URL of the uploaded image.
    """
    try:
        image = Image.open(BytesIO(await file.read()))
        image.verify()
    except (UnidentifiedImageError, IOError, SyntaxError):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid image file")
    file.file.seek(0)
    content_type_to_extension = {
        "image/jpeg": ".jpg",
        "image/png": ".png",
        "image/gif": ".gif",
    }
    file_extension = content_type_to_extension.get(file.content_type)
    if not file_extension:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported image type")
    unique_filename = f"{uuid.uuid4()}{file_extension}"
    try:
        # Ensure bucket exists
        found = await minio_client.bucket_exists(bucket_name)
        if not found:
            await minio_client.make_bucket(bucket_name)
        await minio_client.put_object(
            bucket_name,
            unique_filename,
            file.file,
            length=-1,
            part_size=10 * 1024 * 1024,
            content_type=file.content_type,
        )
        log.info(f"Uploaded {object_name} to {bucket_name} as {unique_filename}")
        image_url = f"http://{s.minio_url}/media/{unique_filename}"
        return image_url
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Upload error: {e}")

async def delete_file(bucket_name: str, object_name: str):
    """Delete a file from MinIO asynchronously.

    Args:
        bucket_name (str): The bucket name.
        object_name (str): The object name (path in bucket).
    """
    try:
        await minio_client.remove_object(bucket_name, object_name)
        log.info(f"Deleted {object_name} from {bucket_name}")
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Delete error: {e}")

async def get_file_url(bucket_name: str, object_name: str):
    """Get the URL for a file stored in MinIO.

    Args:
        bucket_name (str): The bucket name.
        object_name (str): The object name (path in bucket).

    Returns:
        str: The URL to access the file.
    """
    return f"http://{s.minio_url}/media/{object_name}"



    