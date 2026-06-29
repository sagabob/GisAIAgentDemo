import json
from typing import Any

from openai import OpenAI

from api_client import GisApiClient
from config import get_openai_api_key, get_openai_model, get_settings
from places import build_places_answer, dedupe_places, extract_places, extract_total
from prompts import SYSTEM_PROMPT
from schemas import AgentResult
from tools import TOOL_DEFINITIONS, execute_tool


class GisAgent:
    def __init__(
        self,
        *,
        api_client: GisApiClient | None = None,
        openai_client: OpenAI | None = None,
        model: str | None = None,
        max_tool_rounds: int | None = None,
    ) -> None:
        settings = get_settings()
        self.api_client = api_client or GisApiClient()
        self.openai_client = openai_client or OpenAI(api_key=get_openai_api_key())
        self.model = model or get_openai_model()
        self.max_tool_rounds = max_tool_rounds or settings.max_tool_rounds
        self.messages: list[dict[str, Any]] = [{"role": "system", "content": SYSTEM_PROMPT}]

    def close(self) -> None:
        self.api_client.close()

    def ask(self, user_message: str, *, max_tool_rounds: int | None = None) -> str:
        return self.ask_with_metadata(user_message, max_tool_rounds=max_tool_rounds).answer

    def ask_with_metadata(
        self,
        user_message: str,
        *,
        max_tool_rounds: int | None = None,
    ) -> AgentResult:
        rounds = max_tool_rounds or self.max_tool_rounds
        collected_places: list[dict[str, Any]] = []
        collected_total: int | None = None
        self.messages.append({"role": "user", "content": user_message})

        for _ in range(rounds):
            response = self.openai_client.chat.completions.create(
                model=self.model,
                messages=self.messages,
                tools=TOOL_DEFINITIONS,
                tool_choice="auto",
            )
            message = response.choices[0].message

            assistant_message: dict[str, Any] = {
                "role": "assistant",
                "content": message.content or "",
            }
            if message.tool_calls:
                assistant_message["tool_calls"] = [
                    {
                        "id": tool_call.id,
                        "type": "function",
                        "function": {
                            "name": tool_call.function.name,
                            "arguments": tool_call.function.arguments,
                        },
                    }
                    for tool_call in message.tool_calls
                ]
            self.messages.append(assistant_message)

            if not message.tool_calls:
                return self._build_result(message.content, collected_places, collected_total)

            for tool_call in message.tool_calls:
                collected_total = self._execute_tool_call(tool_call, collected_places, collected_total)

        return self._build_result(
            "I need more steps to complete that request. Please try a simpler question.",
            collected_places,
            collected_total,
        )

    def _execute_tool_call(
        self,
        tool_call: Any,
        collected_places: list[dict[str, Any]],
        collected_total: int | None,
    ) -> int | None:
        tool_name = tool_call.function.name
        arguments = json.loads(tool_call.function.arguments or "{}")
        try:
            result = execute_tool(self.api_client, tool_name, arguments)
            collected_places.extend(extract_places(result))
            result_total = extract_total(result)
            if result_total is not None:
                collected_total = max(collected_total or 0, result_total)
            tool_content = json.dumps(result, ensure_ascii=False)
        except Exception as exc:
            tool_content = json.dumps({"error": str(exc)}, ensure_ascii=False)

        self.messages.append(
            {
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": tool_content,
            }
        )
        return collected_total

    def reset(self) -> None:
        self.messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    def _build_result(
        self,
        content: str | None,
        collected_places: list[dict[str, Any]],
        collected_total: int | None,
    ) -> AgentResult:
        places = dedupe_places(collected_places)
        answer = content or "I could not generate a response."
        if places:
            answer = build_places_answer(places, collected_total)
        return AgentResult(answer=answer, places=places, total=collected_total)
