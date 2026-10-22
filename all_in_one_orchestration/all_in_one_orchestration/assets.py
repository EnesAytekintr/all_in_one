import os
from pathlib import Path
import sys
from dagster import AssetExecutionContext, asset
from dagster_dbt import DbtCliResource, dbt_assets
import psycopg2

BASE_DIR = Path(__file__).resolve().parent.parent.parent
if str(BASE_DIR) not in sys.path:
  sys.path.append(str(BASE_DIR))

from all_in_one_data_extracting.model_extracting import models_to_csv
from .project import hf_models_project


@asset(
    key_prefix=["hf_models"],
    name="hf_models_raw",
    group_name="ingestion",
    description="Runs model_extracting.py script and loads generated CSV to Postgres.",
)
def raw_models(context: AssetExecutionContext) -> int:
  limit = int(os.getenv("LIMIT", 1000))

  csv_path = os.getenv(
      "CSV_PATH",
      str(
          BASE_DIR
          / "all_in_one_data_extracting"
          / "model_data"
          / "model.csv"
      ),
  )

  context.log.info(
      f"model_extracting.py running... Target: {csv_path}, Limit: {limit}"
  )

  total_extracted = models_to_csv(csv_path=csv_path, limit=limit)
  context.log.info(
      f"{total_extracted} rows turned into CSV. Now loading to PostgreSQL..."
  )

  conn = psycopg2.connect(
      host=os.getenv("DB_HOST", "localhost"),
      port=os.getenv("DB_PORT", "5432"),
      dbname=os.getenv("DB_NAME", "hf_models_db"),
      user=os.getenv("DB_USER", "postgres"),
      password=os.getenv("DB_PASSWORD", "postgres"),
  )
  cur = conn.cursor()
  try:
    cur.execute("CREATE SCHEMA IF NOT EXISTS raw;")

    cur.execute("""
        CREATE TABLE IF NOT EXISTS raw.models_raw (
            id TEXT,
            author TEXT,
            created_at TEXT,
            last_modified TEXT,
            downloads BIGINT,
            likes BIGINT,
            pipeline_tag TEXT,
            library_name TEXT,
            gated TEXT,
            private BOOLEAN,
            license TEXT,
            base_model TEXT,
            language TEXT,
            datasets TEXT,
            tags TEXT
        );
    """)

    cur.execute("TRUNCATE TABLE raw.models_raw;")
    with open(csv_path, "r", encoding="utf-8") as f:
      cur.copy_expert(
          """
                COPY raw.models_raw (
                    id, author, created_at, last_modified, downloads, likes,
                    pipeline_tag, library_name, gated, private, license,
                    base_model, language, datasets, tags
                ) FROM STDIN WITH (FORMAT csv, HEADER true, DELIMITER ',');
            """,
          f,
      )
    conn.commit()
    context.log.info("raw.models_raw table successfully loaded!")
  finally:
    cur.close()
    conn.close()

  return total_extracted


@dbt_assets(manifest=hf_models_project.manifest_path)
def hf_models_dbt_assets(context: AssetExecutionContext, dbt: DbtCliResource):
    dbt.cli(["deps"]).wait()
    yield from dbt.cli(["build"], context=context).stream()