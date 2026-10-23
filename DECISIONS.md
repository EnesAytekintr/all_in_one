# Architecture Decision Records (ADR): Hugging Face ELT & Analytics Pipeline

This document provides a comprehensive log of the engineering, architectural, operational, and data modeling decisions made during the design and implementation of the end-to-end Hugging Face Hub intelligence pipeline (~3.1+ million AI models).

---

## Table of Contents
1. [Data Ingestion & Raw Layer](#1-data-ingestion--raw-layer)
2. [Data Warehousing & Dimensional Modeling (dbt)](#2-data-warehousing--dimensional-modeling-dbt)
3. [Historical Tracking & SCD Strategy](#3-historical-tracking--scd-strategy)
4. [Backend API Architecture (FastAPI & Async Engine)](#4-backend-api-architecture-fastapi--async-engine)
5. [Orchestration & Workflow Automation (Dagster)](#5-orchestration--workflow-automation-dagster)
6. [Containerization, Networking & Infrastructure (Docker)](#6-containerization-networking--infrastructure-docker)
7. [Environment & Configuration Management](#7-environment--configuration-management)

---

## 1. Data Ingestion & Raw Layer

### ADR-01: Memory-Safe Streaming vs. In-Memory DataFrames
* **Status:** Accepted
* **Context:**
  The Hugging Face Hub hosts over 3 million models. Initial extraction attempts using Pandas (`pd.read_json`) or accumulating objects in a Python list triggered massive RAM consumption (20+ GB), leading to Linux Kernel Out-Of-Memory (OOM) kills (`Killed`).
* **Decision:**
  - Adopt a streaming/generator pattern using Python's native `HfApi.list_models()` generator.
  - Stream records directly to disk row-by-row using Python’s built-in `csv.DictWriter` instead of staging in memory.
  - Implement periodic buffer flushes (`f.flush()`) every 10,000 records to prevent buffer bloat and ensure zero data loss during network or process interruptions.
* **Consequences:**
  - Memory consumption remains flat at under 100 MB regardless of dataset size.
  - High resilience against network failures; progress is immediately persistent on disk.

### ADR-02: API Payload Optimization (`expand` vs. `cardData=True` / `full=True`)
* **Status:** Accepted
* **Context:**
  Calling `list_models(cardData=True, full=True)` forced Hugging Face's backend to parse model README markdown headers and YAML metadata across millions of repositories. This resulted in frequent timeouts, rate limits, `Invalid model-index` parsing warnings, and degraded extraction throughput.
* **Decision:**
  - Deprecate `cardData=True` and `full=True`.
  - Use explicit `expand` parameter lists requesting only required attributes: `author`, `createdAt`, `lastModified`, `downloads`, `likes`, `pipeline_tag`, `library_name`, `gated`, `private`, `tags`, `cardData`.
  - Suppress internal SDK parsing warnings via `logging.getLogger("huggingface_hub").setLevel(logging.ERROR)`.
* **Consequences:**
  - Extraction velocity increased by roughly 4x–5x.
  - Network footprint dropped drastically while gathering complete metadata needed for analytics.

### ADR-03: Single-Pass Direct CSV Streaming (Deprecating JSONL Intermediaries)
* **Status:** Accepted
* **Context:**
  Earlier pipelines generated intermediate `.jsonl` files and executed a second pass to convert them to `.csv`. This two-stage process doubled disk I/O and required substantial local disk overhead.
* **Decision:**
  - Eliminate the `.jsonl` intermediate file entirely.
  - Format incoming records on the fly and write directly to `.csv` in a single pass.
* **Consequences:**
  - Cut ingestion execution time and storage I/O requirements in half.
  - Simplified failure recovery and script maintenance.

### ADR-04: High-Performance Ingestion via PostgreSQL `COPY`
* **Status:** Accepted
* **Context:**
  Standard row-by-row SQL `INSERT` statements or ORM-driven batch inserts would take hours to load millions of records into PostgreSQL.
* **Decision:**
  - Utilize PostgreSQL's binary streaming copy command (`psycopg2.cursor.copy_expert` with `COPY ... FROM STDIN WITH (FORMAT csv, HEADER true)`).
  - Pre-truncate or stage into dedicated `raw.raw_models` tables before downstream processing.
* **Consequences:**
  - Loading hundreds of thousands of records completes within seconds.
  - Relieves database CPU and locks minimal transaction resources.

---

## 2. Data Warehousing & Dimensional Modeling (dbt)

### ADR-05: Modern Analytics Engine & SQL Standards
* **Status:** Accepted
* **Context:**
  Transformation across millions of rows requires strict maintainability, clear DAG lineages, and performant data processing.
* **Decision:**
  - Standardize on `dbt` (data build tool) for transformations.
  - Enforce SQL formatting standards: Uppercase SQL keywords (`SELECT`, `FROM`, `WHERE`, `WITH`), snake_case column identifiers, and Common Table Expressions (CTEs) for intermediate logic.
* **Consequences:**
  - Clean visual DAG lineage inside dbt and Dagster.
  - Readability and consistency maintained across staging, intermediate, and marts layers.

### ADR-06: Materialization Strategy per Layer
* **Status:** Accepted
* **Context:**
  Balancing query latency against storage footprint across 3+ million models.
* **Decision:**
  1. **Staging (`stg_models`):** Materialized as `view`. Acts as a pass-through layer for type casting, deduplication, and initial cleanup without storage overhead.
  2. **Intermediate (`int_model_tags`):** Materialized as `table`. Heavy unnesting operations (`string_to_array`, `unnest`) are pre-computed physically to prevent recurrent CPU spikes.
  3. **Fact (`fct_model_metrics`):** Materialized as `incremental`. Appends or updates changed records using dedicated tracking keys.
  4. **Dimensions (`dim_authors`):** Materialized as `table`. Author cardinality is manageable; full scans ensure metrics like `total_models_published` remain accurate.
  5. **Marts (`mart_author_leaderboard`, `mart_tag_popularity`, `mart_pipeline_overview`, `mart_license_distribution`):** Materialized as physical `table`s to serve sub-millisecond responses to BI dashboards and FastAPI endpoints.
* **Consequences:**
  - Maximum query performance for downstream consumers with balanced compute loads during dbt compilation runs.

### ADR-07: Modeling Many-to-Many Attributes (Tags & Bridge Tables)
* **Status:** Accepted
* **Context:**
  A single model contains multiple tags (e.g., `pytorch`, `llama`, `nlp`), while each tag encompasses thousands of models. Storing array columns directly in fact tables degrades relational JOIN performance and violates 1NF.
* **Decision:**
  - Keep a raw serialized string representation inside staging and fact models for fast visual querying.
  - Create an intermediate normalized bridge model (`int_model_tags`) unnesting tags into individual rows.
  - Generate deterministic surrogate keys using `dbt_utils.generate_surrogate_key(['model_id', 'tag'])`.
* **Consequences:**
  - Enables granular tag popularity analysis and filtering without Cartesian product bugs in the fact table.

### ADR-08: Degenerate Dimensions in Fact Table
* **Status:** Accepted
* **Context:**
  Attributes like `pipeline_tag`, `library_name`, `license`, `base_model`, `gated_status`, and `is_private` represent low-cardinality flags or single-valued descriptors. Creating separate dimension tables (e.g., `dim_base_model`, `dim_license`) would force unnecessary relational JOINs.
* **Decision:**
  - Retain these dimensions directly inside `fct_model_metrics` as degenerate dimensions.
  - Limit dedicated dimension tables to entities exhibiting distinct lifecycle metrics (e.g., `dim_authors`).
* **Consequences:**
  - Dramatically simplifies SQL queries for backend developers and BI dashboards.
  - Decreases execution time of analytical queries.

---

## 3. Historical Tracking & SCD Strategy

### ADR-9: Type 2 Slowly Changing Dimensions (SCD Type 2) via dbt Snapshots
* **Status:** Accepted
* **Context:**
  AI models evolve dynamically on Hugging Face (downloads surge, licenses shift from Apache to proprietary, tags are added). Overwriting records obscures historical adoption trends and delta analysis.
* **Decision:**
  - Introduce `scd_hf_models_snapshot` utilizing dbt's snapshot framework.
  - Configuration:
    - `strategy`: `timestamp`
    - `updated_at`: `last_modified`
    - `unique_key`: `model_id`
    - `target_schema`: dedicated `snapshots` schema (isolated from operational tables).
* **Consequences:**
  - Every update generates a versioned record tagged with `dbt_valid_from`, `dbt_valid_to`, and a unique `dbt_scd_id`.
  - Enables longitudinal tracking (e.g., evaluating download velocity after license changes).

### ADR-10: Fact Table Granularity and Surrogate Key Strategy
* **Status:** Accepted
* **Context:**
  Because the fact table consumes data from an SCD Type 2 snapshot source, `model_id` is no longer unique; a single model can appear across multiple version windows.
* **Decision:**
  - Set fact table grain to: **One record per model version window**.
  - Assign `pk_model_version_id` mapped directly to `dbt_scd_id` as the Primary Key.
  - Add an operational helper flag: `is_current_version` (`CASE WHEN dbt_valid_to IS NULL THEN TRUE ELSE FALSE END`).
  - Configure the fact table's incremental logic:
    ```sql
    {% if is_incremental() %}
        WHERE dbt_updated_at > (SELECT MAX(dbt_updated_at) FROM {{ this }})
        OR dbt_scd_id IN (SELECT pk_model_version_id FROM {{ this }} WHERE is_current)
    {% endif %}
    ```
* **Consequences:**
  - Prevents surrogate key collision and maintains strict referential integrity.
  - Allows consumer marts to filter active snapshots using `WHERE is_current_version = TRUE` while retaining access to full temporal change history.

---

## 4. Backend API Architecture (FastAPI & Async Engine)

### ADR-11: Asynchronous Database Driver (`asyncpg`) & URL Separation
* **Status:** Accepted
* **Context:**
  Synchronous blocking database drivers (`psycopg2`) bottleneck web applications under high concurrency. FastAPI requires non-blocking I/O to achieve high throughput.
* **Decision:**
  - Standardize API database interactions on SQLAlchemy 2.0 Async IO paired with `asyncpg`.
  - Separate connection strings cleanly into:
    - `ASYNC_DATABASE_URL`: `postgresql+asyncpg://...` (Used exclusively by FastAPI).
    - `SYNC_DATABASE_URL`: `postgresql://...` (Used by Dagster, migration scripts, and dbt).
* **Consequences:**
  - FastAPI handles concurrent requests without thread starvation.
  - Zero driver-level protocol collisions between dbt/Dagster sync workloads and API async routes.

### ADR-12: Dynamic Table Versioning via dbt Manifest Parsing
* **Status:** Accepted
* **Context:**
  dbt models frequently increment versions (`fct_model_metrics_v1`, `v2`, etc.). Hardcoding table names into SQLAlchemy ORM classes introduces brittle coupling and manual code updates.
* **Decision:**
  - Implement dynamic table name discovery in `data_models.py` by reading dbt metadata configuration files (`_fct_models.yml`):
    ```python
    fct_model_version = fct_data["models"][0].get("latest_version")
    class ModelMetrics(Base):
        __tablename__ = f"fct_model_metrics_v{fct_model_version}"
    ```
  - Use `Path(__file__).resolve().parent` to reliably resolve project directory paths across container and host environments.
* **Consequences:**
  - Incrementing versions in dbt automatically updates the API layer upon startup without manual schema rewriting.

### ADR-13: API Route Ordering and Static vs. Dynamic Paths
* **Status:** Accepted
* **Context:**
  Declaring a dynamic parameter route (`/{model_id}`) prior to static specialized routes (`/top/downloads`, `/top/likes`) causes FastAPI to match literal strings like `"top"` as `model_id`, producing serialization errors or 404 responses.
* **Decision:**
  - Register all static evaluation endpoints (`/`, `/top/downloads`, `/top/likes`) before the parameterized route (`/{model_id}`).
  - Enforce explicit `response_model=list[ModelMetricsResponse]` for collection routes and single instance schemas for detail routes.
* **Consequences:**
  - Predictable route resolution adhering to OpenAPI standards.

---

## 5. Orchestration & Workflow Automation (Dagster)

### ADR-14: Software-Defined Assets (SDA) Architecture
* **Status:** Accepted
* **Context:**
  Historically, data ingestion and dbt runs existed as detached scripts and manual cron executions, lacking dependency visibility, automated retries, and data lineage tracking.
* **Decision:**
  - Unify the entire ELT cycle within Dagster using Software-Defined Assets (`@asset` and `@dbt_assets`).
  - Encapsulate the ingestion routine (`model_extracting.py`) as an upstream asset (`raw_models`) emitting directly into `raw.raw_models`.
  - Map `raw_models` as the direct upstream source of dbt's staging asset via `dagster-dbt`.
* **Consequences:**
  - A single click ("Materialize All") or schedule automatically triggers: API Extraction $\rightarrow$ PostgreSQL COPY $\rightarrow$ dbt Snapshots $\rightarrow$ dbt Staging $\rightarrow$ Intermediate $\rightarrow$ Marts.
  - Real-time logging, materialization metadata, and execution telemetry are visible in the Dagster Web UI.

### ADR-15: Wrapper Pattern for Extraction Scripts
* **Status:** Accepted
* **Context:**
  Rewriting existing ingestion modules into Dagster-specific code would duplicate business logic and complicate standalone debugging.
* **Decision:**
  - Keep `model_extracting.py` as an independent, decoupled module.
  - Dagster asset definitions import and execute the module’s core functions directly (`models_to_csv()`), followed by database bulk loading.
* **Consequences:**
  - Preserves modularity: ingestion scripts remain runnable from CLI, tests, or Dagster without redundant codebases.

---

## 6. Containerization, Networking & Infrastructure (Docker)

### ADR-16: Service Topology & Container Decoupling
* **Status:** Accepted
* **Context:**
  Deploying the platform across different developer machines or staging servers previously required resolving varying Python versions, system libraries, and database permissions.
* **Decision:**
  - Containerize the architecture using Docker Compose into three isolated services:
    1. `db`: `postgres:16-alpine` (Data persistence layer).
    2. `orchestrator`: Python 3.12-slim running Dagster Webserver, Dagster Daemon, dbt-postgres, and extraction dependencies.
    3. `api`: Python 3.12-slim serving the FastAPI application via Uvicorn.
* **Consequences:**
  - True portability: the system runs identically across macOS, Linux, and Windows via a single command: `docker compose up --build`.

### ADR-17: Split `requirements.txt` Strategy
* **Status:** Accepted
* **Context:**
  Packaging the entire development environment (`pip freeze` containing Dagster, dbt, FastAPI, Pandas, and development tooling) into every Docker container resulted in bloated image sizes (over 2 GB per image) and lengthy build times.
* **Decision:**
  - Segregate dependencies per service responsibility:
    - `all_in_one_api/requirements.txt`: Lightweight web stack (`fastapi`, `uvicorn`, `sqlalchemy`, `asyncpg`, `pydantic`, `slowapi`, `aiosqlite`).
    - `all_in_one_orchestration/requirements.txt`: Data engineering stack (`dagster`, `dagster-dbt`, `dbt-postgres`, `huggingface_hub`, `psycopg2-binary`, `pandas`).
* **Consequences:**
  - Minimized container attack surface and disk footprints.
  - Dramatically accelerated container build caching cycles.

### ADR-18: Docker Inter-Container DNS & Port Mapping
* **Status:** Accepted
* **Context:**
  Developers frequently confuse host-to-container port mapping (e.g., exposing Postgres externally on `5433:5432`) with container-to-container network communication, causing `Connection refused` or DNS lookup failures (`could not translate host name "db"`).
* **Decision:**
  - Establish a dedicated bridge network (`hf_net`) shared across all services.
  - Standardize inter-container communication on default container ports:
    - Containers communicate using Docker's internal DNS service name: `db:5432`.
    - Host machines connect to published external ports (e.g., `localhost:5433` for DBeaver/pgAdmin, `localhost:3000` for Dagster, `localhost:8000` for API).
* **Consequences:**
  - Eliminates fragile references to `host.docker.internal` and local `pg_hba.conf` subnet subnet permissions.
  - Zero network ambiguity across container boundaries.

---

## 7. Environment & Configuration Management

### ADR-19: Unified Environment Configurations (.env Contract)
* **Status:** Accepted
* **Context:**
  Services requiring database credentials must maintain consistent configuration without hardcoding sensitive strings or environment-specific IP addresses.
* **Decision:**
  - Centralize configuration in a root `.env` file referenced across the stack.
  - Provide a tracked `.env.example` defining contract variables:
    ```env
    DB_USER=postgres
    DB_PASSWORD=postgres
    DB_NAME=hf_models_db
    DB_PORT=5432
    TOKEN=hf_your_token_here
    LIMIT=100_000
    ```
  - In Docker Compose, dynamically construct connection strings using environment interpolation:
    ```yaml
    ASYNC_DATABASE_URL: postgresql+asyncpg://${DB_USER:-postgres}:${DB_PASSWORD:-postgres}@db:5432/${DB_NAME:-hf_models_db}
    ```
* **Consequences:**
  - Eliminates secret leakage into source control.
  - Seamless environment switching between local debugging and container orchestration.

---