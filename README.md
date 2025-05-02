# ✈️  Travel-Flight-Agent

> **One LLM, many MCP tools** — a fully-typed LangGraph DAG that searches flights,  
> dedupes results, captures screenshots, computes analytics, and returns a polished
> markdown answer.  
> All tools start **in-process** (`local://`) and can graduate to micro-services by
> editing a single line in their manifest.


## 📖 Table of Contents
1. [Features](#features)  
2. [Project Layout](#project-layout)  
3. [Quickstart](#quickstart)  
4. [API Usage](#api-usage)  
5. [How It Works](#how-it-works)  
6. [Environment & Secrets](#environment--secrets)


## ✨ Features
* **MCP manifests** for every tool — swap runtimes (`local://`→`http://`) without touching Python.  
* **LangGraph ≥ 0.2** DAG orchestrates `flight_search ➜ aggregator ➜ screenshot ➜ analytics ➜ response_builder`.  
* **Schema-guarded router** — LLM output is parsed into a Pydantic model and retried on failure.  
* **Celery + Redis** off-load Playwright screenshots so web API remains snappy.  
* Docker-Compose stack spins up **FastAPI + Celery + Redis** with one command.


## 📂 Project Layout

```text
.
├── app/
│   ├── main.py              # FastAPI entry-point
│   │
│   ├── agent/               #  ←  all LangGraph code
│   │   ├── __init__.py
│   │   ├── constants.py
│   │   ├── state.py
│   │   ├── router_schema.py
│   │   ├── router_prompt.py
│   │   └── graph.py
│   
│   ├── tools/               # MCP tool logic
│   │   ├── flight_search.py
│   │   ├── aggregator.py
│   │   ├── screenshot.py
│   │   ├── analytics.py
│   │   └── manifests/
│   │       ├── flight_search.yaml
│   │       ├── aggregator.yaml
│   │       ├── screenshot.yaml
│   │       └── analytics.yaml
│   
│   └── tasks/               # Celery workers
│       ├── celery_app.py
│       └── screenshot_tasks.py
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

# 2) Launch API + Celery worker + Redis
make run       # -> docker compose up --build

# 3) Hit the API
curl -XPOST http://localhost:8000/search_flights \
     -H "Content-Type: application/json" \
     -d '{"origin":"LGW","destination":"CPT","depart_date":"2025-08-10","return_date":"2025-08-20","pax":1}'
```

You’ll get back:

```json
{
  "markdown": "### Cheapest option: £542 (Qatar)…\n| Price | Airline | Dur | Link | …"
}
```

Open the markdown in VS Code Preview / a blog post and you’ll see screenshots inlined.


## 🛠  API Usage

| Method | Path              | Body fields                                  | Description                |
| ------ | ----------------- | -------------------------------------------- | -------------------------- |
| `POST` | `/search_flights` | `origin` (IATA), `destination`, `depart_date`,<br>`return_date?`, `pax` | End-to-end search flow |

Dates must be ISO `YYYY-MM-DD`. `pax` ≥ 1.


## 🤖 How It Works (30-sec version)

```text
Request /search_flights
    ---> router LLM
        ---> flight_search_tool
            ---> aggregator_tool
                ---> screenshot_tool
                    ---> analytics_tool
                        ---> response_builder
                            ---> API response (markdown)
```

* All five boxes are **MCP tools** described by YAML manifests.  
* Only **two** LLM calls per request (router, answer) → low cost & latency.  
* Playwright screenshots run in Celery workers; API thread never blocks on I/O.  
* Move a tool to its own micro-service? Change `handler:` in its manifest, done.


## 🔐 Environment & Secrets

Copy `.env.example` → `.env` and fill:

```
OPENAI_API_KEY=sk-...
SUPPLIER_AMADEUS_KEY=...
SUPPLIER_SKYSCAN_KEY=...
```

The docker-compose file mounts `.env` into both the API and Celery worker.


### Make commands reference

| Command        | What it does                                                |
| -------------- | ----------------------------------------------------------- |
| `make install` | Create venv → install Python deps → run `playwright install` |
| `make run`     | `docker compose up --build` (api, worker, redis)            |
| `make fmt`     | `ruff format` + `ruff check`                                |
| `make test`    | Run unit tests (pytest coming soon)                         |


