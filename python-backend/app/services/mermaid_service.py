"""Mermaid 流程图生成服务（第 5 期新增）"""

import logging
import subprocess
import tempfile
from pathlib import Path
from typing import Optional

import httpx

from app.config import settings
from app.constants.article import ArticleConstant
from app.models.enums import ImageMethodEnum
from app.schemas.image import ImageData, ImageRequest
from app.services.image_search_service import ImageSearchService

logger = logging.getLogger(__name__)


class MermaidService(ImageSearchService):
    """Mermaid 流程图：优先本地 mmdc；未安装时可选 Kroki 远程渲染。"""

    def __init__(self):
        self.cli_command = settings.mermaid_cli_command
        self.background_color = settings.mermaid_background_color
        self.output_format = settings.mermaid_output_format
        self.width = settings.mermaid_width
        self.timeout = settings.mermaid_timeout / 1000  # 转为秒
        self._local_mmdc = self._probe_mmdc()
        if not self._local_mmdc:
            logger.info(
                "未检测到本地 mmdc（@mermaid-js/mermaid-cli）；"
                "MERMAID 将%s",
                "尝试 Kroki 远程渲染" if settings.mermaid_enable_remote_fallback else "不可用（可在 .env 开启 mermaid_enable_remote_fallback）",
            )

    def _probe_mmdc(self) -> bool:
        try:
            r = subprocess.run(
                [self.cli_command, "--version"],
                capture_output=True,
                timeout=5,
            )
            return r.returncode == 0
        except Exception:
            return False

    async def search_image(self, keywords: str) -> Optional[str]:
        """此方法已废弃，请使用 get_image_data()"""
        return None

    async def get_image(self, request: ImageRequest) -> Optional[str]:
        """此方法已废弃，请使用 get_image_data()"""
        return None

    async def get_image_data(self, request: ImageRequest) -> Optional[ImageData]:
        """获取图片数据"""
        mermaid_code = request.get_effective_param(True)
        return await self.generate_diagram_data(mermaid_code)

    async def generate_diagram_data(self, mermaid_code: str) -> Optional[ImageData]:
        """
        生成 Mermaid 图表数据：本地 mmdc 成功则返回；否则 Kroki（需外网）。
        """
        if not mermaid_code or not mermaid_code.strip():
            logger.warning("Mermaid 代码为空")
            return None

        if self._local_mmdc:
            try:
                return await self._generate_with_mmdc(mermaid_code)
            except Exception as e:
                logger.warning(
                    "Mermaid 本地 mmdc 失败，尝试远程: %s: %r",
                    type(e).__name__,
                    e,
                )

        if settings.mermaid_enable_remote_fallback:
            return await self._generate_via_kroki(mermaid_code)

        logger.error("Mermaid 不可用：无 mmdc 且已关闭远程回退")
        return None

    async def _generate_with_mmdc(self, mermaid_code: str) -> ImageData:
        temp_input_file = None
        temp_output_file = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".mmd", delete=False, encoding="utf-8"
            ) as f:
                f.write(mermaid_code)
                temp_input_file = f.name

            output_extension = f".{self.output_format}"
            with tempfile.NamedTemporaryFile(
                suffix=output_extension, delete=False
            ) as f:
                temp_output_file = f.name

            await self._convert_mermaid_to_image(temp_input_file, temp_output_file)

            with open(temp_output_file, "rb") as f:
                image_bytes = f.read()

            mime_type = self._get_mime_type()
            logger.info(
                "Mermaid 本地图表生成成功, size=%s bytes, format=%s",
                len(image_bytes),
                self.output_format,
            )
            return ImageData.from_bytes(image_bytes, mime_type)
        finally:
            if temp_input_file:
                Path(temp_input_file).unlink(missing_ok=True)
            if temp_output_file:
                Path(temp_output_file).unlink(missing_ok=True)

    async def _generate_via_kroki(self, mermaid_code: str) -> Optional[ImageData]:
        """通过 Kroki 将 Mermaid 渲染为 SVG/PNG（POST diagram 源码）。"""
        fmt = (self.output_format or "svg").lower()
        if fmt not in ("svg", "png"):
            fmt = "svg"
        base = (settings.mermaid_remote_kroki_url or "https://kroki.io").rstrip("/")
        url = f"{base}/mermaid/{fmt}"
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                resp = await client.post(
                    url,
                    content=mermaid_code.encode("utf-8"),
                    headers={
                        "Content-Type": "text/plain; charset=utf-8",
                        "User-Agent": "ai-passage-creator-backend/1.0",
                    },
                )
            if resp.status_code != 200:
                logger.error(
                    "Kroki Mermaid 渲染失败: status=%s body=%s",
                    resp.status_code,
                    (resp.text or "")[:800],
                )
                return None
            mime = "image/svg+xml" if fmt == "svg" else "image/png"
            logger.info("Mermaid Kroki 渲染成功, bytes=%s, fmt=%s", len(resp.content), fmt)
            return ImageData.from_bytes(resp.content, mime)
        except Exception as e:
            logger.error(
                "Kroki Mermaid 请求异常: %s: %r",
                type(e).__name__,
                e,
                exc_info=True,
            )
            return None

    async def _convert_mermaid_to_image(self, input_file: str, output_file: str):
        """转换 Mermaid 代码为图片"""
        cmd = [
            self.cli_command,
            "-i",
            input_file,
            "-o",
            output_file,
            "-b",
            self.background_color,
            "-w",
            str(self.width),
        ]

        logger.info("执行 Mermaid 转换命令: %s", " ".join(cmd))

        result = subprocess.run(
            cmd,
            timeout=self.timeout,
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:
            raise RuntimeError(f"Mermaid 转换失败: {result.stderr}")

    def _get_mime_type(self) -> str:
        """根据输出格式获取 MIME 类型"""
        format_lower = self.output_format.lower()
        if format_lower == "png":
            return "image/png"
        if format_lower == "svg":
            return "image/svg+xml"
        if format_lower == "pdf":
            return "application/pdf"
        return "image/png"

    def get_method(self) -> ImageMethodEnum:
        """获取图片服务类型"""
        return ImageMethodEnum.MERMAID

    def get_fallback_image(self, position: int) -> str:
        """获取降级图片"""
        return ArticleConstant.PICSUM_URL_TEMPLATE.format(position)

    def is_available(self) -> bool:
        """本地 mmdc 可用，或允许 Kroki 远程回退时视为可用。"""
        if self._local_mmdc:
            return True
        return bool(settings.mermaid_enable_remote_fallback)
