"""Tools de ejemplo. El docstring es lo que el LLM lee para decidir cuando usarlas."""

from datetime import datetime

from langchain_core.tools import tool


@tool
def sumar(a: float, b: float) -> float:
    """Suma dos numeros y devuelve el resultado."""
    return a + b


@tool
def hora_actual() -> str:
    """Devuelve la fecha y hora actual del servidor en formato ISO 8601."""
    return datetime.now().isoformat(timespec="seconds")


TOOLS = [sumar, hora_actual]
