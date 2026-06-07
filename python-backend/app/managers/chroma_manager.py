"""ChromaDB 向量索引管理"""

import logging
from typing import Any, Dict, List, Optional

import chromadb

from app.config import settings

logger = logging.getLogger(__name__)

COLLECTION_NAME = "system_knowledge"


class ChromaManager:
    """ChromaDB 持久化客户端（单例）"""

    _instance: Optional["ChromaManager"] = None

    def __init__(self):
        settings.chroma_persist_path.mkdir(parents=True, exist_ok=True)
        self._client = chromadb.PersistentClient(path=str(settings.chroma_persist_path))
        self._collection = self._client.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )
        logger.info("ChromaDB 已初始化, path=%s", settings.chroma_persist_path)

    @classmethod
    def get_instance(cls) -> "ChromaManager":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def upsert_document_chunks(
        self,
        document_id: int,
        title: str,
        chunks: List[str],
        embeddings: List[List[float]],
    ) -> None:
        if not chunks:
            return
        ids = [f"doc_{document_id}_chunk_{index}" for index in range(len(chunks))]
        metadatas = [
            {
                "document_id": document_id,
                "chunk_index": index,
                "title": title,
            }
            for index in range(len(chunks))
        ]
        self._collection.upsert(
            ids=ids,
            documents=chunks,
            embeddings=embeddings,
            metadatas=metadatas,
        )

    def delete_document(self, document_id: int) -> None:
        self._collection.delete(where={"document_id": document_id})

    def query(
        self,
        query_embedding: List[float],
        top_k: int,
    ) -> Dict[str, Any]:
        return self._collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            include=["documents", "metadatas", "distances"],
        )


chroma_manager = ChromaManager.get_instance
