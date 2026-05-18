import sys
import torch
import fitz  # PyMuPDF
from PIL import Image
from pathlib import Path
from langchain_core.documents import Document
from kreuzberg import extract_file_sync, ExtractionConfig

from transformers import AutoProcessor, Qwen2VLForConditionalGeneration
from mineru_vl_utils import MinerUClient
from mineru_vl_utils.post_process import json2md

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

SUPPORTED_EXTENSIONS = [".pdf", ".docx", ".md"]

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
print(f"[System] Khởi tạo Pipeline thành công. Thiết bị xử lý MinerU VLM: {DEVICE.upper()}")


print("[System] Đang nạp mô hình MinerU2.5-Pro-1.2B vào bộ nhớ...")
model = Qwen2VLForConditionalGeneration.from_pretrained(
    "opendatalab/MinerU2.5-Pro-2604-1.2B", 
    dtype="auto", 
    device_map="auto"
)

processor = AutoProcessor.from_pretrained(
    "opendatalab/MinerU2.5-Pro-2604-1.2B", 
    use_fast=True
)

client = MinerUClient(
    backend="transformers", 
    model=model, 
    processor=processor,
    image_analysis=False 
)


def process_pdf_mineru(path: Path) -> list[Document]:
    print(f"  -> [MinerU VLM] Đang phân tích cấu trúc trực quan: {path.name}")
    try:
        full_markdown_parts = []
        doc = fitz.open(path)
        
        for page_index, page in enumerate(doc, start=1):
            pix = page.get_pixmap(dpi=200)
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        
            content_list = client.two_step_extract(img)
            md_page = json2md(content_list)
            
            if md_page.strip():
                full_markdown_parts.append(f"\n\n# Page {page_index}\n{md_page.strip()}")
                
        text = "".join(full_markdown_parts).strip()
        if not text:
            return []

        return [
            Document(
                page_content=text,
                metadata={
                    "source_file": path.name,
                    "file_type": "pdf",
                    "page": None,
                    "parser": "MinerU2.5-Pro-VLM",
                    "device_used": DEVICE
                }
            )
        ]
    except Exception as e:
        print(f"  -> [MinerU VLM ERROR] Không thể bóc tách {path.name}: {e}")
        return []


def process_text_kreuzberg(path: Path) -> list[Document]:
    print(f"  -> [Kreuzberg] Đang trích xuất văn bản gốc: {path.name}")
    
    config = ExtractionConfig(
        enable_quality_processing=True,
    )

    try:
        result = extract_file_sync(path, config=config)
        text = result.content.strip()

        if not text:
            return []

        return [
            Document(
                page_content=text,
                metadata={
                    "source_file": path.name,
                    "file_type": "docx",
                    "page": None,
                    "parser": "Kreuzberg_NativeText",
                    "tables_count": len(result.tables) if result.tables else 0,
                }
            )
        ]
    except Exception as e:
        print(f"  -> [Kreuzberg ERROR] Không thể đọc {path.name}: {e}")
        return []


def process_markdown(path: Path) -> list[Document]:
    print(f"  -> [Native] Đang đọc file Markdown: {path.name}")

    try:
        text = path.read_text(encoding="utf-8-sig").strip()

        if not text:
            return []

        return [
            Document(
                page_content=text,
                metadata={
                    "source_file": path.name,
                    "file_type": "md",
                    "page": None,
                    "parser": "utf8_native",
                }
            )
        ]
    except Exception as e:
        print(f"  -> [Markdown ERROR] Không thể đọc {path.name}: {e}")
        return []


def load_file(path: Path) -> list[Document]:
    """Bộ định tuyến kiểm tra phần mở rộng của tệp để phân phối thuật toán."""
    ext = path.suffix.lower()

    if ext == ".pdf":
        return process_pdf_mineru(path)
    if ext == ".docx":
        return process_text_kreuzberg(path)
    if ext == ".md":
        return process_markdown(path)

    print(f"  -> Bỏ qua định dạng không hỗ trợ: {path.name}")
    return []


def load_documents(raw_data_dir: str) -> list[Document]:
    root = Path(raw_data_dir)
    documents: list[Document] = []

    for path in root.iterdir():
        if not path.is_file():
            continue

        if path.suffix.lower() not in SUPPORTED_EXTENSIONS:
            continue

        documents.extend(load_file(path))

    print(f"\n[Done] Toàn bộ quy trình hoàn tất. Tổng số tài liệu trong hệ thống RAG: {len(documents)}")
    return documents