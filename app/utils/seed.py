from datetime import datetime
from bson import ObjectId
from faker import Faker
from app.database import MongoDB
from app.schema.document import DocumentCreate
from app.schema.base import PyObjectId
from app.services.documentService import DocumentService
from typing import List, Dict
import random

# Initialize Faker
fake = Faker()

async def seed_departments() -> List[Dict]:
    """Seed 20 departments with 20 document types each using Faker"""
    db = MongoDB.get_database()

    # Generate 20 unique department names
    department_names = set()
    while len(department_names) < 20:
        dept_name = fake.catch_phrase().title() + " Department"
        department_names.add(dept_name)
    department_names = list(department_names)

    # Base document type templates
    base_templates = [
        "Proposal", "Report", "Contract", "Specification", "Audit",
        "Manual", "Plan", "Review", "Invoice", "Policy",
        "Agreement", "Budget", "Assessment", "Memo", "Procedure",
        "Schedule", "Analysis", "Forecast", "Guideline", "Summary"
    ]

    document_type_templates = base_templates[:20]

    departments = []
    for dept_name in department_names:
        doc_types = []
        for doc_type in document_type_templates:
            prefix = f"{dept_name[:3].upper()}-{doc_type[:4].upper()}-{random.randint(1000,9999)}"
            doc_types.append({
                "_id": ObjectId(),
                "name": doc_type,
                "prefix": prefix,
                "padding": 4
            })

        departments.append({
            "_id": ObjectId(),
            "name": dept_name,
            "document_types": doc_types
        })

    await db["departments"].delete_many({})
    await db["departments"].insert_many(departments)

    total_doc_types = sum(len(d["document_types"]) for d in departments)
    print(f"Seeded {len(departments)} departments with {total_doc_types} document types")
    return departments


async def seed_documents(departments: List[Dict]) -> None:
    """Seed 100 documents across departments and document types using Faker"""
    db = MongoDB.get_database()
    users = [fake.user_name() for _ in range(10)]  # 10 unique users

    documents = []
    total_target = 100
    all_doc_types = [(dept["_id"], dt["_id"], dt["name"]) for dept in departments for dt in dept["document_types"]]
    random.shuffle(all_doc_types)

    i = 0
    while len(documents) < total_target:
        for dept_id, doc_type_id, doc_type_name in all_doc_types:
            if len(documents) >= total_target:
                break
            title = f"{doc_type_name} for {fake.bs().title()} {i+1}"
            doc = DocumentCreate(
                title=title,
                document_type_id=PyObjectId(doc_type_id),
                department_id=PyObjectId(dept_id),
                created_by=random.choice(users)
            )
            documents.append(doc)
            i += 1

    await db["documents"].delete_many({})

    try:
        created_docs = await DocumentService().bulk_create_documents(documents)
        print(f"Successfully created {len(created_docs)} documents")
    except Exception as e:
        print(f"Error during bulk document creation: {str(e)}")
        raise


async def seed_data():
    """Seed departments and documents"""
    try:
        print("Seeding departments...")
        departments = await seed_departments()

        print("Seeding documents...")
        await seed_documents(departments)

        db = MongoDB.get_database()
        doc_count = await db["documents"].count_documents({})
        print(f" Seeded {doc_count} documents")

        if doc_count < 100:
            print(f" Warning: Seeded only {doc_count} documents, expected 100")

        print("Database seeded successfully")
    except Exception as e:
        print(f" Error seeding database: {str(e)}")
        raise
