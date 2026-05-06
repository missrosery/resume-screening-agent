import asyncio
from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.models.database import Resume
from app.models.schemas import ResumeCompareRequest
from app.services import screening_service as screening_module
from app.services.screening_service import ScreeningService


class FakeDB:
    def __init__(self, resumes: list[Resume] | None = None) -> None:
        self.resumes = {resume.id: resume for resume in resumes or []}

    async def get(self, model, item_id):  # noqa: ANN001
        return self.resumes.get(item_id)


def make_resume(name: str, skills: list[str]) -> Resume:
    resume = Resume(
        id=uuid4(),
        position_id=uuid4(),
        file_name=f"{name}.pdf",
        file_hash=str(uuid4()),
        file_path=f"/tmp/{name}.pdf",
        file_type="pdf",
        parse_status="parsed",
        parsed_data={
            "name": name,
            "highest_degree": "硕士",
            "work_years": 2,
            "skills": skills,
        },
    )
    return resume


def test_normalize_question_items_accepts_strings_and_category_aliases() -> None:
    service = ScreeningService(FakeDB())

    items = service._normalize_question_items(
        [
            "请介绍一个项目",
            {"question": "如何排查线上问题？", "category": "technical"},
            {"question": "一次困难协作经历？", "category": "行为"},
        ]
    )

    assert [item.category for item in items] == ["技术深挖", "技术深挖", "行为判断"]


def test_compare_resumes_requires_two_resumes() -> None:
    service = ScreeningService(FakeDB())

    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(service.compare_resumes(ResumeCompareRequest(resume_ids=[uuid4()])))

    assert exc_info.value.status_code == 400


def test_compare_resumes_falls_back_when_llm_fails(monkeypatch) -> None:
    resume_a = make_resume("张三", ["Python", "FastAPI"])
    resume_b = make_resume("李四", ["React", "TypeScript"])
    service = ScreeningService(FakeDB([resume_a, resume_b]))

    async def fail_complete_text(*args, **kwargs):  # noqa: ANN002, ANN003
        raise RuntimeError("LLM unavailable")

    monkeypatch.setattr(screening_module.llm_client, "complete_text", fail_complete_text)

    response = asyncio.run(
        service.compare_resumes(
            ResumeCompareRequest(
                resume_ids=[resume_a.id, resume_b.id],
                criteria="后端工程能力",
            )
        )
    )

    assert "LLM 对比暂不可用" in response.summary
    assert "张三" in response.summary
    assert "李四" in response.summary
