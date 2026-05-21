# KẾ HOẠCH TRIỂN KHAI DỰ ÁN HR RAG CHATBOT (BẢN FINAL)

## 1. Mục tiêu dự án
Xây dựng trợ lý ảo AI (Chatbot) nội bộ cho phòng Nhân sự, có khả năng tra cứu các chính sách, quy định, và thông tin nhân viên dựa trên dữ liệu thật của doanh nghiệp (PDF, Word, Excel). Đảm bảo tính bảo mật dữ liệu cao nhất và trải nghiệm người dùng mượt mà.

## 2. Kiến trúc Công nghệ
- **Backend Framework:** FastAPI (Python)
- **AI / RAG Framework:** LangChain, OpenAI API (gpt-4o-mini, text-embedding-3-small)
- **Vector Database:** Qdrant
- **Data Ingestion:** Polars + Calamine (đọc Excel siêu tốc), PyMuPDF (đọc PDF)
- **Frontend:** HTML tĩnh + Vanilla JS + Tailwind CSS (truyền thống, nhẹ, không cần build)
- **Bảo mật:** Basic Auth, Configuration via `pydantic-settings`

---

## 3. Các Giai Đoạn Triển Khai (Phases)

### ✅ Giai đoạn 1: Data Ingestion (Xử lý Dữ liệu thô) - [HOÀN THÀNH]
- Xây dựng module đọc PDF/Word với text splitter.
- Xây dựng module `excel_loader.py` kết hợp luồng **Allowlist JSON** để tự động loại bỏ các cột nhạy cảm (Lương, CCCD) trước khi nạp vào AI.
- Đính kèm Metadata chặt chẽ: `source_file`, `page_number` (cho PDF), `row_index` (cho Excel).

### ✅ Giai đoạn 2: Vectorization & Indexing - [HOÀN THÀNH]
- Chuyển đổi Text chunks thành Vectors thông qua OpenAI Embeddings.
- Lưu trữ vào Qdrant (Local/Docker).
- Viết các hàm Query tìm kiếm Semantic Search cơ bản.

### ✅ Giai đoạn 3: Core Chat Engine & Memory - [HOÀN THÀNH]
- Sử dụng `RunnableWithMessageHistory` (Sliding Window) để quản lý lịch sử hội thoại cho từng `session_id`.
- Sử dụng `RunnablePassthrough` để bơm Context (tài liệu) vào Prompt.
- Streaming response: Trả chữ về theo luồng (chunk by chunk) giống ChatGPT.

### ✅ Giai đoạn 4: FastAPI & Security (Mặt tiền hệ thống) - [HOÀN THÀNH]
- Xây dựng cấu hình tập trung bằng `pydantic-settings`.
- Dựng 3 Endpoints: `GET /health`, `POST /api/v1/chat/stream`, `DELETE /api/v1/chat/sessions/{session_id}`.
- Cài đặt "Chốt chặn" bảo mật **Basic Auth** để bảo vệ API khỏi các truy cập trái phép ở giai đoạn UAT.

### ✅ Giai đoạn 5: Frontend UI (Giao diện người dùng) - [HOÀN THÀNH]
- Trang SPA tĩnh (Single Page Application).
- State 1: Form Đăng nhập (Mã hóa credentials gửi kèm API).
- State 2: Khung Chatbot (Bắt sự kiện stream chunks và hiển thị).

---

## 4. Giai Đoạn 6: Nâng Cấp Nâng Cao (Advanced Features - ĐANG THỰC HIỆN)

### Feature 6.1: Routing & Agentic RAG cho File Excel (Danh bạ)
**Vấn đề:** Trí nhớ ngữ nghĩa (Vector) tìm kiếm Exact Match rất kém (ví dụ: tìm "Hoài" ra cả "Nguyễn Hoài Anh").
**Giải pháp:** - Gỡ các chunk Excel ra khỏi Qdrant Vector DB.
- Viết một Tool Python: `tra_cuu_danh_ba(ten_nhan_vien)`.
- Cấu hình Router (LLM Agent): Khi người dùng hỏi chính sách -> Chuyển luồng vào Qdrant (RAG). Khi hỏi thông tin 1 nhân viên -> LLM gọi hàm `tra_cuu_danh_ba` (SQL/Polars Filter) để trả về đích danh chính xác 100%.

### Feature 6.2: Clickable Citations (Trích dẫn xem trước trang - Nice to have)
**Vấn đề:** Bot trả lời có trích dẫn nguồn, nhưng user không thể đối chiếu nhanh.
**Giải pháp:** 1. **Tinh chỉnh Prompt:** Ép AI khi sinh câu trả lời phải format trích dẫn dưới dạng Markdown Link đặc biệt. 
   *Ví dụ:* `[Quy_dinh_thai_san.pdf - Trang 5](/api/v1/documents/preview?file=Quy_dinh_thai_san.pdf&page=5)`.
2. **Backend API mới:** Tạo endpoint `GET /api/v1/documents/preview`. 
   - Nhận parameter: Tên file và Số trang.
   - Logic: Dùng `PyMuPDF` cắt đúng 1 trang đó (render ra ảnh PNG hoặc Text) và trả về.
3. **Frontend Popup:** Bắt sự kiện click vào link trích dẫn -> Không mở tab mới mà hiện lên một **Modal/Popup** ngay giữa màn hình chứa hình ảnh/nội dung của đúng trang tài liệu đó, giúp user an tâm về độ chính xác.

## Giai đoạn 7: Deploy & Monitoring (Triển khai & Giám sát)
*Mục tiêu: Đưa ứng dụng lên môi trường Cloud để người dùng thực tế có thể test.*
* 📝 **Chuyển đổi DB:** Tạo Cluster trên Qdrant Cloud và đẩy dữ liệu (Index) lên bản Cloud.
* 📝 **Deploy Backend:** Đưa FastAPI lên nền tảng Cloud (Render/Fly/Railway).
* 📝 **Thiết lập Giám sát (Monitoring):** Cài đặt structured logging để theo dõi Request ID, Latency (độ trễ), Token Usage và tỷ lệ lỗi.