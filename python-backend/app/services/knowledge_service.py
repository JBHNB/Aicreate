"""系统知识库业务服务"""

import logging
from datetime import datetime
from typing import List, Optional, Tuple

from databases import Database

from app.exceptions import ErrorCode, throw_if, throw_if_not
from app.schemas.knowledge import (
    KnowledgeChunkVO,
    KnowledgeDocumentVO,
    KnowledgeQueryRequest,
    KnowledgeSearchByStatusRequest,
    KnowledgeSearchByTitleRequest,
    KnowledgeStatsVO,
)
from app.services.knowledge_ingest_service import KnowledgeIngestService
from app.managers.chroma_manager import chroma_manager
from app.utils.document_parser import extension_to_file_type, is_allowed_knowledge_file

logger = logging.getLogger(__name__)


def _dt_iso(value) -> str:
    if value is None:
        return ""
    if isinstance(value, datetime):
        return value.isoformat()
    return str(value)


class KnowledgeService:
    """知识库文档 CRUD"""

    def __init__(self, db: Database):
        self.db = db
        self.ingest_service = KnowledgeIngestService(db)

    async def create_and_ingest(
        self,
        title: str,
        file_name: str,
        file_bytes: bytes,
        admin_user_id: int,
    ) -> KnowledgeDocumentVO:
        throw_if(
            not is_allowed_knowledge_file(file_name),
            ErrorCode.PARAMS_ERROR,
            "仅支持 .txt / .md / .docx 文件（旧版 .doc 请先另存为 .docx）",
        )
        ext = extension_to_file_type(file_name)
        throw_if(len(file_bytes) == 0, ErrorCode.PARAMS_ERROR, "文件内容为空")
        throw_if(len(file_bytes) > 5 * 1024 * 1024, ErrorCode.PARAMS_ERROR, "文件大小不能超过 5MB")

        await self.db.execute(
            """
            INSERT INTO knowledge_document
                (title, fileName, fileType, fileSize, status, chunkCount, createdBy)
            VALUES
                (:title, :fileName, :fileType, :fileSize, 'processing', 0, :createdBy)
            """,
            {
                "title": title.strip() or file_name,
                "fileName": file_name,
                "fileType": ext,
                "fileSize": len(file_bytes),
                "createdBy": admin_user_id,
            },
        )
        doc_id = int(await self.db.fetch_val("SELECT LAST_INSERT_ID() AS id"))

        try:
            await self.ingest_service.ingest_file(
                document_id=int(doc_id),
                title=title.strip() or file_name,
                file_name=file_name,
                file_bytes=file_bytes,
            )
        except Exception as exc:
            logger.error("知识库摄入失败, documentId=%s, error=%s", doc_id, exc)
            await self.db.execute(
                """
                UPDATE knowledge_document
                SET status = 'failed', errorMessage = :errorMessage, updateTime = NOW()
                WHERE id = :id
                """,
                {"id": doc_id, "errorMessage": str(exc)[:2000]},
            )
            throw_if(True, ErrorCode.OPERATION_ERROR, f"文档索引失败: {exc}")

        doc = await self.get_by_id(int(doc_id))
        throw_if_not(doc, ErrorCode.SYSTEM_ERROR, "文档创建后查询失败")
        return doc

    async def list_by_page(
        self,
        request: KnowledgeQueryRequest,
    ) -> Tuple[List[KnowledgeDocumentVO], int]:
        conditions = ["isDelete = 0"]
        filter_values: dict = {}
        if request.title:
            conditions.append("title LIKE :title")
            filter_values["title"] = f"%{request.title.strip()}%"
        if request.status:
            conditions.append("status = :status")
            filter_values["status"] = request.status.strip()

        where_sql = " AND ".join(conditions)
        total = await self.db.fetch_val(
            f"SELECT COUNT(*) FROM knowledge_document WHERE {where_sql}",
            filter_values or None,
        )
        page_values = {
            **filter_values,
            "page_limit": request.page_size,
            "page_offset": (request.current - 1) * request.page_size,
        }
        rows = await self.db.fetch_all(
            f"""
            SELECT id, title, fileName, fileType, fileSize, status, chunkCount,
                   errorMessage, createdBy, createTime, updateTime
            FROM knowledge_document
            WHERE {where_sql}
            ORDER BY createTime DESC
            LIMIT :page_limit OFFSET :page_offset
            """,
            page_values,
        )
        records = [self._to_vo(row) for row in rows]
        return records, int(total or 0)

    async def get_by_id(self, document_id: int) -> Optional[KnowledgeDocumentVO]:
        row = await self.db.fetch_one(
            """
            SELECT id, title, fileName, fileType, fileSize, status, chunkCount,
                   errorMessage, createdBy, createTime, updateTime
            FROM knowledge_document
            WHERE id = :id AND isDelete = 0
            """,
            {"id": document_id},
        )
        return self._to_vo(row) if row else None

    async def update_title(self, document_id: int, title: str) -> KnowledgeDocumentVO:
        """重命名文档（仅更新 MySQL 标题，不影响向量索引内容）"""
        normalized = (title or "").strip()
        throw_if(not normalized, ErrorCode.PARAMS_ERROR, "标题不能为空")
        throw_if(len(normalized) > 200, ErrorCode.PARAMS_ERROR, "标题不能超过 200 字")

        row = await self.db.fetch_one(
            "SELECT id FROM knowledge_document WHERE id = :id AND isDelete = 0",
            {"id": document_id},
        )
        throw_if_not(row, ErrorCode.NOT_FOUND_ERROR, "文档不存在")

        await self.db.execute(
            """
            UPDATE knowledge_document
            SET title = :title, updateTime = NOW()
            WHERE id = :id AND isDelete = 0
            """,
            {"id": document_id, "title": normalized},
        )

        document = await self.get_by_id(document_id)
        throw_if_not(document, ErrorCode.SYSTEM_ERROR, "更新后查询失败")
        return document

    async def search_by_status(
        self, request: KnowledgeSearchByStatusRequest
    ) -> List[KnowledgeDocumentVO]:
        """根据状态查询知识库文档（不分页，返回全部匹配项）"""
        status = (request.status or "").strip()
        throw_if(not status, ErrorCode.PARAMS_ERROR, "状态不能为空")

        rows = await self.db.fetch_all(
            """
            SELECT id, title, fileName, fileType, fileSize, status, chunkCount,
                   errorMessage, createdBy, createTime, updateTime
            FROM knowledge_document
            WHERE status = :status AND isDelete = 0
            ORDER BY createTime DESC
            """,
            {"status": status},
        )
        # 没有匹配记录时返回空列表即可，不是错误
        return [self._to_vo(row) for row in rows]

    async def search_by_title(
        self, request: KnowledgeSearchByTitleRequest
    ) -> List[KnowledgeDocumentVO]:
        """根据标题关键词查询知识库文档（不分页，模糊匹配）"""
        title = (request.title or "").strip()
        throw_if(not title, ErrorCode.PARAMS_ERROR, "标题关键词不能为空")

        rows = await self.db.fetch_all(
            """
            SELECT id, title, fileName, fileType, fileSize, status, chunkCount,
                   errorMessage, createdBy, createTime, updateTime
            FROM knowledge_document
            WHERE title LIKE :title AND isDelete = 0
            ORDER BY createTime DESC
            """,
            {"title": f"%{title}%"},
        )
        return [self._to_vo(row) for row in rows]

    async def get_stats(self) -> KnowledgeStatsVO:
        """统计各状态文档数量"""
        row = await self.db.fetch_one(
            """
            SELECT
                COUNT(*) AS total,
                SUM(CASE WHEN status = 'ready' THEN 1 ELSE 0 END) AS ready_count,
                SUM(CASE WHEN status = 'processing' THEN 1 ELSE 0 END) AS processing_count,
                SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) AS failed_count
            FROM knowledge_document
            WHERE isDelete = 0
            """
        )
        data = dict(row or {})
        return KnowledgeStatsVO(
            total=int(data.get("total") or 0),
            readyCount=int(data.get("ready_count") or 0),
            processingCount=int(data.get("processing_count") or 0),
            failedCount=int(data.get("failed_count") or 0),
        )

    async def list_chunks(self, document_id: int) -> List[KnowledgeChunkVO]:
        """查看文档在向量库中的分块内容"""
        document = await self.get_by_id(document_id)
        throw_if_not(document, ErrorCode.NOT_FOUND_ERROR, "文档不存在")

        raw_chunks = chroma_manager().list_document_chunks(document_id)
        return [
            KnowledgeChunkVO(
                chunkIndex=item["chunk_index"],
                content=item["content"],
                title=item["title"] or document.title,
            )
            for item in raw_chunks
        ]

    async def delete_document(self, document_id: int) -> bool:
        row = await self.db.fetch_one(
            "SELECT id FROM knowledge_document WHERE id = :id AND isDelete = 0",
            {"id": document_id},
        )
        throw_if_not(row, ErrorCode.NOT_FOUND_ERROR, "文档不存在")

        await self.ingest_service.delete_vectors(document_id)
        await self.db.execute(
            """
            UPDATE knowledge_document
            SET isDelete = 1, updateTime = NOW()
            WHERE id = :id
            """,
            {"id": document_id},
        )
        return True

    async def reindex_document(self, document_id: int) -> KnowledgeDocumentVO:
        row = await self.db.fetch_one(
            """
            SELECT id, title, fileName
            FROM knowledge_document
            WHERE id = :id AND isDelete = 0
            """,
            {"id": document_id},
        )
        throw_if_not(row, ErrorCode.NOT_FOUND_ERROR, "文档不存在")

        await self.db.execute(
            """
            UPDATE knowledge_document
            SET status = 'processing', errorMessage = NULL, updateTime = NOW()
            WHERE id = :id
            """,
            {"id": document_id},
        )
        try:
            await self.ingest_service.reindex_from_storage(
                document_id=document_id,
                title=row["title"],
                file_name=row["fileName"],
            )
        except Exception as exc:
            await self.db.execute(
                """
                UPDATE knowledge_document
                SET status = 'failed', errorMessage = :errorMessage, updateTime = NOW()
                WHERE id = :id
                """,
                {"id": document_id, "errorMessage": str(exc)[:2000]},
            )
            throw_if(True, ErrorCode.OPERATION_ERROR, f"重建索引失败: {exc}")

        doc = await self.get_by_id(document_id)
        throw_if_not(doc, ErrorCode.SYSTEM_ERROR, "重建索引后查询失败")
        return doc

    def _to_vo(self, row) -> KnowledgeDocumentVO:
        data = dict(row)
        return KnowledgeDocumentVO(
            id=data["id"],
            title=data["title"],
            fileName=data["fileName"],
            fileType=data["fileType"],
            fileSize=data["fileSize"],
            status=data["status"],
            chunkCount=data["chunkCount"],
            errorMessage=data.get("errorMessage"),
            createdBy=data["createdBy"],
            createTime=_dt_iso(data.get("createTime")),
            updateTime=_dt_iso(data.get("updateTime")),
        )
