import os
import sys

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from source.ingestion.metadata import ChunkMetadata


def split_documents(
    documents: list[Document],
    chunk_size: int = 1000,
    chunk_overlap: int = 150,
) -> list[Document]:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )

    chunks = splitter.split_documents(documents)

    for chunk_index, chunk in enumerate(chunks):
        base_metadata = chunk.metadata or {}

        chunk_metadata = ChunkMetadata.create_metadata(
            text=chunk.page_content,
            source_file=base_metadata.get("source_file", "unknown"),
            file_type=base_metadata.get("file_type", "unknown"),
            page=base_metadata.get("page"),
            chunk_index=chunk_index,
            category=base_metadata.get("category"),
            parser=base_metadata.get("parser"),
            block_type=base_metadata.get("block_type", "text"),
        )

        chunk.metadata = {
            **base_metadata,
            **chunk_metadata.model_dump(),
        }

    return chunks
