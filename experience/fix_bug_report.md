# BÁO CÁO: PHÂN TÍCH VÀ GIẢI QUYẾT VẤN ĐỀ TRONG HỆ THỐNG AI CHATBOT

**Ngày**: 30/05/2026  
**Dự án**: Hệ thống HR Chatbot  
**Bối cảnh**: Quá trình sửa lỗi và xây dựng hệ thống

---

## 1. TỔNG QUAN

Trong quá trình sửa lỗi và triển khai hệ thống AI Chatbot cho bộ phận Nhân sự, nhóm phát hiện một số vấn đề ảnh hưởng đến độ chính xác và tin cậy của câu trả lời. Báo cáo này phân tích nguyên nhân gốc rễ của các vấn đề và phương pháp giải quyết đã áp dụng.

---

## 2. CÁC VẤN ĐỀ PHÁT HIỆN

### 2.1 Vấn Đề 1: Tra Cứu Thiếu Tài Liệu

**Biểu hiện**: Hệ thống trả lời thiếu thông tin hoặc đưa ra kết luận sai khi tra cứu tài liệu chính sách.

**Ví dụ thực tế**:
```
Câu hỏi: "quy chuẩn định dạng văn bản"
Kết quả trả về: Nội dung về "lưu trữ hồ sơ" và "phát biểu trước công chúng"
→ Không liên quan đến câu hỏi của người dùng
```

**Vấn đề** được phát hiện trong lần sửa lỗi thứ nhất khi hệ thống không thể tìm ra các quy định cụ thể về định dạng văn bản, mặc dù tài liệu này có trong cơ sở dữ liệu.

### 2.2 Vấn Đề 2: Bịa Đặt Thông Tin (Hallucination)

**Biểu hiện**: Chatbot tự động trả lời dựa trên kiến thức có sẵn từ quá trình huấn luyện (training data) thay vì thực hiện tra cứu tài liệu từ cơ sở dữ liệu của công ty.

**Ví dụ thực tế**:
```
Câu hỏi: "Mây giờ vào làm?"
Câu trả lời: "Giờ làm việc của công ty thường bắt đầu từ 8:00 sáng và kết thúc vào 5:00 chiều..."
→ Thông tin này có thể không chính xác với quy định thực tế của công ty
```

**Nguy cơ**: Khi sử dụng kiến thức từ training data (có thể đã lỗi thời hoặc không phù hợp với context của công ty), hệ thống có thể cung cấp thông tin sai lệ cho người dùng.

### 2.3 Vấn Đề 3: Tra Cứu Excel Phức Tạp

**Biểu hiện**: Với các file Excel có cấu trúc hàng/cột phức tạp và nhiều thông tin trùng lặp, hệ thống gặp khó khăn trong việc trích xuất thông tin chính xác theo yêu cầu người dùng.

**Ví dụ thực tế**:
- File danh bạ nhân viên có nhiều cột với tên tương tự
- Thông tin trùng lặp giữa các sheet hoặc các dòng
- Cấu trúc phức tạp dẫn đến kết quả tra cứu không chính xác

---

## 3. PHÂN TÍCH NGUYÊN NHÂN

### 3.1 Nguyên Nhân Của Vấn Đề 1: Hạn Chế Của Vector Search

Hệ thống tra cứu ban đầu chỉ sử dụng phương pháp Vector Search (tìm kiếm dựa trên sự tương đồng ngữ nghĩa). Phương pháp này hiệu quả với các câu hỏi chung chung nhưng gặp hạn chế với các câu hỏi đặc thù:

**Cơ chế hoạt động của Vector Search**:
- Chuyển đổi câu hỏi và tài liệu thành vector (số hóa)
- Tìm kiếm dựa trên độ tương đồng ngữ nghĩa (cosine similarity)
- Ưu tiên tài liệu có ngữ nghĩa gần giống câu hỏi

**Hạn chế**:
- Bỏ qua sự khớp chính xác từ khóa (keyword matching)
- Với các câu hỏi domain-specific như "quy chuẩn định dạng văn bản", từ khóa quan trọng như "định dạng", "văn bản" bị bỏ qua
- Hệ thống ưu tiên tài liệu có ngữ nghĩa tương tự nhưng không chứa từ khóa cần thiết

**Kết quả**: Tài liệu chứa từ khóa quan trọng bị xếp hạng thấp, trong khi tài liệu không liên quan nhưng có ngữ nghĩa tương tự được xếp hạng cao.

### 3.2 Nguyên Nhân Của Vấn Đề 2: Thiếu Cơ Chế Kiểm Soát

