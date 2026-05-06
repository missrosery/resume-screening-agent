from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class EducationInfo(BaseModel):
    # LLM 从简历中提取出的教育经历结构。
    school: str = ""
    degree: str = ""
    major: str = ""
    start_date: str | None = None
    end_date: str | None = None


class WorkExperience(BaseModel):
    # 工作经历结构。responsibilities 是职责，achievements 是成果。
    company: str = ""
    position: str = ""
    duration: str = ""
    responsibilities: list[str] = Field(default_factory=list)
    achievements: list[str] = Field(default_factory=list)


class ParsedResumeData(BaseModel):
    # 一份简历最终会被整理成这个结构，并保存到 resumes.parsed_data。
    # 后续筛选、对比、出题都优先使用这些字段，而不是反复读取 PDF。
    name: str = ""
    phone: str | None = None
    email: str | None = None
    city: str | None = None
    job_intention: str | None = None
    education: list[EducationInfo] = Field(default_factory=list)
    highest_degree: str = ""
    work_years: int | None = None
    work_experience: list[WorkExperience] = Field(default_factory=list)
    skills: list[str] = Field(default_factory=list)
    certifications: list[str] = Field(default_factory=list)
    summary: str = ""


class PositionCreate(BaseModel):
    # 创建岗位接口的请求体。
    title: str = Field(min_length=1, max_length=200)
    department: str | None = Field(default=None, max_length=100)
    requirements: str | None = Field(default=None, max_length=8000)

    @field_validator("title")
    @classmethod
    def title_must_not_be_blank(cls, value: str) -> str:
        title = value.strip()
        if not title:
            raise ValueError("Position title cannot be blank")
        return title


class PositionResponse(BaseModel):
    # 岗位接口返回给前端的数据结构。
    id: UUID
    title: str
    department: str | None = None
    requirements: str | None = None
    created_at: datetime
    model_config = {"from_attributes": True}


class ResumeResponse(BaseModel):
    # 简历接口返回给前端的数据结构。
    id: UUID
    position_id: UUID
    file_name: str
    file_hash: str | None = None
    file_type: str
    parse_status: str
    parsed_data: dict | None = None
    parse_error: str | None = None
    duplicate: bool = False
    created_at: datetime
    model_config = {"from_attributes": True}


class ScreeningRequest(BaseModel):
    # 筛选接口的请求体：query 是岗位要求或自然语言筛选条件。
    query: str = Field(min_length=1, max_length=2000)
    work_years_min: int | None = Field(default=None, ge=0, le=80)
    degree: str | None = Field(default=None, max_length=50)
    top_n: int = Field(default=5, ge=1, le=20)

    @field_validator("query")
    @classmethod
    def query_must_not_be_blank(cls, value: str) -> str:
        query = value.strip()
        if not query:
            raise ValueError("Screening query cannot be blank")
        return query


class RankedResume(BaseModel):
    # 筛选结果里的单个候选人卡片。
    resume_id: str
    name: str
    match_score: int
    match_reasons: list[str]
    weaknesses: list[str]
    highest_degree: str = ""
    work_years: int | None = None
    skills: list[str] = Field(default_factory=list)


class ScreeningResponse(BaseModel):
    items: list[RankedResume]


class ResumeCompareRequest(BaseModel):
    resume_ids: list[UUID] | None = Field(default=None, max_length=10)
    resume_id_a: UUID | None = None
    resume_id_b: UUID | None = None
    criteria: str | None = Field(default=None, max_length=1000)

    def selected_resume_ids(self) -> list[UUID]:
        raw_ids = self.resume_ids or []
        if not raw_ids and self.resume_id_a and self.resume_id_b:
            raw_ids = [self.resume_id_a, self.resume_id_b]

        unique_ids: list[UUID] = []
        for resume_id in raw_ids:
            if resume_id not in unique_ids:
                unique_ids.append(resume_id)
        return unique_ids


class ResumeCompareResponse(BaseModel):
    summary: str


class InterviewQuestionItem(BaseModel):
    question: str
    category: Literal["技术深挖", "项目复盘", "行为判断"]


class InterviewQuestionGroup(BaseModel):
    category: Literal["技术深挖", "项目复盘", "行为判断"]
    questions: list[str]


class InterviewQuestionsResponse(BaseModel):
    questions: list[str]
    groups: list[InterviewQuestionGroup] = Field(default_factory=list)


class InterviewQuestionLLMItem(BaseModel):
    question: str
    category: str | None = None


class ScreeningSessionCreate(BaseModel):
    title: str = Field(default="New Session", min_length=1, max_length=200)

    @field_validator("title")
    @classmethod
    def title_must_not_be_blank(cls, value: str) -> str:
        title = value.strip()
        if not title:
            raise ValueError("Session title cannot be blank")
        return title


class ScreeningSessionResponse(BaseModel):
    id: UUID
    position_id: UUID
    title: str
    created_at: datetime
    model_config = {"from_attributes": True}


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=2000)

    @field_validator("message")
    @classmethod
    def message_must_not_be_blank(cls, value: str) -> str:
        message = value.strip()
        if not message:
            raise ValueError("Chat message cannot be blank")
        return message


class ScreeningMessage(BaseModel):
    # Agent 流式接口的消息格式。
    # type 告诉前端这条消息该如何展示，data 用来放候选人卡片等结构化数据。
    type: Literal["thinking", "tool_call", "text", "resume_card", "done", "error"]
    content: str = ""
    data: dict | None = None
