from collections.abc import AsyncGenerator

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings
from app.models.database import Base

engine = create_async_engine(settings.database_url, future=True)
# sessionmaker 相当于“数据库会话工厂”。
# 每次请求进来时，get_db 都会用它创建一个独立的 AsyncSession。
AsyncSessionFactory = async_sessionmaker(engine, expire_on_commit=False)


async def init_db() -> None:
    # 启动时保证上传目录存在，并创建 pgvector 扩展和 ORM 表。
    # Base.metadata.create_all 只会创建不存在的表，不会删除已有数据。
    settings.upload_path.mkdir(parents=True, exist_ok=True)
    async with engine.begin() as conn:
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        await conn.run_sync(Base.metadata.create_all)
        await conn.execute(text("ALTER TABLE resumes ADD COLUMN IF NOT EXISTS file_hash VARCHAR(64)"))


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    # FastAPI 的 Depends(get_db) 会把这里 yield 出去的 session 注入到接口函数。
    # 接口执行成功就 commit，抛异常就 rollback，保证事务边界统一。
    async with AsyncSessionFactory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
