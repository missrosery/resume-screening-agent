from app.infrastructure.llm import llm_client

AUGMENT_SYSTEM_PROMPT = """
你是招聘检索查询增强助手。
把用户需求扩展成 3 条适合检索简历的短查询。
严格返回 JSON 数组。
"""


class QueryAugmenter:
    async def augment(self, query: str) -> list[str]:
        try:
            data = await llm_client.complete_json(
                AUGMENT_SYSTEM_PROMPT,
                f"原始查询：{query}",
            )
            if isinstance(data, list):
                return [str(item) for item in data[:3]]
        except Exception:
            return []
        return []


query_augmenter = QueryAugmenter()
