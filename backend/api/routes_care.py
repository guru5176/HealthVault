"""Care Router API routes."""

import json
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from backend.services.care_router import care_router_service
from backend.services.drug_checker import drug_checker

router = APIRouter(prefix="/api/care", tags=["care-router"])


class AnonymizeRequest(BaseModel):
    patient_data: str


class RouteRequest(BaseModel):
    clinical_intent: str
    city: str = ""


class DrugCheckRequest(BaseModel):
    medications: list[str]


@router.post("/anonymize")
async def anonymize(req: AnonymizeRequest):
    """Strip PII from patient data."""
    if not req.patient_data.strip():
        raise HTTPException(status_code=400, detail="Patient data cannot be empty")
    try:
        anonymized = await care_router_service.anonymize(req.patient_data)
        return {
            "original_length": len(req.patient_data),
            "anonymized": anonymized,
            "anonymized_length": len(anonymized),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/route")
async def route_patient(req: RouteRequest):
    """Route patient to appropriate specialist."""
    if not req.clinical_intent.strip():
        raise HTTPException(status_code=400, detail="Clinical intent cannot be empty")
    try:
        result = await care_router_service.route(req.clinical_intent, req.city)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/drug-check")
async def check_drugs(req: DrugCheckRequest):
    """Check drug interactions for a list of medications."""
    if len(req.medications) < 2:
        raise HTTPException(status_code=400, detail="Need at least 2 medications to check")
    interactions = drug_checker.check_multiple(req.medications)
    return {
        "medications": req.medications,
        "interactions": interactions,
        "interaction_count": len(interactions),
        "has_critical": any(i["severity"] == "critical" for i in interactions),
    }
