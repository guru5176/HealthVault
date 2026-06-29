"""Health Wallet — FastAPI Application Entry Point.

Production MLOps web application combining Health Passport + Soma Care Router.
Local LLM inference via Ollama on NVIDIA RTX 4060.
"""

import logging
import time
import os
from contextlib import asynccontextmanager
from pathlib import Path

from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from backend.config import settings
from backend.ml.model_server import model_server
from backend.api.routes_vault import router as vault_router
from backend.api.routes_chat import router as chat_router
from backend.api.routes_care import router as care_router
from backend.api.routes_health import router as health_router

# Logging
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("health_wallet")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown lifecycle."""
    logger.info("🏥 Health Wallet starting...")
    logger.info(f"   Model: {settings.ollama_model}")
    logger.info(f"   Ollama: {settings.ollama_base_url}")
    logger.info(f"   GPU: NVIDIA RTX 4060 (8GB VRAM)")

    # Check Ollama connection
    health = await model_server.health_check()
    if health["status"] == "healthy":
        logger.info(f"   ✅ Ollama connected — {settings.ollama_model} ready")
    else:
        logger.warning(f"   ⚠️  Ollama: {health.get('error', 'not available')}")

    # Try MongoDB connection
    from backend.db.mongo import get_db
    db = get_db()
    if db is not None:
        logger.info(f"   ✅ MongoDB connected — {settings.mongodb_db}")
    else:
        logger.warning("   ⚠️  MongoDB not configured — using fallback data")

    yield

    # Shutdown
    await model_server.close()
    from backend.db.mongo import close_connection
    close_connection()
    logger.info("🏥 Health Wallet stopped")


# App
app = FastAPI(
    title="Health Wallet",
    description="Privacy-first medical records + AI specialist routing. Local LLM inference on RTX 4060.",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.time()
    response = await call_next(request)
    duration = time.time() - start

    if not request.url.path.startswith("/assets"):
        logger.info(
            f"{request.method} {request.url.path} → {response.status_code} ({duration*1000:.0f}ms)"
        )
    return response


# API routes
app.include_router(vault_router)
app.include_router(chat_router)
app.include_router(care_router)
app.include_router(health_router)

# Static files (frontend)
frontend_dir = Path(__file__).parent.parent / "frontend"
if frontend_dir.exists():
    app.mount("/assets", StaticFiles(directory=str(frontend_dir)), name="frontend_assets")


# Serve index.html for all non-API routes (SPA)
@app.get("/")
async def serve_root():
    index_path = frontend_dir / "index.html"
    if index_path.exists():
        return FileResponse(str(index_path))
    return {"message": "Health Wallet API is running. Frontend not found at /frontend/"}


@app.get("/{path:path}")
async def serve_spa(path: str):
    """Serve static files or fall back to index.html for SPA routing."""
    # Check if it's a static file
    file_path = frontend_dir / path
    if file_path.exists() and file_path.is_file():
        return FileResponse(str(file_path))

    # Fall back to index.html for SPA
    index_path = frontend_dir / "index.html"
    if index_path.exists():
        return FileResponse(str(index_path))
    return {"message": "Not found", "path": path}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backend.main:app",
        host=settings.host,
        port=settings.port,
        reload=True,
        log_level=settings.log_level.lower(),
    )
