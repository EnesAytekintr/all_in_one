# Hugging Face AI Models Analytics & ELT Pipeline

An end-to-end, production-ready ELT (Extract, Load, Transform) data engineering pipeline and asynchronous REST API that extracts, tracks, models, and serves analytical metrics for machine learning models hosted on the Hugging Face Hub.

The architecture extracts repository metadata from the Hugging Face API using streaming generators, stages it directly into PostgreSQL via high-throughput binary protocols (`COPY`), tracks metric evolution using dbt Slowly Changing Dimensions (SCD Type 2), materializes analytical star schemas and marts, orchestrates execution graphs using Dagster Software-Defined Assets, and serves consumers via an asynchronous FastAPI microservice.

---

## Architecture Overview

```text
       ┌────────────────────────┐
       │   Hugging Face Hub     │  (Streaming extraction using generator pattern & expand fields)
       │       REST API         │
       └───────────┬────────────┘
                   │
                   │ all_in_one_data_extracting/model_extracting.py
                   ▼
       ┌────────────────────────┐
       │    model_data/         │  (Chunked row-by-row streaming, flat RAM footprint < 100MB)
       │       model.csv        │
       └───────────┬────────────┘
                   │
                   │ all_in_one_orchestration/assets.py
                   ▼ (psycopg2 COPY raw.models_raw FROM STDIN)
       ┌────────────────────────┐
       │   PostgreSQL (Raw)     │  raw.models_raw (Staged raw repository metadata)
       └───────────┬────────────┘
                   │
                   ▼
       ┌────────────────────────┐
       │      dbt Core          │
       │ ┌────────────────────┐ │
       │ │  SCD 2 Snapshots   │ │  snapshots/scd_hf_models_snapshot.sql (Timestamp strategy)
       │ ├────────────────────┤ │
       │ │  Staging Layer     │ │  models/staging/stg_models.sql (Deduplication, normalization)
       │ ├────────────────────┤ │
       │ │  Intermediate      │ │  models/intermediate/int_model_tags.sql (Bridge / unnested tags)
       │ ├────────────────────┤ │
       │ │  Dimensions & Fact │ │  dim_author_v1 (Unique entities), fct_model_metrics_v1 (Incremental)
       │ ├────────────────────┤ │
       │ │  Analytical Marts  │ │  mart_author_leaderboard, mart_pipeline_overview,
       │ │                    │ │  mart_tag_popularity, mart_license_distribution
       │ └────────────────────┘ │
       └───────────┬────────────┘
                   │
         ┌─────────┴─────────┐
         ▼                   ▼
┌──────────────────┐ ┌───────────────────┐
│   FastAPI Web    │ │  Dagster Engine   │
│   (Port 8000)    │ │   (Port 3000)     │
│  - Asyncpg / ORM │ │ - End-to-end DAG  │
│  - Dynamic dbt   │ │ - Weekly Schedule │
│    YAML version  │ │   (Sat 00:00 UTC) │
│    discovery     │ │ - Asset lineage   │
│  - Rate Limiting │ │   telemetry       │
└──────────────────┘ └───────────────────┘
```

---

## Tech Stack & Core Decisions

| Layer | Technology | Key Architectural Decisions |
| :--- | :--- | :--- |
| **Ingestion** | Python 3.12, `huggingface_hub` | Streaming generator avoiding OOM; lightweight `expand` parameter lists avoiding full model-card downloads; single-pass direct CSV streaming. |
| **Data Staging** | PostgreSQL 16 Alpine, `psycopg2` | Ingestion via `COPY ... FROM STDIN WITH (FORMAT csv, HEADER true)` inside orchestrator assets. |
| **Data Warehouse** | PostgreSQL 16 Alpine | Relational storage hosting schemas: `raw`, `snapshots`, and `dev` (staging, intermediate, dimensions, facts, marts). |
| **Transformation** | dbt-core 1.12, `dbt-postgres` | SCD Type 2 snapshotting; surrogate keys via `dbt_utils`; bridge tables for unnested tags; incremental materialization on fact tables. |
| **Orchestration** | Dagster, `dagster-dbt` | Software-Defined Assets (SDA) unifying Python ingestion and dbt compilation into a single directed acyclic graph. |
| **Serving Layer** | FastAPI, SQLAlchemy 2.0, `asyncpg` | Asynchronous database driver; dynamic table name resolution via dbt YAML parsing; in-memory rate limiting via SlowAPI. |
| **Containerization** | Docker, Docker Compose | Fully decoupled multi-container topology (`db`, `orchestrator`, `api`) communicating over a dedicated internal network (`hf_net`). |

---

## Project Directory Tree

