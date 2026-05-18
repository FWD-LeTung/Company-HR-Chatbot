import pytest
from pathlib import Path
import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from source.ingestion.loaders import load_file, SUPPORTED_EXTENSIONS

# ==========================================
# SETUP (Tạo dữ liệu giả lập để test)
# ==========================================
@pytest.fixture
def mock_docs_dir(tmp_path):
    """
    Tạo một thư mục tạm thời (tmp_path) chứa các file giả lập 
    chỉ tồn tại trong lúc chạy test.
    """
    # Tạo file Markdown giả
    md_file = tmp_path / "test_doc.md"
    md_file.write_text("# Tài liệu Test\nĐây là nội dung file MD.", encoding="utf-8-sig")
    
    # Tạo file TXT (không được hỗ trợ)
    txt_file = tmp_path / "unsupported.txt"
    txt_file.write_text("Hello world")
    
    return tmp_path

# ==========================================
# CÁC TEST CASES
# ==========================================

def test_supported_extensions():
    """Kiểm tra xem danh sách đuôi file hỗ trợ có đúng như thiết kế không."""
    assert ".pdf" in SUPPORTED_EXTENSIONS
    assert ".docx" in SUPPORTED_EXTENSIONS
    assert ".md" in SUPPORTED_EXTENSIONS

def test_load_markdown_file(mock_docs_dir):
    """Test luồng đọc file Markdown (luồng nhẹ nhất, không cần model/OCR)"""
    md_path = mock_docs_dir / "test_doc.md"
    
    # Gọi hàm từ loaders.py
    docs = load_file(md_path)
    
    # Kiểm tra kết quả
    assert len(docs) == 1
    assert docs[0].page_content == "# Tài liệu Test\nĐây là nội dung file MD."
    assert docs[0].metadata["file_type"] == "md"
    assert docs[0].metadata["parser"] == "utf8_native"

def test_unsupported_file_format(mock_docs_dir):
    """Test xem hệ thống có bỏ qua file không được hỗ trợ (.txt) không."""
    txt_path = mock_docs_dir / "unsupported.txt"
    
    # Gọi hàm
    docs = load_file(txt_path)
    
    # Kết quả mong đợi là một list rỗng vì không hỗ trợ
    assert len(docs) == 0

# Test này có thể skip (bỏ qua) nếu chạy trên máy chủ CI/CD không có file thật/GPU
@pytest.mark.skip(reason="Chỉ chạy local khi có sẵn file PDF và model MinerU")
def test_real_pdf_file():
    """Test đọc file PDF thật bằng MinerU"""
    pdf_path = Path("raw-data/05.TL.HCNS_Chinh sach TeamBuilding v1.1.pdf")
    if pdf_path.exists():
        docs = load_file(pdf_path)
        assert len(docs) > 0
        assert docs[0].metadata["file_type"] == "pdf"
        assert "MinerU" in docs[0].metadata["parser"]