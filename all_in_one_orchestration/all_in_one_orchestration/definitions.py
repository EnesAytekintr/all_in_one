from dagster import AssetSelection, Definitions, ScheduleDefinition, define_asset_job
from dagster_dbt import DbtCliResource
from .assets import hf_models_dbt_assets, raw_models
from .project import hf_models_project

all_pipeline_job = define_asset_job(
    name="all_pipeline_job",
    selection=AssetSelection.all(),
)

weekly_schedule = ScheduleDefinition(
    job=all_pipeline_job,
    cron_schedule="0 0 * * 6",
)

defs = Definitions(
    assets=[raw_models, hf_models_dbt_assets],
    jobs=[all_pipeline_job],
    schedules=[weekly_schedule],
    resources={
        "dbt": DbtCliResource(project_dir=hf_models_project),
    },
)