# Kế Hoạch Dự Án: HR RAG Chatbot (Phase 1)

**Trạng thái:**
✅ Đã hoàn thành (Done) | ⏳ Đang tiến hành/Cần xử lý ngay (In Progress) | 📝 Tồn đọng (To Do)

## Giai đoạn 1: Xây dựng Data Pipeline (Nền tảng dữ liệu)
*Mục tiêu: Đọc, làm sạch, phân mảnh và gắn nhãn mọi loại tài liệu nhân sự.*
* ✅ **Khởi tạo dự án:** Tổ chức cấu trúc thư mục chuẩn, quản lý dependency bằng `uv` (có `pyproject.toml`, `uv.lock`).
* ✅ **Đọc tài liệu Text/PDF:** Hoàn thiện `loaders.py`, tích hợp thành công MinerU VLM (cho PDF) và Kreuzberg (cho DOCX/MD).
* ✅ **Xử lý Metadata:** Viết module `metadata.py` với cơ chế băm SHA-256 (tạo `chunk_id`, `document_id`) giúp chống trùng lặp dữ liệu.
* ✅ **Chiến thuật Chunking:** Nâng cấp `chunking.py` lên chuẩn Enterprise (Cắt 2 lớp theo Markdown + Bơm Context vào từng chunk).
* ✅ **[HOT] Đọc tài liệu Excel (XLSX):** Viết module đọc Excel có kiểm soát (Allowlist). Chỉ quét các Sheet/Cột được cấp phép, loại bỏ dữ liệu nhạy cảm.

## Giai đoạn 2: Indexing & Retrieval (Lưu trữ và Tìm kiếm)
*Mục tiêu: Mã hóa dữ liệu thành Vector và xây dựng thuật toán truy xuất chính xác.*
* ✅ **Dựng Vector DB:** Cấu hình thành công Qdrant chạy local qua Docker.
* ✅ **Mã hóa (Embedding):** Khởi tạo `vector_store.py`, sử dụng OpenAI `text-embedding-3-small` để nhúng dữ liệu vào Qdrant.
* ✅ **Thuật toán Tìm kiếm:** Xây dựng `search_engine.py` dùng Vector Search kết hợp bộ lọc siêu dữ liệu (Metadata Filtering theo `source_file`).
* 📝 **Tối ưu Tìm kiếm:** Bật tính năng Hybrid Search (nếu cần thiết sau này) để tìm chính xác các mã tài liệu/tên riêng.

## Giai đoạn 3: LLM Generation & Memory (Sinh câu trả lời & Ngữ cảnh)
*Mục tiêu: Gắn "não" cho Chatbot, giúp nó trả lời trôi chảy, có trích dẫn và nhớ được lịch sử chat.*
* ✅ **Kiến trúc Sinh văn bản:** Viết `chat_engine.py`, tích hợp OpenAI `gpt-4o-mini` với tính năng Streaming (phản hồi theo thời gian thực).
* ✅ **Kiểm soát ảo giác (Guardrails):** Chuyển đổi System Prompt sang định dạng XML chuẩn, tách thành file riêng (`prompts/system_prompt.xml`) để ép AI trả lời dựa trên Context và luôn kèm Citation (trích dẫn).
* ✅ **[HOT] Bộ nhớ Hội thoại (Chat Memory):** Tích hợp `ChatMessageHistory` để Chatbot nhớ được ngữ cảnh các câu hỏi trước đó của nhân viên.

## Giai đoạn 4: Đóng gói API & Giao diện (FastAPI + UI)
*Mục tiêu: Biến các script Python thành một dịch vụ Web/API thực thụ.*
* ✅ **Cấu hình hệ thống:** Hoàn thiện `config.py` dùng `pydantic-settings` để quản lý biến môi trường tập trung.
* ✅ **Xây dựng Endpoint:** Bọc logic vào `main.py` với các endpoint `/health` và `/api/v1/chat/stream`.
* ✅ **Giao diện Chat Web:** Xây dựng trang HTML/JS tĩnh đơn giản, có khả năng render Markdown, Streaming và hiển thị Citations.
* ✅ **Bảo mật cơ bản:** Thêm Basic Auth (Username/Password) vào API để bảo vệ dữ liệu khi public nghiệm thu.



## Giai đoạn 5: Deploy & Monitoring (Triển khai & Giám sát)
*Mục tiêu: Đưa ứng dụng lên môi trường Cloud để người dùng thực tế có thể test.*
* 📝 **Chuyển đổi DB:** Tạo Cluster trên Qdrant Cloud và đẩy dữ liệu (Index) lên bản Cloud.
* 📝 **Deploy Backend:** Đưa FastAPI lên nền tảng Cloud (Render/Fly/Railway).
* 📝 **Thiết lập Giám sát (Monitoring):** Cài đặt structured logging để theo dõi Request ID, Latency (độ trễ), Token Usage và tỷ lệ lỗi.