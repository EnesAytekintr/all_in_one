# Hugging Face AI Models Analytics & ELT Pipeline

An end-to-end, containerized data engineering and analytics platform built to ingest, model, track, orchestrate, and serve metadata across 3.1+ million AI models hosted on the Hugging Face Hub.

---

## Architecture Overview

```text
       ┌────────────────────────┐
       │   Hugging Face Hub     │
       │     (REST API)         │
       └───────────┬────────────┘
                   │  Streaming Ingestion (Python generator + csv.DictWriter)
                   ▼
       ┌────────────────────────┐
       │   PostgreSQL (Raw)     │  <--- COPY command into raw.raw_models
       └───────────┬────────────┘
                   │
                   ▼
       ┌────────────────────────┐
       │      dbt Core          │
       │ ┌────────────────────┐ │
       │ │  SCD 2 Snapshots   │ │  <--- scd_hf_models_snapshot (Track metadata drift)
       │ ├────────────────────┤ │
       │ │  Staging Layer     │ │  <--- stg_models (Deduplication, type casting)
       │ ├────────────────────┤ │
       │ │  Intermediate      │ │  <--- int_model_tags (Unnesting tags/bridge)
       │ ├────────────────────┤ │
       │ │  Dimensions & Fact │ │  <--- dim_author, fct_model_metrics (Incremental)
       │ ├────────────────────┤ │
       │ │  Analytical Marts  │ │  <--- Leaderboards, tag/pipeline/license stats
       │ └────────────────────┘ │
       └───────────┬────────────┘
                   │
         ┌─────────┴─────────┐
         ▼                   ▼
┌──────────────────┐ ┌───────────────────┐
│   FastAPI Web    │ │  Dagster Engine   │
│   (Port 8000)    │ │   (Port 3000)     │
│  - Asyncpg / ORM │ │ - End-to-end DAG  │
│  - Dynamic dbt   │ │ - Scheduled runs  │
│    model schemas │ │ - Asset lineage   │
│  - Rate Limiting │ │   telemetry       │
└──────────────────┘ └───────────────────┘
```

---

## Tech Stack & Core Decisions

| Domain | Tool / Framework | Responsibility |
| :--- | :--- | :--- |
| **Ingestion** | Python 3.12, `huggingface_hub` | Memory-safe streaming generation, chunked disk flushing, bulk `COPY` loading. |
| **Storage / DWH** | PostgreSQL 16 | Relational store hosting raw schemas, SCD Type 2 snapshots, facts, and marts. |
| **Transformation** | dbt-core 1.12, dbt-postgres | Dimensional modeling (Kimball-style), surrogate keys, incremental facts, snapshots. |
| **Orchestration** | Dagster, `dagster-dbt` | Software-Defined Assets (SDA) coordinating Python ingestion and dbt builds. |
| **Serving Layer** | FastAPI, SQLAlchemy 2.0, `asyncpg` | High-throughput asynchronous REST API reading versioned dbt marts dynamically. |
| **Containerization** | Docker, Docker Compose | Fully reproducible, multi-service network environment with zero local setup. |

---

## Repository Structure

