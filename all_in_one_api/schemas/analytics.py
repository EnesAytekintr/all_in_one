from pydantic import BaseModel, ConfigDict


class PipelineOverviewResponse(BaseModel):
	model_config = ConfigDict(from_attributes=True)

	pk_pipeline_overview_id: str
	pipeline_tag: str
	dominant_library: str | None = None
	total_models: int
	total_downloads: float
	total_likes: float
	avg_downloads_per_model: float
	avg_likes_per_model: float
	market_share_percentage: float
	rank_by_downloads: int


class LicenseDistributionResponse(BaseModel):
	model_config = ConfigDict(from_attributes=True)

	pk_license_distribution_id: str
	license: str
	total_models: int
	total_downloads: float
	total_likes: float
	avg_downloads_per_model: float
	gated_models_count: int
	gated_percentage: float
	market_share_percentage: float
	rank_by_downloads: int


class TagPopularityResponse(BaseModel):
	model_config = ConfigDict(from_attributes=True)

	pk_tag_popularity_id: str
	tag: str
	total_models_using_tag: int
	total_downloads: float
	total_tag_likes: float
	avg_downloads_per_model: float
	market_share_percentage: float
	rank_by_downloads: int


class AnalyticsSummaryResponse(BaseModel):
	total_models: int
	total_downloads: float
	active_authors: int