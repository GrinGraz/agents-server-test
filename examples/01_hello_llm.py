"""Paso 1: llamar al modelo con LangChain (invoke y stream)."""

from agents.llm import get_llm

llm = get_llm()

print("--- invoke ---")
response = llm.invoke("Explica en una frase que es un ViewModel en Android.")
print(response.content)

print("\n--- stream ---")
for chunk in llm.stream("Dame 3 consejos cortos para escribir tests en Kotlin."):
    print(chunk.text, end="", flush=True)
print()