```text
all_in_one/
├── all_in_one_api/                # FastAPI application
│   ├── routers/                   # API routes (models, authors, analytics)
│   ├── schemas/                   # Pydantic request/response schemas
│   ├── tests/                     # Test files
│   ├── conftest.py                # Test configurations 
│   ├── database.py                # Async engine & session factories
│   ├── data_models.py             # SQLAlchemy models dynamically mapped to dbt marts
│   ├── main.py                    # App entrypoint, middleware, rate-limiters
│   ├── requirements.txt           # Lightweight web dependencies
│   └── Dockerfile
├── all_in_one_data_extracting/    # Core ingestion scripts
│   └── model_extracting.py        # Streaming API caller, CSV sink, PostgreSQL COPY
├── all_in_one_dbt/                # Transformation project
│   └── hf_models/
│       ├── models/                # Staging, intermediate, dimensions, facts, marts
│       ├── snapshots/             # SCD Type 2 tracking definitions
│       ├── tests/                 # Test jinja blocks
│       ├── dbt_project.yml        # Configurations, materialization rules, tags
│       ├── profiles_example.yml   # dbt profiles.yml example
│       └── README.md              # Deep-dive dbt documentation
├── all_in_one_orchestration/      # Dagster orchestration package
│   ├── assets.py                  # Upstream raw ingestion & downstream dbt assets
│   ├── definitions.py             # Pipeline jobs, schedules, resource bindings
│   ├── project.py                 # Dagster dbt project representations
│   ├── requirements.txt           # Data engineering & orchestration dependencies
│   └── Dockerfile
├── docker-compose.yml             # Orchestrates db, api, and orchestrator services
├── DECISIONS.md                   # Architecture Decision Records (ADR)
├── .env.example                   # Environment configuration template
└── README.md
```

---

## Quickstart & Installation

### 1. Prerequisites
* [Docker Engine](https://docs.docker.com/engine/install/) ($\ge 24.0$) and [Docker Compose](https://docs.docker.com/compose/) ($\ge 2.20$).
* Hugging Face User Access Token (read access).

### 2. Environment Configuration
Clone the repository and prepare your `.env` file from the provided template:

```bash
git clone <repository_url>
cd all_in_one
cp .env.example .env
```

Ensure the values in `.env` match your desired setup:

```env
# Database Credentials
DB_USER=postgres
DB_PASSWORD=postgres
DB_NAME=hf_models_db
DB_PORT=5432

# Ingestion Settings
TOKEN=hf_your_huggingface_hub_token
LIMIT=50000
```

### 3. Build & Run via Docker Compose
Launch all services in isolated containers:

```bash
docker compose up --build -d
```

Verify service statuses:

```bash
docker compose ps
```

---

## Operating the Pipeline

### 1. Execute Pipeline via Dagster UI
1. Navigate to `http://localhost:3000`.
2. Inspect the unified asset lineage graph (`hf_models_raw` $\rightarrow$ `stg_models` $\rightarrow$ `snapshots` $\rightarrow$ `fct_model_metrics` $\rightarrow$ `marts`).
3. Click **Materialize all** or navigate to **Jobs** and launch `all_pipeline_job`.
4. Monitor execution logs in real time.

### 2. Ad-Hoc CLI Ingestion
To manually run the extraction script inside the containerized environment without opening the UI:

```bash
docker compose exec orchestrator python /app/all_in_one_data_extracting/model_extracting.py
```

---

## API Reference & Endpoints

FastAPI exposes interactive OpenAPI documentation at `http://localhost:8000/docs`.

### Key Endpoints

* **Health Check:** `GET /health`
* **Models:**
  * `GET /api/v1/models/` — Paginated list of models (supports `limit`, `offset`, `pipeline_tag`, `library_name`).
  * `GET /api/v1/models/top/downloads` — Top models ordered by total downloads.
  * `GET /api/v1/models/top/likes` — Top models ordered by total stars/likes.
  * `GET /api/v1/models/{model_id:path}` — Specific model version metadata.
* **Analytics Marts:**
  * `GET /api/v1/analytics/author-leaderboard` — Author rankings by output and reach.
  * `GET /api/v1/analytics/pipeline-overview` — AI task distribution and dominant libraries.
  * `GET /api/v1/analytics/tag-popularity` — High-frequency tag usage and adoption.
  * `GET /api/v1/analytics/license-distribution` — Open source vs. gated license distributions.

---

## Local Development & Testing

If developing locally without Docker, create a virtual environment:

```bash
uv venv .venv
source .venv/bin/activate
uv pip install -r all_in_one_api/requirements.txt -r all_in_one_orchestration/requirements.txt
```

Run test suites:

```bash
pytest all_in_one_api/tests
```