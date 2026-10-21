from database import Base
from sqlalchemy import BigInteger, Boolean, Column, DateTime, Numeric, String
from pathlib import Path
import yaml

BASE_DIR = Path(__file__).resolve().parent.parent

fct_path = BASE_DIR / "all_in_one_dbt/hf_models/models/marts/fact/_fct_models.yml"
dim_path = BASE_DIR / "all_in_one_dbt/hf_models/models/marts/dimension/_dim_models.yml"
mart_path = BASE_DIR / "all_in_one_dbt/hf_models/models/marts/mart/_mart_models.yml"

with open(fct_path, "r", encoding="utf-8") as f, \
     open(dim_path, "r", encoding="utf-8") as d, \
     open(mart_path, "r", encoding="utf-8") as m:

    fct_data = yaml.safe_load(f)["models"]
    dim_data = yaml.safe_load(d)["models"]
    mart_data = yaml.safe_load(m)["models"]

    facts_by_name = {model["name"]: model for model in fct_data}
    dimensions_by_name = {model["name"]: model for model in dim_data}
    marts_by_name = {model["name"]: model for model in mart_data}

    fct_model_version = facts_by_name.get("fct_model_metrics", {}).get("latest_version")
    dim_model_version = dimensions_by_name.get("dim_author", {}).get("latest_version")

    tag_popularity_version = marts_by_name.get("mart_tag_popularity", {}).get("latest_version")
    license_distribution_version = marts_by_name.get("mart_license_distribution", {}).get("latest_version")
    pipeline_overview_version = marts_by_name.get("mart_pipeline_overview", {}).get("latest_version")
    author_leaderboard_version = marts_by_name.get("mart_author_leaderboard", {}).get("latest_version")

class ModelMetrics(Base):
    __tablename__ = f"fct_model_metrics_v{fct_model_version}"
    __table_args__ = {"schema": "dev"}

    pk_model_version_id = Column(String, primary_key=True)
    model_id = Column(String, nullable=False)
    fk_author_id = Column(String, nullable=False)
    downloads = Column(BigInteger, nullable=False)
    likes = Column(BigInteger, nullable=False)
    pipeline_tag = Column(String)       
    library_name = Column(String)
    license = Column(String)
    base_model = Column(String)
    gated_status = Column(String, nullable=False)
    is_private = Column(Boolean, nullable=False)
    created_at = Column(DateTime, nullable=False)
    last_modified = Column(DateTime, nullable=False)
    is_current = Column(Boolean, nullable=False)
    dbt_updated_at = Column(DateTime)
    dbt_valid_from = Column(DateTime)
    dbt_valid_to = Column(DateTime)


class Author(Base):
    __tablename__ = f"dim_author_v{dim_model_version}"
    __table_args__ = {"schema": "dev"}

    pk_author_id = Column(String, primary_key=True)
    author = Column(String, nullable=False, unique=True)


class AuthorLeaderboard(Base):
    __tablename__ = f"mart_author_leaderboard_v{author_leaderboard_version}"
    __table_args__ = {"schema": "dev"}

    pk_author_leaderboard_id = Column(String, primary_key=True)
    author = Column(String, nullable=False, unique=True)
    total_models = Column(BigInteger, nullable=False)
    total_downloads = Column(Numeric, nullable=False)
    total_likes = Column(Numeric, nullable=False)
    avg_downloads_per_model = Column(Numeric, nullable=False)
    avg_likes_per_model = Column(Numeric, nullable=False)
    first_model_created_at = Column(DateTime, nullable=False)
    last_model_created_at = Column(DateTime, nullable=False)
    rank_by_downloads = Column(BigInteger, nullable=False)
    rank_by_likes = Column(BigInteger, nullable=False)


class LicenseDistribution(Base):
    __tablename__ = f"mart_license_distribution_v{license_distribution_version}"
    __table_args__ = {"schema": "dev"}

    pk_license_distribution_id = Column(String, primary_key=True)
    license = Column(String, nullable=False)
    total_models = Column(BigInteger, nullable=False)
    total_downloads = Column(Numeric, nullable=False)
    total_likes = Column(Numeric, nullable=False)
    avg_downloads_per_model = Column(Numeric, nullable=False)
    gated_models_count = Column(BigInteger, nullable=False)
    gated_percentage = Column(Numeric, nullable=False)
    market_share_percentage = Column(Numeric, nullable=False)
    rank_by_downloads = Column(BigInteger, nullable=False, unique=True)


class PipelineOverview(Base):
    __tablename__ = f"mart_pipeline_overview_v{pipeline_overview_version}"
    __table_args__ = {"schema": "dev"}

    pk_pipeline_overview_id = Column(String, primary_key=True)
    pipeline_tag = Column(String, nullable=False, unique=True)
    dominant_library = Column(String)
    total_models = Column(BigInteger, nullable=False)
    total_downloads = Column(Numeric, nullable=False)
    total_likes = Column(Numeric, nullable=False)
    avg_downloads_per_model = Column(Numeric, nullable=False)
    avg_likes_per_model = Column(Numeric, nullable=False)
    market_share_percentage = Column(Numeric, nullable=False)
    rank_by_downloads = Column(BigInteger, nullable=False, unique=True)


class TagPopularity(Base):
    __tablename__ = f"mart_tag_popularity_v{tag_popularity_version}"
    __table_args__ = {"schema": "dev"}

    pk_tag_popularity_id = Column(String, primary_key=True)
    tag = Column(String, nullable=False, unique=True)
    total_models_using_tag = Column(BigInteger, nullable=False)
    total_downloads = Column(Numeric, nullable=False)
    total_tag_likes = Column(Numeric, nullable=False)
    avg_downloads_per_model = Column(Numeric, nullable=False)
    market_share_percentage = Column(Numeric, nullable=False)
    rank_by_downloads = Column(BigInteger, nullable=False, unique=True)
    
