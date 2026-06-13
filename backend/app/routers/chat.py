from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from app.schemas.requests import ChatRequest
from app.services.chat import SolarChatService

router = APIRouter()


@router.post("/chat")
async def chat(body: ChatRequest) -> StreamingResponse:
    svc = SolarChatService()
    return StreamingResponse(
        svc.stream_response(body.message, body.location_context),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection":    "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
