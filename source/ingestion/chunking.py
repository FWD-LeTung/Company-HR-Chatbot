import os
import sys

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter, MarkdownHeaderTextSplitter
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from source.ingestion.metadata import ChunkMetadata


def split_documents(
    documents: list[Document],
    chunk_size: int = 1000,
    chunk_overlap: int = 150,
) -> list[Document]:
    """
    Chia nhỏ tài liệu thành các chunk tối ưu cho Vector Search (RAG).
    Sử dụng chiến thuật 2 lớp: Chặt theo Markdown Header trước, sau đó mới dùng Recursive.
    """
    if not documents:
        return []

    # 1. Khởi tạo Lớp 1: Cắt theo cấu trúc Markdown (Bảo vệ bảng biểu, danh sách)
    headers_to_split_on = [
        ("#", "h1"),
        ("##", "h2"),
        ("###", "h3"),
        ("####", "h4"),
    ]
    markdown_splitter = MarkdownHeaderTextSplitter(
        headers_to_split_on=headers_to_split_on,
        strip_headers=False,  # Giữ lại header trong text để LLM dễ đọc
    )

    # 2. Khởi tạo Lớp 2: Cắt theo số lượng ký tự (Dành cho các đoạn văn quá dài)
    recursive_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )

    final_chunks: list[Document] = []
    global_chunk_index = 0

    for doc in documents:
        base_metadata = doc.metadata or {}
        source_name = base_metadata.get("source_file", "unknown_document")

        # --- BƯỚC 1: Cắt bằng Markdown ---
        md_docs = markdown_splitter.split_text(doc.page_content)

        # --- BƯỚC 2: Cắt tiếp bằng Recursive (nếu Chunk Markdown vẫn quá to) ---
        # Đồng thời ghép nối Base Metadata vào các Chunk vừa cắt
        for md_doc in md_docs:
            md_doc.metadata = {**base_metadata, **md_doc.metadata}
        
        split_docs = recursive_splitter.split_documents(md_docs)

        # --- BƯỚC 3: Bơm ngữ cảnh (Context Enrichment) & Chỉnh trang Metadata ---
        for chunk in split_docs:
            # Thu thập các thẻ Heading mà Chunk này đang trực thuộc (h1, h2, h3...)
            extracted_headers = [
                chunk.metadata.get(f"h{i}") 
                for i in range(1, 5) 
                if chunk.metadata.get(f"h{i}")
            ]
            
            # Tạo chuỗi ngữ cảnh (Ví dụ: "Chính sách nhân sự > Lương Thưởng > Phụ cấp")
            header_context = " > ".join(extracted_headers) if extracted_headers else "Thông tin chung"
            
            # Bơm ngữ cảnh vào đầu text để RAG Vector Search hiểu chính xác đoạn này nói về cái gì
            enriched_text = (
                f"[Tài liệu: {source_name} | Mục: {header_context}]\n"
                f"{chunk.page_content}"
            )
            chunk.page_content = enriched_text

            # Tạo metadata chuẩn hóa bằng Pydantic model
            chunk_metadata = ChunkMetadata.create_metadata(
                text=chunk.page_content,
                source_file=source_name,
                file_type=base_metadata.get("file_type", "unknown"),
                page=base_metadata.get("page"),
                chunk_index=global_chunk_index,
                category=base_metadata.get("category"),
                parser=base_metadata.get("parser"),
                block_type=base_metadata.get("block_type", "text"),
            )

            # Cập nhật Metadata cuối cùng (dùng exclude_none=True để loại bỏ các trường rỗng cho nhẹ DB)
            chunk.metadata = {
                **chunk.metadata,
                **chunk_metadata.model_dump(exclude_none=True),
            }
            
            final_chunks.append(chunk)
            global_chunk_index += 1

    return final_chunks