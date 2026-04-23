import json
from typing import Any

from openai import AsyncOpenAI
from pydantic import BaseModel

from app.core.config import settings


class LLMClient:
    def __init__(self) -> None:
        self.client = AsyncOpenAI(
            api_key=settings.dashscope_api_key,
            base_url=settings.dashscope_base_url,
        )

    async def complete_text(self, system_prompt: str, user_prompt: str) -> str:
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
            prompt = (
                f"{user_prompt}\n\n"
                f"请严格输出 JSON，字段遵循此 Pydantic Schema: {schema.model_json_schema()}"
            )
        raw = await self.complete_text(system_prompt, prompt)
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
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
