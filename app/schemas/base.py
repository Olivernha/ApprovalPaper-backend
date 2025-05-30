from bson import ObjectId
from pydantic import BaseModel

class PyObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, value, validation_info=None):
        if not (
            value
            and (isinstance(value, ObjectId) or isinstance(value, str))
            and ObjectId().is_valid(value)
        ):
            raise ValueError("Not a valid ObjectId")
        return value

    @classmethod
    def __get_pydantic_json_schema__(cls, field_schema, handler):
        return {"type": "string", "examples": ["66488b368a6801e71d70dfe9"]}