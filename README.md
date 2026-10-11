# agents-server-test

Sandbox local para aprender LangChain y LangGraph (Python). El objetivo final es exponer un
agente por HTTP y consumirlo desde una app Android.

## Requisitos

- Python 3.11 o superior
- [uv](https://docs.astral.sh/uv/)
- Una API key de Anthropic, o Ollama instalado localmente

## Puesta en marcha

```bash
uv sync                      # instala dependencias (agrega --extra ollama si usaras Ollama)
cp .env.example .env         # completa ANTHROPIC_API_KEY
uv run pytest                # tests con modelo falso, no necesitan API key
```

## Ruta de aprendizaje

| Paso | Archivo | Que aprendes |
|---|---|---|
| 1 | `examples/01_hello_llm.py` | Llamar al modelo: `invoke` y `stream` |
| 2 | `examples/02_tool_calling.py` | El modelo pide tools, tu las ejecutas |
| 3 | `examples/03_first_graph.py` | El mismo ciclo como grafo (`StateGraph`) |
| 4 | pendiente | Memoria con checkpointer y `thread_id` |
| 5 | pendiente | Human-in-the-loop (pausar y pedir confirmacion) |
| 6 | pendiente | Servidor FastAPI con endpoint normal y streaming (SSE) |
| 7 | pendiente | Cliente Android (Kotlin, OkHttp/Retrofit) |

```bash
uv run python examples/01_hello_llm.py
uv run python examples/02_tool_calling.py
uv run python examples/03_first_graph.py
```

## Diagramas

Comparación de los tres casos y arquitectura general (Mermaid): [docs/diagramas.md](docs/diagramas.md).

## Estructura

```
src/agents/llm.py     fabrica del modelo (MODEL_PROVIDER=anthropic|ollama)
src/agents/tools.py   tools de ejemplo
src/agents/graph.py   grafo ReAct (build_graph para tests, make_graph para langgraph dev)
examples/             un script por paso
tests/                tests con modelo falso
docs/diagramas.md     diagramas Mermaid
langgraph.json        configuracion para LangGraph Studio
```

## Visualizar el grafo

```bash
uv run langgraph dev
```

Abre LangGraph Studio local para ver el grafo y depurar cada paso.

## Equivalencias con Android

| Concepto | Analogia |
|---|---|
| State | `UiState` |
| Nodo | Funcion que recibe el estado y devuelve cambios (como un reducer) |
| Arista condicional | `when` sobre el estado |
| Checkpointer | `SavedStateHandle` / Room |
| Tool | Caso de uso expuesto al modelo |

## Notas para el paso Android

- El emulador accede a tu maquina en `http://10.0.2.2:8000`.
- HTTP sin TLS requiere un `network_security_config` solo en debug.
- La API key del LLM vive solo en el servidor, nunca en la app.
