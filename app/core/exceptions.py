from fastapi import HTTPException, status
from bson.errors import InvalidId
import logging

logger = logging.getLogger(__name__)

def handle_service_exception(e: Exception) -> None:
    if isinstance(e, HTTPException):
        raise e
    if isinstance(e, InvalidId):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid ObjectId format")
    logger.error(f"Unexpected error: {str(e)}")
    raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))