import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from source.retrieval.bm25_indexer import bm25_indexer

if __name__ == "__main__":
    print("Building BM25 index from Qdrant...")
    bm25_indexer.index_documents()
    print(f"BM25 index built successfully!")
    print(f"Indexed {len(bm25_indexer.documents)} documents")
