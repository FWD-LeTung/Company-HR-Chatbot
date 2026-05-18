# MinerU2.5-Pro trên Windows

Ghi chú này lưu cách dùng MinerU2.5-Pro cho HR RAG chatbot, dựa trên code hiện tại trong `source/ingestion/loaders.py` và `pyproject.toml`.

## 1. Không dùng nhánh legacy

Không dùng các API cũ sau cho MinerU2.5-Pro:

```python
from magic_pdf.pipe.UNIPipe import UNIPipe
from magic_pdf.pipe.TXTPipe import TXTPipe
from magic_pdf.rw.DiskReaderWriter import DiskReaderWriter
```

Nhánh `magic-pdf` 0.6.1 dễ kéo theo `detectron2`, PaddleOCR, NumPy/OpenCV ABI issues. Nó không phải code path chính chủ của MinerU2.5-Pro 1.2B trong README model.

## 2. Thư viện đúng

MinerU2.5-Pro README dùng:

```python
from transformers import AutoProcessor, Qwen2VLForConditionalGeneration
from mineru_vl_utils import MinerUClient
from mineru_vl_utils.post_process import json2md
```

Cài đặt theo project hiện tại:

```bash
uv sync
```

Hoặc cài trực tiếp:

```bash
uv pip install "mineru-vl-utils[transformers]" transformers pymupdf pillow
```

## 3. Python và CUDA

Project hiện dùng:

```toml
requires-python = ">=3.11, <3.13"
```

Torch CUDA 12.4 được cấu hình trong `pyproject.toml`:

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

Kiểm tra GPU:

```bash
python -c "import torch; print(torch.__version__); print(torch.cuda.is_available()); print(torch.version.cuda); print(torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'no cuda')"
```

Nếu thấy `+cpu` hoặc `cuda False`, model sẽ không chạy GPU.

## 4. Code pattern MinerU2.5-Pro

Load model:

```python
model = Qwen2VLForConditionalGeneration.from_pretrained(
    "opendatalab/MinerU2.5-Pro-2604-1.2B",
    dtype="auto",
    device_map="auto",
)

processor = AutoProcessor.from_pretrained(
    "opendatalab/MinerU2.5-Pro-2604-1.2B",
    use_fast=True,
)

client = MinerUClient(
    backend="transformers",
    model=model,
    processor=processor,
    image_analysis=False,
)
```

Parse một page PDF:

```python
doc = fitz.open(path)
page = doc[0]
pix = page.get_pixmap(dpi=200)
img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

content_list = client.two_step_extract(img)
markdown = json2md(content_list)
```

Parse nhiều page:

```python
parts = []

with fitz.open(path) as doc:
    for page_index, page in enumerate(doc, start=1):
        pix = page.get_pixmap(dpi=200)
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        content_list = client.two_step_extract(img)
        md_page = json2md(content_list).strip()
        if md_page:
            parts.append(f"\n\n# Page {page_index}\n{md_page}")

markdown = "".join(parts).strip()
```

## 5. Tích hợp LangChain Document

PDF output nên là Markdown:

```python
Document(
    page_content=markdown,
    metadata={
        "source_file": path.name,
        "file_type": "pdf",
        "page": None,
        "parser": "MinerU2.5-Pro-VLM",
        "device_used": "cuda" if torch.cuda.is_available() else "cpu",
    },
)
```

Sau này nếu muốn citation chính xác theo page, nên trả về một `Document` cho mỗi page thay vì gộp toàn bộ PDF thành một `Document`.

## 6. Test nhanh

Test import:

```bash
python -c "from mineru_vl_utils import MinerUClient; from mineru_vl_utils.post_process import json2md; from transformers import AutoProcessor, Qwen2VLForConditionalGeneration; print('imports ok')"
```

Test GPU:

```bash
python -c "import torch; print(torch.__version__, torch.cuda.is_available(), torch.version.cuda)"
```

Test một PDF:

```bash
python -c "from pathlib import Path; from source.ingestion.loaders import load_file; docs=load_file(Path('raw-data/05.TL.HCNS_Chinh sach TeamBuilding v1.1.pdf')); print(len(docs)); print(docs[0].metadata); print(docs[0].page_content[:500])"
```

## 7. Các lỗi đã gặp

### 7.1. Fallback sang PyMuPDF

Nguyên nhân cũ: dùng nhánh `magic-pdf` legacy, không phải MinerU2.5-Pro chính chủ.

Cách xử lý: dùng `mineru-vl-utils` và `MinerUClient.two_step_extract`.

### 7.2. Không tải được model Hugging Face

Triệu chứng:

```text
Failed to establish a new connection
couldn't connect to https://huggingface.co
```

Nguyên nhân:

- Network bị chặn.
- Sandbox/firewall chặn socket.
- Model chưa có trong local Hugging Face cache.

Cách xử lý:

- Chạy test trong terminal bình thường có internet.
- Đăng nhập Hugging Face nếu cần.
- Tải model trước vào cache.
- Hoặc set model id/path trỏ tới local folder đã tải.

### 7.3. Torch không thấy CUDA

Triệu chứng:

```text
torch ... +cpu
torch.cuda.is_available() == False
```

Cách xử lý:

- Kiểm tra `nvidia-smi`.
- Đảm bảo `pyproject.toml` dùng PyTorch CUDA index.
- Chạy lại `uv sync`.

### 7.4. `magic-pdf[full-cpu]` lỗi detectron2 hoặc NumPy

Đây là nhánh legacy, không dùng cho MinerU2.5-Pro nữa. Nếu bắt buộc dùng legacy, cần Python/NumPy tương thích riêng, nhưng không khuyến nghị cho project này.

## 8. Ghi chú thiết kế

- Không nên load model MinerU trong request web FastAPI.
- Nên chạy MinerU như preprocessing job offline:
  - PDF -> Markdown/JSON cache
  - Loader RAG đọc cache
  - Chunking/indexing chạy trên Markdown đã parse
- Trong giai đoạn Day 1 có thể load trực tiếp trong loader để test, nhưng về sau cần cache để tiết kiệm thời gian.
