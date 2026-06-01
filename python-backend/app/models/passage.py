"""文章创作记录 ORM"""

from sqlalchemy import BigInteger, Column, DateTime, SmallInteger, String, Text, func

from app.database import Base


class Passage(Base):
    """创作记录表"""

    __tablename__ = "passage"

    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="id")
    user_id = Column("userId", BigInteger, nullable=False, comment="作者用户 id")
    title = Column("title", String(512), nullable=False, comment="标题")
    prompt = Column("prompt", String(2048), nullable=True, comment="创作提示")
    content = Column("content", Text, nullable=False, comment="正文")

    create_time = Column(
        "createTime",
        DateTime,
        nullable=False,
        server_default=func.now(),
        comment="创建时间",
    )
    update_time = Column(
        "updateTime",
        DateTime,
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
        comment="更新时间",
    )
    is_delete = Column(
        "isDelete", SmallInteger, nullable=False, default=0, comment="是否删除"
    )
