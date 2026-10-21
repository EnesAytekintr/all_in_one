from pydantic import BaseModel, ConfigDict
from datetime import datetime

class ModelMetricsResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    pk_model_version_id: str
    model_id: str
    fk_author_id: str
    downloads: int 
    likes: int 

    pipeline_tag: str | None = None
    library_name: str | None = None
    license: str | None = None
    base_model: str | None = None
    
    gated_status: str
    is_private: bool
    created_at: datetime
    last_modified: datetime
    is_current: bool
    
    dbt_updated_at: datetime | None = None
    dbt_valid_from: datetime | None = None
    dbt_valid_to: datetime | None = None
