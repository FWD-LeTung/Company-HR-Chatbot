import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings
from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams

# Tải các biến môi trường từ file .env
load_dotenv()

# Đảm bảo import đúng đường dẫn root
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

# Đọc cấu hình từ môi trường
QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
EMBEDDING_MODEL = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")
COLLECTION_NAME = "hr_policies_openai"

print(f"[System] Khởi tạo OpenAI Embeddings với model: {EMBEDDING_MODEL}")

embeddings = OpenAIEmbeddings(model=EMBEDDING_MODEL)
client = QdrantClient(url=QDRANT_URL)


def init_vector_db() -> QdrantVectorStore:
    if not client.collection_exists(COLLECTION_NAME):
        print(f"[Qdrant] Khởi tạo collection mới: {COLLECTION_NAME}")
    
        sample_vector = embeddings.embed_query("Test")
        vector_size = len(sample_vector)
        print(f"[Qdrant] Kích thước Vector tự động nhận diện: {vector_size}")
        
        client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(
                size=vector_size, 
                distance=Distance.COSINE
            ),
        )
    
    return QdrantVectorStore(
        client=client,
        collection_name=COLLECTION_NAME,
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