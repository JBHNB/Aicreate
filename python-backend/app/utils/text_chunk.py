"""文本分块工具"""

import re
from typing import List


def split_text_to_chunks(text: str, chunk_size: int, overlap: int) -> List[str]:
    """按段落优先、超长段落滑动窗口分块。"""
    text = (text or "").strip()
    if not text:
        return []

    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    chunks: List[str] = []
    buffer = ""

    def flush_buffer():
        nonlocal buffer
        if buffer:
            chunks.append(buffer)
            buffer = ""

    def split_long_paragraph(paragraph: str):
        start = 0
        while start < len(paragraph):
            end = min(start + chunk_size, len(paragraph))
            chunks.append(paragraph[start:end])
            if end >= len(paragraph):
                break
            start = max(end - overlap, start + 1)

    for paragraph in paragraphs:
        if len(paragraph) > chunk_size:
            flush_buffer()
            split_long_paragraph(paragraph)
            continue

        candidate = f"{buffer}\n\n{paragraph}".strip() if buffer else paragraph
        if len(candidate) <= chunk_size:
            buffer = candidate
        else:
            flush_buffer()
            buffer = paragraph

    flush_buffer()

    if overlap <= 0 or len(chunks) <= 1:
        return chunks

    merged: List[str] = [chunks[0]]
    for idx in range(1, len(chunks)):
        prev = merged[-1]
        tail = prev[-overlap:] if overlap < len(prev) else prev
        merged.append(f"{tail}{chunks[idx]}")
    return merged
