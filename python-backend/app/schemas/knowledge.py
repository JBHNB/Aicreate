"""系统知识库相关 Schema"""

from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.common import PageRequest


class KnowledgeDocumentVO(BaseModel):
    """知识库文档 VO"""

    model_config = ConfigDict(populate_by_name=True)

    id: int
    title: str
    file_name: str = Field(..., alias="fileName")
    file_type: str = Field(..., alias="fileType")
    file_size: int = Field(..., alias="fileSize")
    status: str
    chunk_count: int = Field(..., alias="chunkCount")
    error_message: Optional[str] = Field(None, alias="errorMessage")
    created_by: int = Field(..., alias="createdBy")
    create_time: str = Field(..., alias="createTime")
    update_time: str = Field(..., alias="updateTime")


class KnowledgeQueryRequest(PageRequest):
    """知识库分页查询"""

    title: Optional[str] = Field(None, description="标题模糊搜索")
    status: Optional[str] = Field(None, description="状态筛选")


class KnowledgeUpdateTitleRequest(BaseModel):
    """重命名知识库文档"""

    model_config = ConfigDict(populate_by_name=True)

    id: int = Field(..., description="文档 ID")
    title: str = Field(..., min_length=1, max_length=200, description="新标题")

class KnowledgeSearchByStatusRequest(BaseModel):
    """按状态查询知识库文档（不分页）"""

    model_config = ConfigDict(populate_by_name=True)

    status: str = Field(..., description="状态：processing / ready / failed")


class KnowledgeSearchByTitleRequest(BaseModel):
    """按标题关键词查询知识库文档（不分页）"""

    model_config = ConfigDict(populate_by_name=True)

    title: str = Field(..., min_length=1, max_length=200, description="标题关键词（模糊匹配）")


class KnowledgeStatsVO(BaseModel):
    """知识库统计概览"""

    model_config = ConfigDict(populate_by_name=True)

    total: int = Field(..., description="文档总数")
    ready_count: int = Field(..., alias="readyCount", description="已就绪数量")
    processing_count: int = Field(..., alias="processingCount", description="处理中数量")
    failed_count: int = Field(..., alias="failedCount", description="失败数量")


class KnowledgeChunkVO(BaseModel):
    """文档分块预览"""

    model_config = ConfigDict(populate_by_name=True)

    chunk_index: int = Field(..., alias="chunkIndex")
    content: str
    title: str


class RetrievalSourceVO(BaseModel):
    """检索命中来源"""

    model_config = ConfigDict(populate_by_name=True)

    document_id: int = Field(..., alias="documentId")
    title: str
    chunk_index: int = Field(..., alias="chunkIndex")
    score: float


class RetrievalResult(BaseModel):
    """检索结果"""

    context: str = ""
    sources: List[RetrievalSourceVO] = Field(default_factory=list)

    @property
    def hit_count(self) -> int:
        return len(self.sources)
