import pickle
from pathlib import Path
from rank_bm25 import BM25Okapi
from typing import List
import sys
import os

from pyvi import ViTokenizer

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from source.config import settings
from qdrant_client import QdrantClient

BM25_INDEX_DIR = Path("data")
BM25_INDEX_PATH = BM25_INDEX_DIR / "bm25_index.pkl"
DOCUMENTS_PATH = BM25_INDEX_DIR / "bm25_documents.pkl"


class BM25Indexer:
    def __init__(self):
        self.bm25: BM25Okapi | None = None
        self.documents: list[dict] = []

    def index_documents(self):
        client = QdrantClient(url=settings.QDRANT_URL, api_key=settings.QDRANT_API_KEY)

        all_points = []
        offset = None
        limit = 100

        while True:
            records, next_offset = client.scroll(
                collection_name=settings.COLLECTION_NAME,
                limit=limit,
                offset=offset,
                with_payload=True,
                with_vectors=False,
            )

            if not records:
                break

            all_points.extend(records)
            offset = next_offset

        self.documents = []
        for point in all_points:
            payload = point.payload or {}
            page_content = payload.get("page_content", "")
            metadata = payload.get("metadata", {})
            self.documents.append({
                "id": str(point.id),
                "text": page_content,
                "metadata": metadata,
            })

        print(f"[BM25] Tokenizing {len(self.documents)} documents with pyvi...")
        tokenized_corpus = [self._tokenize(doc["text"]) for doc in self.documents]
        self.bm25 = BM25Okapi(tokenized_corpus)
        self._save()

    def _tokenize(self, text: str) -> List[str]:
        return ViTokenizer.tokenize(text.lower()).split()

    def search(self, query: str, top_k: int = 3) -> list[dict]:
        if self.bm25 is None:
            self._load()

        tokenized_query = self._tokenize(query)
        scores = self.bm25.get_scores(tokenized_query)

        top_indices = sorted(
            range(len(scores)), key=lambda i: scores[i], reverse=True
        )[:top_k]

        results = []
        for idx in top_indices:
            if scores[idx] > 0:
                doc = self.documents[idx]
                results.append({
                    "id": doc["id"],
                    "score": float(scores[idx]),
                    "text": doc["text"],
                    "metadata": doc["metadata"],
                })
        return results

    def _save(self):
        BM25_INDEX_DIR.mkdir(parents=True, exist_ok=True)
        with open(BM25_INDEX_PATH, "wb") as f:
            pickle.dump(self.bm25, f)
        with open(DOCUMENTS_PATH, "wb") as f:
            pickle.dump(self.documents, f)
        print(f"[BM25] Index saved to {BM25_INDEX_PATH} ({len(self.documents)} docs)")

    def _load(self):
        if not BM25_INDEX_PATH.exists() or not DOCUMENTS_PATH.exists():
            raise FileNotFoundError(
                "BM25 index not found. Run 'python scripts/build_bm25_index.py' first."
            )
        with open(BM25_INDEX_PATH, "rb") as f:
            self.bm25 = pickle.load(f)
        with open(DOCUMENTS_PATH, "rb") as f:
            self.documents = pickle.load(f)


bm25_indexer = BM25Indexer()
