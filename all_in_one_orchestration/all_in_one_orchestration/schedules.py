from dagster_dbt import build_schedule_from_dbt_selection

from .assets import hf_models_dbt_assets

schedules = [
     build_schedule_from_dbt_selection(
         [hf_models_dbt_assets],
         job_name="materialize_dbt_models",
         cron_schedule="0 0 * * 6", # Every Saturday at midnight
         dbt_select="fqn:*",
     ),
]