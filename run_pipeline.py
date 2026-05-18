from pathlib import Path
from source.ingestion.loaders import load_documents
from source.ingestion.chunking import split_documents
from source.indexing.vector_store import index_documents

if __name__ == "__main__":
    # 1. Đọc toàn bộ PDF/Word ra Text
    raw_docs = load_documents("raw-data")
    
    # 2. Cắt nhỏ thành các Chunks có ngữ cảnh
    chunks = split_documents(raw_docs)
    
    # 3. Mã hóa thành Vector và lưu vào Database
    index_documents(chunks)