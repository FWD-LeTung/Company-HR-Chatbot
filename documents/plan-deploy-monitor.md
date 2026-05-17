# Plan Ngày 4: Deploy Public URL + Monitoring

## Summary
Mục tiêu ngày 4 là đưa HR RAG chatbot từ local lên môi trường public test: FastAPI app có URL thật, có basic password, kết nối Qdrant Cloud, dùng OpenAI API production env, và có monitoring tối thiểu để biết app sống, lỗi ở đâu, latency thế nào.

Kết quả cuối ngày: người test có thể mở URL, đăng nhập basic password, hỏi chatbot, nhận câu trả lời có citations từ dữ liệu đã ingest lên Qdrant Cloud.

## 1. Chuẩn Bị Production Config
Tạo bộ env production tách khỏi local:

- `OPENAI_API_KEY`
- `OPENAI_CHAT_MODEL`
- `OPENAI_EMBEDDING_MODEL`
- `QDRANT_URL`
- `QDRANT_API_KEY`
- `QDRANT_COLLECTION`
- `BASIC_AUTH_USERNAME`
- `BASIC_AUTH_PASSWORD`
- `APP_ENV=production`
- `LOG_LEVEL=INFO`
- `CORS_ALLOWED_ORIGINS`

Quy ước:
- Local dùng Qdrant Docker.
- Production dùng Qdrant Cloud.
- Không hardcode secrets trong repo.
- `.env.example` chỉ chứa tên biến và giá trị mẫu giả.

## 2. Qdrant Cloud Setup
Tạo Qdrant Cloud cluster cho môi trường test/public alpha.

Việc cần làm:
- Tạo cluster.
- Tạo API key.
- Lấy cluster URL.
- Chọn collection name production, ví dụ `hr_docs_prod`.
- Chạy ingest một lần từ máy local hoặc one-off job, trỏ env sang Qdrant Cloud.
- Verify collection có points và payload metadata.

Acceptance:
- Qdrant Cloud có collection production.
- Search thử một câu hỏi mẫu trả về chunks đúng.
- App restart/redeploy không làm mất index.

## 3. App Deploy
Deploy FastAPI app lên một app host public, ưu tiên Render/Fly/Railway.

Việc cần làm:
- Thêm start command production:
  - chạy `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- Đảm bảo app đọc `PORT` từ platform.
- Cấu hình env production trên dashboard platform.
- Bật HTTPS/public URL mặc định của platform.
- Đảm bảo static web chat được serve từ FastAPI.
- Không chạy ingest tự động khi app start.

Acceptance:
- `GET /health` trả OK trên public URL.
- Trang chat mở được.
- Basic password chặn truy cập nếu chưa login.
- Chat endpoint gọi được sau khi login.

## 4. Basic Auth Cho Public Test
Áp dụng basic password cho toàn bộ web app hoặc ít nhất các route:

- `GET /`
- `POST /api/chat`
- `GET /api/index-status` nếu có

Quy tắc:
- Username/password lấy từ env.
- Không log password.
- Nếu env thiếu trong production thì app fail fast hoặc route bị khóa, không mở public trống.

Acceptance:
- Truy cập URL yêu cầu username/password.
- Sai password bị từ chối.
- Đúng password dùng chat bình thường.

## 5. Production RAG Smoke Test
Sau khi deploy, chạy checklist câu hỏi thật:

- 3 câu hỏi có trong PDF nội quy/chính sách.
- 1 câu hỏi có trong tài liệu teambuilding.
- 1 câu hỏi có trong tài liệu chứng chỉ/kỹ thuật.
- 1 câu hỏi ngoài tài liệu, bot phải nói không đủ thông tin.
- 1 câu hỏi mơ hồ, bot phải trả lời thận trọng hoặc hỏi lại.

Mỗi câu cần kiểm tra:
- Câu trả lời bằng tiếng Việt.
- Không bịa ngoài context.
- Có citations.
- Citations gồm file + page/sheet + snippet.
- Latency chấp nhận được cho demo.

## 6. Logging
Thêm structured logging đủ để debug production alpha.

Log mỗi request chat:
- `request_id`
- `timestamp`
- `env`
- `latency_ms`
- `question_length`
- `retrieved_count`
- `source_files`
- `llm_model`
- `embedding_model`
- `success`
- `error_type` nếu lỗi

Không log:
- API keys
- Basic password
- Full raw document text
- Thông tin cá nhân nhạy cảm nếu không cần thiết

Acceptance:
- Xem được logs trên platform dashboard.
- Khi chat lỗi, log có request id và error type.
- Khi chat thành công, log thấy latency và source files.

## 7. Monitoring Tối Thiểu
Monitoring ngày 4 không cần phức tạp, nhưng phải đủ để biết hệ thống đang ổn.

Theo dõi:
- App health:
  - `GET /health`
  - deploy platform uptime/restart logs
- App behavior:
  - request latency
  - request error rate qua logs
  - top lỗi thường gặp
- Qdrant:
  - cluster status
  - collection points count
  - dashboard query/usage nếu có
- OpenAI:
  - usage dashboard
  - lỗi rate limit/auth/quota
  - token/cost trong ngày test

Acceptance:
- Có cách kiểm tra app sống.
- Có cách biết lỗi do OpenAI, Qdrant, hay app.
- Có cách xem usage/cost OpenAI sau buổi test.

## 8. Rollback Và Recovery
Chuẩn bị cách xử lý nếu deploy hỏng.

Rollback:
- Revert về deploy trước trên platform.
- Giữ Qdrant collection cũ, không xóa khi deploy app.
- Nếu ingest lỗi, tạo collection mới như `hr_docs_prod_v2`, test xong mới đổi env `QDRANT_COLLECTION`.

Recovery:
- Nếu app lỗi env: sửa env và redeploy.
- Nếu Qdrant lỗi collection: chạy lại ingest.
- Nếu OpenAI quota/rate limit: đổi key/quota hoặc giảm traffic test.
- Nếu citation sai: không hotfix prompt vội; ghi lại câu hỏi và xử lý sau smoke test.

## 9. Deliverables Cuối Ngày
- Public URL của chatbot.
- Basic auth username/password để share cho nhóm test.
- Qdrant Cloud collection đã ingest.
- Checklist smoke test đã chạy và ghi kết quả.
- Ghi chú các lỗi/câu hỏi chatbot trả lời chưa tốt.
- Hướng dẫn ngắn:
  - cách chạy local
  - cách ingest lên production
  - cách xem logs
  - cách kiểm tra OpenAI/Qdrant usage

## Assumptions
- Ngày 1-3 đã có app local hoạt động ổn.
- Ingest script đã có option đọc env để trỏ local hoặc Qdrant Cloud.
- V1 chưa làm CI/CD reindex.
- V1 chưa dùng cloud storage; `raw-data` vẫn nằm trong private repo.
- Public test vẫn cần basic password vì dữ liệu HR có thể nhạy cảm.
