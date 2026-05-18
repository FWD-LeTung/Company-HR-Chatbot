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

### Code pattern hiện tại

Loader PDF trong `source/ingestion/loaders.py` làm theo luồng:

```text
PDF page -> PyMuPDF render image -> MinerUClient.two_step_extract -> json2md -> LangChain Document
```

Model:

```python
Qwen2VLForConditionalGeneration.from_pretrained(
    "opendatalab/MinerU2.5-Pro-2604-1.2B",
    dtype="auto",
    device_map="auto",
)
```

Render page:

```python
pix = page.get_pixmap(dpi=200)
img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
```

Extract:

```python
content_list = client.two_step_extract(img)
md_page = json2md(content_list)
```

### Lỗi đã gặp

- Python 3.13 không phù hợp với nhánh legacy `detectron2`.
- `magic-pdf[full-cpu]` kéo theo dependency cũ, dễ lỗi ABI trên Windows.
- NumPy 2.x từng gây lỗi ABI với OpenCV/detectron2 legacy.
- Torch CPU làm `torch.cuda.is_available()` trả `False`.
- Test thật MinerU2.5-Pro cần tải model từ Hugging Face. Nếu network/sandbox chặn sẽ fail ở bước tải `config.json`.

### Hướng tiếp theo

- Ổn định CUDA/PyTorch trước khi parse toàn bộ PDF.
- Test từng PDF một.
- Sau khi MinerU parse ổn, nên cache Markdown/JSON output để không chạy VLM lại mỗi lần ingest.
- Về lâu dài, MinerU nên là preprocessing job offline, không chạy trực tiếp trong request FastAPI.
