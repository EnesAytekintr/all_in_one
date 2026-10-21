from fastapi import APIRouter, Query, Request
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy import select
from starlette import status
from data_models import Author, AuthorLeaderboard, ModelMetrics
from database import db_dependency
from schemas.author import AuthorLeaderboardResponse, AuthorModelResponse

limiter = Limiter(key_func=get_remote_address)
authors_router = APIRouter(
	prefix="/api/v1/authors",
	tags=["authors"],
)


@authors_router.get(
	"/leaderboard",
	response_model=list[AuthorLeaderboardResponse],
	status_code=status.HTTP_200_OK,
)
@limiter.limit("30/minute")
async def get_author_leaderboard(
	request:Request,
	db: db_dependency,
	limit: int = Query(default=100, ge=1, le=10000),
	offset: int = Query(default=0, ge=0),
):
	query = (
		select(AuthorLeaderboard)
		.order_by(AuthorLeaderboard.rank_by_downloads)
		.offset(offset)
		.limit(limit)
	)
	result = await db.execute(query)
	return result.scalars().all()


@authors_router.get(
	"/{author_name}/models",
	response_model=list[AuthorModelResponse],
	status_code=status.HTTP_200_OK,
)
@limiter.limit("30/minute")
async def get_author_models(
	request:Request,
	author_name: str,
	db: db_dependency,
	limit: int = Query(default=100, ge=1, le=1000),
	offset: int = Query(default=0, ge=0),
):
	query = (
		select(ModelMetrics)
		.join(Author, ModelMetrics.fk_author_id == Author.pk_author_id)
		.where(Author.author == author_name, ModelMetrics.is_current == True)
		.order_by(ModelMetrics.downloads.desc(), ModelMetrics.model_id)
		.offset(offset)
		.limit(limit)
	)
	result = await db.execute(query)
	return result.scalars().all()
