"""AI Chat service — health Q&A with RAG over vault records."""

import logging
from pathlib import Path

from backend.ml.model_server import model_server
from backend.ml.prompts import HEALTH_ASSISTANT_SYSTEM_PROMPT, PROMPT_VERSION
from backend.ml.model_registry import log_inference_experiment
from backend.services.vault_service import vault_service

logger = logging.getLogger("health_wallet.chat")

# Maximum number of conversation turns to keep (user + assistant pairs)
MAX_HISTORY_TURNS = 5  # 5 pairs = 10 messages


class ChatService:
    """AI chat with local LLM + health wallet context (RAG)."""

    def __init__(self):
        self.conversation_history: list[dict] = []

    def _get_relevant_records(self, query: str, max_records: int = 3) -> str:
        """Retrieve only vault records relevant to the user's query.

        Uses simple keyword matching to avoid overloading the small model
        with the entire vault contents (~14KB across 19 files).
        """
        query_lower = query.lower()

        # Extract keywords (skip very short/common words)
        stop_words = {
            "the", "a", "an", "is", "are", "was", "were", "be", "been",
            "what", "how", "why", "when", "where", "who", "which",
            "do", "does", "did", "can", "could", "would", "should",
            "my", "me", "i", "you", "your", "it", "its", "this", "that",
            "in", "on", "at", "to", "for", "of", "with", "and", "or",
            "not", "no", "any", "all", "about", "tell", "show", "give",
            "have", "has", "had", "please", "help", "know", "get",
        }
        keywords = [
            w for w in query_lower.split()
            if len(w) > 2 and w not in stop_words
        ]

        if not keywords:
            # If no meaningful keywords, return a brief summary instead
            records = vault_service.list_records()
            if not records:
                return "No health records found in the vault."
            summary_lines = [f"- {r['title']} ({r['category']})" for r in records[:8]]
            return "Available records:\n" + "\n".join(summary_lines)

        # Score each vault file by keyword relevance
        scored_records = []
        vault_dir = vault_service.vault_dir
        for fpath in sorted(vault_dir.glob("*.md")):
            content = fpath.read_text(encoding="utf-8")
            content_lower = content.lower()
            filename_lower = fpath.name.lower()

            score = 0
            for kw in keywords:
                # Count occurrences in content
                score += content_lower.count(kw) * 2
                # Bonus for filename match
                if kw in filename_lower:
                    score += 5

            if score > 0:
                scored_records.append((score, fpath, content))

        if not scored_records:
            # No matches — return list of available records so the model
            # can tell the user what info is available
            records = vault_service.list_records()
            summary_lines = [f"- {r['title']} ({r['category']})" for r in records[:8]]
            return ("No records matched your query. Available records:\n"
                    + "\n".join(summary_lines))

        # Sort by relevance, take top N
        scored_records.sort(key=lambda x: x[0], reverse=True)
        top = scored_records[:max_records]

        parts = []
        for _, fpath, content in top:
            # Truncate very long records to keep context manageable
            if len(content) > 2000:
                content = content[:2000] + "\n... [truncated]"
            parts.append(f"--- FILE: {fpath.name} ---\n{content}")

        return "\n\n".join(parts)

    def _trim_history(self):
        """Keep only the last MAX_HISTORY_TURNS conversation pairs."""
        max_messages = MAX_HISTORY_TURNS * 2  # each turn = user + assistant
        if len(self.conversation_history) > max_messages:
            self.conversation_history = self.conversation_history[-max_messages:]

    async def chat(self, message: str) -> str:
        """Send a message and get a complete response."""
        relevant_context = self._get_relevant_records(message)
        system_msg = (
            f"{HEALTH_ASSISTANT_SYSTEM_PROMPT}\n\n"
            f"## Relevant Health Records\n{relevant_context}"
        )

        messages = [{"role": "system", "content": system_msg}]
        messages.extend(self.conversation_history)
        messages.append({"role": "user", "content": message})

        response = await model_server.chat(
            messages=messages,
            temperature=0.3,  # Low temp for factual medical responses
            max_tokens=1024,
        )

        # Log to MLflow
        log_inference_experiment(
            model_name=model_server.model,
            prompt_version=PROMPT_VERSION,
            prompt=message,
            response=response,
            latency=0,  # Already logged in model_server
            tokens=len(response.split()),
            endpoint="chat",
            success=True,
        )

        # Track conversation and trim
        self.conversation_history.append({"role": "user", "content": message})
        self.conversation_history.append({"role": "assistant", "content": response})
        self._trim_history()

        return response

    async def chat_stream(self, message: str):
        """Send a message and get a streaming response."""
        relevant_context = self._get_relevant_records(message)
        system_msg = (
            f"{HEALTH_ASSISTANT_SYSTEM_PROMPT}\n\n"
            f"## Relevant Health Records\n{relevant_context}"
        )

        messages = [{"role": "system", "content": system_msg}]
        messages.extend(self.conversation_history)
        messages.append({"role": "user", "content": message})

        full_response = []
        async for token in model_server.chat_stream(
            messages=messages,
            temperature=0.3,
            max_tokens=1024,
        ):
            full_response.append(token)
            yield token

        # Track conversation and trim
        response_text = "".join(full_response)
        self.conversation_history.append({"role": "user", "content": message})
        self.conversation_history.append({"role": "assistant", "content": response_text})
        self._trim_history()

        log_inference_experiment(
            model_name=model_server.model,
            prompt_version=PROMPT_VERSION,
            prompt=message,
            response=response_text,
            latency=0,
            tokens=len(response_text.split()),
            endpoint="chat_stream",
            success=True,
        )

    def clear_history(self):
        """Clear conversation history."""
        self.conversation_history = []

    def get_history(self) -> list[dict]:
        """Get conversation history."""
        return self.conversation_history


chat_service = ChatService()
