import secrets
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from pydantic import BaseModel, Field, field_validator
from typing import AsyncGenerator

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

security = HTTPBasic()


def verify_credentials(credentials: HTTPBasicCredentials = Depends(security)):
    correct_username = secrets.compare_digest(credentials.username, settings.API_USERNAME)
    correct_password = secrets.compare_digest(credentials.password, settings.API_PASSWORD)

    if not (correct_username and correct_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized",
            headers={"WWW-Authenticate": "Basic"},
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


@app.get(
    "/api/v1/auth/verify",
    tags=["Auth"],
    summary="Xác thực",
    description="Kiểm tra credentials có hợp lệ",
    dependencies=[Depends(verify_credentials)]
)
def verify():
    return {"status": "authenticated"}


@app.post(
    "/api/v1/chat/stream",
    tags=["Chat"],
    summary="Chat với Bot (Streaming)",
    description="Nhận câu hỏi và trả lời theo thời gian thực",
)
async def chat_stream(request: ChatRequest, credentials: HTTPBasicCredentials = Depends(security)):
    verify_credentials(credentials)
    async def generate() -> AsyncGenerator[str, None]:
        async for chunk in stream_hr_chatbot(
            user_query=request.message,
            session_id=request.session_id,
            user_id=credentials.username,
        ):
            yield chunk

    return StreamingResponse(
        generate(),
        media_type="text/event-stream"
    )


if __name__ == "__main__":
    import uvicorn
    # Sửa "source.main:app" hoặc biến `app` thành chuỗi "main:app"
    uvicorn.run("main:app", host=settings.HOST, port=settings.PORT, reload=True)