```
    Plan: Deploy Backend + Frontend lên Render                                           │
     │                                                                                       │
     │ Context                                                                               │
     │                                                                                       │
     │ HR-chatbot cần deploy lên production. Qdrant (vector DB) đã lên Qdrant Cloud,         │
     │ Langfuse monitoring đã xong. Còn backend (FastAPI) và frontend (static HTML/CSS/JS)   │
     │ chưa được deploy. Platform chọn: Render. Backend không cần GPU (chỉ gọi OpenAI API).  │
     │                                                                                       │
     │ Key observations                                                                      │
     │                                                                                       │
     │ - Frontend là static files thuần (source/frontend/: index.html, login.html, CSS, JS)  │
     │ - Frontend đang hardcode API_URL = 'http://localhost:8000/...' trong app.js và        │
     │ login.js                                                                              │
     │ - Backend dùng uv package manager, Python 3.11-3.12                                   │
     │ - Torch + CUDA là dependency nặng (~2GB) nhưng không cần trên production — chỉ dùng   │
     │ khi indexing offline                                                                  │
     │ - Có docker-compose.yml nhưng chỉ cho Qdrant local, không có Dockerfile cho app       │
     │                                                                                       │
     │ ---                                                                                   │
     │ Step 1: Tạo .env.example và dọn dẹp .env                                              │
     │                                                                                       │
     │ File: .env.example (tạo mới)                                                          │
     │                                                                                       │
     │ Tạo file .env.example với placeholder values cho tất cả biến môi trường cần thiết.    │
     │ Giúp Render và developer mới biết cần config gì.                                      │
     │                                                                                       │
     │ File: .gitignore — đảm bảo .env đã trong gitignore (chứa secrets thật).               │
     │                                                                                       │
     │ ---                                                                                   │
     │ Step 2: Tạo Dockerfile cho backend                                                    │
     │                                                                                       │
     │ File: Dockerfile (tạo mới)                                                            │
     │                                                                                       │
     │ Multi-stage build:                                                                    │
     │ 1. Builder stage: Dùng ghcr.io/astral-sh/uv:latest image, install dependencies với uv │
     │  sync                                                                                 │
     │ 2. Runtime stage: Copy virtualenv từ builder, chạy với uvicorn                        │
     │                                                                                       │
     │ Tối ưu quan trọng:                                                                    │
     │ - Dùng torch CPU-only (không CUDA) để giảm image size từ ~5GB xuống ~1GB              │
     │ - Trong Dockerfile, override torch source để install bản CPU: uv sync --extra torch   │
     │ hoặc cấu hình pyproject.toml có optional [gpu] group                                  │
     │ - Set ENV LANGFUSE_PUBLIC_KEY="" etc. — Render sẽ inject env vars thực tế             │
     │                                                                                       │
     │ ---                                                                                   │
     │ Step 3: Tách GPU dependencies thành optional group                                    │
     │                                                                                       │
     │ File: pyproject.toml                                                                  │
     │                                                                                       │
     │ Tạo optional dependency group [gpu] cho torch/torchvision/mineru-vl-utils:            │
     │ [project.optional-dependencies]                                                       │
     │ gpu = ["torch>=2.6.0", "torchvision", "mineru-vl-utils[transformers]>=0.1.0"]         │
     │                                                                                       │
     │ Base dependencies chỉ cần: fastapi, uvicorn, langchain-openai, langchain-qdrant,      │
     │ langfuse, pydantic-settings, polars, etc.                                             │
     │                                                                                       │
     │ Dockerfile install: uv sync --no-extra gpu (không cài GPU packages)                   │
     │                                                                                       │
     │ ---                                                                                   │
     │ Step 4: Làm API_URL động trong frontend                                               │
     │                                                                                       │
     │ File: source/frontend/app.js và source/frontend/login.js                              │
     │                                                                                       │
     │ Thay hardcode http://localhost:8000 bằng relative URL hoặc auto-detect:               │
     │ const API_BASE = window.location.origin;                                              │
     │ const API_URL = `${API_BASE}/api/v1/chat/stream`;                                     │
     │                                                                                       │
     │ Điều này cho phép frontend gọi API cùng domain khi được serve từ Render.              │
     │                                                                                       │
     │ ---                                                                                   │
     │ Step 5: Serve frontend từ FastAPI                                                     │
     │                                                                                       │
     │ File: main.py                                                                         │
     │                                                                                       │
     │ Mount static files từ source/frontend/ vào FastAPI:                                   │
     │ from fastapi.staticfiles import StaticFiles                                           │
     │ app.mount("/", StaticFiles(directory="source/frontend", html=True), name="frontend")  │
     │                                                                                       │
     │ Đặt sau tất cả API routes. Khi đó:                                                    │
     │ - /api/v1/* → FastAPI endpoints                                                       │
     │ - / → serve index.html                                                                │
     │ - /login.html → serve login page                                                      │
     │                                                                                       │
     │ Lợi ích: 1 service duy nhất trên Render, không cần configure CORS, không cần 2        │
     │ separate deployments.                                                                 │
     │                                                                                       │
     │ ---                                                                                   │
     │ Step 6: Cập nhật CORS config                                                          │
     │                                                                                       │
     │ File: main.py                                                                         │
     │                                                                                       │
     │ Vì frontend và backend cùng domain, CORS allow_origins=["*"] có thể thắt lại thành    │
     │ cùng domain. Nhưng nếu muốn linh hoạt (dev local) thì giữ nguyên cũng được.           │
     │                                                                                       │
     │ ---                                                                                   │
     │ Step 7: Cấu hình Render                                                               │
     │                                                                                       │
     │ Backend (Web Service)                                                                 │
     │                                                                                       │
     │ 1. Create new Web Service trên Render, connect GitHub repo                            │
     │ 2. Build: Docker (Render tự detect Dockerfile)                                        │
     │ 3. Environment Variables set trên Render Dashboard:                                   │
     │   - OPENAI_API_KEY                                                                    │
     │   - OPENAI_CHAT_MODEL = gpt-4o                                                        │
     │   - OPENAI_EMBEDDING_MODEL = text-embedding-3-small                                   │
     │   - API_USERNAME / API_PASSWORD                                                       │
     │   - QDRANT_URL / QDRANT_API_KEY / COLLECTION_NAME                                     │
     │   - LANGFUSE_PUBLIC_KEY / LANGFUSE_SECRET_KEY / LANGFUSE_BASE_URL                     │
     │ 4. Render auto-assign domain dạng hr-chatbot.onrender.com                             │
     │                                                                                       │
     │ Không cần separate Static Site                                                        │
     │                                                                                       │
     │ Vì frontend được serve từ FastAPI (Step 5), chỉ cần 1 Web Service.                    │
     │                                                                                       │
     │ ---                                                                                   │
     │ Step 8: Cấu hình production cho uvicorn                                               │
     │                                                                                       │
     │ File: main.py                                                                         │
     │                                                                                       │
     │ Sửa __main__ block: tắt reload=True khi chạy production (Render dùng Docker, không    │
     │ cần reload):                                                                          │
     │ if __name__ == "__main__":                                                            │
     │     uvicorn.run("main:app", host=settings.HOST, port=settings.PORT, reload=True)      │
     │                                                                                       │
     │ Trong Dockerfile, CMD sẽ là:                                                          │
     │ CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "$PORT"]                   │
     │                                                                                       │
     │ Render tự set PORT env var, nên dùng $PORT thay vì hardcode 8000.                     │
     │                                                                                       │
     │ ---                                                                                   │
     │ Files cần tạo/sửa                                                                     │
     │                                                                                       │
     │ ┌──────────────────────────┬──────────────┬────────────────────────────────────┐      │
     │ │           File           │    Action    │               Mô tả                │      │
     │ ├──────────────────────────┼──────────────┼────────────────────────────────────┤      │
     │ │ Dockerfile               │ Tạo mới      │ Multi-stage build, torch CPU-only  │      │
     │ ├──────────────────────────┼──────────────┼────────────────────────────────────┤      │
     │ │ .env.example             │ Tạo mới      │ Template cho env vars              │      │
     │ ├──────────────────────────┼──────────────┼────────────────────────────────────┤      │
     │ │ pyproject.toml           │ Sửa          │ Tách GPU thành optional dependency │      │
     │ ├──────────────────────────┼──────────────┼────────────────────────────────────┤      │
     │ │ source/frontend/app.js   │ Sửa          │ API_URL động thay vì hardcode      │      │
     │ ├──────────────────────────┼──────────────┼────────────────────────────────────┤      │
     │ │ source/frontend/login.js │ Sửa          │ API_URL động thay vì hardcode      │      │
     │ ├──────────────────────────┼──────────────┼────────────────────────────────────┤      │
     │ │ main.py                  │ Sửa          │ Mount static files, dùng $PORT     │      │
     │ ├──────────────────────────┼──────────────┼────────────────────────────────────┤      │
     │ │ .gitignore               │ Sửa/Kiểm tra │ Đảm bảo .env bị ignore             │      │
     │ └──────────────────────────┴──────────────┴────────────────────────────────────┘      │
     │                                                                                       │
     │ ---                                                                                   │
     │ Verification                                                                          │
     │                                                                                       │
     │ 1. Build Docker image local: docker build -t hr-chatbot .                             │
     │ 2. Chạy local: docker run -p 8000:8000 --env-file .env hr-chatbot                     │
     │ 3. Test: mở http://localhost:8000 → thấy login page                                   │
     │ 4. Login → chat → verify traces xuất hiện trên Langfuse                               │
     │ 5. Push lên GitHub → Render auto-deploy → test trên URL production  

```