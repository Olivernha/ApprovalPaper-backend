from bson import ObjectId
from faker import Faker

from motor.motor_asyncio import AsyncIOMotorGridFSBucket
from typing import List, Dict
import random
import io
import logging

from app.core.database import MongoDB
from app.schemas.admin import AdminUser
from app.schemas.base import PyObjectId
from app.schemas.document import DocumentCreate
from app.services.document import DocumentService

# Initialize Faker
fake = Faker()

# Set up logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


async def seed_users() -> List[Dict]:
    """Seed 10 users with usernames"""
    db = MongoDB.get_database()
    users = []
    usernames = set()

    while len(usernames) < 10:
        usernames.add(fake.user_name())
    usernames = list(usernames)

    for username in usernames:
        user = AdminUser(username=username)
        users.append(user.model_dump(by_alias=True))
        users[-1]["_id"] = ObjectId()

    await db["users"].delete_many({})
    await db["users"].insert_many(users)
    logger.info(f"Seeded {len(users)} users")
    return users


async def seed_departments() -> List[Dict]:
    """Seed 20 departments with 20 document types using Faker"""
    db = MongoDB.get_database()

    department_names = set()
    while len(department_names) < 20:
        dept_name = fake.catch_phrase().title() + " Department"
        department_names.add(dept_name)
    department_names = list(department_names)

    document_type_templates = [
        "Proposal", "Report", "Contract", "Specification", "Audit",
        "Manual", "Plan", "Review", "Invoice", "Policy",
        "Agreement", "Budget", "Assessment", "Memo", "Procedure",
        "Schedule", "Analysis", "Forecast", "Guideline", "Summary"
    ]

    departments = []
    for i, dept_name in enumerate(department_names):
        doc_types = [
            {
                "_id": ObjectId(),
                "name": document_type_templates[i],
                "prefix": f"{dept_name[:3].upper()}-{document_type_templates[i][:4].upper()}",
                "padding": 4
            }
        ]
        departments.append({
            "_id": ObjectId(),
            "name": dept_name,
            "document_types": doc_types
        })

    await db["departments"].delete_many({})
    result = await db["departments"].insert_many(departments)
    logger.info(
        f"Seeded {len(departments)} departments with {sum(len(d['document_types']) for d in departments)} document types")
    return departments

async def seed_documents(departments: List[Dict], users: List[Dict]) -> None:
    """Seed 100 documents without attaching dummy PDF files"""
    db = MongoDB.get_database()
    usernames = [user["username"] for user in users]
    document_service = DocumentService()
    docs_per_type = 5
    await db["documents"].delete_many({})
    for dept in departments:
        for doc_type in dept["document_types"]:
            for i in range(docs_per_type):
                title = f"{doc_type['name']} for {fake.bs().title()} {i + 1}"

                # Create document without file
                doc = DocumentCreate(
                    title=title,
                    document_type_id=PyObjectId(doc_type["_id"]),
                    department_id=PyObjectId(dept["_id"]),
                    created_by=random.choice(usernames)
                )
                created_doc = await document_service.create_document(doc)
                logger.info(f"Created document: {created_doc.title} (ID: {created_doc.id})")

    doc_count = await db["documents"].count_documents({})
    logger.info(f"Seeded {doc_count} documents (no files attached)")
    if doc_count < 100:
        logger.warning(f"Seeded only {doc_count} documents, expected 100")

async def seed_data():
    """Seed all data (10 users, 20 departments, 20 document types, 100 documents with GridFS files)"""
    try:
        logger.info("Seeding users...")
        users = await seed_users()

        logger.info("Seeding departments...")
        departments = await seed_departments()

        logger.info("Seeding documents...")
        await seed_documents(departments, users)

        logger.info("Database seeded successfully")
    except Exception as e:
        logger.error(f"Error seeding database: {str(e)}")
        raise