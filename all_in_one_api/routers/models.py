from fastapi import APIRouter, HTTPException, Query, Request
from slowapi import Limiter
from slowapi.util import get_remote_address
from starlette import status
from database import db_dependency
from data_models import ModelMetrics
from schemas.models import ModelMetricsResponse
from sqlalchemy import select


limiter = Limiter(key_func=get_remote_address)
models_router = APIRouter(
    prefix="/api/v1/models",
    tags=["models"]
)


@models_router.get(
        "/",
        response_model=list[ModelMetricsResponse],
        status_code=status.HTTP_200_OK)
@limiter.limit("30/minute")
async def get_models(
    request:Request,
    db: db_dependency,
    pipeline_tag: str | None = Query(default=None),
    library_name: str | None = Query(default=None),
    license: str | None = Query(default=None),
    gated_status: str | None = Query(default=None),
    limit: int = Query(default=100, ge= 1, le=10000, description="Limit of the records to display."), 
    offset: int = Query(default=0, ge=0, description="Amount of records to skip.")):

    conditions = [ModelMetrics.is_current == True]

    if pipeline_tag:
        conditions.append(ModelMetrics.pipeline_tag == pipeline_tag)
    if library_name:
        conditions.append(ModelMetrics.library_name == library_name)
    if license:
        conditions.append(ModelMetrics.license == license)
    if gated_status:
        conditions.append(ModelMetrics.gated_status == gated_status)

    query = (select(ModelMetrics)
            .where(*conditions)
            .order_by(ModelMetrics.model_id)
            .offset(offset)
            .limit(limit))
    result = await db.execute(query)
    models = result.scalars().all()

    return models

@models_router.get(
        "/top/downloads",
        response_model=list[ModelMetricsResponse], 
        status_code=status.HTTP_200_OK)
@limiter.limit("30/minute")
async def get_top_downloaded(
    request:Request,
    db: db_dependency, 
    limit: int = Query(default=100, ge=1, le=10000, description="Limit of top records"),
    offset: int = Query(default=0, ge=0, description="Amount of records to skip.")):

    query = (
        select(ModelMetrics)
        .order_by(ModelMetrics.downloads.desc())
        .where(ModelMetrics.is_current == True)
        .offset(offset)
        .limit(limit)
    )

    result_raw = await db.execute(query)
    result = result_raw.scalars().all()

    return result

@models_router.get(
        "/top/likes", 
        response_model=list[ModelMetricsResponse], 
        status_code=status.HTTP_200_OK)
@limiter.limit("30/minute")
async def get_top_likes(
    request:Request,
    db: db_dependency, 
    limit: int = Query(default=100, ge=1, le=10000, description="Limit of top records"),
    offset: int = Query(default=0, ge=0, description="Amount of records to skip.")):

    query = (
        select(ModelMetrics)
        .order_by(ModelMetrics.likes.desc())
        .where(ModelMetrics.is_current == True)
        .offset(offset)
        .limit(limit)
    )

    result_raw = await db.execute(query)
    result = result_raw.scalars().all()

    return result

@models_router.get(
        "/{model_id}", 
        response_model=ModelMetricsResponse, 
        status_code=status.HTTP_200_OK)
@limiter.limit("30/minute")
async def get_model_by_id(
    request:Request,
    db:db_dependency, 
    model_id: str):
    
    query = (select(ModelMetrics)
            .where(ModelMetrics.is_current == True,
            ModelMetrics.model_id == model_id)
            )
            
    
    result = await db.execute(query)

    model= result.scalars().first()

    if not model:
        raise HTTPException(status_code=404, detail="No model found with this id.")

    return model

