from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.models.schemas import ChatRequest, PositionCreate, ResumeCompareRequest, ScreeningRequest


def test_position_title_is_stripped() -> None:
    body = PositionCreate(title="  Backend Engineer  ")

    assert body.title == "Backend Engineer"


def test_position_title_rejects_blank_text() -> None:
    with pytest.raises(ValidationError):
        PositionCreate(title="   ")


def test_screening_request_rejects_invalid_top_n() -> None:
    with pytest.raises(ValidationError):
        ScreeningRequest(query="Python", top_n=0)


def test_chat_request_rejects_blank_message() -> None:
    with pytest.raises(ValidationError):
        ChatRequest(message="\n\t")


def test_compare_request_deduplicates_selected_ids() -> None:
    resume_id_a = uuid4()
    resume_id_b = uuid4()
    body = ResumeCompareRequest(resume_ids=[resume_id_a, resume_id_a, resume_id_b])

    assert body.selected_resume_ids() == [resume_id_a, resume_id_b]
