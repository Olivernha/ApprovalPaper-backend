# app/services/user_service.py
from datetime import datetime
from typing import List, Optional
from bson import ObjectId


from ..database.DBconnection import MongoDB




class UserService:
    collection_name = "users"
    
    @staticmethod
    def get_collection():
        return MongoDB.get_database()[UserService.collection_name]
    