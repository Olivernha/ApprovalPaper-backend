from bson import ObjectId
from fastapi import HTTPException, status, UploadFile
from motor.motor_asyncio import AsyncIOMotorGridFSBucket
import logging

logger = logging.getLogger(__name__)

def to_object_id(value: str) -> ObjectId:
    try:
        return ObjectId(value)
    except Exception:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid ObjectId format")

async def upload_file_to_gridfs(file: UploadFile, gridfs_bucket: AsyncIOMotorGridFSBucket) -> str:
    allowed_types = [
        "application/pdf",
        "application/msword",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "text/plain",
        "image/jpeg",
        "image/png",
        "image/jpg",
    ]
    max_size = 10 * 1024 * 1024

    if file.content_type not in allowed_types:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid file type. Allowed: {', '.join(allowed_types)}")

    content = await file.read()
    if len(content) > max_size:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="File size exceeds 10MB limit")

    try:
        file_id = await gridfs_bucket.upload_from_stream(
            filename=file.filename,
            source=content,
            metadata={"content_type": file.content_type}
        )
        return str(file_id)
    except Exception as e:
        logger.error(f"GridFS upload failed: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"GridFS upload failed: {str(e)}")