from fastapi import HTTPException, status
from app.schemas.admin import AuthInAdminDB
from app.services.admin import AdminService
import logging

logger = logging.getLogger(__name__)

async def get_current_user_from_header() -> AuthInAdminDB:
    username = "hbake1r"  # Replace with actual header extraction in production
    if not username:
        logger.warning("No username provided in X-User-Name header")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication credentials missing",
            headers={"WWW-Authenticate": "X-User-Name required"},
        )

    try:
        admin_service = AdminService()
        user = await admin_service.get_user_by_username(username)
        user_payload = {
            "username": username,
            "is_admin": user is not None
        }
        return AuthInAdminDB(**user_payload)
    except Exception as e:
        logger.error(f"Authentication error: {e}")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication failed")