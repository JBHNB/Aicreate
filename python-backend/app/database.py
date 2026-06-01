"""数据库连接管理"""

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from databases import Database

from app.config import settings

engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
    pool_recycle=3600,
    echo=False,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

database = Database(settings.async_database_url)


async def get_db():
    """获取 databases 连接（依赖注入）"""
    yield database
