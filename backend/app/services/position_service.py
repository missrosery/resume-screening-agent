import asyncio
import shutil
from pathlib import Path
from uuid import UUID

from sqlalchemy import delete, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.database import JobPosition, Resume, ScreeningResult, ScreeningSession
from app.models.schemas import PositionCreate


class PositionService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create(self, body: PositionCreate) -> JobPosition:
        # SQLAlchemy ORM 的写法：先创建 Python 对象，再 add 到 session。
        # flush 会把 SQL 发给数据库，但事务真正提交由 get_db 统一 commit。
        position = JobPosition(
            title=body.title,
            department=body.department,
            requirements=body.requirements,
        )
        self.db.add(position)
        await self.db.flush()
        await self.db.refresh(position)
        return position

    async def list_all(self) -> list[JobPosition]:
        stmt = select(JobPosition).order_by(JobPosition.created_at.desc())
        return list((await self.db.execute(stmt)).scalars().all())

    async def get(self, position_id: UUID) -> JobPosition | None:
        return await self.db.get(JobPosition, position_id)

    async def delete(self, position_id: UUID) -> bool:
        position = await self.db.get(JobPosition, position_id)
        if not position:
            return False

        # 先查出该岗位下所有简历的 ID 和文件路径。
        # ID 用来删数据库关联数据，文件路径用来删 uploads 目录里的真实文件。
        resume_rows = (
            await self.db.execute(
                select(Resume.id, Resume.file_path).where(Resume.position_id == position_id)
            )
        ).all()
        resume_ids = [row.id for row in resume_rows]

        if resume_ids:
            # 删除顺序很重要：先删依赖简历的筛选结果和向量文档，再删简历本身。
            # 否则数据库外键或向量库里的脏数据会留下问题。
            await self.db.execute(
                delete(ScreeningResult).where(ScreeningResult.resume_id.in_(resume_ids))
            )
            await self._delete_vector_documents(position_id)
            await self.db.execute(delete(Resume).where(Resume.position_id == position_id))

        await self.db.execute(delete(ScreeningSession).where(ScreeningSession.position_id == position_id))
        await self.db.delete(position)
        await self.db.flush()
        await self.db.commit()

        for row in resume_rows:
            file_path = Path(row.file_path)
            if file_path.exists():
                try:
                    # 文件清理失败不应该影响“删除岗位”这个主流程，
                    # 所以这里吞掉异常。生产项目里可以再补日志。
                    file_path.unlink()
                except Exception:
                    pass

        position_dir = settings.upload_path / str(position_id)
        if position_dir.exists():
            try:
                await self._remove_directory(position_dir)
            except Exception:
                pass

        return True

    async def _delete_vector_documents(self, position_id: UUID) -> None:
        # langchain_pg_embedding 是 LangChain PGVector 自动维护的表。
        # 本项目把 position_id 存在 cmetadata 里，删除岗位时按 metadata 清向量。
        table_exists = await self.db.scalar(text("select to_regclass('public.langchain_pg_embedding')"))
        if not table_exists:
            return

        await self.db.execute(
            text("delete from langchain_pg_embedding where cmetadata ->> 'position_id' = :position_id"),
            {"position_id": str(position_id)},
        )

    async def _remove_directory(self, path: Path) -> None:
        # shutil.rmtree 是同步阻塞函数，用 asyncio.to_thread 放到线程里执行，
        # 避免阻塞 FastAPI 的异步事件循环。
        await asyncio.to_thread(shutil.rmtree, path)
