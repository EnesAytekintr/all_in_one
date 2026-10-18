from dagster import AssetExecutionContext
from dagster_dbt import DbtCliResource, dbt_assets

from .project import hf_models_project


@dbt_assets(manifest=hf_models_project.manifest_path)
def hf_models_dbt_assets(context: AssetExecutionContext, dbt: DbtCliResource):
    yield from dbt.cli(["build"], context=context).stream()
    