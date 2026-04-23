import asyncio

from langchain_community.embeddings import DashScopeEmbeddings
from langchain_core.documents import Document
from langchain_postgres import PGVector

from app.core.config import settings


class ResumeVectorStore:
    def __init__(self) -> None:
        self.store: PGVector | None = None

    def _get_store(self) -> PGVector:
        if self.store is None:
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
        await asyncio.to_thread(self._get_store().add_documents, documents)

    async def similarity_search(self, query: str, position_id: str, k: int) -> list[Document]:
        return await asyncio.to_thread(
            self._get_store().similarity_search,
            query,
            k,
            {"position_id": position_id},
        )


resume_vector_store = ResumeVectorStore()
