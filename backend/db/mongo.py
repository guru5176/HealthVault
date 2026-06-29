"""MongoDB Atlas connection and collections."""

import logging
from typing import Optional

from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.errors import PyMongoError

from backend.config import settings

logger = logging.getLogger("health_wallet.db")

_client: Optional[MongoClient] = None
_db = None
_connection_attempted: bool = False


def get_db():
    """Get MongoDB database connection."""
    global _client, _db, _connection_attempted

    if _db is not None:
        return _db

    # Don't retry if we already failed — avoids 20s DNS timeout on every request
    if _connection_attempted:
        return None

    uri = settings.mongodb_uri
    if not uri:
        logger.warning("MONGODB_URI not set — database features disabled")
        _connection_attempted = True
        return None

    _connection_attempted = True
    try:
        _client = MongoClient(uri, serverSelectionTimeoutMS=5000)
        _client.admin.command("ping")
        _db = _client[settings.mongodb_db]
        logger.info("MongoDB connected", extra={"db": settings.mongodb_db})
        return _db
    except PyMongoError as e:
        logger.error(f"MongoDB connection failed: {e}")
        return None


def get_providers_collection() -> Optional[Collection]:
    """Get the providers collection."""
    db = get_db()
    return db["providers"] if db is not None else None


def get_drug_interactions_collection() -> Optional[Collection]:
    """Get the drug interactions collection."""
    db = get_db()
    return db["drug_interactions"] if db is not None else None


def get_prescriptions_collection() -> Optional[Collection]:
    """Get the prescriptions collection for storing scanned/uploaded prescriptions."""
    db = get_db()
    return db["prescriptions"] if db is not None else None


def check_connection() -> dict:
    """Check MongoDB connection health."""
    try:
        db = get_db()
        if db is None:
            return {"status": "not_configured", "message": "MONGODB_URI not set"}
        _client.admin.command("ping")
        return {
            "status": "connected",
            "database": settings.mongodb_db,
            "collections": db.list_collection_names(),
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}


def close_connection():
    """Close MongoDB connection."""
    global _client, _db, _connection_attempted
    if _client:
        _client.close()
        _client = None
        _db = None
    _connection_attempted = False
