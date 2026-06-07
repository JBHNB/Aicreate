"""RAG 检索服务"""

import logging
from typing import List, Optional

from app.config import settings
from app.constants.prompt import PromptConstant
from app.managers.chroma_manager import chroma_manager
from app.schemas.article import OutlineSection
from app.schemas.knowledge import RetrievalResult, RetrievalSourceVO
from app.services.embedding_service import embedding_service

logger = logging.getLogger(__name__)


class RetrievalService:
    """按文章上下文检索系统知识库"""

    async def retrieve_for_article(
        self,
        topic: str,
        main_title: str,
        sub_title: str,
        outline_sections: Optional[List[OutlineSection]],
        top_k: Optional[int] = None,
    ) -> RetrievalResult:
        if not settings.rag_enabled:
            return RetrievalResult()

        if not (settings.dashscope_api_key or "").strip():
            logger.warning("RAG 已开启但 DASHSCOPE_API_KEY 未配置，跳过检索")
            return RetrievalResult()

        query_text = self._build_query_text(topic, main_title, sub_title, outline_sections)
        if not query_text.strip():
            return RetrievalResult()

        try:
            query_embedding = await embedding_service.embed_query(query_text)
            raw = chroma_manager().query(
                query_embedding=query_embedding,
                top_k=top_k or settings.rag_top_k,
            )
            return self._format_result(raw)
        except Exception as exc:
            logger.error("RAG 检索失败: %s", exc, exc_info=True)
            return RetrievalResult()

    def build_reference_section(self, retrieval: RetrievalResult) -> str:
        if not retrieval.context.strip():
            return ""
        return PromptConstant.AGENT3_REFERENCE_SECTION.replace(
            "{referenceContext}",
            retrieval.context,
        )

    def _build_query_text(
        self,
        topic: str,
        main_title: str,
        sub_title: str,
        outline_sections: Optional[List[OutlineSection]],
    ) -> str:
        parts = [
            f"选题：{topic or ''}",
            f"主标题：{main_title or ''}",
            f"副标题：{sub_title or ''}",
        ]
        if outline_sections:
            for section in outline_sections:
                points = "；".join(section.points or [])
                parts.append(f"章节{section.section}：{section.title}（{points}）")
        query = "\n".join(part for part in parts if part.strip())
        return query[:500]

    def _format_result(self, raw: dict) -> RetrievalResult:
        documents = (raw.get("documents") or [[]])[0]
        metadatas = (raw.get("metadatas") or [[]])[0]
        distances = (raw.get("distances") or [[]])[0]

        sources: List[RetrievalSourceVO] = []
        context_parts: List[str] = []

        for index, document in enumerate(documents):
            if not document:
                continue
            metadata = metadatas[index] if index < len(metadatas) else {}
            distance = distances[index] if index < len(distances) else 1.0
            score = max(0.0, 1.0 - float(distance))
            if score < settings.rag_min_score:
                continue

            title = str(metadata.get("title") or "未知来源")
            document_id = int(metadata.get("document_id") or 0)
            chunk_index = int(metadata.get("chunk_index") or 0)
            sources.append(
                RetrievalSourceVO(
                    documentId=document_id,
                    title=title,
                    chunkIndex=chunk_index,
                    score=round(score, 4),
                )
            )
            context_parts.append(
                f"【参考资料{len(sources)}】来源：《{title}》\n{document.strip()}"
            )

        context = "\n\n".join(context_parts)
        logger.info("RAG 检索完成, hits=%s", len(sources))
        return RetrievalResult(context=context, sources=sources)


retrieval_service = RetrievalService()
