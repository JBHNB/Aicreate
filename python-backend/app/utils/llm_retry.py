"""LLM 调用重试与 JSON 抽取（智能体 JSON 输出容错）"""

import asyncio
import json
import logging
import re
from typing import Any, Awaitable, Callable, List, TypeVar

from pydantic import ValidationError

logger = logging.getLogger(__name__)

T = TypeVar("T")

# 可触发重试的异常类型
RETRYABLE_EXCEPTIONS = (
    json.JSONDecodeError,
    ValidationError,
    RuntimeError,
    TimeoutError,
    ConnectionError,
)


def extract_json_text(raw: str) -> str:
    """
    从模型输出中抽取 JSON 文本：去掉 markdown 代码块、常见前后说明。
    不再用 rfind 截断（字符串内的 ] 会导致截断错误）；完整边界由 raw_decode 判定。
    """
    if not raw:
        return ""
    text = raw.strip()
    fence = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text, re.IGNORECASE)
    if fence:
        text = fence.group(1).strip()
    idx_arr = text.find("[")
    idx_obj = text.find("{")
    if idx_arr >= 0 and (idx_obj < 0 or idx_arr <= idx_obj):
        return text[idx_arr:].strip()
    if idx_obj >= 0:
        return text[idx_obj:].strip()
    return text.strip()


def _loads_first_json(cleaned: str, name: str) -> Any:
    """解析首个完整 JSON 值，忽略其后多余说明文字。"""
    text = cleaned.strip()
    if not text:
        raise RuntimeError(f"{name}解析失败：内容为空")
    decoder = json.JSONDecoder()
    try:
        result, end = decoder.raw_decode(text)
    except json.JSONDecodeError as e:
        logger.warning("%s JSONDecodeError: %s, snippet=%s", name, e, text[:200])
        raise RuntimeError(f"{name}解析失败") from e
    rest = text[end:].strip()
    if rest:
        logger.info("%s 已忽略 JSON 后的多余文本: %s", name, rest[:80])
    return result


def _coerce_to_list(obj: Any, name: str) -> list:
    if isinstance(obj, list):
        return obj
    if isinstance(obj, dict):
        for key in ("titleOptions", "titles", "options", "data", "result", "items"):
            val = obj.get(key)
            if isinstance(val, list):
                return val
    raise RuntimeError(f"{name}解析失败：响应不是 JSON 数组")


def parse_json_object(content: str, name: str = "JSON") -> dict:
    """解析 JSON 对象，失败抛 RuntimeError 供重试层捕获。"""
    cleaned = extract_json_text(content)
    result = _loads_first_json(cleaned, name)
    if not isinstance(result, dict):
        raise RuntimeError(f"{name}解析失败：响应不是 JSON 对象")
    return result


def parse_json_list(content: str, name: str = "JSON") -> list:
    """解析 JSON 数组（兼容外包一层对象或 JSON 后附带说明）。"""
    cleaned = extract_json_text(content)
    result = _loads_first_json(cleaned, name)
    return _coerce_to_list(result, name)


def is_retryable(exc: BaseException) -> bool:
    if isinstance(exc, RETRYABLE_EXCEPTIONS):
        return True
    # OpenAI / httpx 限流等
    name = type(exc).__name__
    if name in ("RateLimitError", "APITimeoutError", "APIConnectionError"):
        return True
    msg = str(exc).lower()
    if "rate" in msg and "limit" in msg:
        return True
    if "timeout" in msg:
        return True
    return False


async def async_retry_llm(
    coro_factory: Callable[[int], Awaitable[T]],
    *,
    max_attempts: int,
    base_delay: float,
    agent_name: str = "llm",
) -> T:
    """
    异步重试：coro_factory(attempt_index) 返回 awaitable。
    attempt_index 从 0 开始；重试时可在 factory 内追加 prompt 修正。
    """
    last_exc: BaseException | None = None
    attempts = max(1, max_attempts)
    for attempt in range(attempts):
        try:
            return await coro_factory(attempt)
        except BaseException as exc:
            last_exc = exc
            if not is_retryable(exc) or attempt >= attempts - 1:
                raise
            delay = min(30.0, base_delay * (2**attempt))
            logger.warning(
                "%s retry attempt=%s/%s, delay=%ss: %s: %s",
                agent_name,
                attempt + 2,
                attempts,
                delay,
                type(exc).__name__,
                exc,
            )
            await asyncio.sleep(delay)
    raise last_exc  # pragma: no cover
