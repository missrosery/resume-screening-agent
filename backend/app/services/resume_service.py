import asyncio
import hashlib
from pathlib import Path
from uuid import UUID, uuid4

from fastapi import HTTPException, UploadFile
from sqlalchemy import delete, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.infrastructure.database import AsyncSessionFactory
from app.models.database import Resume, ScreeningResult
from app.rag.resume_parser import resume_parser
from app.rag.vector_store import resume_vector_store


class ResumeService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def upload_resumes(self, position_id: UUID, files: list[UploadFile]) -> list[tuple[Resume, bool]]:
        # 返回值里的 bool 表示“是否重复上传”。
        # 这样前端可以告诉用户：这个文件已存在，本次没有重复解析。
        uploads: list[tuple[Resume, bool]] = []
        seen_by_hash: dict[str, Resume] = {}
        for file in files:
            ext = Path(file.filename or "").suffix.lower().lstrip(".")
            if ext not in {"pdf", "docx"}:
                raise HTTPException(status_code=400, detail=f"Unsupported file type: {ext}")

            target_dir = settings.upload_path / str(position_id)
            target_dir.mkdir(parents=True, exist_ok=True)
            content = await file.read()
            # 用文件内容算 hash，比单纯比较文件名更可靠：
            # 同一份简历即使改了文件名，hash 仍然相同。
            file_hash = hashlib.sha256(content).hexdigest()

            if file_hash in seen_by_hash:
                uploads.append((seen_by_hash[file_hash], True))
                continue

            await self._lock_file_hash(position_id, file_hash)
            existing = await self._get_existing_by_hash(position_id, file_hash)
            if existing:
                seen_by_hash[file_hash] = existing
                uploads.append((existing, True))
                await self.db.commit()
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
            await self.db.commit()
            seen_by_hash[file_hash] = resume
            uploads.append((resume, False))

        return uploads

    @classmethod
    async def parse_pending_resumes(cls, resume_ids: list[UUID]) -> None:
        for resume_id in resume_ids:
            async with AsyncSessionFactory() as session:
                service = cls(session)
                await service.parse_resume(resume_id)

    async def parse_resume(self, resume_id: UUID) -> None:
        resume = await self.db.get(Resume, resume_id)
        if not resume or resume.parse_status != "parsing":
            return

        target_path = Path(resume.file_path)
        try:
            # 解析分三步：
            # 1. 从 PDF/DOCX 提取文本；
            # 2. 调 LLM 把文本整理成结构化字段；
            # 3. 把摘要和经历写入向量库，供后续语义检索。
            parsed = await resume_parser.parse(target_path, resume.file_type, resume.id, resume.position_id)
            resume.raw_text = parsed.raw_text
            resume.parsed_data = parsed.parsed_data.model_dump()
            resume.parse_status = "parsed"
            resume.parse_error = None
            await resume_vector_store.add_documents(parsed.documents)
        except Exception as exc:
            # 单份简历解析失败时，只把状态标记为 failed，
            # 不让整个批量上传接口直接崩掉，方便前端展示失败原因。
            resume.parse_status = "failed"
            resume.parse_error = str(exc)

        await self.db.flush()
        await self.db.commit()

    async def _lock_file_hash(self, position_id: UUID, file_hash: str) -> None:
        await self.db.execute(
            text("select pg_advisory_xact_lock(hashtext(:lock_key)::bigint)"),
            {"lock_key": f"resume-upload:{position_id}:{file_hash}"},
        )

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
        rows = list((await self.db.execute(stmt)).scalars().all())
        return self._dedupe_by_file_hash(rows)

    def _dedupe_by_file_hash(self, resumes: list[Resume]) -> list[Resume]:
        deduped: dict[str, Resume] = {}
        for resume in resumes:
            key = resume.file_hash or str(resume.id)
            current = deduped.get(key)
            if current is None or (current.parse_status != "parsed" and resume.parse_status == "parsed"):
                deduped[key] = resume
        return list(deduped.values())

    async def get(self, resume_id: UUID) -> Resume | None:
        return await self.db.get(Resume, resume_id)

    async def delete(self, resume_id: UUID) -> bool:
        resume = await self.db.get(Resume, resume_id)
        if not resume:
            return False

        # 删除简历时要同步清理三类数据：
        # 筛选结果表、向量库文档、本地上传文件。
        await self.db.execute(delete(ScreeningResult).where(ScreeningResult.resume_id == resume_id))
        await self._delete_vector_documents(resume_id)

        file_path = Path(resume.file_path)
        await self.db.delete(resume)
        await self.db.flush()
        await self.db.commit()

        if file_path.exists():
            try:
                await asyncio.to_thread(file_path.unlink)
            except Exception:
                pass

        return True

    async def _delete_vector_documents(self, resume_id: UUID) -> None:
        # 如果项目刚启动还没写过向量，langchain_pg_embedding 表可能不存在。
        # 先判断表是否存在，可以避免删除时报 SQL 错。
        table_exists = await self.db.scalar(text("select to_regclass('public.langchain_pg_embedding')"))
        if not table_exists:
            return

        await self.db.execute(
            text("delete from langchain_pg_embedding where cmetadata ->> 'resume_id' = :resume_id"),
            {"resume_id": str(resume_id)},
        )
