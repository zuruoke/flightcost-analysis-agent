# ✈️  Travel-Flight-Agent

> **One LLM, many MCP tools** — a fully-typed LangGraph DAG that searches flights,  
> aggregates results, captures screenshots, computes analytics, and returns comprehensive
> flight search results.  
> All tools start **in-process** (`local://`) and can graduate to micro-services by
> editing a single line in their manifest.


## 📖 Table of Contents
1. [Features](#features)  
2. [Project Layout](#project-layout)  
3. [Quickstart](#quickstart)  
4. [API Usage](#api-usage)  
5. [How It Works](#how-it-works)  
6. [Architecture](#architecture)  
7. [Environment & Secrets](#environment--secrets)


## ✨ Features
* **MCP Tools** — modular components for flight search, aggregation, screenshots, and analytics
* **LangGraph DAG** — orchestrates the workflow with state management and tracing
* **Async Execution** — non-blocking operations with proper error handling
* **Streamlit UI** — user-friendly interface for flight search and results visualization
* **Comprehensive Logging** — detailed tracing of agent execution and state transitions


## 📂 Project Layout

```text
.
├── app/
│   ├── agent/               # LangGraph agent implementation
│   │   ├── client.py       # MCP client management
│   │   ├── graph.py        # DAG construction and workflow
│   │   ├── runner.py       # Agent execution interface
│   │   ├── state.py        # Graph state management
│   │   └── tracing.py      # Execution tracing utilities
│   │
│   ├── mcp_servers/        # MCP tool servers
│   │   ├── flight_search_server.py
│   │   ├── aggregator_server.py
│   │   ├── analytics_server.py
│   │   └── screenshot_server.py
│   │
│   ├── tools/              # Tool implementations
│   │   ├── flight_search.py
│   │   ├── aggregator.py
│   │   ├── analytics.py
│   │   ├── screenshot.py
│   │   └── models/         # Pydantic models
│   │
│   ├── home.py             # Streamlit UI
│   └── api/                # API endpoints
│
├── docker-compose.yml
├── app.Dockerfile
├── celery.Dockerfile
├── pyproject.toml
└── README.md
```

## 🚀 Quickstart

```bash
# 1) Clone + install everything into a virtualenv
make install   # -> poetry / uv / pip, your choice (see Makefile)

# 2) Launch the Streamlit app
streamlit run app/home.py

# 3) Or use the API directly
curl -XPOST http://localhost:8000/search_flights \
     -H "Content-Type: application/json" \
     -d '{
       "origin": "LHR",
       "destination": "JFK",
       "num_adults": 1,
       "departure_date": "2024-08-10"
     }'
```

You'll get back:

```json
{
  "quotes": [...],
  "aggregated_quotes": {...},
  "screenshots": [...],
  "analytics": {...}
}
```

## 🛠  API Usage

| Method | Path              | Body fields                                  | Description                |
| ------ | ----------------- | -------------------------------------------- | -------------------------- |
| `POST` | `/search_flights` | `origin` (IATA), `destination`, `num_adults`,<br>`departure_date` | End-to-end flight search |

Dates must be ISO `YYYY-MM-DD`. `num_adults` ≥ 1.

## 🤖 How It Works

```text
User Request
    └─> Streamlit UI / API
        └─> Agent Runner
            └─> LangGraph DAG
                ├─> Flight Search Tool
                ├─> Quote Aggregator
                ├─> Screenshot Tool
                └─> Analytics Tool
                    └─> Results
```

1. **Input Processing**
   - User provides search parameters via Streamlit UI or API
   - Parameters are validated and sanitized
   - Initial state is created for the agent

2. **Agent Execution**
   - LangGraph DAG orchestrates the workflow
   - Each tool runs as an MCP service
   - State transitions are traced and logged
   - Results are aggregated and returned

3. **Results Processing**
   - Flight quotes are displayed with prices and details
   - Aggregated statistics show price ranges and trends
   - Screenshots provide visual confirmation
   - Analytics offer insights into pricing patterns

## 🏗 Architecture

### Core Components

1. **Model Context Protocol (MCP)**
   - Standardized interface for LLM tool integration
   - Enables seamless transition between local and remote execution
   - [MCP Documentation](https://docs.anthropic.com/en/docs/agents-and-tools/mcp)

2. **LangGraph DAG**
   - Stateful workflow orchestration
   - Async execution with proper error handling
   - [LangGraph Introduction](https://langchain-ai.github.io/langgraph/tutorials/introduction/)

3. **Streamlit UI**
   - Interactive flight search interface
   - Real-time results visualization
   - Built-in state management

### Design Decisions

1. **Modular Architecture**
   - Each tool is isolated and independently deployable
   - Clear separation of concerns between components
   - Easy to extend with new capabilities

2. **Async Execution**
   - Non-blocking operations for better performance
   - Proper error handling and recovery
   - Efficient resource utilization

3. **State Management**
   - Pydantic models for type safety
   - Clear state transitions in the DAG
   - Comprehensive logging and tracing

4. **Tool Integration**
   - MCP standard for tool communication
   - Flexible deployment options (local/remote)
   - Easy to add new tools or modify existing ones

## 🔐 Environment & Secrets

Copy `.env.example` → `.env` and fill:

```
OPENAI_API_KEY=sk-...
KIWI_API_KEY=...
```

The system uses these keys for:
- OpenAI API for LLM operations
- Kiwi API for flight search


### Make commands reference

| Command        | What it does                                                |
| -------------- | ----------------------------------------------------------- |
| `make install` | Create venv → install Python deps → run `playwright install` |
| `make run`     | `docker compose up --build` (api, worker, redis)            |
| `make fmt`     | `ruff format` + `ruff check`                                |
| `make test`    | Run unit tests (pytest coming soon)                         |

## 📚 References

1. [Model Context Protocol (MCP)](https://docs.anthropic.com/en/docs/agents-and-tools/mcp) - Standard for LLM tool integration
2. [LangGraph Documentation](https://langchain-ai.github.io/langgraph/tutorials/introduction/) - Workflow orchestration framework
3. [Streamlit Documentation](https://docs.streamlit.io/) - Web app framework
4. [Pydantic Documentation](https://docs.pydantic.dev/) - Data validation and settings management


