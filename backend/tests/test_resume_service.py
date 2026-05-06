import asyncio
import io
from datetime import datetime
from pathlib import Path
from uuid import uuid4

import pytest
from fastapi import HTTPException, UploadFile

from app.core.config import settings
from app.models.database import Resume
from app.services.resume_service import ResumeService


class FakeDB:
    def __init__(self) -> None:
        self.added: list[Resume] = []
        self.commits = 0

    def add(self, item: Resume) -> None:
        self.added.append(item)

    async def flush(self) -> None:
        for item in self.added:
            if item.id is None:
                item.id = uuid4()
            if item.created_at is None:
                item.created_at = datetime.utcnow()

    async def commit(self) -> None:
        self.commits += 1


class UploadService(ResumeService):
    async def _lock_file_hash(self, position_id, file_hash: str) -> None:  # noqa: ANN001
        return None

    async def _get_existing_by_hash(self, position_id, file_hash: str) -> Resume | None:  # noqa: ANN001
        return None


def make_upload(filename: str, content: bytes) -> UploadFile:
    return UploadFile(filename=filename, file=io.BytesIO(content))


def test_upload_rejects_unsupported_file_type() -> None:
    service = UploadService(FakeDB())

    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(service.upload_resumes(uuid4(), [make_upload("resume.txt", b"hello")]))

    assert exc_info.value.status_code == 400
    assert "PDF or DOCX" in exc_info.value.detail


def test_upload_rejects_empty_file() -> None:
    service = UploadService(FakeDB())

    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(service.upload_resumes(uuid4(), [make_upload("resume.pdf", b"")]))

    assert exc_info.value.status_code == 400
    assert "empty" in exc_info.value.detail


def test_upload_sanitizes_filename_and_writes_inside_position_dir(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(settings, "upload_dir", str(tmp_path))
    db = FakeDB()
    service = UploadService(db)
    position_id = uuid4()

    uploads = asyncio.run(
        service.upload_resumes(position_id, [make_upload("../nested\\evil?.PDF", b"%PDF-1.4")])
    )

    resume, duplicate = uploads[0]
    assert duplicate is False
    assert resume.file_name == "evil_.PDF"
    assert resume.file_type == "pdf"
    assert db.added == [resume]
    saved_path = Path(resume.file_path)
    assert saved_path.parent == tmp_path / str(position_id)
    assert saved_path.exists()


def test_upload_marks_duplicate_files_in_same_request(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(settings, "upload_dir", str(tmp_path))
    db = FakeDB()
    service = UploadService(db)

    uploads = asyncio.run(
        service.upload_resumes(
            uuid4(),
            [
                make_upload("first.pdf", b"same-content"),
                make_upload("second.pdf", b"same-content"),
            ],
        )
    )

    assert [duplicate for _, duplicate in uploads] == [False, True]
    assert len(db.added) == 1
