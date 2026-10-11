"""Paso 3: el mismo flujo del paso 2, pero como grafo de LangGraph.

Ahora el ciclo "modelo -> tools -> modelo" lo maneja el grafo, no un for manual.
`stream_mode="updates"` muestra que nodo se ejecuto y que agrego al estado.
"""

from agents.graph import make_graph

graph = make_graph()

inputs = {"messages": [{"role": "user", "content": "Que hora es y cuanto es 40 + 2?"}]}

for update in graph.stream(inputs, stream_mode="updates"):
    for node, payload in update.items():
        print(f"[{node}]")
        for msg in payload["messages"]:
            print("  ", msg.type, "->", msg.content if msg.content else msg.tool_calls)
