"""文章创作业务（当前为占位生成，便于后续接入 LLM / 多 Agent）"""

from datetime import datetime
from typing import Any

from databases import Database
from sqlalchemy import and_, func, select

from app.config import settings
from app.exceptions import ErrorCode, throw_if, throw_if_not
from app.models.passage import Passage
from app.utils import llm as llm_util
from app.schemas.passage import (
    PassageCreateRequest,
    PassageListItemVO,
    PassageUpdateRequest,
    PassageVO,
)

P = Passage.__table__


def _dt_iso(v: Any) -> str:
    if v is None:
        return ""
    if isinstance(v, datetime):
        return v.isoformat()
    return str(v)


def stub_generate_content(title: str, prompt: str) -> str:
    """占位生成：未配置 API Key 或模型失败时使用。"""
    return (
        f"# {title}\n\n"
        f"> 创作主题：{prompt}\n\n"
        "---\n\n"
        "当前为 **占位输出**。在 `.env` 中配置 `DASHSCOPE_API_KEY` 后将调用通义千问生成正文。\n"
    )


async def resolve_generated_content(title: str, prompt: str) -> str:
    """优先调用百炼；未配置或失败时回退占位。"""
    if settings.dashscope_api_key.strip():
        try:
            text = await llm_util.generate_markdown_article(title, prompt)
            if text and text.strip():
                return text.strip()
        except Exception as e:
            print(f"[llm] 调用失败，使用占位输出: {e}")
    return stub_generate_content(title, prompt)


def _row_to_passage_vo(r: dict) -> PassageVO:
    """表字段为驼峰时，用别名填充 PassageVO。"""
    return PassageVO.model_validate(
        {
            "id": r["id"],
            "userId": r["userId"],
            "title": r["title"],
            "prompt": r.get("prompt"),
            "content": r["content"],
            "createTime": _dt_iso(r.get("createTime")),
        }
    )


class PassageService:
    def __init__(self, db: Database):
        self.db = db

    async def generate_and_save(
        self, user_id: int, request: PassageCreateRequest
    ) -> PassageVO:
        content = await resolve_generated_content(request.title, request.prompt)
        q = """
        INSERT INTO passage (userId, title, prompt, content)
        VALUES (:userId, :title, :prompt, :content)
        """
        await self.db.execute(
            q,
            {
                "userId": user_id,
                "title": request.title,
                "prompt": request.prompt,
                "content": content,
            },
        )
        last_id = await self.db.fetch_val("SELECT LAST_INSERT_ID() AS id")
        pid = int(last_id)
        row = await self.db.fetch_one(select(P).where(P.c.id == pid))
        throw_if_not(row is not None, ErrorCode.NOT_FOUND_ERROR, "记录不存在")
        r = dict(row)
        return _row_to_passage_vo(r)

    async def get_by_id(self, passage_id: int, user_id: int) -> PassageVO:
        row = await self.db.fetch_one(
            select(P).where(
                and_(P.c.id == passage_id, P.c.userId == user_id, P.c.isDelete == 0)
            )
        )
        throw_if_not(row is not None, ErrorCode.NOT_FOUND_ERROR, "文章不存在")
        r = dict(row)
        return _row_to_passage_vo(r)

    async def update(
        self, user_id: int, request: PassageUpdateRequest
    ) -> PassageVO:
        row = await self.db.fetch_one(
            select(P).where(
                and_(
                    P.c.id == request.id,
                    P.c.userId == user_id,
                    P.c.isDelete == 0,
                )
            )
        )
        throw_if_not(row is not None, ErrorCode.NOT_FOUND_ERROR, "文章不存在")
        fields: dict[str, Any] = {"updateTime": datetime.now()}
        if request.title is not None:
            fields["title"] = request.title
        if request.prompt is not None:
            fields["prompt"] = request.prompt
        if request.content is not None:
            fields["content"] = request.content
        throw_if(
            len(fields) == 1,
            ErrorCode.PARAMS_ERROR,
            "请至少提供 title、prompt、content 之一",
        )
        set_parts = [f"`{k}` = :{k}" for k in fields]
        params = {**fields, "id": request.id, "uid": user_id}
        sql = (
            f"UPDATE passage SET {', '.join(set_parts)} "
            "WHERE id = :id AND userId = :uid AND isDelete = 0"
        )
        await self.db.execute(sql, params)
        row2 = await self.db.fetch_one(
            select(P).where(
                and_(P.c.id == request.id, P.c.userId == user_id, P.c.isDelete == 0)
            )
        )
        throw_if_not(row2 is not None, ErrorCode.NOT_FOUND_ERROR, "文章不存在")
        return _row_to_passage_vo(dict(row2))

    async def soft_delete(self, passage_id: int, user_id: int) -> bool:
        row = await self.db.fetch_one(
            select(P.c.id).where(
                and_(P.c.id == passage_id, P.c.userId == user_id, P.c.isDelete == 0)
            )
        )
        throw_if_not(row is not None, ErrorCode.NOT_FOUND_ERROR, "文章不存在")
        await self.db.execute(
            "UPDATE passage SET isDelete = 1, updateTime = :t "
            "WHERE id = :id AND userId = :uid",
            {"id": passage_id, "uid": user_id, "t": datetime.now()},
        )
        return True

    async def list_by_user(
        self, user_id: int, current: int, page_size: int
    ) -> tuple[list[dict], int]:
        where_clause = and_(P.c.userId == user_id, P.c.isDelete == 0)
        total = await self.db.fetch_val(
            select(func.count()).select_from(P).where(where_clause)
        )
        total = int(total or 0)
        offset = (current - 1) * page_size
        stmt = (
            select(P)
            .where(where_clause)
            .order_by(P.c.createTime.desc())
            .offset(offset)
            .limit(page_size)
        )
        rows = await self.db.fetch_all(stmt)
        records: list[dict] = []
        for row in rows:
            r = dict(row)
            item = PassageListItemVO(
                id=r["id"],
                title=r["title"],
                prompt=r.get("prompt"),
                createTime=_dt_iso(r.get("createTime")),
            )
            records.append(item.model_dump(by_alias=True))
        return records, total
