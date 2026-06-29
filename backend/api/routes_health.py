"""Health and monitoring API routes — MLOps dashboard data."""

from fastapi import APIRouter
from pydantic import BaseModel

from backend.ml.model_server import model_server
from backend.ml.monitor import monitor
from backend.ml.model_registry import get_experiment_history
from backend.db.mongo import check_connection as check_mongo

router = APIRouter(prefix="/api/health", tags=["health"])


class SwitchModelRequest(BaseModel):
    model: str


@router.get("")
async def health_check():
    """Overall system health check."""
    ollama_status = await model_server.health_check()
    mongo_status = check_mongo()

    overall = "healthy"
    if ollama_status.get("status") != "healthy":
        overall = "degraded"
    if ollama_status.get("status") == "offline":
        overall = "unhealthy"

    return {
        "status": overall,
        "components": {
            "ollama": ollama_status,
            "mongodb": mongo_status,
        },
    }


@router.get("/metrics")
async def get_metrics():
    """Get inference metrics for monitoring dashboard."""
    return monitor.get_metrics()


@router.get("/models")
async def list_models():
    """List available Ollama models."""
    models = await model_server.list_models()
    return {
        "current_model": model_server.model,
        "available_models": models,
        "gpu": "NVIDIA RTX 4060 (8GB VRAM)",
    }


@router.post("/switch-model")
async def switch_model(req: SwitchModelRequest):
    """Switch the active Ollama model at runtime."""
    old_model = model_server.model
    model_server.model = req.model

    # Verify the new model is accessible
    health = await model_server.health_check()
    if health.get("status") in ("healthy", "model_missing"):
        return {
            "status": "ok",
            "previous_model": old_model,
            "current_model": req.model,
            "ollama_status": health.get("status"),
        }
    else:
        # Revert on failure
        model_server.model = old_model
        return {
            "status": "error",
            "message": f"Model '{req.model}' is not available. Reverted to '{old_model}'.",
            "ollama_status": health.get("status"),
        }


@router.get("/model-stats")
async def model_stats():
    """Per-model inference statistics."""
    return monitor.get_model_stats()


@router.get("/experiments")
async def get_experiments(limit: int = 20):
    """Get recent MLflow experiment runs."""
    return {"experiments": get_experiment_history(limit=limit)}

