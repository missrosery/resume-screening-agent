from dataclasses import dataclass
import re
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.chat_memory import chat_memory
from app.infrastructure.llm import llm_client
from app.models.database import JobPosition, Resume
from app.models.schemas import ResumeCompareRequest, ScreeningMessage, ScreeningRequest
from app.services.screening_service import ScreeningService

ROUTER_SYSTEM_PROMPT = """
你是一个招聘助手的工具路由器。
根据用户消息判断应该调用哪个工具。
只返回 JSON，格式：
{"tool":"search_resumes|compare_resumes|generate_interview_questions","arguments":{...}}

规则：
1. 搜索候选人时使用 search_resumes，参数里放 query。
2. 对比候选人时优先输出 resume_id_a / resume_id_b。
3. 如果用户只提供名字，可以输出 candidate_name_a / candidate_name_b。
4. 如果用户说“对比前两个候选人”“对比前2个”“对比刚才推荐的前两位”，输出 {"compare_recent": true}。
5. 如果用户说“对比候选人A和候选人B”“对比A和B”，可输出 {"candidate_name_a":"候选人A","candidate_name_b":"候选人B"}。
6. 生成面试题时优先输出 resume_id。
7. 如果用户只提供名字，可以输出 candidate_name。
8. 如果用户说“给第一个候选人生成面试题”“给刚才推荐的第二位出题”，输出 {"recent_index": 0} 或 {"recent_index": 1}。
9. 如果用户说“给候选人B生成面试题”“候选人B是谁”，可输出 {"candidate_name":"候选人B"}。
"""


@dataclass
class ToolDecision:
    # Agent 路由后的结果：tool 表示要调用哪个业务工具，
    # arguments 是该工具需要的参数，例如 query、resume_id_a、recent_index。
    tool: str
    arguments: dict


