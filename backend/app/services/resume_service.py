import asyncio
import hashlib
from pathlib import Path
from uuid import UUID, uuid4

from fastapi import HTTPException, UploadFile
from sqlalchemy import delete, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.database import Resume, ScreeningResult
from app.rag.resume_parser import resume_parser
from app.rag.vector_store import resume_vector_store


class ResumeService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def upload_and_parse(self, position_id: UUID, files: list[UploadFile]) -> list[tuple[Resume, bool]]:
        uploads: list[tuple[Resume, bool]] = []
        for file in files:
            ext = Path(file.filename or "").suffix.lower().lstrip(".")
            if ext not in {"pdf", "docx"}:
                raise HTTPException(status_code=400, detail=f"Unsupported file type: {ext}")

            target_dir = settings.upload_path / str(position_id)
            target_dir.mkdir(parents=True, exist_ok=True)
            content = await file.read()
            file_hash = hashlib.sha256(content).hexdigest()

            existing = await self._get_existing_by_hash(position_id, file_hash)
            if existing:
                uploads.append((existing, True))
                continue

            target_path = target_dir / f"{uuid4()}_{file.filename}"
            await asyncio.to_thread(target_path.write_bytes, content)

            resume = Resume(
                position_id=position_id,
                file_name=file.filename or target_path.name,
                file_hash=file_hash,
                file_path=str(target_path),
                file_type=ext,
                parse_status="parsing",
            )
            self.db.add(resume)
            await self.db.flush()

            try:
                parsed = await resume_parser.parse(target_path, ext, resume.id, position_id)
                resume.raw_text = parsed.raw_text
                resume.parsed_data = parsed.parsed_data.model_dump()
                resume.parse_status = "parsed"
                await resume_vector_store.add_documents(parsed.documents)
            except Exception as exc:
                resume.parse_status = "failed"
                resume.parse_error = str(exc)

            uploads.append((resume, False))

        await self.db.flush()
        return uploads

    async def _get_existing_by_hash(self, position_id: UUID, file_hash: str) -> Resume | None:
        stmt = select(Resume).where(
            Resume.position_id == position_id,
            Resume.file_hash == file_hash,
        )
        return (await self.db.execute(stmt)).scalars().first()

    async def list_by_position(self, position_id: UUID) -> list[Resume]:
        stmt = (
            select(Resume)
            .where(Resume.position_id == position_id)
            .order_by(Resume.created_at.desc())
        )
        return list((await self.db.execute(stmt)).scalars().all())

    async def get(self, resume_id: UUID) -> Resume | None:
        return await self.db.get(Resume, resume_id)

    async def delete(self, resume_id: UUID) -> bool:
        resume = await self.db.get(Resume, resume_id)
        if not resume:
            return False

        await self.db.execute(delete(ScreeningResult).where(ScreeningResult.resume_id == resume_id))
        await self._delete_vector_documents(resume_id)

        file_path = Path(resume.file_path)
        if file_path.exists():
            try:
                await asyncio.to_thread(file_path.unlink)
            except Exception:
                pass

        await self.db.delete(resume)
        await self.db.flush()
        return True

    async def _delete_vector_documents(self, resume_id: UUID) -> None:
        table_exists = await self.db.scalar(text("select to_regclass('public.langchain_pg_embedding')"))
        if not table_exists:
            return

        await self.db.execute(
            text("delete from langchain_pg_embedding where cmetadata ->> 'resume_id' = :resume_id"),
            {"resume_id": str(resume_id)},
        )
