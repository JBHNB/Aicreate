"""文章创作路由"""

import asyncio
import json

from databases import Database
from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse

from app.database import get_db
from app.deps import require_login
from app.schemas.common import BaseResponse, DeleteRequest
from app.schemas.passage import PassageCreateRequest, PassageUpdateRequest, PassageVO
from app.schemas.user import LoginUserVO
from app.services.passage_service import PassageService

router = APIRouter(prefix="/passage", tags=["文章创作"])


@router.post(
    "/generate",
    response_model=BaseResponse[PassageVO],
    response_model_by_alias=True,
)
async def generate_passage(
    request: PassageCreateRequest,
    db: Database = Depends(get_db),
    current_user: LoginUserVO = Depends(require_login),
):
    """根据标题与提示生成正文并落库；若配置 DASHSCOPE_API_KEY 则调用通义千问。"""
    service = PassageService(db)
    vo = await service.generate_and_save(current_user.id, request)
    return BaseResponse.success(data=vo, message="生成成功")


@router.get("/stream/demo")
async def stream_demo(
    current_user: LoginUserVO = Depends(require_login),
):
    """
    SSE 推送演示（对应教程「流式输出」入门）。
    前端可用 EventSource('/api/passage/stream/demo') 订阅（经 Vite 代理同源）。
    """

    async def event_gen():
        display = current_user.user_name or current_user.user_account
        chunks = [
            json.dumps({"type": "meta", "user": display}, ensure_ascii=False),
            json.dumps({"type": "token", "text": "这"}, ensure_ascii=False),
            json.dumps({"type": "token", "text": "是"}, ensure_ascii=False),
            json.dumps({"type": "token", "text": " S"}, ensure_ascii=False),
            json.dumps({"type": "token", "text": "S"}, ensure_ascii=False),
            json.dumps({"type": "token", "text": "E "}, ensure_ascii=False),
            json.dumps({"type": "token", "text": "分"}, ensure_ascii=False),
            json.dumps({"type": "token", "text": "块"}, ensure_ascii=False),
            json.dumps({"type": "token", "text": "演"}, ensure_ascii=False),
            json.dumps({"type": "token", "text": "示"}, ensure_ascii=False),
            json.dumps({"type": "token", "text": "。\n"}, ensure_ascii=False),
        ]
        for payload in chunks:
            await asyncio.sleep(0.2)
            yield f"data: {payload}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(
        event_gen(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get(
    "/get",
    response_model=BaseResponse[PassageVO],
    response_model_by_alias=True,
)
async def get_passage(
    id: int,
    db: Database = Depends(get_db),
    current_user: LoginUserVO = Depends(require_login),
):
    service = PassageService(db)
    vo = await service.get_by_id(id, current_user.id)
    return BaseResponse.success(data=vo)


@router.get(
    "/list",
    response_model=BaseResponse[dict],
    response_model_by_alias=True,
)
async def list_my_passages(
    db: Database = Depends(get_db),
    current_user: LoginUserVO = Depends(require_login),
    current: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100, alias="pageSize"),
):
    """分页查询当前用户的创作记录。"""
    service = PassageService(db)
    records, total = await service.list_by_user(
        current_user.id, current, page_size
    )
    return BaseResponse.success(
        data={
            "records": records,
            "total": total,
            "current": current,
            "size": page_size,
        }
    )


@router.post(
    "/update",
    response_model=BaseResponse[PassageVO],
    response_model_by_alias=True,
)
async def update_passage(
    request: PassageUpdateRequest,
    db: Database = Depends(get_db),
    current_user: LoginUserVO = Depends(require_login),
):
    """更新本人文章（标题 / 提示 / 正文至少改一项）。"""
    service = PassageService(db)
    vo = await service.update(current_user.id, request)
    return BaseResponse.success(data=vo, message="更新成功")


@router.post(
    "/delete",
    response_model=BaseResponse[bool],
    response_model_by_alias=True,
)
async def delete_passage(
    request: DeleteRequest,
    db: Database = Depends(get_db),
    current_user: LoginUserVO = Depends(require_login),
):
    """软删除本人文章。"""
    service = PassageService(db)
    ok = await service.soft_delete(request.id, current_user.id)
    return BaseResponse.success(data=ok, message="删除成功")
