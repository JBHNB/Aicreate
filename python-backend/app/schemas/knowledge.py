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
