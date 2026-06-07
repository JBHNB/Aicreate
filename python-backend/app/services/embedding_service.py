"""DashScope Embedding 服务"""

import logging
from typing import List

from openai import AsyncOpenAI

from app.config import settings

logger = logging.getLogger(__name__)

# DashScope text-embedding-v3 单次 batch 上限为 10
_EMBED_BATCH_SIZE = 10


class EmbeddingService:
    """文本向量化（DashScope OpenAI 兼容接口）"""

    def __init__(self):
        self._client = AsyncOpenAI(
            api_key=settings.dashscope_api_key,
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
            timeout=120.0,
        )
        self._model = settings.dashscope_embedding_model

    async def embed_texts(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []
        if not (settings.dashscope_api_key or "").strip():
            raise RuntimeError("DASHSCOPE_API_KEY 未配置，无法生成 Embedding")

        all_embeddings: List[List[float]] = []
        batch_size = max(1, min(settings.rag_embed_batch_size, _EMBED_BATCH_SIZE))
        for start in range(0, len(texts), batch_size):
            batch = texts[start : start + batch_size]
            response = await self._client.embeddings.create(
                model=self._model,
                input=batch,
            )
            ordered = sorted(response.data, key=lambda item: item.index)
            all_embeddings.extend([item.embedding for item in ordered])
            logger.debug(
                "Embedding 批次完成, batch=%s, total=%s",
                len(batch),
                len(all_embeddings),
            )
        return all_embeddings

    async def embed_query(self, text: str) -> List[float]:
        vectors = await self.embed_texts([text])
        return vectors[0] if vectors else []


embedding_service = EmbeddingService()
