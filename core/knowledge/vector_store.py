"""
ChromaDB-backed semantic vector store.
Replaces the hash-embedding system in alpha_skills/knowledge_retriever.py.
"""
from __future__ import annotations
import sys
from pathlib import Path

_ROOT = Path(__file__).parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

CHROMA_DIR = _ROOT / "data" / "chroma"
EMBED_MODEL = "all-MiniLM-L6-v2"


class VectorStore:
    """Thin wrapper around ChromaDB with sentence-transformer embeddings."""

    def __init__(self, persist_dir: Path = CHROMA_DIR):
        import chromadb
        from chromadb.utils import embedding_functions

        self._client = chromadb.PersistentClient(path=str(persist_dir))
        self._ef = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name=EMBED_MODEL
        )
        self._knowledge = self._client.get_or_create_collection(
            name="alpha_knowledge",
            embedding_function=self._ef,
            metadata={"hnsw:space": "cosine"},
        )
        self._fields = self._client.get_or_create_collection(
            name="wqb_fields",
            embedding_function=self._ef,
            metadata={"hnsw:space": "cosine"},
        )

    def add_chunks(self, chunks: list[dict]) -> int:
        """
        Add document chunks to alpha_knowledge collection.
        Each chunk: {id, content, metadata: {source_id, source_type, category, ...}}
        """
        if not chunks:
            return 0
        ids       = [c["id"] for c in chunks]
        documents = [c["content"] for c in chunks]
        metadatas = [c.get("metadata", {}) for c in chunks]
        self._knowledge.add(ids=ids, documents=documents, metadatas=metadatas)
        return len(chunks)

    def add_fields(self, fields: list[dict]) -> int:
        """Add WQB field/operator facts to wqb_fields collection."""
        if not fields:
            return 0
        ids       = [f["id"] for f in fields]
        documents = [f["content"] for f in fields]
        metadatas = [f.get("metadata", {}) for f in fields]
        self._fields.add(ids=ids, documents=documents, metadatas=metadatas)
        return len(fields)

    def search(self, query: str, top_k: int = 5, collection: str = "alpha_knowledge") -> list[dict]:
        """
        Semantic search. Returns list of {content, score, metadata}.
        collection: 'alpha_knowledge' | 'wqb_fields'
        """
        col = self._knowledge if collection == "alpha_knowledge" else self._fields
        try:
            results = col.query(query_texts=[query], n_results=min(top_k, col.count()))
        except Exception:
            return []

        out = []
        docs      = results.get("documents", [[]])[0]
        distances = results.get("distances", [[]])[0]
        metas     = results.get("metadatas", [[]])[0]
        for doc, dist, meta in zip(docs, distances, metas):
            out.append({
                "content":  doc,
                "score":    round(1 - dist, 4),  # cosine similarity
                "metadata": meta,
            })
        return out

    def stats(self) -> dict:
        return {
            "alpha_knowledge": self._knowledge.count(),
            "wqb_fields": self._fields.count(),
        }

    def chunk_exists(self, chunk_id: str) -> bool:
        try:
            r = self._knowledge.get(ids=[chunk_id])
            return len(r["ids"]) > 0
        except Exception:
            return False