class ResumeScreeningAgent:
    def __init__(self, db: AsyncSession, position: JobPosition, session_id: UUID) -> None:
        self.db = db
        self.position = position
        self.session_id = session_id
        self.service = ScreeningService(db)

    async def route(self, message: str) -> ToolDecision:
        # 这里不是让 LLM 直接回答用户，而是让 LLM 判断“该调用哪个工具”。
        # 例如：搜索候选人、对比两人、给某人生成面试题。
        data = await llm_client.complete_json(
            ROUTER_SYSTEM_PROMPT,
            (
                f"岗位名称：{self.position.title}\n"
                f"岗位要求：{self.position.requirements or ''}\n"
                f"用户消息：{message}"
            ),
        )
        return ToolDecision(tool=data.get("tool", "search_resumes"), arguments=data.get("arguments", {}))

    async def _resumes_for_position(self) -> list[Resume]:
        # Agent 只能在当前岗位下找候选人，并且只找已经解析成功的简历。
        stmt = select(Resume).where(
            Resume.position_id == self.position.id,
            Resume.parse_status == "parsed",
        )
        return list((await self.db.execute(stmt)).scalars().all())

    def _recent_candidates(self) -> list[dict]:
        # 最近一次搜索结果保存在内存里。
        # 用户后续说“第一个候选人”“刚才前两个”，就靠这里解析。
        return chat_memory.load_candidates(self.session_id)

    def _parse_index_token(self, token: str) -> int | None:
        # 把中文/数字序号转成 Python 列表下标。
        # 用户说“第一位”，实际代码里对应 index=0。
        mapping = {
            "1": 0,
            "一": 0,
            "首": 0,
            "2": 1,
            "二": 1,
            "两": 1,
            "3": 2,
            "三": 2,
            "4": 3,
            "四": 3,
            "5": 4,
            "五": 4,
        }
        return mapping.get(token.strip())

    def _recent_by_index(self, index: int) -> dict | None:
        recent = self._recent_candidates()
        if 0 <= index < len(recent):
            return recent[index]
        return None

    def _find_recent_by_reference(self, reference: str) -> tuple[dict | None, str | None]:
        # 支持几种引用方式：
        # 1. 候选人A / 候选人B；
        # 2. 第一个 / 第二个；
        # 3. 直接说候选人姓名或姓名的一部分。
        recent = self._recent_candidates()
        if not recent:
            return None, "当前会话里还没有最近推荐的候选人，请先执行一次候选人搜索。"

        normalized = reference.strip().lower()
        alias = chat_memory.load_compare_alias(self.session_id, normalized)
        if alias:
            return alias, None

        ordinal_match = re.search(r"第([12345一二两三四五首])", normalized)
        if ordinal_match:
            index = self._parse_index_token(ordinal_match.group(1))
            if index is not None:
                candidate = self._recent_by_index(index)
                if candidate:
                    return candidate, None
                return None, "最近推荐列表里没有这个序号的候选人，请先重新搜索或换个更准确的描述。"

        for candidate in recent:
            name = str(candidate.get("name") or "").strip().lower()
            if name and (normalized == name or normalized in name or name in normalized):
                return candidate, None

        return None, None

    async def _resolve_resume_by_name(self, candidate_name: str) -> tuple[Resume | None, str | None]:
        # 先在最近推荐列表里找，因为用户聊天时最常引用刚才看到的人。
        # 找不到再遍历当前岗位下的所有已解析简历。
        recent_candidate, recent_error = self._find_recent_by_reference(candidate_name)
        if recent_candidate:
            resume = await self.db.get(Resume, UUID(str(recent_candidate["resume_id"])))
            if resume:
                return resume, None
        if recent_error:
            return None, recent_error

        resumes = await self._resumes_for_position()
        normalized = candidate_name.strip().lower()
        matches: list[Resume] = []
        for resume in resumes:
            parsed = resume.parsed_data or {}
            name = str(parsed.get("name") or "").strip().lower()
            if not name:
                continue
            if normalized == name or normalized in name or name in normalized:
                matches.append(resume)

        if len(matches) == 1:
            return matches[0], None
        if len(matches) > 1:
            names = "、".join(str((item.parsed_data or {}).get("name") or item.file_name) for item in matches)
            return None, f"找到多个同名或近似候选人：{names}，请改用更完整名字或直接使用 resume_id。"
        return None, f"没有找到名为 {candidate_name} 的候选人，请先搜索候选人，或提供更准确的名字。"

    async def _resolve_compare_request(self, arguments: dict) -> tuple[ResumeCompareRequest | None, str | None]:
        # 对比请求可能来自多种说法：
        # 直接给两个 resume_id、说“对比前两个”、或给两个人名。
        # 这个函数负责把这些说法统一转换成 ResumeCompareRequest。
        resume_id_a = arguments.get("resume_id_a")
        resume_id_b = arguments.get("resume_id_b")
        if resume_id_a and resume_id_b:
            try:
                return (
                    ResumeCompareRequest(
                        resume_id_a=UUID(str(resume_id_a)),
                        resume_id_b=UUID(str(resume_id_b)),
                        criteria=arguments.get("criteria"),
                    ),
                    None,
                )
            except Exception:
                return None, "候选人 ID 格式不正确，请重新选择候选人。"

        if arguments.get("compare_recent"):
            recent = self._recent_candidates()
            if len(recent) >= 2:
                return (
                    ResumeCompareRequest(
                        resume_id_a=UUID(str(recent[0]["resume_id"])),
                        resume_id_b=UUID(str(recent[1]["resume_id"])),
                        criteria=arguments.get("criteria"),
                    ),
                    None,
                )
            return None, "最近推荐候选人不足两位，请先重新搜索候选人。"

        candidate_name_a = arguments.get("candidate_name_a")
        candidate_name_b = arguments.get("candidate_name_b")
        if not candidate_name_a or not candidate_name_b:
            return None, "请提供两位候选人的名字，或直接提供 resume_id_a 和 resume_id_b。"

        resume_a, error_a = await self._resolve_resume_by_name(str(candidate_name_a))
        if error_a:
            return None, error_a
        resume_b, error_b = await self._resolve_resume_by_name(str(candidate_name_b))
        if error_b:
            return None, error_b
        if not resume_a or not resume_b:
            return None, "候选人解析失败，请重新输入更准确的名字。"
        return (
            ResumeCompareRequest(
                resume_id_a=resume_a.id,
                resume_id_b=resume_b.id,
                criteria=arguments.get("criteria"),
            ),
            None,
        )

    async def _resolve_resume_id(self, arguments: dict) -> tuple[UUID | None, str | None]:
        # 生成面试题只需要锁定一份简历。
        # 这里同样支持 resume_id、最近列表序号、候选人姓名三种方式。
        resume_id = arguments.get("resume_id")
        if resume_id:
            try:
                return UUID(str(resume_id)), None
            except Exception:
                return None, "候选人 ID 格式不正确，请重新选择候选人。"

        recent_index = arguments.get("recent_index")
        if recent_index is not None:
            try:
                index = int(recent_index)
            except Exception:
                index = None
            if index is not None:
                recent = self._recent_by_index(index)
                if recent:
                    return UUID(str(recent["resume_id"])), None
                return None, "最近推荐列表里没有这个序号的候选人。"

        candidate_name = arguments.get("candidate_name")
        if not candidate_name:
            return None, "请提供候选人名字，或直接提供 resume_id。"

        resume, error = await self._resolve_resume_by_name(str(candidate_name))
        if error:
            return None, error
        if not resume:
            return None, "没有找到对应候选人。"
        return resume.id, None

    async def stream(self, message: str):
        # stream 是 Agent 的主入口，使用 yield 分多次返回消息。
        # 前端收到不同 type 后，可以展示思考状态、工具调用、候选人卡片和最终文本。
        yield ScreeningMessage(type="thinking", content="正在分析你的请求")
        try:
            decision = await self.route(message)
        except Exception:
            # 路由模型失败时，默认把用户消息当作搜索条件。
            decision = ToolDecision(tool="search_resumes", arguments={"query": message})

        yield ScreeningMessage(type="tool_call", content=f"调用工具：{decision.tool}")

        if decision.tool == "compare_resumes":
            # 对比工具：先把用户说法解析成两份简历 ID，再调用 ScreeningService。
            compare_request, error = await self._resolve_compare_request(decision.arguments)
            if error or not compare_request:
                yield ScreeningMessage(type="text", content=error or "无法识别要对比的两位候选人。")
                return

            result = await self.service.compare_resumes(compare_request)
            resume_a = await self.db.get(Resume, compare_request.resume_id_a)
            resume_b = await self.db.get(Resume, compare_request.resume_id_b)
            if resume_a and resume_b:
                # 保存“候选人A/B”的别名，方便用户下一轮继续追问。
                chat_memory.save_compare_aliases(
                    self.session_id,
                    {
                        "resume_id": str(resume_a.id),
                        "name": (resume_a.parsed_data or {}).get("name") or resume_a.file_name,
                    },
                    {
                        "resume_id": str(resume_b.id),
                        "name": (resume_b.parsed_data or {}).get("name") or resume_b.file_name,
                    },
                )
            yield ScreeningMessage(type="text", content=result.summary)
            yield ScreeningMessage(type="done", content="completed")
            return

        if decision.tool == "generate_interview_questions":
            # 出题工具：先定位某一份简历，再按结构化简历生成问题。
            resume_id, error = await self._resolve_resume_id(decision.arguments)
            if error or not resume_id:
                yield ScreeningMessage(type="text", content=error or "无法识别候选人。")
                return
            result = await self.service.generate_interview_questions(resume_id)
            content_lines: list[str] = []
            for group in result.groups:
                content_lines.append(f"{group.category}:")
                content_lines.extend(f"{idx + 1}. {question}" for idx, question in enumerate(group.questions))
                content_lines.append("")
            yield ScreeningMessage(type="text", content="\n".join(line for line in content_lines if line is not None).strip())
            yield ScreeningMessage(type="done", content="completed")
            return

        # 默认工具是搜索候选人。搜索结果会写入 chat_memory，
        # 这样下一轮可以支持“对比刚才前两个”。
        screen = await self.service.screen_position(
            self.position.id,
            ScreeningRequest(
                query=decision.arguments.get("query") or message,
                work_years_min=decision.arguments.get("work_years_min"),
                degree=decision.arguments.get("degree"),
                top_n=decision.arguments.get("top_n", 5),
            ),
        )
        candidates = [item.model_dump() for item in screen]
        chat_memory.save_candidates(self.session_id, candidates)
        for item in screen:
            yield ScreeningMessage(type="resume_card", data=item.model_dump())
        yield ScreeningMessage(type="text", content=f"已找到 {len(screen)} 位候选人")
        yield ScreeningMessage(type="done", content="completed")
