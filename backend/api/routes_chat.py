"""AI Chat API routes with SSE streaming."""

import json
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from backend.services.chat_service import chat_service

router = APIRouter(prefix="/api/chat", tags=["chat"])


class ChatRequest(BaseModel):
    message: str
    stream: bool = True


@router.post("")
async def chat(req: ChatRequest):
    """Send a message to the AI assistant."""
    if not req.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    if req.stream:
        async def event_stream():
            try:
                async for token in chat_service.chat_stream(req.message):
                    yield f"data: {json.dumps({'token': token})}\n\n"
                yield f"data: {json.dumps({'done': True})}\n\n"
            except Exception as e:
                yield f"data: {json.dumps({'error': str(e)})}\n\n"

        return StreamingResponse(
            event_stream(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            },
        )
    else:
        try:
            response = await chat_service.chat(req.message)
            return {"response": response}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))


@router.get("/history")
async def get_history():
    """Get conversation history."""
    return {"history": chat_service.get_history()}


@router.post("/clear")
async def clear_history():
    """Clear conversation history."""
    chat_service.clear_history()
    return {"message": "History cleared"}
