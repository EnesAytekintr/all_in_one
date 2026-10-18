from dagster import Definitions
from dagster_dbt import DbtCliResource
from .assets import hf_models_dbt_assets
from .project import hf_models_project
from .schedules import schedules

defs = Definitions(
    assets=[hf_models_dbt_assets],
    schedules=schedules,
    resources={
        "dbt": DbtCliResource(project_dir=hf_models_project),
    },
)