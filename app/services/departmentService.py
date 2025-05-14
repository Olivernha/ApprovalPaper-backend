from app.database import MongoDB
from app.schema import DepartmentCreate

class DepartmentService:
    def __init__(self, collection_name: str = "departments"):
        self.collection_name = collection_name

    def get_collection(self):
        return MongoDB.get_database()[self.collection_name]
    
    
    async def create_department(self, department_data : DepartmentCreate):
        """Create a new department in the database."""
        # Check if the department already exists

        existing_department = await self.get_collection().find_one({"name": department_data.name})
        if existing_department:
            return {"message": "Department already exists", "data": existing_department}
        
        # Insert the new department into the database
        await self.get_collection().insert_one(department_data.model_dump())
        return {"message": "Department created successfully", "data": department_data}