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
    usernames = [
        "alvinloh",
        "tracysoo",
        "joanneloh",
        "mildredphua",
        "pricilialee",
        "angys",
        "jasminetan",
        "chuacy"
    ]

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

    department_map = {
        "TPG": [
            "Tender Committee", "Chairman", "PCEO", "VP(IT)",
            "SVP(G) - OLD REFNO", "VP(HCM)", "TBP Project",
            "SVP(BD)", "VP(BD) - OLD REFNO", "Vice President (Generation)/Plant Manager",
            "Senior Vice President (Generation & Utilities)", "Chief Compliance Officer/General Counsel",
            "VP (M&E) / Dy Plant Manager", "Chief Operating Officer"
        ],
        "TPL": [
            "Tender Committee", "Chairman", "PCEO - OLD REF NO", "VP(IT)",
            "SVP(G)", "VP(HCM)", "TBP Project", "SVP(BD)",
            "VP(BD) - OLD REFNO", "Director", "Chief Compliance Officer/General Counsel"
        ],
        "TPU": [
            "Chairman", "Director", "Senior Vice President (Technical Services)",
            "Senior Vice President (Utilities) - OLD REFNO", "Senior Vice President (Project) - OLD REFNO",
            "Chief Financial Officer", "Vice President (Business Development) - OLD REFNO",
            "VP(IT)", "VP(Production) - OLD REFNO", "Vice President (Utilities)/Plant Manager",
            "Senior Vice President (Generation & Utilities)", "Senior Vice President (Business Development)",
            "AVP(JIDP Business)", "Chief Compliance Officer/General Counsel"
        ],
        "SP": ["TPG-CCO", "TPG-COO/SVP(F&T)", "TPG-PCEO"],
        "SSS": ["TPG-CCO", "TPG-COO/SVP(F&T)", "TPG-PCEO"],
        "SSD": ["TPG-CCO", "TPG-COO/SVP(F&T)", "TPG-PCEO"],
        "SGI": ["TPG-CCO", "TPG-COO/SVP(F&T)", "TPG-PCEO"]
    }

    def generate_prefix(dept_code: str, doc_type_name: str) -> str:
        prefix_map = {
            "Tender Committee": "TC",
            "Chairman": "CH",
            "PCEO": "PCEO",
            "PCEO - OLD REF NO": "PCEOOLD",
            "VP(IT)": "VPIT",
            "VP(HCM)": "VPHCM",
            "SVP(G)": "SVPG",
            "SVP(G) - OLD REFNO": "SVPGOLD",
            "SVP(BD)": "SVPBD",
            "VP(BD) - OLD REFNO": "VPBDOLD",
            "TBP Project": "TBP",
            "Director": "DIR",
            "Chief Compliance Officer/General Counsel": "CCO",
            "Chief Financial Officer": "CFO",
            "Chief Operating Officer": "COO",
            "Senior Vice President (Technical Services)": "SVPTS",
            "Senior Vice President (Utilities) - OLD REFNO": "SVPUOLD",
            "Senior Vice President (Project) - OLD REFNO": "SVPPOLD",
            "Vice President (Business Development) - OLD REFNO": "VPBDOLD",
            "VP(Production) - OLD REFNO": "VPPROOLD",
            "Vice President (Utilities)/Plant Manager": "VPUPM",
            "Senior Vice President (Generation & Utilities)": "SVPGU",
            "Senior Vice President (Business Development)": "SVPBD",
            "AVP(JIDP Business)": "AVPJIDP",
            "VP (M&E) / Dy Plant Manager": "VPMEDPM",
            "Vice President (Generation)/Plant Manager": "VPGPM",
            "TPG-CCO": "CCO",
            "TPG-COO/SVP(F&T)": "COOSVPFT",
            "TPG-PCEO": "PCEO"
        }

        prefix_code = prefix_map.get(doc_type_name, ''.join(filter(str.isalnum, doc_type_name)).upper()[:6])
        return f"{dept_code}-{prefix_code}"

    departments = []
    for dept_name, doc_type_names in department_map.items():
        doc_types = []
        for doc_type_name in doc_type_names:
            doc_types.append({
                "_id": ObjectId(),
                "name": doc_type_name,
                "prefix": generate_prefix(dept_name, doc_type_name),
                "padding": 4,
                "created_date": fake.date_time_this_decade()
            })

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
