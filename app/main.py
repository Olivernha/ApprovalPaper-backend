from fastapi import FastAPI

from app.database import MongoDB
from app.services import DocumentTypeService
from app.routes import adminRoute, documentRoute, documentTypeRoute , departmentRoute
async def lifespan(app: FastAPI):
    """Lifespan event for the application"""
    print("Connecting to MongoDB...")
    await MongoDB.connect_to_database()
    await DocumentTypeService.ensure_indexes()
    print("Connected to MongoDB.")
    yield
    await MongoDB.close_database_connection()

app = FastAPI(lifespan=lifespan)


app.include_router(adminRoute.router)
app.include_router(documentTypeRoute.router)
app.include_router(departmentRoute.router)
app.include_router(documentRoute.router)


