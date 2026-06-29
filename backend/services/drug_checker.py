"""Drug interaction checker."""

import json
import logging

logger = logging.getLogger("health_wallet.drug_checker")

# Known drug interaction database (production would use MongoDB)
DRUG_INTERACTIONS = {
    ("escitalopram", "phenelzine"): {
        "severity": "critical",
        "description": "SSRI + MAOI combination can cause serotonin syndrome, a potentially life-threatening condition.",
        "recommendation": "NEVER combine these medications. Allow at least 14 days washout between switching.",
    },
    ("escitalopram", "tramadol"): {
        "severity": "high",
        "description": "Increased risk of serotonin syndrome and seizures when combining SSRI with tramadol.",
        "recommendation": "Avoid combination. If necessary, monitor closely for serotonin symptoms.",
    },
    ("escitalopram", "ibuprofen"): {
        "severity": "moderate",
        "description": "SSRIs may increase bleeding risk when combined with NSAIDs.",
        "recommendation": "Use with caution. Consider gastroprotective therapy if long-term use needed.",
    },
    ("metformin", "alcohol"): {
        "severity": "high",
        "description": "Alcohol increases risk of lactic acidosis with metformin.",
        "recommendation": "Limit alcohol consumption. Avoid binge drinking.",
    },
    ("lisinopril", "potassium"): {
        "severity": "moderate",
        "description": "ACE inhibitors can increase potassium levels. Supplementation may cause hyperkalemia.",
        "recommendation": "Monitor potassium levels regularly if supplements are needed.",
    },
    ("warfarin", "aspirin"): {
        "severity": "high",
        "description": "Greatly increased bleeding risk when combining anticoagulant with antiplatelet.",
        "recommendation": "Only combine under close medical supervision with regular INR monitoring.",
    },
    ("atorvastatin", "grapefruit"): {
        "severity": "moderate",
        "description": "Grapefruit inhibits CYP3A4, increasing statin blood levels and risk of myopathy.",
        "recommendation": "Avoid large amounts of grapefruit or grapefruit juice.",
    },
    ("escitalopram", "methylphenidate"): {
        "severity": "moderate",
        "description": "Theoretical risk of serotonin syndrome, though generally well-tolerated.",
        "recommendation": "Can be used together with monitoring. Report unusual symptoms.",
    },
}


class DrugChecker:
    """Check drug-drug interactions."""

    def check(self, drug_a: str, drug_b: str) -> dict | None:
        """Check interaction between two drugs."""
        a, b = drug_a.lower().strip(), drug_b.lower().strip()

        # Check both orderings
        result = DRUG_INTERACTIONS.get((a, b)) or DRUG_INTERACTIONS.get((b, a))
        if result:
            return {
                "drug_a": drug_a,
                "drug_b": drug_b,
                **result,
            }
        return None

    def check_multiple(self, medications: list[str]) -> list[dict]:
        """Check all pairwise interactions for a list of medications."""
        interactions = []
        meds = [m.lower().strip() for m in medications if m.strip()]

        for i in range(len(meds)):
            for j in range(i + 1, len(meds)):
                result = self.check(meds[i], meds[j])
                if result:
                    interactions.append(result)

        return interactions

    async def check_from_text(self, text: str) -> list[dict]:
        """Extract medications from text and check interactions."""
        known_drugs = [
            "escitalopram", "phenelzine", "tramadol", "ibuprofen", "metformin",
            "lisinopril", "warfarin", "aspirin", "atorvastatin", "methylphenidate",
            "omeprazole", "loratadine", "amoxicillin", "sertraline", "fluoxetine",
        ]
        text_lower = text.lower()
        found = [d for d in known_drugs if d in text_lower]

        if len(found) >= 2:
            return self.check_multiple(found)
        return []


drug_checker = DrugChecker()
