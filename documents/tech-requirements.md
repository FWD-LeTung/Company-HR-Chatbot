# Plan Chatbot RAG HR Theo Kiểu Cùng Làm

## Summary
Xây dựng HR RAG chatbot bằng **FastAPI monolith**, web chat có citations, dùng **OpenAI API** cho chat/embedding và **Qdrant** làm vector database. Cách làm theo milestone: bạn code từng phần, mình hướng dẫn, review thiết kế, giúp debug và điều chỉnh test.

Nguồn dữ liệu v1 là `raw-data`, repo private. Public URL có **basic password** để nhiều người test mà không mở dữ liệu HR hoàn toàn ra ngoài.

## Architecture
- **Backend/UI**: FastAPI monolith.
  - Serve web chat HTML/CSS/JS đơn giản.
  - API chính: chat query, health check, metadata/index status.
- **Vector DB**:
  - Dev local: Qdrant Docker.
  - Deploy: Qdrant Cloud managed để web app public chạy ổn và không phụ thuộc disk của app host.
  - Qdrant Cloud có free cluster theo docs/pricing hiện tại: https://qdrant.tech/documentation/cloud/create-cluster/, https://qdrant.tech/pricing/
- **Deploy path**:
  - Phase đầu: local ingest trước.
  - Phase deploy: app host như Render/Fly/Railway + Qdrant Cloud.
  - CI/CD reindex để sau, không làm ngay ở milestone đầu.
  - Fly/Render đều hỗ trợ Docker deploy; nếu dùng persistent disk thì phải cẩn thận vì app disk/volume không phải lựa chọn đẹp nhất cho vector DB production. Sources: https://fly.io/docs/launch/deploy/, https://fly.io/docs/volumes/overview/, https://render.com/docs/deploys/

## Data Processing
- Tạo pipeline offline `ingest`:
  - Đọc PDF, DOCX, XLSX từ `raw-data`.
  - Parse text, normalize tiếng Việt, bỏ dòng rỗng/nhiễu lặp nếu cần.
  - Chunk theo cấu trúc tài liệu trước: page/heading/sheet/row group.
  - Fallback chunk theo token/character với overlap nhỏ.
- Excel dùng chính sách **index có chọn lọc**:
  - Không index toàn bộ workbook mặc định.
  - Tạo allowlist sheet/cột được phép.
  - Contact/personnel data chỉ đưa vào nếu có lý do rõ và được cấu hình.
- Mỗi chunk lưu vào Qdrant gồm vector + payload metadata:
  - `source_file`
  - `file_type`
  - `page` hoặc `sheet`
  - `row_range` nếu từ Excel
  - `chunk_id`
  - `text`
  - `content_hash`
  - `ingested_at`
  - `allowed_audience` mặc định `internal_test`
- Khi file đổi, dùng `content_hash` để biết cần reindex.

## RAG Behavior
- Retrieval:
  - Embed câu hỏi.
  - Search Qdrant top-k.
  - Optional rerank ở phase sau, chưa bắt buộc v1.
- Answer policy:
  - Trả lời tiếng Việt.
  - Chỉ dùng retrieved context.
  - Nếu không đủ nguồn, nói rõ không có đủ thông tin trong dữ liệu hiện có.
  - Luôn trả citations dạng: file + page/sheet + snippet.
- UI:
  - Chat input, history, loading state.
  - Hiển thị citations dưới câu trả lời.
  - Có basic password cho public test.

## Testing
- Core tests trước:
  - Parser đọc được PDF/DOCX/XLSX mẫu.
  - Chunker tạo metadata đúng.
  - Excel allowlist không index cột/sheet ngoài cấu hình.
  - Retrieval trả về đúng source cho câu hỏi mẫu.
  - Guardrail: câu hỏi ngoài tài liệu phải trả lời “không đủ thông tin”.
- Eval chất lượng dùng **LLM-as-judge**:
  - Tạo file golden questions gồm: question, expected source, expected facts.
  - Judge kiểm tra groundedness, citation correctness, answer completeness.
  - Chạy thủ công/local trước; CI eval để phase sau vì có chi phí OpenAI.

## Milestones
1. **Project skeleton**
   - FastAPI app chạy được local.
   - Qdrant Docker chạy được.
   - `.env.example` có OpenAI/Qdrant/basic auth config.

2. **Ingestion v1**
   - Parse PDF/DOCX.
   - Chunk + metadata.
   - Upsert vào Qdrant.
   - Test parser/chunker cơ bản.

3. **Excel controlled ingestion**
   - Thêm allowlist sheet/cột.
   - Index có chọn lọc.
   - Test chống index nhầm dữ liệu nhạy cảm.

4. **RAG API**
   - Endpoint chat.
   - Retrieval từ Qdrant.
   - Prompt grounded answer + citations.
   - Test retrieval/guardrail.

5. **Web chat**
   - UI chat tối giản, mượt.
   - Citations rõ ràng.
   - Basic password.

6. **Deploy alpha**
   - Qdrant Cloud.
   - Deploy FastAPI app public.
   - Chạy ingest local hoặc one-off job trỏ vào Qdrant Cloud.
   - Sau khi ổn mới thêm CI/CD reindex.

## Collaboration Workflow
- Bạn code theo từng milestone.
- Mình hướng dẫn trước mỗi milestone: mục tiêu, file nên tạo, lệnh test, lỗi thường gặp.
- Sau mỗi milestone, bạn gửi code/log/lỗi; mình review và đề xuất chỉnh.
- Mình không implement toàn bộ thay bạn, trừ khi bạn yêu cầu một đoạn mẫu hoặc cần debug cụ thể.

## Assumptions
- Repo là private.
- V1 chưa cần login user thật, chỉ basic password.
- V1 chưa cần upload tài liệu qua UI.
- Cloud storage chuyên nghiệp sẽ là phase sau, khi đã có RAG chạy ổn với `raw-data` committed trong private repo.
