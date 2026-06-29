"""Health Wallet service — CRUD operations for medical records.

Prescriptions are also persisted to MongoDB for durable cloud storage.
"""

import os
import uuid
import logging
from datetime import datetime
from pathlib import Path

logger = logging.getLogger("health_wallet.vault")

VAULT_DIR = Path(__file__).parent.parent / "data" / "health_vault"


class VaultService:
    """Manages health records stored as markdown files + MongoDB persistence for prescriptions."""

    def __init__(self):
        self.vault_dir = VAULT_DIR
        self.vault_dir.mkdir(parents=True, exist_ok=True)

    def list_records(self) -> list[dict]:
        """List all health records."""
        records = []
        for fpath in sorted(self.vault_dir.glob("*.md")):
            content = fpath.read_text(encoding="utf-8")
            records.append({
                "id": fpath.stem,
                "filename": fpath.name,
                "title": self._extract_title(content),
                "category": self._categorize(fpath.name),
                "size_bytes": fpath.stat().st_size,
                "modified": datetime.fromtimestamp(fpath.stat().st_mtime).isoformat(),
                "preview": content[:200].strip(),
            })
        return records

    def get_record(self, record_id: str) -> dict | None:
        """Get a single record by ID (filename stem)."""
        fpath = self.vault_dir / f"{record_id}.md"
        if not fpath.exists():
            return None
        content = fpath.read_text(encoding="utf-8")
        return {
            "id": record_id,
            "filename": fpath.name,
            "title": self._extract_title(content),
            "category": self._categorize(fpath.name),
            "content": content,
            "size_bytes": fpath.stat().st_size,
            "modified": datetime.fromtimestamp(fpath.stat().st_mtime).isoformat(),
        }

    def create_record(self, title: str, content: str, category: str = "general") -> dict:
        """Create a new health record."""
        safe_title = title.replace(" ", "_").replace("/", "_")[:50]
        filename = f"{safe_title}.md"
        fpath = self.vault_dir / filename

        # Avoid overwrites
        if fpath.exists():
            filename = f"{safe_title}_{uuid.uuid4().hex[:6]}.md"
            fpath = self.vault_dir / filename

        full_content = f"# {title}\n\n{content}"
        fpath.write_text(full_content, encoding="utf-8")

        logger.info("record_created", extra={"record_filename": filename})
        return self.get_record(fpath.stem)

    def save_prescription_to_mongo(self, title: str, content: str, ocr_raw: str, record_id: str) -> bool:
        """Persist a prescription record to MongoDB for durable storage."""
        try:
            from backend.db.mongo import get_prescriptions_collection
            collection = get_prescriptions_collection()
            if collection is None:
                logger.warning("MongoDB not available — prescription saved locally only")
                return False

            doc = {
                "record_id": record_id,
                "title": title,
                "content": content,
                "ocr_raw": ocr_raw,
                "category": "medications",
                "created_at": datetime.utcnow().isoformat(),
                "source": "prescription_scanner",
            }
            collection.insert_one(doc)
            logger.info("prescription_saved_to_mongo", extra={"record_id": record_id, "title": title})
            return True
        except Exception as e:
            logger.error(f"Failed to save prescription to MongoDB: {e}")
            return False

    def search_records(self, query: str) -> list[dict]:
        """Full-text search across all records."""
        query_lower = query.lower()
        results = []
        for fpath in self.vault_dir.glob("*.md"):
            content = fpath.read_text(encoding="utf-8")
            if query_lower in content.lower():
                # Find matching lines for context
                matches = []
                for i, line in enumerate(content.split("\n")):
                    if query_lower in line.lower():
                        matches.append({"line": i + 1, "text": line.strip()})

                results.append({
                    "id": fpath.stem,
                    "filename": fpath.name,
                    "title": self._extract_title(content),
                    "category": self._categorize(fpath.name),
                    "matches": matches[:5],  # Top 5 matching lines
                    "match_count": len(matches),
                })
        return results

    def get_all_content(self) -> str:
        """Get all vault content concatenated (for RAG context)."""
        parts = []
        for fpath in sorted(self.vault_dir.glob("*.md")):
            content = fpath.read_text(encoding="utf-8")
            parts.append(f"--- FILE: {fpath.name} ---\n{content}\n")
        return "\n".join(parts)

    def _extract_title(self, content: str) -> str:
        """Extract the first H1 heading as the title."""
        for line in content.split("\n"):
            line = line.strip()
            if line.startswith("# "):
                return line[2:].strip()
        return "Untitled"

    def _categorize(self, filename: str) -> str:
        """Categorize a record based on filename patterns."""
        name = filename.lower()
        if ("med" in name or "prescription" in name or "pres" in name) and "timeline" not in name:
            return "medications"
        elif "timeline" in name:
            return "timeline"
        else:
            return "general"


vault_service = VaultService()
