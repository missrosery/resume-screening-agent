from app.infrastructure.llm import llm_client

AUGMENT_SYSTEM_PROMPT = """
你是招聘检索查询增强助手。
把用户需求扩展成 3 条适合检索简历的短查询。
严格返回 JSON 数组。
"""


class QueryAugmenter:
    async def augment(self, query: str) -> list[str]:
        # 用户自然语言可能很口语，比如“找个会后端的”。
        # 查询增强会让 LLM 生成更具体的检索短句，提高向量召回质量。
        try:
            data = await llm_client.complete_json(
                AUGMENT_SYSTEM_PROMPT,
                f"原始查询：{query}",
            )
            if isinstance(data, list):
                return [str(item) for item in data[:3]]
        except Exception:
            # 查询增强失败不影响主流程，直接用原始 query 检索即可。
            return []
        return []


query_augmenter = QueryAugmenter()
