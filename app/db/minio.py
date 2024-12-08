from minio import Minio
from minio.error import S3Error
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
    """
    Vérifie si la connexion à MinIO est établie.
    """
    try:
        buckets = minio_client.list_buckets()
        if not buckets:
            log.info("No buckets found")            
        else:
            log.info(f"Successfully connected to MinIO Buckets")              
    except S3Error as e:
        log.info(f"Failed to connect to MinIO: {e}")
        

async def upload_file(file: UploadFile, bucket_name: str, object_name: str):
    """
    Upload un fichier vers MinIO.
    """
    # Check the content of the file to see if it is a valid image
    try:
        image = Image.open(BytesIO(await file.read()))
        image.verify()  # Verify that it is, in fact, an image
    except (UnidentifiedImageError, IOError, SyntaxError):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid image file")
    
    # Reset the file pointer to the beginning
    file.file.seek(0)
    
    # Determine the file extension based on the content type
    content_type_to_extension = {
        "image/jpeg": ".jpg",
        "image/png": ".png",
        "image/gif": ".gif",
        
    }
    file_extension = content_type_to_extension.get(file.content_type)
    if not file_extension:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported image type")
    
    # Generate a unique image name
    unique_filename = f"{uuid.uuid4()}{file_extension}"
    
    # Put the image in the bucket
    try:
        minio_client.put_object(
            bucket_name,
            unique_filename,
            file.file,
            length=-1,
            part_size=10 * 1024 * 1024,  # Part size
            content_type=file.content_type,
        )
        log.info(f"Uploaded {object_name} to {bucket_name} as {unique_filename}")
        image_url = f"http://{s.minio_url}/media/{unique_filename}"
        return image_url
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Upload error: {e}")