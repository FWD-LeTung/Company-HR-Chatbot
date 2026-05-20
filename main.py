from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field, field_validator
from typing import Generator

from source.config import settings
from source.generation.chat_engine import stream_hr_chatbot

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, description="Nội dung câu hỏi của người dùng")
    session_id: str = Field(default="default", description="ID phiên chat")

    @field_validator("message")
    @classmethod
    def validate_message(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Nội dung câu hỏi không được để trống")
        return v.strip()


@app.get(
    "/health",
    tags=["System"],
    summary="Health Check",
    description="Kiểm tra trạng thái hoạt động của API"
)
def health():
    return {
        "status": "healthy",
        "version": settings.APP_VERSION,
        "environment": "development"
    }


@app.post(
    "/api/v1/chat/stream",
    tags=["Chat"],
    summary="Chat với Bot (Streaming)",
    description="Nhận câu hỏi và trả lời theo thời gian thực"
)
async def chat_stream(request: ChatRequest):
    def generate() -> Generator[str, None, None]:
        for chunk in stream_hr_chatbot(user_query=request.message, session_id=request.session_id):
            yield chunk

    return StreamingResponse(
        generate(),
        media_type="text/event-stream"
    )


if __name__ == "__main__":
    import uvicorn
    # Sửa "source.main:app" hoặc biến `app` thành chuỗi "main:app"
    uvicorn.run("main:app", host=settings.HOST, port=settings.PORT, reload=True)