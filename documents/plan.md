# Kế Hoạch 3 Ngày: HR RAG Chatbot Phase 1

## Summary
Mục tiêu 3 ngày là có bản local chạy được: ingest tài liệu từ `raw-data`, lưu vector vào Qdrant, hỏi đáp qua FastAPI/web chat, trả lời có citations. Phase 1 dùng LangChain nhưng giữ flow rõ ràng, chưa dùng LangGraph.

Stack:
- FastAPI monolith
- LangChain: `langchain-core`, `langchain-openai`, `langchain-qdrant`, `langchain-text-splitters`, `langchain-community`
- Qdrant local bằng Docker
- OpenAI API
- Pytest cho core tests

## Ngày 1: Project Skeleton + Ingestion Cơ Bản
Mục tiêu cuối ngày: chạy được Qdrant local, đọc được PDF/DOCX từ `raw-data`, split thành chunks có metadata.

Việc bạn code:
- Tạo cấu trúc thư mục:
  - `source/main.py`
  - `source/config.py`
  - `source/ingestion/loaders.py`
  - `source/ingestion/chunking.py`
  - `source/ingestion/metadata.py`
  - `scripts/ingest.py`
  - `tests/`
- Thêm dependency cần thiết:
  - `fastapi`, `uvicorn`
  - `langchain-core`
  - `langchain-openai`
  - `langchain-qdrant`
  - `langchain-text-splitters`
  - `langchain-community`
  - `qdrant-client`
  - parser libs cho PDF/DOCX/XLSX
  - `pytest`, `python-dotenv`
- Tạo `.env.example` với:
  - `OPENAI_API_KEY`
  - `OPENAI_CHAT_MODEL`
  - `OPENAI_EMBEDDING_MODEL`
  - `QDRANT_URL`
  - `QDRANT_COLLECTION`
  - `BASIC_AUTH_USERNAME`
  - `BASIC_AUTH_PASSWORD`
- Tạo `docker-compose.yml` cho Qdrant local.
- Viết loader cho PDF/DOCX trước.
- Dùng LangChain `Document` làm object chuẩn.
- Metadata tối thiểu:
  - `source_file`
  - `file_type`
  - `page` nếu có
  - `chunk_id`
  - `content_hash`
- Dùng `RecursiveCharacterTextSplitter` để split documents.

Mình hỗ trợ:
- Review cấu trúc thư mục.
- Giải thích loader/chunker.
- Debug lỗi dependency/parser.
- Review metadata trước khi qua ngày 2.

Test cuối ngày:
- Chạy Qdrant local được.
- Chạy script thử load documents và in ra số document/chunk.
- Pytest cho:
  - loader trả về `Document`
  - chunk có metadata bắt buộc
  - `content_hash` ổn định với cùng nội dung

## Ngày 2: Qdrant Ingest + Retrieval + Excel Có Kiểm Soát
Mục tiêu cuối ngày: ingest chunks vào Qdrant, retrieve được kết quả đúng source, Excel chỉ index sheet/cột được phép.

Việc bạn code:
- Viết module vector store:
  - khởi tạo `OpenAIEmbeddings`
  - khởi tạo `QdrantVectorStore`
  - tạo collection nếu chưa có
  - upsert documents
- Hoàn thiện `scripts/ingest.py`:
  - đọc toàn bộ `raw-data`
  - parse
  - chunk
  - upsert Qdrant
  - log số file/chunk đã ingest
- Thêm Excel ingestion có allowlist:
  - config dạng file Python/YAML/JSON đều được, nhưng phải rõ sheet/cột nào được phép
  - không index toàn bộ Excel mặc định
- Metadata cho Excel:
  - `source_file`
  - `file_type: xlsx`
  - `sheet`
  - `row_range`
  - `chunk_id`
  - `content_hash`
- Viết retrieval function:
  - input: question
  - output: list retrieved docs với score/source metadata
- Tạo bộ câu hỏi test nhỏ:
  - 3 câu về nội quy lao động
  - 2 câu về teambuilding
  - 2 câu về chứng chỉ/kỹ thuật
  - 1 câu ngoài tài liệu

Mình hỗ trợ:
- Review cách map Excel row thành text.
- Gợi ý chunk size/overlap.
- Debug Qdrant collection/vector dimension.
- Review output retrieval xem có bị chunk xấu hoặc metadata thiếu.

Test cuối ngày:
- Ingest thành công vào Qdrant.
- Query thử trả về đúng file/source.
- Pytest cho:
  - Excel allowlist không index sheet/cột ngoài danh sách
  - Qdrant retrieval trả về metadata cần thiết
  - câu hỏi mẫu retrieve đúng nhóm tài liệu

## Ngày 3: FastAPI Chat + Citations + Guardrail
Mục tiêu cuối ngày: có web chat local, hỏi đáp HR bằng RAG, câu trả lời có citations và không bịa khi thiếu nguồn.

Việc bạn code:
- Tạo FastAPI endpoints:
  - `GET /health`
  - `POST /api/chat`
  - `GET /`
- Tạo RAG service:
  - receive question
  - retrieve top-k docs từ Qdrant
  - build prompt có context
  - gọi `ChatOpenAI`
  - trả answer + citations
- Prompt policy:
  - trả lời tiếng Việt
  - chỉ dùng context
  - nếu không đủ thông tin thì nói không đủ thông tin trong dữ liệu hiện có
  - không tự suy diễn chính sách HR
- Citation response format:
  - `source_file`
  - `page` hoặc `sheet`
  - `snippet`
- Tạo web chat tối giản:
  - input câu hỏi
  - history câu trả lời
  - loading state
  - citations dưới câu trả lời
- Thêm basic password:
  - đơn giản bằng HTTP Basic Auth cho toàn app hoặc route chat
  - dùng env config

Mình hỗ trợ:
- Review prompt.
- Debug LangChain `ChatOpenAI`.
- Review API response schema.
- Review UI đủ dùng cho demo.
- Giúp tạo checklist demo.

Test cuối ngày:
- Hỏi một câu có trong policy, nhận câu trả lời đúng và có citation.
- Hỏi câu ngoài tài liệu, bot nói không đủ thông tin.
- Web chat chạy local.
- Pytest cho:
  - `/health`
  - `/api/chat` với mock retriever/LLM
  - citation format
  - guardrail khi retrieved docs rỗng

## Definition Of Done Sau 3 Ngày
- Qdrant local chạy bằng Docker.
- `scripts/ingest.py` ingest được `raw-data`.
- FastAPI app chạy local.
- Web chat hỏi đáp được.
- Câu trả lời có citations.
- Excel được index có chọn lọc.
- Có core tests cho parser, chunking, metadata, retrieval guard.
- Chưa cần deploy public, chưa cần CI/CD reindex, chưa cần cloud storage.

## Assumptions
- Bạn sẽ là người code chính.
- Mình hướng dẫn theo từng milestone, review và debug cùng bạn.
- Phase 1 ưu tiên học đúng RAG pipeline hơn là làm production hoàn chỉnh.
- LangGraph chưa dùng trong 3 ngày này.
