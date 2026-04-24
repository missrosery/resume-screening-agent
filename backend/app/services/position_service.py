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

        resume_rows = (
            await self.db.execute(
                select(Resume.id, Resume.file_path).where(Resume.position_id == position_id)
            )
        ).all()
        resume_ids = [row.id for row in resume_rows]

        if resume_ids:
            await self.db.execute(
                delete(ScreeningResult).where(ScreeningResult.resume_id.in_(resume_ids))
            )
            await self._delete_vector_documents(position_id)
            await self.db.execute(delete(Resume).where(Resume.position_id == position_id))

        await self.db.execute(delete(ScreeningSession).where(ScreeningSession.position_id == position_id))
        await self.db.delete(position)
        await self.db.flush()

        for row in resume_rows:
            file_path = Path(row.file_path)
            if file_path.exists():
                try:
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
        table_exists = await self.db.scalar(text("select to_regclass('public.langchain_pg_embedding')"))
        if not table_exists:
            return

        await self.db.execute(
            text("delete from langchain_pg_embedding where cmetadata ->> 'position_id' = :position_id"),
            {"position_id": str(position_id)},
        )

    async def _remove_directory(self, path: Path) -> None:
        await asyncio.to_thread(shutil.rmtree, path)
