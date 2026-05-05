from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field


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
    title: str
    department: str | None = None
    requirements: str | None = None


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
    query: str
    work_years_min: int | None = None
    degree: str | None = None
    top_n: int = 5


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
    resume_id_a: UUID
    resume_id_b: UUID
    criteria: str | None = None


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
    title: str = "New Session"


class ScreeningSessionResponse(BaseModel):
    id: UUID
    position_id: UUID
    title: str
    created_at: datetime
    model_config = {"from_attributes": True}


class ChatRequest(BaseModel):
    message: str


class ScreeningMessage(BaseModel):
    # Agent 流式接口的消息格式。
    # type 告诉前端这条消息该如何展示，data 用来放候选人卡片等结构化数据。
    type: Literal["thinking", "tool_call", "text", "resume_card", "done", "error"]
    content: str = ""
    data: dict | None = None