```text
all_in_one/
├── .github/
│   └── workflows/
│       └── ci.yml                     # Continuous integration & testing pipeline
├── all_in_one_api/                    # Asynchronous FastAPI Microservice
│   ├── routers/                       # Endpoint routers (models, authors, analytics)
│   ├── schemas/                       # Pydantic serialization models (request/response)
│   ├── tests/                         # Pytest test suites (async client tests)
│   ├── data_models.py                 # Dynamic SQLAlchemy models mapping to dbt marts
│   ├── database.py                    # Async SQLAlchemy engine & session dependency
│   ├── main.py                        # FastAPI entrypoint & SlowAPI configuration
│   ├── Dockerfile                     # API image specification
│   └── requirements.txt               # API dependencies
├── all_in_one_data_extracting/        # Ingestion & Streaming Module
│   ├── model_data/                    # Directory for generated CSV dumps
│   │   └── model.csv
│   └── model_extracting.py            # Generator-based metadata extractor
├── all_in_one_dbt/                    # dbt Dimensional Modeling Project
│   ├── hf_models/                     # Core dbt workspace
│   │   ├── models/                    # Staging, intermediate, dimensions, facts, marts
│   │   ├── snapshots/                 # SCD Type 2 snapshots
│   │   └── dbt_project.yml            # Model configurations, materializations, tags
│   ├── profiles.yml                   # Container database connection profile
│   ├── profiles_example.yml           # Local template profile
│   └── README.md                      # Transformation & star schema documentation
├── all_in_one_orchestration/          # Dagster Orchestration Platform
│   ├── all_in_one_orchestration/      # Dagster module
│   │   ├── assets.py                  # Upstream raw ingestion & dbt asset definitions
│   │   ├── definitions.py             # Dagster Definitions, jobs, and weekly schedule
│   │   └── project.py                 # Dagster dbt project binding
│   ├── Dockerfile                     # Orchestrator image specification
│   └── requirements.txt               # Data engineering & orchestration dependencies
├── .env.example                       # Environment configuration template
├── .gitignore
├── DECISIONS.md                       # Comprehensive Architecture Decision Records (ADR)
├── docker-compose.yml                 # Multi-service container orchestration
└── README.md                          # Main project documentation
```

---

## Quickstart & Installation

### 1. Prerequisites
* [Docker Engine](https://docs.docker.com/engine/install/) ($\ge 24.0$) and [Docker Compose](https://docs.docker.com/compose/) ($\ge 2.20$).
* A Hugging Face User Access Token (read access).

### 2. Environment Configuration & dbt Profile Setup
Clone the repository and set up the local configuration files:

```bash
git clone https://github.com/EnesAytekintr/all_in_one.git
cd all_in_one

# 1. Instantiate the root environment variables
cp .env.example .env

# 2. Instantiate the dbt connection profile
cp all_in_one_dbt/hf_models/profiles_example.yml all_in_one_dbt/hf_models/profiles.yml
```

Ensure your root `.env` contains the required keys:

```env
# PostgreSQL Credentials
DB_USER=postgres
DB_PASSWORD=postgres
DB_NAME=hf_models_db
DB_HOST=localhost
DB_PORT=5432

# Ingestion Settings
TOKEN=hf_your_actual_token_here
LIMIT=50000
CSV_PATH=/app/all_in_one_data_extracting/model_data/model.csv

# Application Settings
IS_DEBUG=False
```

> **Note on Container Networking:** When running through Docker Compose, internal service communication automatically targets the `db` service container on internal port `5432`. The external port `5433` is mapped to your host machine for external database viewers (DBeaver, pgAdmin, etc.).

### 3. Build & Run via Docker Compose
Start all containers in detached mode:

```bash
docker compose up --build -d
```

Verify service status and health checks:

```bash
docker compose ps
```

| Service | Container Name | Port Mapping | Status Check |
| :--- | :--- | :--- | :--- |
| **Database** | `hf_postgres_db` | `5433:5432` | `pg_isready` healthcheck |
| **Orchestrator**| `hf_dagster_service` | `3000:3000` | UI accessible at `localhost:3000` |
| **API** | `hf_fastapi_service` | `8000:8000` | Docs accessible at `localhost:8000/docs` |

---

## Running the Pipeline

### 1. End-to-End Execution via Dagster UI
1. Navigate to `http://localhost:3000`.
2. Trigger the full pipeline by clicking **Materialize all** or launching `all_pipeline_job`.
3. The orchestrator triggers:
   * `model_extracting.py` extracts metadata and streams rows into `model.csv`.
   * `psycopg2` executes a `TRUNCATE` and binary `COPY` into `raw.models_raw`.
   * `dbt build` executes snapshots, incremental models, and analytical marts.
4. The scheduled job (`weekly_schedule`) set to run every Saturday at 00:00 UTC but in default it is passive.

### 2. Manual CLI Extraction (Optional)
To execute the extraction script manually inside the orchestrator container:

```bash
docker compose exec orchestrator python /app/all_in_one_data_extracting/model_extracting.py
```

---

## API Reference & Endpoints

Interactive OpenAPI documentation is available at `http://localhost:8000/docs`.

### Endpoint Overview

| Method | Endpoint | Description | Query Parameters |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/v1/health` | Health check & connection validation | None |
| `GET` | `/api/v1/models/` | Paginated current models list | `pipeline_tag`, `library_name`, `license`, `gated_status`, `limit`, `offset` |
| `GET` | `/api/v1/models/top/downloads` | Models ordered by total downloads | `limit`, `offset` |
| `GET` | `/api/v1/models/top/likes` | Models ordered by total likes | `limit`, `offset` |
| `GET` | `/api/v1/models/{model_id}` | Detailed metrics for a single model | `model_id` (path) |
| `GET` | `/api/v1/authors/leaderboard` | Author metrics and rankings | `limit`, `offset` |
| `GET` | `/api/v1/authors/{author_name}/models` | All current models from an author | `author_name` (path) |
| `GET` | `/api/v1/analytics/pipelines` | Task market share & dominant libraries | None |
| `GET` | `/api/v1/analytics/licenses` | Open-source vs. gated license distribution | None |
| `GET` | `/api/v1/analytics/tags` | Tag rankings and adoption metrics | None |

---

## Local Development & Automated Tests

To run the application or test suite locally outside of Docker:

```bash
# 1. Create and activate virtual environment
python3.12 -m venv .venv
source .venv/bin/activate

# 2. Install split dependencies
pip install -r all_in_one_api/requirements.txt -r all_in_one_orchestration/requirements.txt

# 3. Run the automated test suite
pytest all_in_one_api/tests -v
```
