"""Pexels 图片检索服务"""

import re
import httpx
import logging
from typing import Optional
from urllib.parse import quote

from app.config import settings
from app.constants.article import ArticleConstant
from app.models.enums import ImageMethodEnum
from app.services.image_search_service import ImageSearchService

logger = logging.getLogger(__name__)


class PexelsService(ImageSearchService):
    """Pexels 图片检索服务"""

    def __init__(self):
        self.api_key = (settings.pexels_api_key or "").strip()
        self.client = httpx.AsyncClient(timeout=30.0)

    def is_available(self) -> bool:
        """未配置 Key 时不调用接口，避免反复 401"""
        return bool(self.api_key)
    
    async def search_image(self, keywords: str) -> Optional[str]:
        """
        搜索图片
        
        Args:
            keywords: 搜索关键词
            
        Returns:
            图片 URL，未找到返回 None
        """
        try:
            if not self.api_key:
                return None

            headers = {"Authorization": self.api_key}
            first = await self._search_once(keywords, headers)
            if first:
                return first

            # 纯中文等检索词在 Stock 上常零结果，用英文词根再试一次
            alt = self._english_stock_fallback_query(keywords)
            if alt != self._normalize_pexels_query(keywords):
                second = await self._search_once(alt, headers)
                if second:
                    return second
            third = "technology creative abstract"
            if third != alt:
                return await self._search_once(third, headers)
            return None
        except Exception as e:
            logger.error(
                "Pexels API 调用异常: %s: %r",
                type(e).__name__,
                e,
                exc_info=True,
            )
            return None
    
    def get_method(self) -> ImageMethodEnum:
        """获取配图方式"""
        return ImageMethodEnum.PEXELS
    
    def get_fallback_image(self, position: int) -> str:
        """获取降级图片"""
        return ArticleConstant.PICSUM_URL_TEMPLATE.format(position)

    def _english_stock_fallback_query(self, raw: str) -> str:
        """从标题里抽英文词作 Stock 检索；没有则用通用词。"""
        if not raw:
            return "abstract technology"
        words = re.findall(r"[a-zA-Z]{3,}", raw)
        if words:
            return " ".join(words[:10])
        return "abstract technology"

    async def _search_once(self, query: str, headers: dict) -> Optional[str]:
        req_url = self._build_search_url(query)
        response = await self.client.get(req_url, headers=headers)
        if response.status_code != 200:
            logger.error(f"Pexels API 调用失败: {response.status_code}")
            return None
        return self._extract_image_url(response.json(), query)

    def _normalize_pexels_query(self, raw: str) -> str:
        """去掉控制字符、压缩空白，避免 httpx 报 URL 非法；Stock 检索不宜过长。"""
        if not raw:
            return "nature"
        s = re.sub(r"[\x00-\x1f\x7f-\x9f]", " ", raw)
        s = " ".join(s.split()).strip()
        if len(s) > 400:
            s = s[:400].rsplit(" ", 1)[0] if " " in s[:400] else s[:400]
        return s or "nature"

    def _build_search_url(self, keywords: str) -> str:
        """构建搜索 URL（query 必须 percent-encode）"""
        q = quote(self._normalize_pexels_query(keywords), safe="")
        return (
            f"{ArticleConstant.PEXELS_API_URL}"
            f"?query={q}"
            f"&per_page={ArticleConstant.PEXELS_PER_PAGE}"
            f"&orientation={ArticleConstant.PEXELS_ORIENTATION_LANDSCAPE}"
        )
    
    def _extract_image_url(self, response_data: dict, keywords: str) -> Optional[str]:
        """从响应中提取图片 URL"""
        photos = response_data.get("photos", [])
        
        if not photos:
            logger.warning(f"Pexels 未检索到图片: {keywords}")
            return None
        
        photo = photos[0]
        src = photo.get("src", {})
        return src.get("large")
    
    async def close(self):
        """关闭 HTTP 客户端"""
        await self.client.aclose()