Sau khi phân tích, nhóm phát hiện hai nguyên nhân chính:

**Nguyên nhân 1: System Prompt Cho Phép Bypass Tool**

Câu lệnh hệ thống (system prompt) ban đầu quy định:
```
"CHỈ gọi tool khi cần thiết. Tránh gọi tool nếu câu hỏi quá mơ hồ."
```

Quy định này cho phép AI tự quyết định khi nào KHÔNG cần công cụ tra cứu, tạo ra kẽ hở để AI bypass công cụ và trả lời từ kiến thức có sẵn.

**Nguyên nhân 2: Không Có Validation Logic**

Quy trình xử lý câu hỏi không có bước kiểm tra xem công cụ tra cứu có được gọi hay không:
```
Câu hỏi → AI Xử Lý → Trả Lời
              ↑
         Không có kiểm tra
```

Điều này cho phép AI trả lời trực tiếp mà không cần tra cứu, dẫn đến thông tin bịa đặt từ training data.

### 3.3 Nguyên Nhân Của Vấn Đề 3: Cấu Trúc Excel Phức Tạp

File danh bạ nhân viên có các đặc điểm:
- Nhiều cột với tên tương tự hoặc nội dung trùng lặp
- Cấu trúc hàng/cột phức tạp
- Thông tin phân tán qua nhiều sheet

Phương pháp tra cứu bằng `endswith` (khớp đuôi tên) hoạt động tốt với tên đơn giản nhưng gặp hạn chế khi:
- Tên nhân viên có định dạng phức tạp
- Thông tin trùng lặp giữa các dòng
- Cần trích xuất nhiều trường thông tin cùng lúc

---

## 4. PHƯƠNG PHÁP GIẢI QUYẾT

### 4.1 Giải Quyết Vấn Đề 1: Hybrid Search

Để khắc phục hạn chế của Vector Search, nhóm đã triển khai phương pháp Hybrid Search kết hợp Vector Search và BM25 Keyword Search.

**Nguyên lý hoạt động**:

**Vector Search** (tìm kiếm ngữ nghĩa):
- Tìm tài liệu có ngữ nghĩa tương tự câu hỏi
- Phù hợp với câu hỏi chung chung

**BM25 Keyword Search** (tìm kiếm từ khóa):
- Tìm tài liệu chứa từ khóa chính xác
- Phù hợp với câu hỏi domain-specific

**RRF Fusion** (kết hợp kết quả):
```
Score_hybrid = 1/(k + rank_vector) + 1/(k + rank_bm25)
```

Tài liệu xuất hiện trong cả hai kết quả tìm kiếm sẽ được xếp hạng cao nhất.

**Triển khai**:
- Sử dụng pyvi (Vietnamese tokenizer) để phân tách từ tiếng Việt chính xác
  - Ví dụ: "định dạng văn bản" → ["định", "dạng", "văn_bản"]
  - Từ ghép "văn_bản" được xem như một đơn vị duy nhất
- Xây dựng chỉ mục BM25 từ tài liệu trong Qdrant
- Kết hợp kết quả từ hai phương pháp bằng RRF fusion

**Kết quả**:
- Câu hỏi "quy chuẩn định dạng văn bản": Tìm được tài liệu liên quan đến giao tiếp email và định dạng tài liệu
- Câu hỏi "nghỉ phép năm": Tìm được file "QUY ĐỊNH VỀ NGHỈ PHÉP.docx" chính xác

### 4.2 Giải Quyết Vấn Đề 2: Tool Enforcement

Nhóm đã triển khai cơ chế kiểm soát hai lớp để đảm bảo AI luôn sử dụng công cụ tra cứu.

**Lớp 1: Cập Nhật System Prompt**

Câu lệnh hệ thống được cập nhật:
```
"Đối với MỖI câu hỏi: BẮT BUỘC phải gọi một trong hai công cụ: tra_cuu_chinh_sach hoặc tra_cuu_danh_ba. 
KHÔNG TỰ TRẢ LỜI từ knowledge của mình."
```

**Lớp 2: Validation Logic**

Quy trình xử lý mới:
```
Câu hỏi → AI Xử Lý → Kiểm Tra Tool Calls → Trả Lời
                              ↑
                         Bắt buộc kiểm tra
```

Logic kiểm tra:
1. Theo dõi xem có tool nào được gọi không
2. Nếu không có tool → trả về thông báo liên hệ HR
3. Nếu tool được gọi nhưng không tìm thấy kết quả → trả về thông báo liên hệ HR

