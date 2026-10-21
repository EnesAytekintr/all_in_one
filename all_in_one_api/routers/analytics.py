from fastapi import APIRouter, Query, Request
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy import func, select
from database import db_dependency
from starlette import status
from data_models import LicenseDistribution, ModelMetrics, PipelineOverview, TagPopularity
from schemas.analytics import (
	AnalyticsSummaryResponse,
	LicenseDistributionResponse,
	PipelineOverviewResponse,
	TagPopularityResponse,
)

limiter = Limiter(key_func=get_remote_address)
analytics_router = APIRouter(
	prefix="/api/v1/analytics",
	tags=["analytics"],
)



@analytics_router.get(
	"/pipelines",
	response_model=list[PipelineOverviewResponse],
	status_code=status.HTTP_200_OK,
)
@limiter.limit("30/minute")
async def get_pipeline_overview(
	request:Request,
	db: db_dependency,
	limit: int = Query(default=100, ge=1, le=10000),
	offset: int = Query(default=0, ge=0),
):
	query = (
		select(PipelineOverview)
		.order_by(PipelineOverview.rank_by_downloads)
		.offset(offset)
		.limit(limit)
	)
	result = await db.execute(query)
	return result.scalars().all()


@analytics_router.get(
	"/licenses",
	response_model=list[LicenseDistributionResponse],
	status_code=status.HTTP_200_OK
)
@limiter.limit("30/minute")
async def get_license_distribution(
	request:Request,
	db: db_dependency,
	limit: int = Query(default=100, ge=1, le=10000),
	offset: int = Query(default=0, ge=0)):
	
    query = (
		select(LicenseDistribution)
		.order_by(LicenseDistribution.rank_by_downloads)
		.offset(offset)
		.limit(limit)
	)

    result_raw = await db.execute(query)

    result = result_raw.scalars().all()

    return result


@analytics_router.get(
	"/tags",
	response_model=list[TagPopularityResponse],
	status_code=status.HTTP_200_OK,
)
@limiter.limit("30/minute")
async def get_tag_popularity(
	request:Request,
	db: db_dependency,
	limit: int = Query(default=100, ge=1, le=10000),
	offset: int = Query(default=0, ge=0),
):
	query = (
		select(TagPopularity)
		.where(TagPopularity.tag != None)
		.order_by(TagPopularity.rank_by_downloads)
		.offset(offset)
		.limit(limit)
	)
	result = await db.execute(query)
	return result.scalars().all()


@analytics_router.get(
	"/summary",
	response_model=AnalyticsSummaryResponse,
	status_code=status.HTTP_200_OK,
)
@limiter.limit("30/minute")
async def get_analytics_summary(
	request:Request,
	db: db_dependency):
	query = select(
		func.count(func.distinct(ModelMetrics.model_id)),
		func.coalesce(func.sum(ModelMetrics.downloads), 0),
		func.count(func.distinct(ModelMetrics.fk_author_id)),
	).where(ModelMetrics.is_current == True)
	
	result = await db.execute(query)
	total_models, total_downloads, active_authors = result.one()

	return AnalyticsSummaryResponse(
		total_models=total_models,
		total_downloads=total_downloads,
		active_authors=active_authors,
	)