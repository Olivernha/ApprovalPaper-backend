from bson import ObjectId
from faker import Faker
from typing import List, Dict
import random
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

    def generate_doc_type(name_prefix, i, dept_name):
        return {
            "_id": ObjectId(),
            "name": f"{name_prefix} {i+1}",
            "prefix": f"{dept_name[:3].upper()}-{name_prefix[:4].upper()}{i+1}",
            "padding": 4,
            "created_date": fake.date_time_this_decade()
        }

    departments = []
    for i, dept_name in enumerate(department_names):
        if i == 0:  # First department gets 8 document types
            doc_types = [
                generate_doc_type(document_type_templates[j % len(document_type_templates)], j, dept_name)
                for j in range(8)
            ]
        else:  # Others get 1 document type
            doc_types = [generate_doc_type(document_type_templates[i % len(document_type_templates)], 0, dept_name)]

        departments.append({
            "_id": ObjectId(),
            "name": dept_name,
            "document_types": doc_types,
            "created_date": fake.date_time_this_decade()
        })

    await db["departments"].delete_many({})
    await db["departments"].insert_many(departments)
    logger.info(
        f"Seeded {len(departments)} departments with {sum(len(d['document_types']) for d in departments)} document types"
    )
    return departments


async def seed_documents(departments: List[Dict], users: List[Dict]) -> None:
    db = MongoDB.get_database()
    usernames = [user["username"] for user in users]
    document_service = DocumentService()
    await db["documents"].delete_many({})
    await db["sequence_counters"].delete_many({})

    doc_type_with_100_created = False

    for dept in departments:
        for doc_type in dept["document_types"]:
            num_docs = 100 if not doc_type_with_100_created else 5
            doc_type_with_100_created = True if num_docs == 100 else doc_type_with_100_created

            for i in range(num_docs):
                title = f"{doc_type['name']} for {fake.bs().title()} {i + 1}"

                doc = DocumentCreate(
                    title=title,
                    document_type_id=PyObjectId(doc_type["_id"]),
                    department_id=PyObjectId(dept["_id"]),
                    created_by=random.choice(usernames)
                )
                created_doc = await document_service.create_document(doc)
                logger.info(f"Created document: {created_doc.title} (ID: {created_doc.id})")

    doc_count = await db["documents"].count_documents({})
    logger.info(f"Seeded {doc_count} documents")
    if doc_count < 100:
        logger.warning(f"Expected at least 100 documents, but got {doc_count}")


async def seed_data():
    """Seed all data (10 users, 20 departments, 1 department with 8 document types, 1 document type with 100 documents)"""
    try:
        logger.info("Seeding users...")
        users = await seed_users()

        logger.info("Seeding departments...")
        departments = await seed_departments()

        logger.info("Seeding documents...")
        await seed_documents(departments, users)

        logger.info("✅ Database seeded successfully")
    except Exception as e:
        logger.error(f"❌ Error seeding database: {str(e)}")
        raise
