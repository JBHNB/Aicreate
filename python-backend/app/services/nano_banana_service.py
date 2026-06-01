"""Nano Banana：VIP AI 配图（Gemini 或阿里云通义万相 wanx）"""

import asyncio
import logging
from typing import Any, Dict, Optional

import httpx
from google import genai
from google.genai import types

from app.config import settings
from app.constants.article import ArticleConstant
from app.models.enums import ImageMethodEnum
from app.services.image_search_service import ImageSearchService
from app.schemas.image import ImageData, ImageRequest

logger = logging.getLogger(__name__)

_DASHSCOPE_SYNTHESIS_PATH = "/api/v1/services/aigc/text2image/image-synthesis"

# 万相 QPS 极低：全进程串行执行「创建任务 + 轮询」，避免并行 burst 429
_dash_wanx_lock: Optional[asyncio.Lock] = None


def _wanx_global_lock() -> asyncio.Lock:
    global _dash_wanx_lock
    if _dash_wanx_lock is None:
        _dash_wanx_lock = asyncio.Lock()
    return _dash_wanx_lock


class NanoBananaService(ImageSearchService):
    """VIP AI 生图：默认 Google Gemini；可选 DashScope 通义万相（国内）。"""

    def __init__(self):
        self.provider = (settings.nano_banana_provider or "gemini").strip().lower()
        self.model = settings.nano_banana_model
        self.aspect_ratio = settings.nano_banana_aspect_ratio
        self.image_size = settings.nano_banana_image_size
        self.api_key = (settings.nano_banana_api_key or "").strip()
        self.client = None

        if self.provider == "dashscope":
            if not (settings.dashscope_api_key or "").strip():
                logger.warning(
                    "NANO_BANANA_PROVIDER=dashscope 但未配置 DASHSCOPE_API_KEY，"
                    "通义万相生图不可用"
                )
            return

        if self.api_key:
            self.client = genai.Client(api_key=self.api_key)
        else:
            logger.warning(
                "NANO_BANANA_PROVIDER=gemini 且 NANO_BANANA_API_KEY 未配置，跳过 Gemini；"
                "可改用 NANO_BANANA_PROVIDER=dashscope + DASHSCOPE_API_KEY（通义万相）"
            )

    def is_available(self) -> bool:
        if self.provider == "dashscope":
            return bool((settings.dashscope_api_key or "").strip())
        return self.client is not None

    async def search_image(self, keywords: str) -> Optional[str]:
        """此方法已废弃，请使用 get_image_data()"""
        return None

    async def get_image_data(self, request: ImageRequest) -> Optional[ImageData]:
        """获取图片数据"""
        prompt = request.get_effective_param(True)
        return await self.generate_image_data(prompt)

    def _wanx_size_from_aspect(self) -> str:
        """万相允许的 size，参见百炼文档。"""
        ar = (self.aspect_ratio or "16:9").strip()
        if ar in ("9:16", "3:4", "2:3", "portrait"):
            return "720*1280"
        if ar in ("1:1", "1x1", "square"):
            return "1024*1024"
        return "1280*720"

    async def _generate_image_data_dashscope(self, prompt: str) -> Optional[ImageData]:
        """阿里云通义万相文生图（异步任务 + 轮询）。全进程串行 + 429 退避，避免 Throttling.RateQuota。"""
        key = (settings.dashscope_api_key or "").strip()
        if not key:
            logger.warning("DashScope 文生图：缺少 DASHSCOPE_API_KEY")
            return None

        base = (settings.dashscope_wanx_base_url or "https://dashscope.aliyuncs.com").rstrip(
            "/"
        )
        model = (settings.dashscope_wanx_model or "wanx-v1").strip()
        text = (prompt or "").strip()[:1800]

        headers_create = {
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
            "X-DashScope-Async": "enable",
        }
        body: Dict[str, Any] = {
            "model": model,
            "input": {"prompt": text or "abstract technology illustration"},
            "parameters": {
                "style": "<auto>",
                "size": self._wanx_size_from_aspect(),
                "n": 1,
            },
        }

        async with _wanx_global_lock():
            await asyncio.sleep(max(0.0, settings.dashscope_wanx_min_interval_seconds))
            try:
                async with httpx.AsyncClient(timeout=180.0) as client:
                    url_create = f"{base}{_DASHSCOPE_SYNTHESIS_PATH}"
                    logger.info(
                        "DashScope 万相开始创建生图任务, model=%s, size=%s",
                        model,
                        body["parameters"]["size"],
                    )

                    data: Dict[str, Any] = {}
                    max_try = max(1, settings.dashscope_wanx_create_max_retries)
                    base_wait = max(0.5, settings.dashscope_wanx_retry_base_seconds)

                    for attempt in range(max_try):
                        resp = await client.post(
                            url_create, headers=headers_create, json=body
                        )
                        data = resp.json() if resp.content else {}

                        throttled = resp.status_code == 429 or (
                            isinstance(data, dict)
                            and data.get("code") == "Throttling.RateQuota"
                        )
                        if throttled:
                            wait = min(90.0, base_wait * (2**attempt))
                            logger.warning(
                                "DashScope 万相限流，%ss 后重试 (%s/%s): %s",
                                wait,
                                attempt + 1,
                                max_try,
                                data.get("message") or resp.status_code,
                            )
                            await asyncio.sleep(wait)
                            continue

                        if resp.status_code != 200:
                            logger.error(
                                "DashScope 创建任务 HTTP 失败: %s %s",
                                resp.status_code,
                                data,
                            )
                            return None

                        if data.get("code"):
                            logger.error(
                                "DashScope 创建任务失败: %s %s",
                                data.get("code"),
                                data.get("message"),
                            )
                            return None

                        break
                    else:
                        logger.error(
                            "DashScope 万相创建任务在限流重试后仍失败，已尝试 %s 次",
                            max_try,
                        )
                        return None

                    output = data.get("output") or {}
                    task_id = output.get("task_id")
                    if not task_id:
                        logger.error("DashScope 创建任务响应无 task_id: %s", data)
                        return None

                    headers_poll = {"Authorization": f"Bearer {key}"}
                    task_url = f"{base}/api/v1/tasks/{task_id}"

                    for poll_i in range(100):
                        await asyncio.sleep(1.5)
                        tr = await client.get(task_url, headers=headers_poll)
                        tdata = tr.json() if tr.content else {}

                        if tr.status_code == 429:
                            logger.warning(
                                "DashScope 查询任务限流 429，3s 后再试 poll=%s",
                                poll_i,
                            )
                            await asyncio.sleep(3.0)
                            continue

                        if tr.status_code != 200:
                            logger.error(
                                "DashScope 查询任务失败: status=%s body=%s",
                                tr.status_code,
                                tdata,
                            )
                            return None

                        out = tdata.get("output") or {}
                        status = out.get("task_status")
                        if status == "SUCCEEDED":
                            results = out.get("results") or []
                            for item in results:
                                if isinstance(item, dict) and item.get("url"):
                                    u = item["url"]
                                    logger.info(
                                        "DashScope 万相生图成功, poll=%s url=%s...",
                                        poll_i + 1,
                                        u[:80],
                                    )
                                    return ImageData.from_url(u)
                            logger.error("DashScope 成功但无图片 URL: %s", out)
                            return None
                        if status == "FAILED":
                            logger.error(
                                "DashScope 任务失败: %s %s",
                                out.get("code"),
                                out.get("message"),
                            )
                            return None
                        if status in ("PENDING", "RUNNING", None):
                            continue
                        logger.warning("DashScope 未知任务状态: %s", status)

                    logger.error("DashScope 万相任务轮询超时: task_id=%s", task_id)
                    return None
            except Exception as e:
                logger.error("DashScope 万相生图异常: %s", e, exc_info=True)
                return None

    async def generate_image_data(self, prompt: str) -> Optional[ImageData]:
        """
        根据提示词生成图片数据

        Args:
            prompt: 生图提示词

        Returns:
            ImageData 包含图片字节或 URL，生成失败返回 None
        """
        if self.provider == "dashscope":
            return await self._generate_image_data_dashscope(prompt)

        try:
            if not self.client:
                logger.warning("Nano Banana（Gemini）未配置 API Key，跳过生图")
                return None
            image_config_params: Dict[str, Any] = {"aspect_ratio": self.aspect_ratio}

            if self.model and "gemini-3-pro" in self.model:
                image_config_params["image_size"] = self.image_size

            image_config = types.ImageConfig(**image_config_params)

            config = types.GenerateContentConfig(
                response_modalities=["TEXT", "IMAGE"],
                image_config=image_config,
            )

            logger.info(
                "Nano Banana（Gemini）开始生成图片, model=%s, prompt=%s",
                self.model,
                prompt[:200] if prompt else "",
            )

            response = self.client.models.generate_content(
                model=self.model or "gemini-2.5-flash-image",
                contents=prompt,
                config=config,
            )

            if response.candidates and response.candidates[0].content.parts:
                for part in response.candidates[0].content.parts:
                    if part.inline_data:
                        image_bytes = part.inline_data.data
                        mime_type = part.inline_data.mime_type or "image/png"

                        logger.info(
                            "Nano Banana（Gemini）图片生成成功, "
                            "size=%s bytes, mimeType=%s",
                            len(image_bytes),
                            mime_type,
                        )

                        return ImageData.from_bytes(image_bytes, mime_type)

            logger.error("Nano Banana（Gemini）响应中未找到图片数据")
            return None
        except Exception as e:
            logger.error("Nano Banana（Gemini）生成图片异常: %s", e)
            return None

    def get_method(self) -> ImageMethodEnum:
        """获取图片服务类型"""
        return ImageMethodEnum.NANO_BANANA

    def get_fallback_image(self, position: int) -> str:
        """获取降级图片"""
        return ArticleConstant.PICSUM_URL_TEMPLATE.format(position)
