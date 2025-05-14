from typing import Annotated

from pydantic import BeforeValidator
from .admin import AdminUser
from .documentType import DocumentType , DocumentTypeCreate, DocumentTypeInDB, DocumentTypeResponse, DocumentTypeWithDepartment 
from .department import Department, DepartmentCreate ,DepartmentInDB , DepartmentResponse 
from .base import PyObjectId
 
