from datetime import datetime

from pydantic import BaseModel, ConfigDict

from schemas.models import ModelMetricsResponse


class AuthorLeaderboardResponse(BaseModel):
	model_config = ConfigDict(from_attributes=True)

	pk_author_leaderboard_id: str
	author: str
	total_models: int
	total_downloads: float
	total_likes: float
	avg_downloads_per_model: float
	avg_likes_per_model: float
	first_model_created_at: datetime
	last_model_created_at: datetime
	rank_by_downloads: int
	rank_by_likes: int


class AuthorModelResponse(ModelMetricsResponse):
	pass
