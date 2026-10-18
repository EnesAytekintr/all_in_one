from setuptools import find_packages, setup

setup(
    name="all_in_one_orchestration",
    version="0.0.1",
    packages=find_packages(),
    package_data={
        "all_in_one_orchestration": [
            "dbt-project/**/*",
        ],
    },
    install_requires=[
        "dagster",
        "dagster-cloud",
        "dagster-dbt",
        "dbt-core<1.12",
        "dbt-postgres<1.12",
    ],
    extras_require={
        "dev": [
            "dagster-webserver",
        ]
    },
)