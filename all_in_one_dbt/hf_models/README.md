# dbt Dimensional Modeling & Transformation Layer

This subdirectory houses the analytical transformation core of the project, turning raw Hugging Face metadata into clean, Kimball-inspired star schemas, bridge models, incremental facts, and analytical marts.

---

## Layered Architecture (DAG)

```text
               ┌────────────────────────┐
               │  source: raw_models   │  (Postgres raw.raw_models)
               └──────────┬─────────────┘
                          │
                          ▼
               ┌────────────────────────┐
               │ scd_hf_models_snapshot │  (SCD Type 2: tracks last_modified changes)
               └──────────┬─────────────┘
                          │
                          ▼
               ┌────────────────────────┐
               │       stg_models       │  (Deduplication, type-casting, null handling)
               └──────┬─────────┬───────┘
                      │         │
          ┌───────────┘         └───────────┐
          ▼                                 ▼
┌──────────────────┐               ┌──────────────────┐
│  int_model_tags  │               │    dim_author    │
│ (Unnested bridge)│               │  (Unique authors)│
└─────────┬────────┘               └────────┬─────────┘
          │                                 │
          │         ┌───────────────────────┘
          ▼         ▼
┌──────────────────────────────────────┐
│          fct_model_metrics           │  (Incremental fact: grain = version window)
└──────────────────┬───────────────────┘
                   │
                   ├───► mart_author_leaderboard
                   ├───► mart_pipeline_overview
                   ├───► mart_tag_popularity
                   └───► mart_license_distribution
```

---

## Model Descriptions & Materialization Strategy

| Layer | Model Name | Materialization | Description & Business Purpose |
| :--- | :--- | :--- | :--- |
| **Snapshot** | `scd_hf_models_snapshot` | `snapshot` | Slowly Changing Dimension Type 2 tracking `last_modified` changes on `model_id`. Preserves historical state transitions in `snapshots` schema. |
| **Staging** | `stg_models` | `view` | Deduplicates records using window functions (`ROW_NUMBER()`), casts timestamps/integers, normalizes boolean attributes. |
| **Intermediate** | `int_model_tags` | `table` | Bridge model normalizing colon-delimited model tags into single rows with a composite surrogate key (`model_id`, `tag`). |
| **Dimension** | `dim_author` | `table` | Unique list of author and organization entities with surrogate key `pk_author_id`. |
| **Fact** | `fct_model_metrics` | `incremental` | Core fact table. Primary key is `pk_model_version_id` (`dbt_scd_id`). Tracks version-level likes, downloads, and lifecycle flags (`is_current`). |
| **Marts** | `mart_author_leaderboard` | `table` | Author metrics: aggregated models, total downloads, total likes, and ranks. |
| **Marts** | `mart_pipeline_overview` | `table` | Domain breakdown by `pipeline_tag`: dominant libraries, download counts, and task market share. |
| **Marts** | `mart_tag_popularity` | `table` | Tag rankings: model adoption counts, aggregated downloads, and engagement metrics. |
| **Marts** | `mart_license_distribution`| `table` | License share metrics, gated model counts, and commercial friendliness distribution. |

---

## Slowly Changing Dimensions (SCD Type 2) Implementation

To track updates across dynamic repositories (e.g., download spikes, license alterations from MIT to proprietary), snapshots are configured in `snapshots/scd_hf_models_snapshot.sql`:

* **Strategy:** `timestamp`
* **Target Schema:** `snapshots`
* **Unique Key:** `id`
* **Updated At:** `last_modified`

Every run computes delta rows and assigns metadata columns:
* `dbt_scd_id`: Deterministic hash representing the distinct record version.
* `dbt_valid_from`: Start timestamp of the version window.
* `dbt_valid_to`: Expiration timestamp (`NULL` if actively valid).

### Fact Table Grain Alignment
The fact table (`fct_model_metrics`) defines its granularity as **One row per model version window**:

```sql
{{
    config(
        materialized='incremental',
        unique_key='pk_model_version_id',
        on_schema_change='sync_all_columns'
    )
}}

WITH models AS (
    SELECT
        dbt_scd_id AS pk_model_version_id,
        model_id,
        {{ dbt_utils.generate_surrogate_key(['author']) }} AS fk_author_id,
        downloads,
        likes,
        pipeline_tag,
        library_name,
        license,
        base_model,
        gated_status,
        is_private,
        created_at,
        last_modified,
        CASE 
            WHEN dbt_valid_to IS NULL THEN TRUE
            ELSE FALSE
        END AS is_current,
        dbt_updated_at,
        dbt_valid_from,
        dbt_valid_to
    FROM {{ ref('stg_models') }}

    {% if is_incremental() %}
        WHERE dbt_updated_at > (SELECT MAX(dbt_updated_at) FROM {{ this }})
        OR dbt_scd_id IN (SELECT pk_model_version_id FROM {{ this }} WHERE is_current)
    {% endif %}
)

SELECT * FROM models
```

---

## Dynamic Model Versioning for Downstream APIs

Marts and facts utilize dbt model versions (e.g., `_fct_models.yml`, `_mart_models.yml`). 

The downstream FastAPI backend parses these YAML definitions on startup using `latest_version` tags, constructing dynamic table bindings (e.g., `fct_model_metrics_v1`). Upgrading dbt model versions never requires breaking manual schema modifications in the API service.

---

## CLI Usage (Standalone)

When developing or debugging inside the `orchestrator` container or local virtual environment:

```bash
# Compile and test database connection
dbt debug

# Execute snapshot tracking
dbt snapshot

# Run all models
dbt run

# Run specific layers using tags
dbt run --select tag:stg
dbt run --select tag:fct
dbt run --select tag:mrts

# Execute dbt tests (uniqueness, not-null, relationships)
dbt test

# Build everything (snapshots, models, tests) sequentially
dbt build
```