import os
import sys
from pathlib import Path
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings
from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from source.config import settings

print(f"[System] Khởi tạo OpenAI Embeddings với model: {settings.OPENAI_EMBEDDING_MODEL}")

embeddings = OpenAIEmbeddings(model=settings.OPENAI_EMBEDDING_MODEL,
                              api_key=settings.OPENAI_API_KEY)
client = QdrantClient(url=settings.QDRANT_URL)


def init_vector_db() -> QdrantVectorStore:
    if not client.collection_exists(settings.COLLECTION_NAME):
        print(f"[Qdrant] Khởi tạo collection mới: {settings.COLLECTION_NAME}")

        sample_vector = embeddings.embed_query("Test")
        vector_size = len(sample_vector)
        print(f"[Qdrant] Kích thước Vector tự động nhận diện: {vector_size}")

        client.create_collection(
            collection_name=settings.COLLECTION_NAME,
            vectors_config=VectorParams(
                size=vector_size,
                distance=Distance.COSINE
            ),
        )

    return QdrantVectorStore(
        client=client,
        collection_name=settings.COLLECTION_NAME,
        embedding=embeddings,
    )


def index_documents(chunks: list[Document]):
    if not chunks:
        print("[Indexing] Không có chunk nào để lưu.")
        return

    vector_store = init_vector_db()
    print(f"[Indexing] Bắt đầu nhúng {len(chunks)} chunks vào Qdrant qua OpenAI API...")
    vector_store.add_documents(documents=chunks)
    print("[Indexing] Hoàn tất lưu trữ Vector lên Qdrant thành công!")