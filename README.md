[![Tech Stack](https://skillicons.dev/icons?i=py,fastapi,html,css,js,docker)](https://skillicons.dev)

# HR Chatbot

HR Chatbot là trợ lý nội bộ cho phòng Nhân sự, hỗ trợ hỏi đáp chính sách HR và tra cứu danh bạ nhân viên. Hệ thống gồm backend FastAPI, giao diện chat tĩnh, RAG với Qdrant + OpenAI, và agent LangChain để chọn đúng công cụ tra cứu.

## Tổng quan

- Chat streaming qua API `POST /api/v1/chat/stream`.
- Giao diện web tĩnh được serve trực tiếp từ FastAPI.
- Đăng nhập bằng Basic Auth.
- Tra cứu chính sách HR bằng RAG trên Qdrant.
- Tra cứu danh bạ nhân viên từ Excel bằng Polars và allowlist.
- Theo dõi trace qua Langfuse.

## Tech stack

- **Backend:** Python, FastAPI, Uvicorn
- **AI/RAG:** LangChain, OpenAI API, Qdrant
- **Data:** Polars, Calamine, Kreuzberg, MinerU, PyMuPDF
- **Frontend:** HTML, CSS, Vanilla JavaScript
- **Tooling:** uv, Docker, Docker Compose, Langfuse

## Cấu hình môi trường

Sao chép file `.env.example` thành `.env` rồi điền các biến cần thiết:

```env
OPENAI_API_KEY=
OPENAI_LLM_MODEL=gpt-4o
OPENAI_EMBEDDING_MODEL=text-embedding-3-small

QDRANT_URL=
QDRANT_API_KEY=
COLLECTION_NAME=hr_policies_openai

API_USERNAME=
API_PASSWORD=

LANGFUSE_SECRET_KEY=
LANGFUSE_PUBLIC_KEY=
LANGFUSE_BASE_URL=https://cloud.langfuse.com

HOST=0.0.0.0
PORT=8000
```

## Cách chạy local

Cài dependencies:

```bash
uv sync
```

Chạy Qdrant local:

```bash
docker-compose up -d
```

Nạp dữ liệu vào Qdrant:

```bash
uv run python run_pipeline.py
```

Chạy ứng dụng:

```bash
uv run uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

Mở trình duyệt tại:

```text
http://localhost:8000
```

## Chạy test

```bash
uv run pytest
```

## Chạy bằng Docker

Build image:

```bash
docker build -t hr-chatbot .
```

Chạy container:

```bash
docker run --env-file .env -p 10000:10000 hr-chatbot
```
