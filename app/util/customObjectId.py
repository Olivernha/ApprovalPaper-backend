from bson import ObjectId
from typing import Any

class PyObjectId(str):
    """Custom ObjectId class for Pydantic"""
    
    @classmethod
    def __get_validators__(cls):
        """Pydantic validators for ObjectId"""
        yield cls.validate

    @classmethod
    def validate(cls, v: Any , field) -> ObjectId:
        """Validate and convert a string to ObjectId"""
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return ObjectId(v)

    @classmethod
    def __get_pydantic_json_schema__(cls, field_schema):
        """Modify the schema to treat ObjectId as a string"""
        field_schema.update(type="string")