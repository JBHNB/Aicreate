"""大模型调用（阿里云百炼 OpenAI 兼容接口，与教程 DashScope / 通义体系对齐）"""

import httpx

from app.config import settings

_DASHSCOPE_COMPAT_URL = (
    "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions"
)


async def generate_markdown_article(title: str, prompt: str) -> str:
    """
    调用通义千问兼容接口，返回 Markdown 正文。
    需在 .env 中配置 DASHSCOPE_API_KEY。
    """
    key = settings.dashscope_api_key.strip()
    if not key:
        raise ValueError("DASHSCOPE_API_KEY 未配置")

    async with httpx.AsyncClient(timeout=120.0) as client:
        resp = await client.post(
            _DASHSCOPE_COMPAT_URL,
            headers={
                "Authorization": f"Bearer {key}",
                "Content-Type": "application/json",
            },
            json={
                "model": settings.resolved_llm_model,
                "messages": [
                    {
                        "role": "system",
                        "content": (
                            "你是资深自媒体作者，用中文写作，只输出 Markdown 正文，"
                            "不要前言后语、不要代码围栏包裹全文。"
                        ),
                    },
                    {
                        "role": "user",
                        "content": (
                            f"文章标题：{title}\n\n"
                            f"创作需求：{prompt}\n\n"
                            "请写完整正文（可有二级标题分段）。"
                        ),
                    },
                ],
            },
        )
        resp.raise_for_status()
        data = resp.json()
        return str(data["choices"][0]["message"]["content"])
