import os
import aiofiles
from fastapi import UploadFile, HTTPException, status
from pathlib import Path

import re

from app.core.config import Settings

settings = Settings()

class FileStorageService:
    def __init__(self):
        # Resolve and create base storage directory
        self.storage_path = Path(settings.STORAGE_PATH).resolve()
        self.storage_type = settings.STORAGE_TYPE
        if self.storage_type == "local":
            os.makedirs(self.storage_path, exist_ok=True)

    def _sanitize_name(self, name: str) -> str:
        """Sanitize department name or ref_no for filesystem compatibility."""
        # Replace non-alphanumeric characters (except dots, underscores, hyphens) with underscores
        sanitized = re.sub(r'[^a-zA-Z0-9._-]', '_', name.strip())
        # Remove leading/trailing underscores and multiple underscores
        sanitized = re.sub(r'_+', '_', sanitized).strip('_')
        if not sanitized:
            raise HTTPException(status_code=400, detail="Invalid name for filesystem")
        return sanitized

    async def save_file(self, file: UploadFile, department_name: str, ref_no: str, created_date: str) -> str:
        """Save the uploaded file to department_name/year/ref_no.extension and return the relative path."""
        if self.storage_type != "local":
            raise HTTPException(status_code=400, detail="Only local storage is supported in this configuration")

        # Validate inputs
        if not department_name or not ref_no or not created_date:
            raise HTTPException(status_code=400, detail="Department name, reference number, and created date are required")

        # Sanitize department name and ref_no
        sanitized_dept_name = self._sanitize_name(department_name)
        sanitized_ref_no = self._sanitize_name(ref_no)

        # Extract year from created_date (assuming ISO format, e.g., "2025-05-15T13:00:00Z")
        try:
            year = created_date.split("-")[0]
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid created_date format")

        # Get file extension
        file_extension = os.path.splitext(file.filename)[1]
        if not file_extension:
            raise HTTPException(status_code=400, detail="File must have an extension")

        filename = f"{sanitized_ref_no}{file_extension}"

        # Build folder structure: STORAGE_PATH/department_name/year/
        department_path = self.storage_path / sanitized_dept_name / year
        os.makedirs(department_path, exist_ok=True)

        # Full file path
        file_path = department_path / filename

        try:
            async with aiofiles.open(file_path, "wb") as out_file:
                content = await file.read()
                await out_file.write(content)
            # Return relative path from storage_path
            return str(file_path.relative_to(self.storage_path))
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to save file: {str(e)}"
            )

    async def delete_file(self, relative_path: str) -> None:
        """Delete a file from storage."""
        if self.storage_type != "local":
            raise HTTPException(status_code=400, detail="Only local storage is supported in this configuration")

        file_path = self.storage_path / relative_path
        try:
            if file_path.exists():
                os.remove(file_path)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to delete file: {str(e)}"
            )

    def get_file_path(self, relative_path: str) -> Path:
        """Get the absolute path for a stored file."""
        return self.storage_path / relative_path