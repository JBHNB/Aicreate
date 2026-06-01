"""文章创作相关模型"""

from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class PassageCreateRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    title: str = Field(..., min_length=1, max_length=512, description="标题")
    prompt: str = Field(..., min_length=1, max_length=2048, description="创作提示/主题")


class PassageVO(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: int
    user_id: int = Field(..., alias="userId")
    title: str
    prompt: Optional[str] = Field(None, alias="prompt")
    content: str
    create_time: str = Field(..., alias="createTime")


class PassageListItemVO(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: int
    title: str
    prompt: Optional[str] = Field(None, alias="prompt")
    create_time: str = Field(..., alias="createTime")


class PassageUpdateRequest(BaseModel):
    """更新本人文章（与教程文章管理 CRUD 对齐）"""

    model_config = ConfigDict(populate_by_name=True)

    id: int = Field(..., description="文章 id")
    title: Optional[str] = Field(None, min_length=1, max_length=512, description="标题")
    prompt: Optional[str] = Field(None, min_length=1, max_length=2048, description="创作提示")
    content: Optional[str] = Field(None, min_length=1, description="正文 Markdown")
