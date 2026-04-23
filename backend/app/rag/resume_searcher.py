from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.infrastructure.llm import llm_client
from app.models.database import Resume
from app.models.schemas import RankedResume
from app.rag.query_augmenter import query_augmenter
from app.rag.vector_store import resume_vector_store

RERANK_SYSTEM_PROMPT = """
你是招聘筛选助手。请根据岗位要求对候选人进行打分和解释。
严格返回 JSON 数组，每项包含：
resume_id, name, match_score, match_reasons, weaknesses, highest_degree, work_years, skills
"""


class ResumeSearcher:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def search(
        self,
        query: str,
        position_id: str | UUID,
        work_years_min: int | None = None,
        degree: str | None = None,
        top_n: int | None = None,
    ) -> list[RankedResume]:
        queries = [query] + await query_augmenter.augment(query)
        resume_ids: list[str] = []
        for item in queries:
            docs = await resume_vector_store.similarity_search(
                item,
                str(position_id),
                settings.vector_recall_k,
            )
            for doc in docs:
                resume_id = doc.metadata.get("resume_id")
                if resume_id and resume_id not in resume_ids:
                    resume_ids.append(resume_id)

        if not resume_ids:
            stmt = select(Resume).where(Resume.position_id == position_id)
            rows = (await self.db.execute(stmt)).scalars().all()
        else:
            stmt = select(Resume).where(Resume.id.in_([UUID(item) for item in resume_ids]))
            rows = (await self.db.execute(stmt)).scalars().all()

        candidates = []
        for resume in rows:
            parsed = resume.parsed_data or {}
            if work_years_min is not None and (parsed.get("work_years") or 0) < work_years_min:
                continue
            if degree and parsed.get("highest_degree") != degree:
                continue
            candidates.append(
                {
                    "resume_id": str(resume.id),
                    "name": parsed.get("name") or resume.file_name,
                    "highest_degree": parsed.get("highest_degree") or "",
                    "work_years": parsed.get("work_years"),
                    "skills": parsed.get("skills") or [],
                    "summary": parsed.get("summary") or "",
                    "job_intention": parsed.get("job_intention") or "",
                    "work_experience": parsed.get("work_experience") or [],
                }
            )

        if not candidates:
            return []

        try:
            reranked = await llm_client.complete_json(
                RERANK_SYSTEM_PROMPT,
                f"岗位需求：{query}\n候选人列表：{candidates}\n返回前 {top_n or settings.rerank_top_n} 名。",
            )
            return [RankedResume.model_validate(item) for item in reranked[: top_n or settings.rerank_top_n]]
        except Exception:
            fallback = []
            for item in candidates[: top_n or settings.rerank_top_n]:
                fallback.append(
                    RankedResume(
                        resume_id=item["resume_id"],
                        name=item["name"],
                        match_score=60,
                        match_reasons=["基于关键词和摘要的基础匹配"],
                        weaknesses=["LLM 精排失败，当前为降级结果"],
                        highest_degree=item["highest_degree"],
                        work_years=item["work_years"],
                        skills=item["skills"],
                    )
                )
            return fallback
