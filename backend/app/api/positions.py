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
    # 接口层只负责“收请求、调服务、返回响应”。
    # 真正的数据库写入放在 PositionService，避免接口函数变得很臃肿。
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
    # 路径参数 position_id 会被 FastAPI 自动转换成 UUID。
    # 如果数据库里查不到，就返回标准的 404，前端可以据此提示“岗位不存在”。
    position = await PositionService(db).get(position_id)
    if not position:
        raise HTTPException(status_code=404, detail="Position not found")
    return PositionResponse.model_validate(position)


@router.delete("/{position_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_position(
    position_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> Response:
    # 删除岗位不是只删 job_positions 一行，还要清理关联简历、筛选结果、
    # 向量库里的文档和本地上传文件，所以交给服务层统一处理。
    deleted = await PositionService(db).delete(position_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Position not found")
    return Response(status_code=status.HTTP_204_NO_CONTENT)
