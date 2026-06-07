"""系统知识库文档摄入服务"""

import logging
from pathlib import Path

from databases import Database

from app.config import settings
from app.managers.chroma_manager import chroma_manager
from app.services.embedding_service import embedding_service
from app.utils.document_parser import extract_text_from_bytes, is_allowed_knowledge_file
from app.utils.text_chunk import split_text_to_chunks

logger = logging.getLogger(__name__)


class KnowledgeIngestService:
    """解析、分块、向量化并写入 Chroma"""

    def __init__(self, db: Database):
        self.db = db

    async def ingest_file(
        self,
        document_id: int,
        title: str,
        file_name: str,
        file_bytes: bytes,
    ) -> int:
        if not is_allowed_knowledge_file(file_name):
            raise ValueError("仅支持 .txt / .md / .docx 文件（旧版 .doc 请先另存为 .docx）")

        text = extract_text_from_bytes(file_name, file_bytes)

        storage_path = await self._save_file(document_id, file_name, file_bytes)
        chunks = split_text_to_chunks(
            text,
            settings.rag_chunk_size,
            settings.rag_chunk_overlap,
        )
        if not chunks:
            raise ValueError("分块结果为空")

        embeddings = await embedding_service.embed_texts(chunks)
        manager = chroma_manager()
        manager.delete_document(document_id)
        manager.upsert_document_chunks(document_id, title, chunks, embeddings)

        await self.db.execute(
            """
            UPDATE knowledge_document
            SET status = 'ready',
                chunkCount = :chunkCount,
                errorMessage = NULL,
                updateTime = NOW()
            WHERE id = :id AND isDelete = 0
            """,
            {"id": document_id, "chunkCount": len(chunks)},
        )
        logger.info(
            "知识库文档摄入成功, documentId=%s, chunks=%s, storage=%s",
            document_id,
            len(chunks),
            storage_path,
        )
        return len(chunks)

    async def reindex_from_storage(self, document_id: int, title: str, file_name: str) -> int:
        file_path = self._resolve_storage_path(document_id, file_name)
        if not file_path.exists():
            raise FileNotFoundError("原始文件不存在，无法重建索引")
        return await self.ingest_file(
            document_id=document_id,
            title=title,
            file_name=file_name,
            file_bytes=file_path.read_bytes(),
        )

    async def delete_vectors(self, document_id: int) -> None:
        chroma_manager().delete_document(document_id)

    async def _save_file(self, document_id: int, file_name: str, file_bytes: bytes) -> Path:
        settings.knowledge_files_path.mkdir(parents=True, exist_ok=True)
        safe_name = Path(file_name).name
        target = settings.knowledge_files_path / f"{document_id}_{safe_name}"
        target.write_bytes(file_bytes)
        return target

    def _resolve_storage_path(self, document_id: int, file_name: str) -> Path:
        safe_name = Path(file_name).name
        return settings.knowledge_files_path / f"{document_id}_{safe_name}"
