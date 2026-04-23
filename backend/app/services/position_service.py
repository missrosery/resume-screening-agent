from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.database import JobPosition, Resume
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
