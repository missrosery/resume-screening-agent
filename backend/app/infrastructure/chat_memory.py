from collections import defaultdict
from typing import Any
from uuid import UUID


class ChatMemoryStore:
    def __init__(self) -> None:
        self._recent_candidates: dict[str, list[dict[str, Any]]] = defaultdict(list)
        self._last_compare_aliases: dict[str, dict[str, dict[str, Any]]] = defaultdict(dict)

    def save_candidates(self, session_id: UUID, candidates: list[dict[str, Any]]) -> None:
        self._recent_candidates[str(session_id)] = candidates[:10]

    def load_candidates(self, session_id: UUID) -> list[dict[str, Any]]:
        return self._recent_candidates.get(str(session_id), [])

    def save_compare_aliases(
        self,
        session_id: UUID,
        candidate_a: dict[str, Any],
        candidate_b: dict[str, Any],
    ) -> None:
        self._last_compare_aliases[str(session_id)] = {
            "a": candidate_a,
            "b": candidate_b,
            "候选人a": candidate_a,
            "候选人b": candidate_b,
        }

    def load_compare_alias(self, session_id: UUID, alias: str) -> dict[str, Any] | None:
        return self._last_compare_aliases.get(str(session_id), {}).get(alias.strip().lower())


chat_memory = ChatMemoryStore()
