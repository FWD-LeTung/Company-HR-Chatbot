import hashlib
from typing import Optional

from pydantic import BaseModel, Field


def make_content_hash(text: str) -> str:
    normalized_text = text.strip()
    return hashlib.sha256(normalized_text.encode("utf-8")).hexdigest()


def make_document_id(source_file: str) -> str:
    return hashlib.sha256(source_file.encode("utf-8")).hexdigest()


def make_chunk_id(
    source_file: str,
    file_type: str,
    page: int | None,
    chunk_index: int,
    content_hash: str,
) -> str:
    raw_id = f"{source_file}|{file_type}|{page}|{chunk_index}|{content_hash}"
    return hashlib.sha256(raw_id.encode("utf-8")).hexdigest()


class ChunkMetadata(BaseModel):
    document_id: str
    chunk_id: str
    source_file: str
    file_type: str
    page: Optional[int] = Field(default=None, description="Page number if available")
    chunk_index: int = Field(..., description="Chunk order within the source document")
    content_hash: str
    parser: Optional[str] = None
    block_type: str = "text"
    category: Optional[str] = Field(default=None, description="Document category, e.g. HR or IT")

    @classmethod
    def create_metadata(
        cls,
        text: str,
        source_file: str,
        file_type: str,
        chunk_index: int,
        page: Optional[int] = None,
        category: Optional[str] = None,
        parser: Optional[str] = None,
        block_type: str = "text",
    ) -> "ChunkMetadata":
        content_hash = make_content_hash(text)

        return cls(
            document_id=make_document_id(source_file),
            chunk_id=make_chunk_id(source_file, file_type, page, chunk_index, content_hash),
            source_file=source_file,
            file_type=file_type,
            page=page,
            chunk_index=chunk_index,
            content_hash=content_hash,
            parser=parser,
            block_type=block_type,
            category=category,
        )