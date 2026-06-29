"""Seed MongoDB Atlas with provider and drug interaction data."""

import logging
from backend.db.mongo import get_db

logger = logging.getLogger("health_wallet.seed")

PROVIDERS = [
    {"name": "Dr. Sarah Chen", "specialty": "Endocrinology", "city": "San Francisco",
     "hospital": "UCSF Medical Center", "rating": 4.8, "accepting_new": True,
     "conditions": ["diabetes", "thyroid disorders", "metabolic syndrome", "elevated A1C"],
     "phone": "+1-415-555-0101", "insurance": ["Aetna", "Blue Cross", "Medicare"]},

    {"name": "Dr. Raj Patel", "specialty": "Endocrinology", "city": "San Francisco",
     "hospital": "Stanford Health Care", "rating": 4.9, "accepting_new": True,
     "conditions": ["type 2 diabetes", "adrenal disorders", "osteoporosis"],
     "phone": "+1-650-555-0102", "insurance": ["United", "Cigna", "Aetna"]},

    {"name": "Dr. Maria Reyes", "specialty": "Psychiatry", "city": "Manila",
     "hospital": "St. Luke's Medical Center", "rating": 4.7, "accepting_new": True,
     "conditions": ["anxiety", "depression", "ADHD", "OCD"],
     "phone": "+63-2-555-0103", "insurance": ["PhilHealth", "Maxicare"]},

    {"name": "Dr. James Liu", "specialty": "Psychiatry", "city": "San Francisco",
     "hospital": "Kaiser Permanente", "rating": 4.6, "accepting_new": True,
     "conditions": ["anxiety disorders", "mood disorders", "PTSD"],
     "phone": "+1-415-555-0104", "insurance": ["Kaiser", "Blue Shield"]},

    {"name": "Dr. Michael Torres", "specialty": "Cardiology", "city": "San Francisco",
     "hospital": "UCSF Medical Center", "rating": 4.9, "accepting_new": False,
     "conditions": ["hypertension", "heart failure", "arrhythmia", "coronary artery disease"],
     "phone": "+1-415-555-0105", "insurance": ["Aetna", "Blue Cross", "Medicare", "Medicaid"]},

    {"name": "Dr. Emily Nakamura", "specialty": "Dermatology", "city": "San Francisco",
     "hospital": "Pacific Dermatology", "rating": 4.8, "accepting_new": True,
     "conditions": ["eczema", "psoriasis", "skin cancer screening", "acne"],
     "phone": "+1-415-555-0106", "insurance": ["United", "Aetna", "Blue Cross"]},

    {"name": "Dr. Wei Zhang", "specialty": "Nephrology", "city": "Taipei",
     "hospital": "National Taiwan University Hospital", "rating": 4.9, "accepting_new": True,
     "conditions": ["chronic kidney disease", "dialysis", "kidney stones", "elevated creatinine"],
     "phone": "+886-2-555-0107", "insurance": ["NHI Taiwan"]},

    {"name": "Dr. Priya Sharma", "specialty": "Neurology", "city": "Mumbai",
     "hospital": "Hinduja Hospital", "rating": 4.7, "accepting_new": True,
     "conditions": ["migraines", "epilepsy", "neuropathy", "multiple sclerosis"],
     "phone": "+91-22-555-0108", "insurance": ["Star Health", "HDFC Ergo"]},

    {"name": "Dr. Anna Kim", "specialty": "Ophthalmology", "city": "San Francisco",
     "hospital": "Pacific Vision Institute", "rating": 4.8, "accepting_new": True,
     "conditions": ["myopia", "glaucoma", "cataracts", "retinal disorders"],
     "phone": "+1-415-555-0109", "insurance": ["VSP", "EyeMed", "Aetna"]},

    {"name": "Dr. Carlos Mendoza", "specialty": "Internal Medicine", "city": "San Francisco",
     "hospital": "Sutter Health", "rating": 4.5, "accepting_new": True,
     "conditions": ["general checkup", "preventive care", "chronic disease management"],
     "phone": "+1-415-555-0110", "insurance": ["Aetna", "Blue Cross", "United", "Cigna"]},
]


def seed_database():
    """Seed MongoDB with sample data. Idempotent."""
    db = get_db()
    if db is None:
        logger.warning("Cannot seed — no database connection")
        return False

    # Seed providers
    providers_col = db["providers"]
    if providers_col.count_documents({}) == 0:
        providers_col.insert_many(PROVIDERS)
        logger.info(f"Seeded {len(PROVIDERS)} providers")
    else:
        logger.info(f"Providers already seeded ({providers_col.count_documents({})} docs)")

    # Create indexes
    providers_col.create_index("specialty")
    providers_col.create_index("city")
    providers_col.create_index([("specialty", 1), ("city", 1)])

    return True


if __name__ == "__main__":
    import sys
    sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent.parent.parent))
    from dotenv import load_dotenv
    load_dotenv()
    seed_database()
    print("✅ Database seeded successfully")
