import json
from typing import Any

from openai import AsyncOpenAI
from pydantic import BaseModel

from app.core.config import settings


class LLMClient:
    def __init__(self) -> None:
        # DashScope 提供 OpenAI 兼容接口，所以这里可以直接使用 openai SDK。
        # base_url 和 api_key 都从 .env 读取，避免把密钥写进代码。
        self.client = AsyncOpenAI(
            api_key=settings.dashscope_api_key,
            base_url=settings.dashscope_base_url,
        )

    async def complete_text(self, system_prompt: str, user_prompt: str) -> str:
        # system_prompt 负责告诉模型“你是谁、输出规则是什么”，
        # user_prompt 放本次业务数据，比如简历内容、岗位要求。
        response = await self.client.chat.completions.create(
            model=settings.llm_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.2,
        )
        return response.choices[0].message.content or ""

    async def complete_json(
        self,
        system_prompt: str,
        user_prompt: str,
        schema: type[BaseModel] | None = None,
    ) -> Any:
        prompt = user_prompt
        if schema:
            # 把 Pydantic schema 塞进提示词，是为了让模型按后端字段结构输出 JSON。
            prompt = (
                f"{user_prompt}\n\n"
                f"请严格输出 JSON，字段遵循此 Pydantic Schema: {schema.model_json_schema()}"
            )
        raw = await self.complete_text(system_prompt, prompt)
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            # 模型偶尔会在 JSON 前后加解释文字。这里尝试截取 {...} 或 [...]
            # 再解析，提升接口容错性。
            start = raw.find("{")
            end = raw.rfind("}")
            if start >= 0 and end > start:
                data = json.loads(raw[start : end + 1])
            else:
                start = raw.find("[")
                end = raw.rfind("]")
                if start >= 0 and end > start:
                    data = json.loads(raw[start : end + 1])
                else:
                    raise
        if schema:
            return schema.model_validate(data)
        return data


llm_client = LLMClient()
