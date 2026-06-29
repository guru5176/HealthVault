"""Health Wallet API routes."""

from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel

from backend.services.vault_service import vault_service
from backend.services.ocr_service import ocr_service
from backend.ml.model_server import model_server

router = APIRouter(prefix="/api/vault", tags=["vault"])


@router.post("/upload-prescription")
async def upload_prescription(file: UploadFile = File(...)):
    """Upload a prescription image, run OCR, structure the output via local LLM, and save it to the vault."""
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Uploaded file must be an image")

    try:
        content_bytes = await file.read()
        
        # Run OCR
        ocr_text = ocr_service.extract_text(content_bytes)
        if not ocr_text.strip():
            raise HTTPException(status_code=422, detail="No readable text detected in the prescription image")
        
        # Structure the OCR output using the local LLM
        prompt = (
            "You are a clinical AI assistant. You have been given the raw text extracted via OCR "
            "from a handwritten prescription. Your task is to correct any OCR transcription errors, "
            "clean spelling mistakes, and format the prescriptions into a structured medical record.\n\n"
            "Raw OCR Text:\n"
            f"\"\"\"\n{ocr_text}\n\"\"\"\n\n"
            "Please format the output exactly as structured Markdown. Follow this layout:\n\n"
            "# Prescription Record\n\n"
            "## Clinical Summary\n"
            "[Provide a brief explanation of the medical intent/condition, e.g. antibiotic treatment]\n\n"
            "## Prescribed Medications\n"
            "- **[Medication Name]** [Dosage, e.g., 500mg] - [Frequency, e.g., 3x daily] - [Duration, e.g., 7 days]\n"
            "  * Instructions: [Special instructions, e.g., take with food]\n\n"
            "## Safety & Clinical Notes\n"
            "- Note: Transcribed locally using OCR. Please cross-reference with the original image before administration.\n"
        )
        
        structured_markdown = await model_server.generate(
            prompt=prompt,
            system_prompt="You are a medical assistant formatting prescription texts.",
            temperature=0.2,
            max_tokens=1024,
        )
        
        # Save to vault
        # Generate title from the first medication or generic
        title = "Prescription Scan"
        for line in structured_markdown.split("\n"):
            if line.strip().startswith("- **"):
                import re
                match = re.search(r'\*\*(.*?)\*\*', line)
                if match:
                    title = f"Prescription - {match.group(1)}"
                    break
        
        record = vault_service.create_record(
            title=title,
            content=structured_markdown,
            category="medications"
        )
        
        # Persist prescription to MongoDB for durable cloud storage
        mongo_saved = vault_service.save_prescription_to_mongo(
            title=title,
            content=structured_markdown,
            ocr_raw=ocr_text,
            record_id=record["id"],
        )
        
        return {
            "message": "Prescription processed successfully",
            "ocr_raw": ocr_text,
            "structured": structured_markdown,
            "record": record,
            "mongo_saved": mongo_saved,
        }
    except HTTPException:
        raise
    except Exception as e:
        import logging
        logging.getLogger("health_wallet.vault").error(f"Upload prescription failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")



class CreateRecordRequest(BaseModel):
    title: str
    content: str
    category: str = "general"


@router.get("/records")
async def list_records(category: str = None):
    """List all health records, optionally filtered by category."""
    records = vault_service.list_records()
    if category:
        records = [r for r in records if r["category"] == category]
    return {"records": records, "count": len(records)}


@router.get("/records/{record_id}")
async def get_record(record_id: str):
    """Get a single health record by ID."""
    record = vault_service.get_record(record_id)
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")
    return record


@router.post("/records")
async def create_record(req: CreateRecordRequest):
    """Create a new health record."""
    record = vault_service.create_record(req.title, req.content, req.category)
    return {"message": "Record created", "record": record}


@router.get("/search")
async def search_records(q: str):
    """Full-text search across all records."""
    if not q or len(q) < 2:
        raise HTTPException(status_code=400, detail="Query must be at least 2 characters")
    results = vault_service.search_records(q)
    return {"query": q, "results": results, "count": len(results)}
