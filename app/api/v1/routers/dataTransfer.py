from fastapi import HTTPException, UploadFile

from app.services.csvservice import CSVImportService

from fastapi import APIRouter

from app.core.config import settings

router = APIRouter(
    prefix=f"{settings.API_V1_PREFIX}/import-csv",
    tags=["import-csv"],
    responses={
        404: {"description": "User not found"},
        409: {"description": "Username already exists"},
        500: {"description": "Internal server error"}
    }
)

@router.post("/import-csv", response_model=dict)
async def import_csv_files(
    department_file: UploadFile,
    document_type_file: UploadFile,
    generated_id_file: UploadFile,
    approval_paper_file: UploadFile,
    admin_file: UploadFile 
):
    """
    Import CSV files to populate departments, document types, documents, and admins in the database.

    Args:
        department_file: CSV file containing department data (id, name)
        document_type_file: CSV file containing document type data (id, name, departmentid)
        generated_id_file: CSV file containing prefix data (documenttypeid, year, prefix, padding, number)
        approval_paper_file: Optional CSV file containing document data (id, RefNo, Title, etc.)
        admin_file: Optional CSV file containing admin data (id, username)

    Returns:
        A dictionary with processed departments, documents, and admins.
    """
    try:
        service = CSVImportService()

        # Process department-related CSVs
        departments = await service.import_csv(department_file, document_type_file, generated_id_file)
        
        # Process approval paper CSV if provided
        documents = []
        if approval_paper_file:
            documents = await service.import_documents_from_csv(approval_paper_file)

        # Process admin CSV if provided
        admins = []
        if admin_file:
            admins = await service.import_admins_from_csv(admin_file)

        # Prepare response
        response = {
            "departments": [dept.dict() for dept in departments],
            "documents": [doc.dict() for doc in documents] if documents else [],
            "admins": [admin.dict() for admin in admins] if admins else []
        }

        return response

    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing CSV files: {str(e)}")