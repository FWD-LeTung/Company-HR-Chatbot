import sys
from typing import Optional
import os
from langchain_openai import OpenAIEmbeddings
from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient
from qdrant_client.http import models

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from source.config import settings

embeddings = OpenAIEmbeddings(model=settings.OPENAI_EMBEDDING_MODEL,
                              api_key=settings.OPENAI_API_KEY
                              )
client = QdrantClient(url=settings.QDRANT_URL,
                      api_key=settings.QDRANT_API_KEY)
vector_store = QdrantVectorStore(
    client=client,
    collection_name=settings.COLLECTION_NAME,
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


def hybrid_search_hr_policies(
    query: str,
    top_k: int = 3,
    source_file_filter: Optional[str] = None,
    category_filter: Optional[str] = None,
):
    from source.retrieval.bm25_indexer import bm25_indexer
    from langchain_core.documents import Document

    # 1. Vector search
    vector_results = search_hr_policies(
        query=query,
        top_k=top_k * 2,
        source_file_filter=source_file_filter,
        category_filter=category_filter,
    )

    # 2. BM25 search
    try:
        bm25_raw = bm25_indexer.search(query, top_k=top_k * 2)
    except FileNotFoundError:
        print("[Hybrid] BM25 index not found, falling back to vector-only search.")
        return vector_results[:top_k]

    bm25_results = []
    for item in bm25_raw:
        doc = Document(page_content=item["text"], metadata=item["metadata"])
        bm25_results.append((doc, item["score"]))

    # 3. RRF fusion
    k = 60
    fused_scores: dict[str, float] = {}
    all_docs: dict[str, Document] = {}

    for rank, (doc, _score) in enumerate(vector_results, 1):
        doc_id = doc.metadata.get("chunk_id", id(doc))
        fused_scores[doc_id] = fused_scores.get(doc_id, 0) + 1 / (k + rank)
        all_docs[doc_id] = doc

    for rank, (doc, _score) in enumerate(bm25_results, 1):
        doc_id = doc.metadata.get("chunk_id", id(doc))
        fused_scores[doc_id] = fused_scores.get(doc_id, 0) + 1 / (k + rank)
        if doc_id not in all_docs:
            all_docs[doc_id] = doc

    sorted_ids = sorted(fused_scores.items(), key=lambda x: x[1], reverse=True)[:top_k]

    final_results = []
    for doc_id, fusion_score in sorted_ids:
        doc = all_docs[doc_id]
        final_results.append((doc, fusion_score))

    return final_results