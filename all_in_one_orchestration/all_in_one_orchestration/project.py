from pathlib import Path

from dagster_dbt import DbtProject

hf_models_project = DbtProject(
    project_dir=Path(__file__).joinpath("..", "..", "..", "all_in_one_dbt", "hf_models").resolve(),
    packaged_project_dir=Path(__file__).joinpath("..", "..", "dbt-project").resolve(),
)
hf_models_project.prepare_if_dev()