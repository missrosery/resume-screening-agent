from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database import get_db
from app.models.schemas import PositionCreate, PositionResponse
from app.services.position_service import PositionService

router = APIRouter()


@router.post("", response_model=PositionResponse, status_code=status.HTTP_201_CREATED)
async def create_position(
    body: PositionCreate,
    db: AsyncSession = Depends(get_db),
) -> PositionResponse:
    position = await PositionService(db).create(body)
    return PositionResponse.model_validate(position)


@router.get("", response_model=list[PositionResponse])
async def list_positions(
    db: AsyncSession = Depends(get_db),
) -> list[PositionResponse]:
    positions = await PositionService(db).list_all()
    return [PositionResponse.model_validate(item) for item in positions]


@router.get("/{position_id}", response_model=PositionResponse)
async def get_position(
    position_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> PositionResponse:
    position = await PositionService(db).get(position_id)
    if not position:
        raise HTTPException(status_code=404, detail="Position not found")
    return PositionResponse.model_validate(position)


@router.delete("/{position_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_position(
    position_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> Response:
    deleted = await PositionService(db).delete(position_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Position not found")
    return Response(status_code=status.HTTP_204_NO_CONTENT)
