from typing import Any

from fastapi import HTTPException, UploadFile

from app.services.csvservice import CSVImportService

from fastapi import APIRouter

from app.core.config import settings

router = APIRouter(
    prefix=f"{settings.API_V1_PREFIX}",
    tags=["import-csv"],
    responses={
        404: {"description": "User not found"},
        409: {"description": "Username already exists"},
        500: {"description": "Internal server error"}
    }
)

@router.post("/import-csv-departments", response_model=dict)
async def import_csv_departments(
    department_file: UploadFile,
    document_type_file: UploadFile,
    generated_id_file: UploadFile,
    admin_file: UploadFile 
):
    """
    Import CSV files to populate departments, document types, and admins in the database.

    Args:
        department_file: CSV file containing department data (id, name)
        document_type_file: CSV file containing document type data (id, name, departmentid)
        generated_id_file: CSV file containing prefix data (documenttypeid, year, prefix, padding, number)
        admin_file: Optional CSV file containing admin data (id, username)

    Returns:
        A dictionary with processed departments and admins.
    """
    try:
        service = CSVImportService()

        # Process department-related CSVs
        departments = await service.import_csv(department_file, document_type_file, generated_id_file)

        # Process admin CSV if provided
        admins = []
        if admin_file:
            admins = await service.import_admins_from_csv(admin_file)

        # Prepare response
        response = {
            "departments": [dept for dept in departments],
            "admins": [admin for admin in admins] if admins else []
        }

        return response

    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing CSV files: {str(e)}")


@router.post("/import-csv-documents", response_model=list[Any] | dict[str, int | str])
async def import_csv_documents(
    approval_paper_file: UploadFile
):
    """
    Import CSV file to populate documents in the database.

    Args:
        approval_paper_file: CSV file containing document data (id, RefNo, Title, etc.)

    Returns:
        A list of processed documents.
    """
    try:
        service = CSVImportService()

        # Process approval paper CSV
        documents = await service.import_documents_from_csv(approval_paper_file)

        # Prepare response

        return documents

    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing CSV files: {str(e)}")
