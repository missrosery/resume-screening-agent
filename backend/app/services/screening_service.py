from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.llm import llm_client
from app.models.database import Resume, ScreeningSession
from app.models.schemas import (
    InterviewQuestionGroup,
    InterviewQuestionItem,
    InterviewQuestionLLMItem,
    InterviewQuestionsResponse,
    RankedResume,
    ResumeCompareRequest,
    ResumeCompareResponse,
    ScreeningRequest,
)
from app.rag.resume_searcher import ResumeSearcher

COMPARE_SYSTEM_PROMPT = """
你是招聘助手。请对两位候选人做简洁对比。
输出时必须直接使用候选人的真实姓名，不要使用 A、B、候选人A、候选人B 这类代号。
输出内容包含：
1. 候选人一的优势
2. 候选人二的优势
3. 最终建议及理由
"""

QUESTIONS_SYSTEM_PROMPT = """
你是面试官助手。请基于候选人简历生成 5 个定制化问题。
严格输出 JSON 数组。
数组每一项必须是对象，格式为：
{"question":"问题文本","category":"技术深挖|项目复盘|行为判断"}
分类只能从这三个值里选择。
"""


class ScreeningService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create_session(self, position_id: UUID, title: str) -> ScreeningSession:
        # 创建一条对话会话记录。当前聊天上下文存在内存里，
        # 数据库中的 session 主要用来标识“这是哪个岗位下的一次对话”。
        session = ScreeningSession(position_id=position_id, title=title)
        self.db.add(session)
        await self.db.flush()
        await self.db.refresh(session)
        return session

    async def get_session(self, session_id: UUID) -> ScreeningSession | None:
        return await self.db.get(ScreeningSession, session_id)

    async def screen_position(self, position_id: UUID, body: ScreeningRequest) -> list[RankedResume]:
        # ScreeningService 不直接写检索逻辑，而是委托给 ResumeSearcher。
        # 这样筛选入口保持简单，RAG 召回和 LLM 精排集中在 rag/resume_searcher.py。
        searcher = ResumeSearcher(self.db)
        return await searcher.search(
            query=body.query,
            position_id=position_id,
            work_years_min=body.work_years_min,
            degree=body.degree,
            top_n=body.top_n,
        )

    async def compare_resumes(self, body: ResumeCompareRequest) -> ResumeCompareResponse:
        # 对比功能的输入是两份简历 ID。服务层先查数据库，
        # 再把两份 parsed_data 拼进提示词，让 LLM 输出对比结论。
        resume_a = await self.db.get(Resume, body.resume_id_a)
        resume_b = await self.db.get(Resume, body.resume_id_b)
        if not resume_a or not resume_b:
            raise HTTPException(status_code=404, detail="Resume not found")

        name_a = (resume_a.parsed_data or {}).get("name") or resume_a.file_name
        name_b = (resume_b.parsed_data or {}).get("name") or resume_b.file_name
        content = await llm_client.complete_text(
            COMPARE_SYSTEM_PROMPT,
            f"对比标准：{body.criteria or '综合匹配度'}\n"
            f"候选人一姓名：{name_a}\n"
            f"候选人一简历：{resume_a.parsed_data}\n"
            f"候选人二姓名：{name_b}\n"
            f"候选人二简历：{resume_b.parsed_data}",
        )
        return ResumeCompareResponse(summary=content)

    async def generate_interview_questions(self, resume_id: UUID) -> InterviewQuestionsResponse:
        # 出题功能依赖结构化简历 parsed_data，而不是原始 PDF。
        # 这样提示词更短，模型更容易按技能、项目、经历生成针对性问题。
        resume = await self.db.get(Resume, resume_id)
        if not resume:
            raise HTTPException(status_code=404, detail="Resume not found")
        try:
            data = await llm_client.complete_json(
                QUESTIONS_SYSTEM_PROMPT,
                f"候选人简历：{resume.parsed_data}",
            )
            items = self._normalize_question_items(data)
        except Exception:
            # LLM 调用失败或返回格式不对时，使用兜底题目。
            # 这是简历项目里很值得讲的“降级策略”：外部 AI 不稳定，业务仍能返回结果。
            items = [
                InterviewQuestionItem(question="请介绍你最有代表性的一个项目，并说明你的具体职责。", category="项目复盘"),
                InterviewQuestionItem(question="你在过往经历中如何定位和解决复杂问题？", category="行为判断"),
                InterviewQuestionItem(question="请举例说明你如何验证交付结果的质量。", category="项目复盘"),
                InterviewQuestionItem(question="面对不熟悉的技术栈时，你通常如何快速补齐能力？", category="行为判断"),
                InterviewQuestionItem(question="你认为自己和当前岗位最匹配的能力是什么？", category="技术深挖"),
            ]
        groups = self._group_question_items(items)
        return InterviewQuestionsResponse(
            questions=[item.question for item in items],
            groups=groups,
        )

    def _normalize_question_items(self, data: object) -> list[InterviewQuestionItem]:
        # LLM 不一定完全听话：可能返回字符串数组，也可能返回对象数组。
        # 这里把多种返回形式统一整理成 InterviewQuestionItem。
        if not isinstance(data, list):
            raise ValueError("Interview questions payload must be a list")

        items: list[InterviewQuestionItem] = []
        for item in data:
            if isinstance(item, str):
                question = item.strip()
                category = "技术深挖"
            elif isinstance(item, dict):
                llm_item = InterviewQuestionLLMItem.model_validate(item)
                question = llm_item.question.strip()
                category = self._normalize_category(llm_item.category)
            else:
                question = str(item).strip()
                category = "技术深挖"

            if question:
                items.append(InterviewQuestionItem(question=question, category=category))

            if len(items) >= 5:
                break

        if not items:
            raise ValueError("No valid interview questions returned")

        return items

    def _normalize_category(self, category: str | None) -> str:
        # 把模型可能输出的同义分类统一成前端认可的三个分类。
        mapping = {
            "技术深挖": "技术深挖",
            "技术": "技术深挖",
            "technical": "技术深挖",
            "项目复盘": "项目复盘",
            "项目": "项目复盘",
            "project": "项目复盘",
            "行为判断": "行为判断",
            "行为": "行为判断",
            "behavior": "行为判断",
        }
        normalized = (category or "").strip().lower()
        for key, value in mapping.items():
            if normalized == key.lower():
                return value
        return "技术深挖"

    def _group_question_items(self, items: list[InterviewQuestionItem]) -> list[InterviewQuestionGroup]:
        # 前端既需要完整 questions 列表，也需要按分类分组后的 groups。
        # 这里固定分组顺序，让页面展示更稳定。
        ordered_categories = ["技术深挖", "项目复盘", "行为判断"]
        groups: list[InterviewQuestionGroup] = []
        for category in ordered_categories:
            questions = [item.question for item in items if item.category == category]
            if questions:
                groups.append(InterviewQuestionGroup(category=category, questions=questions))
        return groups
