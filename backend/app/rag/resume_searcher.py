import re
from typing import Any
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

DEGREE_LEVELS = {
    "大专": 1,
    "专科": 1,
    "本科": 2,
    "学士": 2,
    "硕士": 3,
    "研究生": 3,
    "博士": 4,
}

AGENT_QUERY_MARKERS = (
    "agent",
    "智能体",
    "langgraph",
    "autogen",
    "crewai",
    "tool calling",
    "function calling",
)
AGENT_RESUME_MARKERS = (
    "agent",
    "智能体",
    "langgraph",
    "autogen",
    "crewai",
    "tool calling",
    "function calling",
)


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
        # 这里是 RAG 筛选主流程：
        # 1. 用 LLM 把用户查询扩展成几条更适合检索的短查询；
        # 2. 去 pgvector 里按语义相似度召回简历文档；
        # 3. 用 resume_id 去重，拿到候选人完整结构化信息；
        # 4. 再让 LLM 按岗位要求精排并给出解释。
        # 前端当前只传 query，所以“学历为硕士”这类自然语言也要在后端解析成硬条件。
        required_degree = self._infer_degree_requirement(query, degree)
        require_agent_experience = self._requires_agent_experience(query)
        use_or_logic = self._uses_or_logic(query) and bool(required_degree and require_agent_experience)

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

        if not resume_ids or use_or_logic:
            # 如果向量召回没有命中，就退化为读取该岗位下所有简历。
            # 这样至少还能让 LLM 基于结构化信息做一次排序，而不是直接返回空。
            # OR 查询也必须读取全量候选人，否则“只满足学历、不满足 Agent 关键词”的人
            # 可能不会被向量召回，后续就没有机会被结构化条件命中。
            stmt = select(Resume).where(Resume.position_id == position_id)
            rows = (await self.db.execute(stmt)).scalars().all()
        else:
            stmt = select(Resume).where(Resume.id.in_([UUID(item) for item in resume_ids]))
            rows = (await self.db.execute(stmt)).scalars().all()

        candidates = []
        for resume in rows:
            parsed = resume.parsed_data or {}
            if not self._passes_hard_filters(
                parsed,
                required_degree=required_degree,
                require_agent_experience=require_agent_experience,
                work_years_min=work_years_min,
                use_or_logic=use_or_logic,
            ):
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
            # 精排阶段让 LLM 输出 match_score、匹配理由、短板等可解释信息。
            # 这正是项目区别于普通关键词搜索的地方。
            reranked = await llm_client.complete_json(
                RERANK_SYSTEM_PROMPT,
                f"岗位需求：{query}\n候选人列表：{candidates}\n返回前 {top_n or settings.rerank_top_n} 名。",
            )
            ranked = [RankedResume.model_validate(item) for item in reranked]
            # LLM 已经判断为 0 分的候选人，不应该再展示在“筛选结果”里。
            return [item for item in ranked if item.match_score > 0][: top_n or settings.rerank_top_n]
        except Exception:
            # AI 精排失败时返回基础结果，保证接口可用。
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

    def _infer_degree_requirement(self, query: str, degree: str | None) -> str | None:
        if degree:
            return self._canonical_degree(degree)

        if re.search(r"学历\s*(不限|无要求)", query):
            return None

        normalized = query.lower()
        for keyword in ("博士", "硕士", "研究生", "本科", "学士", "大专", "专科"):
            if keyword.lower() in normalized:
                return self._canonical_degree(keyword)
        return None

    def _canonical_degree(self, degree: str | None) -> str | None:
        level = self._degree_level(degree)
        if level >= 4:
            return "博士"
        if level == 3:
            return "硕士"
        if level == 2:
            return "本科"
        if level == 1:
            return "大专"
        return None

    def _degree_level(self, degree: str | None) -> int:
        normalized = (degree or "").strip().lower()
        if not normalized:
            return 0

        # 顺序从高到低，避免“博士研究生”被“研究生”误判成硕士。
        for keyword in ("博士", "硕士", "研究生", "本科", "学士", "大专", "专科"):
            if keyword.lower() in normalized:
                return DEGREE_LEVELS[keyword]
        return 0

    def _degree_satisfies(self, candidate_degree: str | None, required_degree: str) -> bool:
        # 招聘里的“硕士要求”通常表示硕士及以上，所以这里按学历层级比较，
        # 而不是做 parsed_data["highest_degree"] == "硕士" 的字符串相等。
        return self._degree_level(candidate_degree) >= self._degree_level(required_degree)

    def _requires_agent_experience(self, query: str) -> bool:
        normalized = query.lower()
        return any(marker in normalized for marker in AGENT_QUERY_MARKERS)

    def _uses_or_logic(self, query: str) -> bool:
        normalized = query.lower()
        if re.search(r"\bor\b", normalized):
            return True
        if any(marker in normalized for marker in ("或者", "或是", "任一", "任选", "二选一", "满足其一")):
            return True
        return bool(re.search(r"[\w\u4e00-\u9fff]或[\w\u4e00-\u9fff]", normalized))

    def _passes_hard_filters(
        self,
        parsed: dict[str, Any],
        required_degree: str | None,
        require_agent_experience: bool,
        work_years_min: int | None,
        use_or_logic: bool,
    ) -> bool:
        # 年限仍然作为全局硬条件处理。比如“硕士或者 Agent，且 3 年以上”，
        # 应该先满足年限，再判断学历/Agent 这组 OR 条件。
        if work_years_min is not None and (parsed.get("work_years") or 0) < work_years_min:
            return False

        degree_ok = (
            self._degree_satisfies(parsed.get("highest_degree"), required_degree)
            if required_degree
            else False
        )
        agent_ok = self._has_agent_experience(parsed) if require_agent_experience else False

        if use_or_logic:
            return degree_ok or agent_ok

        if required_degree and not degree_ok:
            return False
        if require_agent_experience and not agent_ok:
            return False
        return True

    def _has_agent_experience(self, parsed: dict[str, Any]) -> bool:
        searchable = " ".join(
            [
                str(parsed.get("summary") or ""),
                str(parsed.get("job_intention") or ""),
                " ".join(str(item) for item in parsed.get("skills") or []),
                str(parsed.get("work_experience") or ""),
            ]
        ).lower()
        return any(marker in searchable for marker in AGENT_RESUME_MARKERS)
