"""系统知识库文档 ORM 模型"""

from datetime import datetime

from sqlalchemy import BigInteger, Column, DateTime, Integer, SmallInteger, String, Text
from sqlalchemy.sql import func

from app.database import Base


class KnowledgeDocument(Base):
    """系统知识库文档表"""

    __tablename__ = "knowledge_document"

    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="id")
    title = Column(String(200), nullable=False, comment="文档标题")
    file_name = Column("fileName", String(255), nullable=False, comment="原始文件名")
    file_type = Column("fileType", String(20), nullable=False, comment="文件类型")
    file_size = Column("fileSize", BigInteger, nullable=False, default=0, comment="文件大小")
    status = Column(String(20), nullable=False, default="processing", comment="状态")
    chunk_count = Column("chunkCount", Integer, nullable=False, default=0, comment="分块数量")
    error_message = Column("errorMessage", Text, nullable=True, comment="失败原因")
    created_by = Column("createdBy", BigInteger, nullable=False, comment="上传管理员ID")
    create_time = Column("createTime", DateTime, nullable=False, default=func.now(), comment="创建时间")
    update_time = Column("updateTime", DateTime, nullable=False, default=func.now(), onupdate=func.now(), comment="更新时间")
    is_delete = Column("isDelete", SmallInteger, nullable=False, default=0, comment="是否删除")
