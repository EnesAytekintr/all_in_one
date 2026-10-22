import pytest
from httpx import AsyncClient
from fastapi import status
from sqlalchemy.ext.asyncio import AsyncSession

from data_models import LicenseDistribution, PipelineOverview, TagPopularity


@pytest.mark.asyncio
async def test_get_license_distribution(client: AsyncClient, db_session: AsyncSession):
    entry = LicenseDistribution(
        pk_license_distribution_id="lic_1",
        license="apache-2.0",
        total_models=5000,
        total_downloads=1000000,
        total_likes=50000,
        avg_downloads_per_model=200.0,
        gated_models_count=50,
        gated_percentage=1.0,
        market_share_percentage=45.5,
        rank_by_downloads=1,
    )
    db_session.add(entry)
    await db_session.commit()

    response = await client.get("/api/v1/analytics/licenses")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) == 1
    assert data[0]["license"] == "apache-2.0"
    assert data[0]["market_share_percentage"] == 45.5

@pytest.mark.asyncio
async def test_get_pipeline_overview(client: AsyncClient, db_session: AsyncSession):
    entry = PipelineOverview(
        pk_pipeline_overview_id="pipe_1",
        pipeline_tag="text-generation",
        dominant_library="transformers",
        total_models=1200,
        total_downloads=500000,
        total_likes=25000,
        avg_downloads_per_model=416.6,
        avg_likes_per_model=20.8,
        market_share_percentage=35.5,
        rank_by_downloads=1
    )
    db_session.add(entry)
    await db_session.commit()

    response = await client.get("/api/v1/analytics/pipelines")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) == 1
    assert data[0]["pipeline_tag"] == "text-generation"
    assert data[0]["dominant_library"] == "transformers"


@pytest.mark.asyncio
async def test_get_tag_popularity(client: AsyncClient, db_session: AsyncSession):
    entry = TagPopularity(
        pk_tag_popularity_id="tag_1",
        tag="pytorch",
        total_models_using_tag=850,
        total_downloads=900000,
        total_tag_likes=45000,
        avg_downloads_per_model=1058.8,
        market_share_percentage=28.4,
        rank_by_downloads=1
    )
    db_session.add(entry)
    await db_session.commit()

    response = await client.get("/api/v1/analytics/tags")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) == 1
    assert data[0]["tag"] == "pytorch"
    assert data[0]["rank_by_downloads"] == 1