**Thông báo fallback**:
```
"Tôi không có câu trả lời cho câu hỏi này. 
Các thông tin về hành chính vui lòng liên hệ HR Admin Nguyễn Thị Quỳnh Anh - SĐT 0913244513. 
Các thông tin về chương trình đào tạo và học tập vui lòng liên hệ HR L&D Bùi Thị Hà - SĐT 0313214512"
```

### 4.3 Giải Quyết Vấn Đề 3: Cải Thiện Tra Cứu Excel

Phương pháp hiện tại sử dụng Polars DataFrame để xử lý file Excel với các cải tiến:

**Phương pháp tra cứu hiện tại**:
- Sử dụng `endswith` để khớp tên nhân viên
- Lọc theo chức danh nếu có thông tin
- Xử lý trường hợp trùng tên bằng cách yêu cầu xác nhận từ người dùng

**Điểm mạnh**:
- Tra cứu nhanh với DataFrame cache
- Xử lý tốt trường hợp trùng tên
- Yêu cầu xác nhận trước khi cung cấp thông tin liên hệ

**Hạn chế vẫn còn**:
- Cần cải thiện xử lý file Excel với cấu trúc phức tạp hơn
- Cần thêm phương pháp trích xuất thông tin từ các cell merged hoặc phức tạp

---

## 5. KẾT QUẢ & ĐÁNH GIÁ

### 5.1 Kết Quả Testing

**Test Suite**: 7/7 bài kiểm tra vượt qua

**Kết quả so sánh trước/sau**:

| Vấn đề | Trước | Sau | Kết quả |
|--------|-------|-----|---------|
| "Mây giờ vào làm?" | Trả lời từ training data (không gọi tool) | Bắt buộc gọi tool, trả lời từ database | ✅ Đã fix |
| "quy chuẩn định dạng văn bản" | Kết quả không liên quan | Tìm được tài liệu liên quan hơn | ✅ Cải thiện |
| "nghỉ phép năm" | Kết quả mixed | Tìm được file chính xác | ✅ Cải thiện |

### 5.2 Đánh Giá Hiệu Suất

**Ưu điểm**:
- Tool enforcement hoàn toàn ngăn chặn hallucination từ training data
- Hybrid search cải thiện độ chính xác cho các câu hỏi domain-specific
- pyvi tokenizer xử lý tốt từ ghép tiếng Việt

**Hạn chế**:
- Thời gian tra cứu tăng thêm ~10-20ms do BM25 processing
- Cần rebuild BM25 index khi có tài liệu mới (manual process)
- Tra cứu Excel vẫn cần cải thiện cho cấu trúc phức tạp

### 5.3 Bài Học Rút Ra

1. **Cần enforcement layer cho AI systems**: AI model không thể tự tin cậy để luôn follow instructions - cần validation logic
2. **Hybrid search phù hợp cho domain-specific queries**: Vector search alone không đủ cho các chuyên ngành
3. **Vietnamese NLP cần word segmentation**: pyvi giúp xử lý từ ghép tiếng Việt chính xác hơn
4. **Excel processing cần chiến lược linh hoạt**: Cần combine multiple methods cho các cấu trúc phức tạp

---

## 6. KẾT LUẬN

Các vấn đề phát hiện trong quá trình sửa lỗi đã được phân tích và giải quyết:

1. **Tra cứu thiếu tài liệu**: Giải quyết bằng Hybrid Search (Vector + BM25)
2. **Bịa đặt thông tin**: Giải quyết bằng Tool Enforcement (System Prompt + Validation Logic)
3. **Tra cứu Excel phức tạp**: Đã có cải thiện, vẫn cần tiếp tục optimize

Hệ thống hiện tại đã tin cậy hơn, đảm bảo AI luôn tra cứu từ cơ sở dữ liệu của công ty trước khi trả lời, và phương pháp tìm kiếm kết hợp cung cấp kết quả chính xác hơn cho các câu hỏi cụ thể.

---

## TÀI LIỆU THAM KHẢO

1. BM25 Algorithm: Robertson & Zaragoza (2009) - "The Probabilistic Relevance Framework: BM25 and Beyond"
2. RRF Fusion: Cormack et al. (2009) - "Reciprocal Rank Fusion outperforms Condorcet and individual Rank Learning Methods"
3. pyvi: Vietnamese Word Segmentation Toolkit
4. LangChain: Framework for building LLM applications
5. Qdrant: Vector Database for similarity search

---

**Người lập báo cáo**: Nhóm phát triển HR Chatbot  
**Ngày**: 30/05/2026  
**Trạng thái**: Đã hoàn thành fix và testing
