"""Tests del grafo con un modelo falso: corren sin API key ni red."""

from collections.abc import Sequence

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage
from langchain_core.outputs import ChatGeneration, ChatResult

from agents.graph import build_graph


class ScriptedChatModel(BaseChatModel):
    """Devuelve respuestas predefinidas en orden."""

    responses: list[AIMessage]
    index: int = 0

    @property
    def _llm_type(self) -> str:
        return "scripted"

    def bind_tools(self, tools: Sequence, **kwargs):
        return self

    def _generate(self, messages: list[BaseMessage], stop=None, run_manager=None, **kwargs):
        message = self.responses[self.index]
        self.index += 1
        return ChatResult(generations=[ChatGeneration(message=message)])


def test_graph_executes_tool_and_returns_final_answer():
    llm = ScriptedChatModel(
        responses=[
            AIMessage(
                content="",
                tool_calls=[{"name": "sumar", "args": {"a": 2, "b": 3}, "id": "call_1"}],
            ),
            AIMessage(content="El resultado es 5"),
        ]
    )
    graph = build_graph(llm)

    result = graph.invoke({"messages": [{"role": "user", "content": "2 + 3?"}]})

    types = [m.type for m in result["messages"]]
    assert types == ["human", "ai", "tool", "ai"]
    assert result["messages"][2].content == "5.0"
    assert result["messages"][-1].content == "El resultado es 5"
