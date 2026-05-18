import os
import sys
from typing import Optional
from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings
from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient
from qdrant_client.http import models

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
load_dotenv()

QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
EMBEDDING_MODEL = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")
COLLECTION_NAME = "hr_policies_openai"

embeddings = OpenAIEmbeddings(model=EMBEDDING_MODEL)
client = QdrantClient(url=QDRANT_URL)
vector_store = QdrantVectorStore(
    client=client,
    collection_name=COLLECTION_NAME,
    embedding=embeddings,
)

def search_hr_policies(
    query: str, 
    top_k: int = 3, 
    category_filter: Optional[str] = None,
    source_file_filter: Optional[str] = None
):
    filter_conditions = []
    if source_file_filter:
        print(f"   [+] Áp dụng phễu lọc File: {source_file_filter}")
        filter_conditions.append(
            models.FieldCondition(
                key="metadata.source_file",
                match=models.MatchValue(value=source_file_filter)
            )
        )
    qdrant_filter = None
    if filter_conditions:
        qdrant_filter = models.Filter(must=filter_conditions)
    results = vector_store.similarity_search_with_score(
        query=query, 
        k=top_k,
        filter=qdrant_filter
    )
    
    if not results:
        print("Không tìm thấy tài liệu phù hợp.")
        return []

    return results