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
    """Seed 20 departments with 20 document types using Faker"""
    db = MongoDB.get_database()
    
    # Generate 20 realistic department names
    department_names = set()
    while len(department_names) < 20:
        dept_name = fake.catch_phrase().title() + " Department"
        department_names.add(dept_name)
    department_names = list(department_names)

    # Define document type templates
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
    print(f"Seeded {len(departments)} departments with {sum(len(d['document_types']) for d in departments)} document types")
    return departments

async def seed_documents(departments: List[Dict]) -> None:
    """Seed 100 documents across departments and document types using Faker"""
    db = MongoDB.get_database()
    
    # Generate realistic user names
    users = [fake.user_name() for _ in range(10)]  # 10 unique users

    # Generate 100 documents (5 per document type, 20 types)
    documents = []
    docs_per_type = 5

    for dept in departments:
        for doc_type in dept["document_types"]:
            for i in range(docs_per_type):
                # Generate a realistic document title
                title = f"{doc_type['name']} for {fake.bs().title()} {i+1}"
                doc = DocumentCreate(
                    title=title,
                    document_type_id=PyObjectId(doc_type["_id"]),
                    department_id=PyObjectId(dept["_id"]),
                    created_by=random.choice(users)
                )
                documents.append(doc)

    await db["documents"].delete_many({})
    
    # Shuffle documents to mix up creation order
    random.shuffle(documents)
    
    # Create documents in bulk using DocumentService
    try:
        created_docs = await DocumentService().bulk_create_documents(documents)
        print(f"Successfully created {len(created_docs)} documents")
    except Exception as e:
        print(f"Error during bulk document creation: {str(e)}")
        raise

async def seed_data():
    """Seed all data (20 departments, 20 document types, 100 documents)"""
    try:
        print("Seeding departments...")
        departments = await seed_departments()
        
        print("Seeding documents...")
        await seed_documents(departments)
        
        # Verify document count
        db = MongoDB.get_database()
        doc_count = await db["documents"].count_documents({})
        print(f"Seeded {doc_count} documents")
        
        if doc_count < 100:
            print(f"Warning: Seeded only {doc_count} documents, expected 100")
        
        print("Database seeded successfully")
    except Exception as e:
        print(f"Error seeding database: {str(e)}")
        raise