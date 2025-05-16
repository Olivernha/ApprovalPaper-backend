from fastapi import FastAPI

from app.database import MongoDB
from app.routes import adminRoute, documentRoute, departmentRoute
from app.models.departmentModel import DepartmentModel
from app.models.documentModel import DocumentModel
async def lifespan(app: FastAPI):
    """Lifespan event for the application"""
    print("Connecting to MongoDB...")
    await MongoDB.connect_to_database()
    print("Connected to MongoDB.")
    print("Ensuring indexes...")
    await DepartmentModel.ensure_indexes()
    await DocumentModel.ensure_indexes()
    print("Ensured indexes.")
    yield
    await MongoDB.close_database_connection()

app = FastAPI(lifespan=lifespan)
app.include_router(departmentRoute.router)
app.include_router(adminRoute.router)

app.include_router(documentRoute.router)


