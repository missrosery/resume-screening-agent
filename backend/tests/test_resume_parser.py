from uuid import uuid4

from app.models.schemas import ParsedResumeData, WorkExperience
from app.rag.resume_parser import ResumeParser


def test_sanitize_text_removes_control_chars_and_extra_spacing() -> None:
    parser = ResumeParser()

    cleaned = parser.sanitize_text("张三\x00\x01  Python\n\n\n\nFastAPI")

    assert cleaned == "张三 Python\n\nFastAPI"


def test_build_documents_adds_summary_and_experience_metadata() -> None:
    parser = ResumeParser()
    resume_id = uuid4()
    position_id = uuid4()
    data = ParsedResumeData(
        name="张三",
        job_intention="后端工程师",
        summary="熟悉 FastAPI",
        skills=["Python", "PostgreSQL"],
        work_experience=[
            WorkExperience(
                company="示例科技",
                position="后端开发",
                duration="2024-2025",
                responsibilities=["负责 API 开发"],
            )
        ],
    )

    docs = parser.build_documents(data, resume_id, position_id)

    assert len(docs) == 2
    assert docs[0].metadata == {
        "resume_id": str(resume_id),
        "position_id": str(position_id),
        "doc_type": "summary",
    }
    assert docs[1].metadata["company"] == "示例科技"
    assert "负责 API 开发" in docs[1].page_content
