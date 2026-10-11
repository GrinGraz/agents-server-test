"""Paso 2: tool calling manual.

El modelo NO ejecuta las tools: solo responde con "quiero llamar a X con estos
argumentos". Ejecutarlas y devolverle el resultado es trabajo nuestro (o del grafo).
"""

from langchain_core.messages import HumanMessage, ToolMessage

from agents.llm import get_llm
from agents.tools import TOOLS

tools_by_name = {t.name: t for t in TOOLS}
llm = get_llm().bind_tools(TOOLS)

messages = [HumanMessage("Cuanto es 1234 + 5678? Usa la tool.")]
ai_message = llm.invoke(messages)
messages.append(ai_message)

print("El modelo pidio:", ai_message.tool_calls)

for call in ai_message.tool_calls:
    result = tools_by_name[call["name"]].invoke(call["args"])
    messages.append(ToolMessage(content=str(result), tool_call_id=call["id"]))

final = llm.invoke(messages)
print("Respuesta final:", final.text)
