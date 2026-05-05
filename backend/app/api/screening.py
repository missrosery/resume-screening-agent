import json
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.resume_screener import ResumeScreeningAgent
from app.infrastructure.database import get_db
from app.models.schemas import (
    ChatRequest,
    InterviewQuestionsResponse,
    ResumeCompareRequest,
    ResumeCompareResponse,
    ScreeningRequest,
    ScreeningResponse,
    ScreeningSessionCreate,
    ScreeningSessionResponse,
)
from app.services.position_service import PositionService
from app.services.resume_service import ResumeService
from app.services.screening_service import ScreeningService

router = APIRouter()


@router.post(
    "/positions/{position_id}/sessions",
    response_model=ScreeningSessionResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_session(
    position_id: UUID,
    body: ScreeningSessionCreate,
    db: AsyncSession = Depends(get_db),
) -> ScreeningSessionResponse:
    # session 可以理解为一次“和招聘助手的聊天窗口”。
    # 它绑定岗位，后面用户说“对比刚才前两个候选人”时，需要靠 session 找上下文。
    position = await PositionService(db).get(position_id)
    if not position:
        raise HTTPException(status_code=404, detail="Position not found")
    session = await ScreeningService(db).create_session(position_id, body.title)
    return ScreeningSessionResponse.model_validate(session)


@router.post("/positions/{position_id}/screen", response_model=ScreeningResponse)
async def screen_position(
    position_id: UUID,
    body: ScreeningRequest,
    db: AsyncSession = Depends(get_db),
) -> ScreeningResponse:
    # 筛选流程：先确认岗位存在，再把 query、学历、年限、top_n 等条件交给服务层。
    # 服务层继续调用 RAG 检索和 LLM 精排，最后返回候选人卡片需要的数据。
    position = await PositionService(db).get(position_id)
    if not position:
        raise HTTPException(status_code=404, detail="Position not found")
    results = await ScreeningService(db).screen_position(position_id, body)
    return ScreeningResponse(items=results)


@router.post("/resumes/compare", response_model=ResumeCompareResponse)
async def compare_resumes(
    body: ResumeCompareRequest,
    db: AsyncSession = Depends(get_db),
) -> ResumeCompareResponse:
    return await ScreeningService(db).compare_resumes(body)


@router.post(
    "/resumes/{resume_id}/interview-questions",
    response_model=InterviewQuestionsResponse,
)
async def interview_questions(
    resume_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> InterviewQuestionsResponse:
    resume = await ResumeService(db).get(resume_id)
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")
    return await ScreeningService(db).generate_interview_questions(resume_id)


@router.post("/sessions/{session_id}/chat")
async def chat(
    session_id: UUID,
    body: ChatRequest,
    db: AsyncSession = Depends(get_db),
):
    # 对话接口是流式返回：后端不是等所有内容生成完再返回，
    # 而是一边执行 Agent，一边用 NDJSON 把 thinking/tool_call/card/text 推给前端。
    session = await ScreeningService(db).get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    position = await PositionService(db).get(session.position_id)
    if not position:
        raise HTTPException(status_code=404, detail="Position not found")

    agent = ResumeScreeningAgent(db=db, position=position, session_id=session_id)

    async def event_stream():
        async for message in agent.stream(body.message):
            # ensure_ascii=False 可以保留中文，不把中文转成 \u4e2d 这类转义字符。
            yield json.dumps(message.model_dump(), ensure_ascii=False) + "\n"

    return StreamingResponse(event_stream(), media_type="application/x-ndjson")
