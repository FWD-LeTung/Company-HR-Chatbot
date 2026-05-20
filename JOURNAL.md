# Journal

## 18/05 - Config và FastAPI skeleton

- Dùng `pydantic-settings` thay vì tự gọi `dotenv.load_dotenv()` trong app backend.
- Lý do:
  - Có schema config rõ ràng.
  - Có default value và type validation.
  - Hợp với FastAPI/Pydantic.
  - Dễ mở rộng sang production env.
- FastAPI skeleton đã có endpoint `/health` trả:

```json
{
  "status": "ok",
  "env": "local"
}
```

## 18/05 - Loader tài liệu

### Quyết định ban đầu

- Dùng LangChain `Document` làm object chuẩn cho ingestion.
- Metadata tối thiểu:
  - `source_file`
  - `file_type`
  - `page`
  - `parser`
- DOCX dùng Kreuzberg.
- Markdown đọc trực tiếp bằng `utf-8-sig`.
- PDF cần parser mạnh hơn Kreuzberg vì tài liệu HR có layout, bảng, font tiếng Việt và scan/text-layer không ổn định.

### Kinh nghiệm với Kreuzberg

- Kreuzberg phù hợp cho DOCX/native text.
- Không nên dùng OCR built-in của Kreuzberg cho PDF trong project này.
- OCR/Kreuzberg từng cho output PDF bị mất dấu hoặc sai ký tự tiếng Việt, ví dụ `PHAT TRl£N`, `NQI BO`, `Ngimi`.

Kết luận:

```text
PDF  -> MinerU2.5-Pro VLM
DOCX -> Kreuzberg native text, không OCR
MD   -> đọc trực tiếp utf-8-sig
```

## 18/05 - MinerU2.5-Pro

### Điều quan trọng đã học

- `magic-pdf` 0.6.1 là pipeline legacy, không phải cách dùng chính chủ cho MinerU2.5-Pro 1.2B.
- Không nên tiếp tục dùng:
  - `magic_pdf.pipe.UNIPipe`
  - `magic_pdf.pipe.TXTPipe`
  - `magic_pdf.rw.DiskReaderWriter`
- Cách đúng theo README MinerU2.5-Pro là:
  - `mineru-vl-utils`
  - `MinerUClient`
  - `client.two_step_extract(image)`
  - `json2md(content_list)`

### Dependency hiện tại

`pyproject.toml` đang dùng:

```toml
requires-python = ">=3.11, <3.13"
```

Các dependency chính cho MinerU:

```toml
"mineru-vl-utils[transformers]>=0.1.0"
"pymupdf>=1.24.0"
"pillow>=10.0.0"
"torch>=2.6.0"
"torchvision"
```

Torch được cấu hình tải từ CUDA 12.4 index:

```toml
[[tool.uv.index]]
name = "pytorch-cu124"
url = "https://download.pytorch.org/whl/cu124"
explicit = true

[tool.uv.sources]
torch = { index = "pytorch-cu124" }
torchvision = { index = "pytorch-cu124" }
torchaudio = { index = "pytorch-cu124" }
```



### Lỗi đã gặp

- Python 3.13 không phù hợp với nhánh legacy `detectron2`.
- `magic-pdf[full-cpu]` kéo theo dependency cũ, dễ lỗi ABI trên Windows.
- NumPy 2.x từng gây lỗi ABI với OpenCV/detectron2 legacy.
- Torch CPU làm `torch.cuda.is_available()` trả `False`.
- Test thật MinerU2.5-Pro cần tải model từ Hugging Face. Nếu network/sandbox chặn sẽ fail ở bước tải `config.json`.

## 18-05

## 18/05 - Indexing, Vector Store, Chunking, Retrieval

- Chunking dùng LangChain `Document` làm object chuẩn, sau đó chia 2 lớp:
  - `MarkdownHeaderTextSplitter` cắt theo cấu trúc heading `#`, `##`, `###`, `####`.
  - `RecursiveCharacterTextSplitter` cắt tiếp các đoạn quá dài với `chunk_size=1000`, `chunk_overlap=150`.
- Mỗi chunk được bơm thêm ngữ cảnh vào đầu text:
  - tên tài liệu
  - đường dẫn heading dạng `h1 > h2 > h3`
  - giúp embedding/retrieval hiểu chunk đang thuộc mục nào.
- Metadata được chuẩn hóa bằng Pydantic `ChunkMetadata`, gồm:
  - `document_id`
  - `chunk_id`
  - `source_file`
  - `file_type`
  - `page`
  - `chunk_index`
  - `content_hash`
  - `parser`
  - `block_type`
  - `category`
- `content_hash`, `document_id`, `chunk_id` dùng SHA-256 để định danh nội dung ổn định, phục vụ reindex/dedupe về sau.
- Vector store dùng:
  - `OpenAIEmbeddings`
  - model lấy từ `OPENAI_EMBEDDING_MODEL`, mặc định `text-embedding-3-small`
  - `QdrantClient`
  - `QdrantVectorStore`
- Collection Qdrant hiện dùng tên `hr_policies_openai`.
- Khi collection chưa tồn tại, code gọi thử `embeddings.embed_query("Test")` để tự nhận diện vector dimension, rồi tạo collection với `Distance.COSINE`.
- Indexing flow:
  - nhận list chunks
  - init Qdrant collection nếu cần
  - gọi `vector_store.add_documents(documents=chunks)`
  - LangChain tự embed bằng OpenAI API và upsert vào Qdrant.
- Retrieval flow:
  - dùng cùng `OpenAIEmbeddings` và cùng collection Qdrant
  - gọi `similarity_search_with_score(query, k=top_k)`
  - hỗ trợ filter theo `metadata.source_file` bằng Qdrant `FieldCondition`
  - kết quả trả về dạng `(Document, score)`.
- Chat generation flow:
  - `stream_hr_chatbot()` gọi retrieval trước với `top_k=4`
  - format các retrieved chunks thành context block có source
  - dùng `ChatPromptTemplate` từ `system_prompt_v1.xml`
  - gọi `ChatOpenAI` với model từ `OPENAI_CHAT_MODEL`, `temperature=0.1`
  - stream từng phần câu trả lời về UI/API.

### Tiếp theo, tích hợp memory. 