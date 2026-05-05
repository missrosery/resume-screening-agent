import asyncio

from langchain_community.embeddings import DashScopeEmbeddings
from langchain_core.documents import Document
from langchain_postgres import PGVector

from app.core.config import settings


class ResumeVectorStore:
    def __init__(self) -> None:
        # PGVector 初始化会连接数据库和 embedding 服务，成本较高。
        # 所以这里先不创建，等第一次真正使用时再懒加载。
        self.store: PGVector | None = None

    def _get_store(self) -> PGVector:
        if self.store is None:
            # embedding 模型负责把文本转成向量，PGVector 负责把向量存进 PostgreSQL。
            self.store = PGVector(
                embeddings=DashScopeEmbeddings(
                    model=settings.embedding_model,
                    dashscope_api_key=settings.dashscope_api_key,
                ),
                collection_name=settings.vector_collection_name,
                connection=settings.sync_database_url,
                use_jsonb=True,
            )
        return self.store

    async def add_documents(self, documents: list[Document]) -> None:
        # LangChain 的 add_documents 是同步方法，放到线程里运行，
        # 避免阻塞 FastAPI 的异步请求处理。
        await asyncio.to_thread(self._get_store().add_documents, documents)

    async def similarity_search(self, query: str, position_id: str, k: int) -> list[Document]:
        # metadata 过滤保证只在当前岗位的简历文档中检索，
        # 避免 A 岗位搜索到 B 岗位上传的候选人。
        return await asyncio.to_thread(
            self._get_store().similarity_search,
            query,
            k,
            {"position_id": position_id},
        )


resume_vector_store = ResumeVectorStore()
