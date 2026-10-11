# Diagramas

Todos los diagramas usan Mermaid y se ven directamente en GitHub.

Contenido:

1. [Los tres casos en una mirada](#1-los-tres-casos-en-una-mirada)
2. [Caso 1: Hello LLM](#2-caso-1-hello-llm)
3. [Caso 2: Tool calling manual](#3-caso-2-tool-calling-manual)
4. [Caso 3: Primer grafo](#4-caso-3-primer-grafo)
5. [Comparación: quién controla el ciclo](#5-comparación-quién-controla-el-ciclo)
6. [Arquitectura general](#6-arquitectura-general)
7. [Dependencias entre módulos del repo](#7-dependencias-entre-módulos-del-repo)

---

## 1. Los tres casos en una mirada

Cada caso agrega una capa sobre el anterior.

```mermaid
flowchart LR
    subgraph C1["Caso 1: 01_hello_llm"]
        direction TB
        A1["get_llm()"] --> B1["invoke / stream"]
    end

    subgraph C2["Caso 2: 02_tool_calling"]
        direction TB
        A2["get_llm() + bind_tools"] --> B2["invoke"]
        B2 --> D2["TU codigo ejecuta las tools<br/>en un for manual"]
        D2 --> B2
    end

    subgraph C3["Caso 3: 03_first_graph"]
        direction TB
        A3["make_graph()"] --> B3["StateGraph<br/>nodo agent + nodo tools"]
        B3 --> D3["LangGraph ejecuta el ciclo<br/>y guarda el estado"]
    end

    C1 -->|"+ tools"| C2
    C2 -->|"+ grafo y estado"| C3
```

| | Caso 1 | Caso 2 | Caso 3 |
|---|---|---|---|
| Archivo | `examples/01_hello_llm.py` | `examples/02_tool_calling.py` | `examples/03_first_graph.py` |
| Llamadas al LLM | 1 | 2 (o más si el modelo encadena tools) | Las que haga falta, el grafo repite el ciclo |
| Usa tools | No | Sí, ejecutadas a mano | Sí, ejecutadas por `ToolNode` |
| Quién decide si seguir | Nadie, es una sola llamada | Tu código (`for` sobre `tool_calls`) | La arista condicional `tools_condition` |
| Historial de mensajes | No existe | Lista que armas y mantienes tú | `MessagesState` administrado por el grafo |
| Código de control propio | Ninguno | Alto | Bajo, se declara el grafo |
| Qué se aprende | Cómo hablar con el modelo | El modelo pide tools, no las ejecuta | Nodos, estado y aristas condicionales |

**Parecido entre los tres:** usan `get_llm()`, el mismo modelo y los mismos mensajes (`HumanMessage`, `AIMessage`).
**Diferencia clave:** a quién le toca el ciclo "modelo, tool, modelo".

---

## 2. Caso 1: Hello LLM

Una sola pregunta, una sola respuesta. Sin tools ni estado.

```mermaid
sequenceDiagram
    actor Dev as Script 01
    participant F as get_llm()
    participant LLM as Modelo (Claude u Ollama)

    Dev->>F: crear modelo segun MODEL_PROVIDER
    F-->>Dev: ChatModel

    Note over Dev,LLM: invoke: respuesta completa
    Dev->>LLM: "Explica que es un ViewModel"
    LLM-->>Dev: AIMessage(content)

    Note over Dev,LLM: stream: respuesta por trozos
    Dev->>LLM: "Dame 3 consejos de tests en Kotlin"
    loop por cada chunk
        LLM-->>Dev: chunk.text
    end
```

---

## 3. Caso 2: Tool calling manual

El modelo **pide** una tool, pero **no la ejecuta**. Tu código hace de intermediario.

```mermaid
sequenceDiagram
    actor Dev as Script 02
    participant LLM as Modelo con bind_tools
    participant T as Tool sumar

    Dev->>LLM: [HumanMessage "Cuanto es 1234 + 5678?"]
    LLM-->>Dev: AIMessage con tool_calls = sumar(a=1234, b=5678)

    Note over Dev,T: Tu codigo ejecuta la tool
    Dev->>T: invoke({a: 1234, b: 5678})
    T-->>Dev: 6912.0

    Dev->>LLM: [Human, AIMessage, ToolMessage "6912.0"]
    LLM-->>Dev: AIMessage "El resultado es 6912"
```

Si el modelo necesitara otra tool después, este script no lo maneja: haría falta repetir el ciclo a mano. Eso es lo que resuelve el caso 3.

---

## 4. Caso 3: Primer grafo

El ciclo lo maneja LangGraph. Esta es la forma del grafo definido en `src/agents/graph.py`.

```mermaid
flowchart TD
    S(["START"]) --> AG["agent<br/>LLM con tools + system prompt"]
    AG --> D{"tools_condition<br/>el ultimo mensaje<br/>tiene tool_calls?"}
    D -->|"si"| TL["tools<br/>ToolNode ejecuta las tools<br/>y agrega ToolMessage"]
    D -->|"no"| E(["END"])
    TL --> AG
```

Cómo cambia el estado (`MessagesState`) en una ejecución típica:

```mermaid
sequenceDiagram
    actor Dev as Script 03
    participant G as Grafo
    participant A as Nodo agent
    participant T as Nodo tools
    participant LLM as Modelo

    Dev->>G: stream({messages: [user]}, stream_mode="updates")
    G->>A: estado = [human]
    A->>LLM: system + historial
    LLM-->>A: AIMessage(tool_calls: hora_actual, sumar)
    A-->>G: update agent
    G-->>Dev: [agent] tool_calls

    G->>T: estado = [human, ai]
    T-->>G: ToolMessage x2
    G-->>Dev: [tools] resultados

    G->>A: estado = [human, ai, tool, tool]
    A->>LLM: system + historial
    LLM-->>A: AIMessage(texto final)
    A-->>G: update agent
    G-->>Dev: [agent] respuesta final
    Note over G: tools_condition: sin tool_calls, termina en END
```

---

## 5. Comparación: quién controla el ciclo

```mermaid
flowchart LR
    subgraph U1["Caso 1"]
        direction TB
        a1["Tu codigo"] -->|"1 llamada"| m1["Modelo"]
        m1 --> r1["Respuesta"]
    end

    subgraph U2["Caso 2"]
        direction TB
        a2["Tu codigo<br/>for + ToolMessage manual"] -->|"llamada 1"| m2["Modelo"]
        m2 -->|"tool_calls"| a2
        a2 -->|"llamada 2"| m2
        m2 --> r2["Respuesta"]
    end

    subgraph U3["Caso 3"]
        direction TB
        a3["Tu codigo<br/>solo graph.stream"] --> g3["LangGraph<br/>maneja el ciclo y el estado"]
        g3 <--> m3["Modelo"]
        g3 <--> t3["Tools"]
        g3 --> r3["Respuesta"]
    end
```

Analogía Android:

| Caso | Equivalente |
|---|---|
| 1 | Una llamada Retrofit suelta |
| 2 | Un ViewModel donde tú mismo orquestas varias llamadas con `if` y `while` |
| 3 | Una máquina de estados declarativa con `UiState` y transiciones |

---

## 6. Arquitectura general

Lo que ya existe está en azul. Lo planificado (pasos 4 a 7 de la ruta) va punteado.

```mermaid
flowchart TB
    subgraph CLIENT["Cliente (paso 7, pendiente)"]
        APP["App Android<br/>Kotlin + OkHttp / Retrofit<br/>emulador: 10.0.2.2:8000"]
    end

    subgraph SERVER["Servidor local"]
        API["FastAPI (paso 6, pendiente)<br/>endpoint normal + streaming SSE"]

        subgraph AGENT["Agente LangGraph (src/agents/graph.py)"]
            direction TB
            NA["nodo agent"]
            NT["nodo tools<br/>(ToolNode)"]
            NA <-->|"tools_condition"| NT
        end

        CP[("Checkpointer<br/>thread_id (paso 4, pendiente)")]
        TOOLS["tools.py<br/>sumar, hora_actual"]
        FACT["llm.py<br/>get_llm()"]
    end

    subgraph PROV["Proveedor del modelo"]
        ANT["Anthropic API<br/>claude-opus-5-5 por defecto"]
        OLL["Ollama local<br/>llama3.1"]
    end

    subgraph DEV["Herramientas de desarrollo"]
        EX["examples/01..03"]
        STU["langgraph dev<br/>LangGraph Studio"]
        TEST["pytest + modelo falso<br/>sin API key"]
    end

    ENV[".env<br/>MODEL_PROVIDER, ANTHROPIC_API_KEY"]

    APP -.->|"HTTP / SSE"| API
    API -.-> AGENT
    AGENT -.-> CP
    NT --> TOOLS
    NA --> FACT
    FACT -->|"MODEL_PROVIDER=anthropic"| ANT
    FACT -->|"MODEL_PROVIDER=ollama"| OLL
    ENV --> FACT

    EX --> AGENT
    STU --> AGENT
    TEST --> AGENT

    classDef done fill:#dbeafe,stroke:#2563eb,color:#111;
    classDef todo fill:#f3f4f6,stroke:#9ca3af,color:#111,stroke-dasharray: 5 5;
    class NA,NT,TOOLS,FACT,ANT,OLL,EX,STU,TEST,ENV done;
    class APP,API,CP todo;
```

Puntos de seguridad y red:

- La API key del LLM vive solo en el servidor (`.env`). La app Android nunca la ve.
- El emulador llega a tu máquina por `10.0.2.2`. En un dispositivo físico se usa la IP de la red local.
- HTTP sin TLS requiere un `network_security_config` solo en el build debug.

---

## 7. Dependencias entre módulos del repo

```mermaid
flowchart LR
    ex1["examples/01_hello_llm.py"] --> llm["src/agents/llm.py"]
    ex2["examples/02_tool_calling.py"] --> llm
    ex2 --> tools["src/agents/tools.py"]
    ex3["examples/03_first_graph.py"] --> grafo["src/agents/grafo.py"]
    grafo --> llm
    grafo --> tools
    test["tests/test_graph.py"] --> grafo
    lgjson["langgraph.json"] -->|"make_graph"| grafo
```

El caso 3 usa `make_graph()` (con el modelo real) y el test usa `build_graph(llm)` con un modelo falso. Por eso `graph.py` separa las dos funciones.
