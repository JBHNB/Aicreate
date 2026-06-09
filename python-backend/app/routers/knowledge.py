"""系统知识库路由（管理员）"""

from typing import List, Optional

from databases import Database
from fastapi import APIRouter, Depends, File, Form, UploadFile

from app.database import get_db
from app.deps import require_admin
from app.exceptions import ErrorCode, throw_if
from app.schemas.common import BaseResponse, DeleteRequest
from app.schemas.knowledge import (
    KnowledgeChunkVO,
    KnowledgeDocumentVO,
    KnowledgeQueryRequest,
    KnowledgeUpdateTitleRequest,
    KnowledgeSearchByStatusRequest,
    KnowledgeSearchByTitleRequest,
    KnowledgeStatsVO,
)
from app.schemas.user import LoginUserVO
from app.services.knowledge_service import KnowledgeService

router = APIRouter(prefix="/knowledge", tags=["系统知识库"])


@router.post("/upload", response_model=BaseResponse[KnowledgeDocumentVO])
async def upload_knowledge_document(
    file: UploadFile = File(...),
    title: Optional[str] = Form(None),
    db: Database = Depends(get_db),
    admin: LoginUserVO = Depends(require_admin),
):
    """上传并索引知识库文档（.txt / .md / .docx）"""
    throw_if(not file.filename, ErrorCode.PARAMS_ERROR, "文件名不能为空")
    file_bytes = await file.read()
    service = KnowledgeService(db)
    document = await service.create_and_ingest(
        title=(title or "").strip() or file.filename,
        file_name=file.filename,
        file_bytes=file_bytes,
        admin_user_id=admin.id,
    )
    return BaseResponse.success(data=document, message="上传并索引成功")


@router.post("/list/page", response_model=BaseResponse[dict])
async def list_knowledge_documents(
    request: KnowledgeQueryRequest,
    db: Database = Depends(get_db),
    _: LoginUserVO = Depends(require_admin),
):
    service = KnowledgeService(db)
    records, total = await service.list_by_page(request)
    return BaseResponse.success(
        data={
            "records": records,
            "total": total,
            "current": request.current,
            "size": request.page_size,
        }
    )


@router.get("/stats", response_model=BaseResponse[KnowledgeStatsVO])
async def get_knowledge_stats(
    db: Database = Depends(get_db),
    _: LoginUserVO = Depends(require_admin),
):
    """知识库统计概览（各状态文档数量）"""
    service = KnowledgeService(db)
    stats = await service.get_stats()
    return BaseResponse.success(data=stats)


@router.post("/search/title", response_model=BaseResponse[List[KnowledgeDocumentVO]])
async def search_knowledge_documents_by_title(
    request: KnowledgeSearchByTitleRequest,
    db: Database = Depends(get_db),
    _: LoginUserVO = Depends(require_admin),
):
    """根据标题关键词搜索知识库文档（不分页）"""
    service = KnowledgeService(db)
    documents = await service.search_by_title(request)
    return BaseResponse.success(data=documents, message="搜索成功")


@router.post("/search/status", response_model=BaseResponse[List[KnowledgeDocumentVO]])
async def search_knowledge_documents_by_status(
    request: KnowledgeSearchByStatusRequest,
    db: Database = Depends(get_db),
    _: LoginUserVO = Depends(require_admin),
):
    """根据状态搜索知识库文档"""
    service = KnowledgeService(db)
    documents = await service.search_by_status(request)
    return BaseResponse.success(data=documents, message="搜索成功")


@router.get("/{document_id}/chunks", response_model=BaseResponse[List[KnowledgeChunkVO]])
async def list_knowledge_document_chunks(
    document_id: int,
    db: Database = Depends(get_db),
    _: LoginUserVO = Depends(require_admin),
):
    """查看文档分块内容（向量库中的切片预览）"""
    service = KnowledgeService(db)
    chunks = await service.list_chunks(document_id)
    return BaseResponse.success(data=chunks)


@router.get("/{document_id}", response_model=BaseResponse[KnowledgeDocumentVO])
async def get_knowledge_document(
    document_id: int,
    db: Database = Depends(get_db),
    _: LoginUserVO = Depends(require_admin),
):
    service = KnowledgeService(db)
    document = await service.get_by_id(document_id)
    throw_if(not document, ErrorCode.NOT_FOUND_ERROR, "文档不存在")
    return BaseResponse.success(data=document)


@router.post("/update/title", response_model=BaseResponse[KnowledgeDocumentVO])
async def update_knowledge_document_title(
    request: KnowledgeUpdateTitleRequest,
    db: Database = Depends(get_db),
    _: LoginUserVO = Depends(require_admin),
):
    """重命名知识库文档标题"""
    service = KnowledgeService(db)
    document = await service.update_title(request.id, request.title)
    return BaseResponse.success(data=document, message="标题已更新")


@router.post("/delete", response_model=BaseResponse[bool])
async def delete_knowledge_document(
    request: DeleteRequest,
    db: Database = Depends(get_db),
    _: LoginUserVO = Depends(require_admin),
):
    service = KnowledgeService(db)
    result = await service.delete_document(request.id)
    return BaseResponse.success(data=result, message="删除成功")


@router.post("/reindex/{document_id}", response_model=BaseResponse[KnowledgeDocumentVO])
async def reindex_knowledge_document(
    document_id: int,
    db: Database = Depends(get_db),
    _: LoginUserVO = Depends(require_admin),
):
    service = KnowledgeService(db)
    document = await service.reindex_document(document_id)
    return BaseResponse.success(data=document, message="重建索引成功")
