from fastapi import UploadFile, File, HTTPException, status , Depends, APIRouter
from motor.motor_asyncio import AsyncIOMotorGridFSBucket
import traceback

from app.database.DBconnection import MongoDB

router = APIRouter(
    prefix="/attachment",
    tags=["attachment"],
    responses={404: {"description": "Not found"}},
)

async def get_gridfs_bucket():
    return AsyncIOMotorGridFSBucket(MongoDB.get_database())


@router.post("/", status_code=status.HTTP_201_CREATED)
async def upload_attachment(
    file: UploadFile = File(...),
    gridfs_bucket: AsyncIOMotorGridFSBucket = Depends(get_gridfs_bucket)
):
    """Upload a file to GridFS"""
    try:
        print("📁 Receiving file:", file.filename)
        # Validate file type
        allowed_types = [
            "application/pdf",
            "application/msword",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "text/plain",
            "image/jpeg",
            "image/png",
            "image/jpg",
        ]
        if file.content_type not in allowed_types:
            raise HTTPException(status_code=400, detail=f"Invalid file type. Allowed: {', '.join(allowed_types)}")

        # Validate file size
        content = await file.read()
        max_size = 10 * 1024 * 1024  # 10MB
        if len(content) > max_size:
            raise HTTPException(status_code=400, detail="File size exceeds 10MB limit")

        print("✅ File validated. Uploading to GridFS...")

        # Upload to GridFS
        file_id = await gridfs_bucket.upload_from_stream(
            filename=file.filename,
            source=content,
            metadata={"content_type": file.content_type}
        )

        print("✅ Uploaded with ID:", str(file_id))
        return {"file_id": str(file_id)}

    except Exception as e:
        print("❌ Exception occurred:", e)
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"GridFS upload failed: {str(e)}")
