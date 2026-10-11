"""Grafo ReAct minimo hecho a mano con LangGraph.

    START -> agent --(pidio tools?)--> tools -> agent -> ... -> END

- `agent`: el LLM mira el historial y responde o pide llamar tools.
- `tools`: ejecuta las tools pedidas y agrega sus resultados al historial.
- La arista condicional decide si seguir en el ciclo o terminar.
"""

from langchain_core.language_models.chat_models import BaseChatModel
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.graph import END, START, MessagesState, StateGraph
from langgraph.prebuilt import ToolNode, tools_condition

from agents.llm import get_llm
from agents.tools import TOOLS

SYSTEM_PROMPT = "Eres un asistente conciso. Usa las tools cuando ayuden a responder."


def build_graph(llm: BaseChatModel, checkpointer: BaseCheckpointSaver | None = None):
    llm_with_tools = llm.bind_tools(TOOLS)

    def agent(state: MessagesState) -> dict:
        response = llm_with_tools.invoke(
            [{"role": "system", "content": SYSTEM_PROMPT}, *state["messages"]]
        )
        return {"messages": [response]}

    builder = StateGraph(MessagesState)
    builder.add_node("agent", agent)
    builder.add_node("tools", ToolNode(TOOLS))
    builder.add_edge(START, "agent")
    builder.add_conditional_edges("agent", tools_condition, {"tools": "tools", END: END})
    builder.add_edge("tools", "agent")
    return builder.compile(checkpointer=checkpointer)


def make_graph():
    """Punto de entrada para `langgraph dev` (ver langgraph.json)."""
    return build_graph(get_llm())
