from bson import ObjectId
from typing import Any
from pydantic_core import core_schema
from pydantic import GetCoreSchemaHandler, GetJsonSchemaHandler

class PyObjectId(str):
    """Custom ObjectId class for Pydantic v2"""
    
    @classmethod
    def validate(cls, value: Any, handler) -> ObjectId:
        """Validate and convert a value to ObjectId"""
        if isinstance(value, ObjectId):
            return value
        if isinstance(value, str) and ObjectId.is_valid(value):
            return ObjectId(value)
        raise ValueError("Invalid ObjectId")

    @classmethod
    def __get_pydantic_core_schema__(cls, source_type: Any, handler: GetCoreSchemaHandler) -> core_schema.CoreSchema:
        """Define the core schema for Pydantic v2"""
        return core_schema.with_info_plain_validator_function(
            cls.validate,
            serialization=core_schema.to_string_ser_schema(),
        )

    @classmethod
    def __get_pydantic_json_schema__(cls, core_schema: core_schema.CoreSchema, handler: GetJsonSchemaHandler) -> dict:
        """Generate JSON schema for Pydantic v2"""
        json_schema = handler(core_schema)
        json_schema.update(type="string", format="objectid")
        return json_schema