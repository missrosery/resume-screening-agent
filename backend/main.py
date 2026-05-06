from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import positions, resumes, screening
from app.core.config import settings
from app.core.exceptions import register_exception_handlers
from app.infrastructure.database import init_db


@asynccontextmanager
async def lifespan(_: FastAPI):
    # FastAPI 启动时会先进入这里。项目把建表、创建向量扩展、创建上传目录
    # 都放在 init_db 里，这样本地第一次启动服务时不需要手动建表。
    # 临时注释掉，用于排查启动问题
    # await init_db()
    yield


app = FastAPI(title="Resume Screening Agent", lifespan=lifespan)
register_exception_handlers(app)

# 浏览器里的前端页面和后端 API 通常不是同一个端口。
# CORS 中间件负责允许前端从 localhost:3000 等地址调用后端接口。
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 这里把不同业务模块的接口挂到 FastAPI 应用上。
# positions 负责岗位，resumes 负责简历，screening 负责筛选/对比/Agent 对话。
app.include_router(positions.router, prefix="/positions", tags=["positions"])
app.include_router(resumes.router, tags=["resumes"])
app.include_router(screening.router, tags=["screening"])


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
