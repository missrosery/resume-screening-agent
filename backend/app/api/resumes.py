from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, Response, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database import get_db
from app.models.schemas import ResumeResponse
from app.services.position_service import PositionService
from app.services.resume_service import ResumeService

router = APIRouter()


@router.post(
    "/positions/{position_id}/resumes/upload",
    response_model=list[ResumeResponse],
    status_code=status.HTTP_201_CREATED,
)
async def upload_resumes(
    position_id: UUID,
    files: list[UploadFile] = File(...),
    db: AsyncSession = Depends(get_db),
) -> list[ResumeResponse]:
    position = await PositionService(db).get(position_id)
    if not position:
        raise HTTPException(status_code=404, detail="Position not found")

    service = ResumeService(db)
    resumes = await service.upload_and_parse(position_id, files)
    responses = []
    for item, duplicate in resumes:
        payload = ResumeResponse.model_validate(item).model_dump()
        payload["duplicate"] = duplicate
        responses.append(ResumeResponse.model_validate(payload))
    return responses


@router.get("/positions/{position_id}/resumes", response_model=list[ResumeResponse])
async def list_resumes(
    position_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> list[ResumeResponse]:
    service = ResumeService(db)
    items = await service.list_by_position(position_id)
    return [ResumeResponse.model_validate(item) for item in items]


@router.get("/resumes/{resume_id}", response_model=ResumeResponse)
async def get_resume(
    resume_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> ResumeResponse:
    resume = await ResumeService(db).get(resume_id)
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")
    return ResumeResponse.model_validate(resume)


@router.delete("/resumes/{resume_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_resume(
    resume_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> Response:
    deleted = await ResumeService(db).delete(resume_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Resume not found")
    return Response(status_code=status.HTTP_204_NO_CONTENT)
