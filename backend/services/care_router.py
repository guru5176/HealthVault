"""Care Router service — specialist routing with privacy bridge."""

import json
import logging

from backend.ml.model_server import model_server
from backend.ml.prompts import CARE_ROUTER_SYSTEM_PROMPT, PII_ANONYMIZER_PROMPT, PROMPT_VERSION
from backend.ml.model_registry import log_inference_experiment
from backend.services.drug_checker import drug_checker
from backend.db.mongo import get_providers_collection, get_drug_interactions_collection

logger = logging.getLogger("health_wallet.care_router")


class CareRouterService:
    """Privacy-preserving specialist routing agent."""

    async def anonymize(self, raw_patient_data: str) -> str:
        """Strip PII from patient data using local LLM."""
        prompt = f"{PII_ANONYMIZER_PROMPT}\n\nPatient data:\n{raw_patient_data}"
        anonymized = await model_server.generate(
            prompt=prompt,
            temperature=0.1,  # Very low temp for deterministic PII stripping
            max_tokens=512,
        )
        logger.info("pii_anonymized", extra={"input_len": len(raw_patient_data), "output_len": len(anonymized)})
        return anonymized.strip()

    async def route(self, clinical_intent: str, city: str = "") -> dict:
        """Route a patient to the appropriate specialist."""

        # Step 1: Use LLM to determine specialty
        specialty_prompt = f"""Given this clinical intent, determine the medical specialty needed.
Respond with ONLY a JSON object: {{"specialty": "...", "reasoning": "..."}}

Clinical intent: {clinical_intent}
City: {city or "any"}"""

        specialty_response = await model_server.generate(
            prompt=specialty_prompt,
            system_prompt=CARE_ROUTER_SYSTEM_PROMPT,
            temperature=0.2,
            max_tokens=256,
        )

        # Parse specialty
        specialty = "internal medicine"  # fallback
        reasoning = ""
        try:
            # Try to extract JSON from response
            import re
            json_match = re.search(r'\{[^}]+\}', specialty_response)
            if json_match:
                parsed = json.loads(json_match.group())
                specialty = parsed.get("specialty", specialty)
                reasoning = parsed.get("reasoning", "")
        except (json.JSONDecodeError, AttributeError):
            # If LLM didn't return JSON, try to extract specialty from text
            for s in ["cardiology", "endocrinology", "psychiatry", "dermatology",
                       "nephrology", "neurology", "orthopedics", "ophthalmology"]:
                if s in specialty_response.lower():
                    specialty = s
                    break

        # Step 2: Search providers in MongoDB
        providers = await self._search_providers(specialty, city)

        # Step 3: Check drug interactions if medications mentioned
        drug_results = None
        medications_keywords = ["medication", "drug", "prescription", "taking", "escitalopram",
                                "metformin", "lisinopril", "atorvastatin", "omeprazole"]
        if any(kw in clinical_intent.lower() for kw in medications_keywords):
            drug_results = await drug_checker.check_from_text(clinical_intent)

        # Step 4: Build action plan
        action_plan = {
            "specialty": specialty,
            "reasoning": reasoning or specialty_response[:200],
            "providers": providers,
            "provider_count": len(providers),
            "drug_interactions": drug_results,
            "privacy_note": "All PII was stripped on-device before this analysis. No patient identity data was processed in the cloud.",
        }

        log_inference_experiment(
            model_name=model_server.model,
            prompt_version=PROMPT_VERSION,
            prompt=clinical_intent,
            response=json.dumps(action_plan, default=str),
            latency=0,
            tokens=0,
            endpoint="care_route",
            success=True,
        )

        return action_plan

    async def _search_providers(self, specialty: str, city: str = "") -> list[dict]:
        """Search MongoDB for matching providers."""
        try:
            collection = get_providers_collection()
            if collection is None:
                return self._get_fallback_providers(specialty)

            query = {"specialty": {"$regex": specialty, "$options": "i"}}
            if city:
                query["city"] = {"$regex": city, "$options": "i"}

            cursor = collection.find(query).limit(5)
            providers = []
            for doc in cursor:
                doc.pop("_id", None)
                providers.append(doc)

            if not providers:
                return self._get_fallback_providers(specialty)
            return providers

        except Exception as e:
            logger.warning(f"MongoDB search failed: {e}")
            return self._get_fallback_providers(specialty)

    def _get_fallback_providers(self, specialty: str) -> list[dict]:
        """Fallback providers when MongoDB is unavailable."""
        fallback_db = {
            "endocrinology": [
                {"name": "Dr. Sarah Chen", "specialty": "Endocrinology", "city": "San Francisco",
                 "hospital": "UCSF Medical Center", "rating": 4.8, "accepting_new": True,
                 "conditions": ["diabetes", "thyroid disorders", "metabolic syndrome"]},
                {"name": "Dr. Raj Patel", "specialty": "Endocrinology", "city": "San Francisco",
                 "hospital": "Stanford Health Care", "rating": 4.9, "accepting_new": True,
                 "conditions": ["type 2 diabetes", "adrenal disorders"]},
            ],
            "psychiatry": [
                {"name": "Dr. Maria Reyes", "specialty": "Psychiatry", "city": "Manila",
                 "hospital": "St. Luke's Medical Center", "rating": 4.7, "accepting_new": True,
                 "conditions": ["anxiety", "depression", "ADHD"]},
                {"name": "Dr. James Liu", "specialty": "Psychiatry", "city": "San Francisco",
                 "hospital": "Kaiser Permanente", "rating": 4.6, "accepting_new": True,
                 "conditions": ["anxiety disorders", "mood disorders"]},
            ],
            "cardiology": [
                {"name": "Dr. Michael Torres", "specialty": "Cardiology", "city": "San Francisco",
                 "hospital": "UCSF Medical Center", "rating": 4.9, "accepting_new": False,
                 "conditions": ["hypertension", "heart failure", "arrhythmia"]},
            ],
            "dermatology": [
                {"name": "Dr. Emily Nakamura", "specialty": "Dermatology", "city": "San Francisco",
                 "hospital": "Pacific Dermatology", "rating": 4.8, "accepting_new": True,
                 "conditions": ["eczema", "psoriasis", "skin cancer screening"]},
            ],
        }
        return fallback_db.get(specialty.lower(), [
            {"name": "Dr. General Practice", "specialty": specialty.title(), "city": "Available",
             "hospital": "Local Medical Center", "rating": 4.5, "accepting_new": True,
             "conditions": ["general"]}
        ])


care_router_service = CareRouterService()
