"""Ollama model server client with GPU acceleration.

Wraps Ollama's OpenAI-compatible API for local LLM inference on RTX 4060.
Handles streaming responses, retries, and inference metrics.
"""

import time
import asyncio
import logging
from typing import AsyncGenerator, Optional

import httpx

from backend.config import settings
from backend.ml.monitor import monitor

logger = logging.getLogger("health_wallet.model_server")


class ModelServer:
    """Client for Ollama local LLM inference."""

    def __init__(self):
        self.base_url = settings.ollama_base_url
        self.model = settings.ollama_model
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                timeout=httpx.Timeout(120.0, connect=10.0),
            )
        return self._client

    async def close(self):
        if self._client and not self._client.is_closed:
            await self._client.aclose()

    async def health_check(self) -> dict:
        """Check if Ollama is running and model is available."""
        try:
            client = await self._get_client()
            resp = await client.get("/api/tags")
            if resp.status_code == 200:
                models = resp.json().get("models", [])
                model_names = [m.get("name", "") for m in models]
                has_model = any(self.model in n for n in model_names)
                return {
                    "status": "healthy" if has_model else "model_missing",
                    "ollama": "connected",
                    "model": self.model,
                    "available_models": model_names,
                    "gpu": "RTX 4060 (8GB VRAM)",
                }
            return {"status": "unhealthy", "error": f"HTTP {resp.status_code}"}
        except httpx.ConnectError:
            return {"status": "offline", "error": "Ollama not running. Start with: ollama serve"}
        except Exception as e:
            return {"status": "error", "error": str(e)}

    async def list_models(self) -> list[dict]:
        """List all available Ollama models."""
        try:
            client = await self._get_client()
            resp = await client.get("/api/tags")
            if resp.status_code == 200:
                return resp.json().get("models", [])
            return []
        except Exception:
            return []

    async def generate(
        self,
        prompt: str,
        system_prompt: str = "",
        temperature: float = 0.7,
        max_tokens: int = 1024,
    ) -> str:
        """Generate a complete response (non-streaming)."""
        client = await self._get_client()
        start_time = time.time()

        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
                "num_gpu": 99,  # Use all GPU layers (RTX 4060)
            },
        }
        if system_prompt:
            payload["system"] = system_prompt

        try:
            resp = await client.post("/api/generate", json=payload)
            resp.raise_for_status()
            data = resp.json()

            latency = time.time() - start_time
            response_text = data.get("response", "")
            tokens = data.get("eval_count", len(response_text.split()))

            # Log metrics
            monitor.log_inference(
                model=self.model,
                latency=latency,
                tokens=tokens,
                endpoint="generate",
                success=True,
            )

            logger.info(
                "inference_complete",
                extra={
                    "model": self.model,
                    "latency_ms": round(latency * 1000),
                    "tokens": tokens,
                },
            )

            return response_text

        except Exception as e:
            latency = time.time() - start_time
            monitor.log_inference(
                model=self.model,
                latency=latency,
                tokens=0,
                endpoint="generate",
                success=False,
            )
            logger.error("inference_failed", extra={"error": str(e)})
            raise

    async def generate_stream(
        self,
        prompt: str,
        system_prompt: str = "",
        temperature: float = 0.7,
        max_tokens: int = 1024,
    ) -> AsyncGenerator[str, None]:
        """Generate a streaming response (token by token)."""
        client = await self._get_client()
        start_time = time.time()
        total_tokens = 0

        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": True,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
                "num_gpu": 99,
            },
        }
        if system_prompt:
            payload["system"] = system_prompt

        try:
            async with client.stream("POST", "/api/generate", json=payload) as resp:
                resp.raise_for_status()
                async for line in resp.aiter_lines():
                    if not line:
                        continue
                    import json
                    data = json.loads(line)
                    token = data.get("response", "")
                    if token:
                        total_tokens += 1
                        yield token
                    if data.get("done", False):
                        break

            latency = time.time() - start_time
            monitor.log_inference(
                model=self.model,
                latency=latency,
                tokens=total_tokens,
                endpoint="generate_stream",
                success=True,
            )

        except Exception as e:
            latency = time.time() - start_time
            monitor.log_inference(
                model=self.model,
                latency=latency,
                tokens=total_tokens,
                endpoint="generate_stream",
                success=False,
            )
            logger.error("stream_inference_failed", extra={"error": str(e)})
            raise

    async def chat(
        self,
        messages: list[dict],
        temperature: float = 0.7,
        max_tokens: int = 1024,
    ) -> str:
        """Chat completion using Ollama's chat API."""
        client = await self._get_client()
        start_time = time.time()

        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
                "num_gpu": 99,
            },
        }

        try:
            resp = await client.post("/api/chat", json=payload)
            resp.raise_for_status()
            data = resp.json()

            latency = time.time() - start_time
            response_text = data.get("message", {}).get("content", "")
            tokens = data.get("eval_count", len(response_text.split()))

            monitor.log_inference(
                model=self.model,
                latency=latency,
                tokens=tokens,
                endpoint="chat",
                success=True,
            )

            return response_text

        except Exception as e:
            latency = time.time() - start_time
            monitor.log_inference(
                model=self.model,
                latency=latency,
                tokens=0,
                endpoint="chat",
                success=False,
            )
            raise

    async def chat_stream(
        self,
        messages: list[dict],
        temperature: float = 0.7,
        max_tokens: int = 1024,
    ) -> AsyncGenerator[str, None]:
        """Streaming chat completion."""
        client = await self._get_client()
        start_time = time.time()
        total_tokens = 0

        payload = {
            "model": self.model,
            "messages": messages,
            "stream": True,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
                "num_gpu": 99,
            },
        }

        try:
            async with client.stream("POST", "/api/chat", json=payload) as resp:
                resp.raise_for_status()
                async for line in resp.aiter_lines():
                    if not line:
                        continue
                    import json
                    data = json.loads(line)
                    token = data.get("message", {}).get("content", "")
                    if token:
                        total_tokens += 1
                        yield token
                    if data.get("done", False):
                        break

            latency = time.time() - start_time
            monitor.log_inference(
                model=self.model,
                latency=latency,
                tokens=total_tokens,
                endpoint="chat_stream",
                success=True,
            )

        except Exception as e:
            latency = time.time() - start_time
            monitor.log_inference(
                model=self.model,
                latency=latency,
                tokens=total_tokens,
                endpoint="chat_stream",
                success=False,
            )
            raise


# Singleton instance
model_server = ModelServer()
