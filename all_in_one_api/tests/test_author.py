import pytest
from datetime import datetime, timezone
from httpx import AsyncClient
from fastapi import status
from sqlalchemy.ext.asyncio import AsyncSession

from data_models import AuthorLeaderboard, ModelMetrics, Author


@pytest.mark.asyncio
async def test_get_author_leaderboard_empty(client: AsyncClient):
    response = await client.get("/api/v1/authors/leaderboard")
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == []


@pytest.mark.asyncio
async def test_get_author_leaderboard_success(client: AsyncClient, db_session: AsyncSession):
    entry = AuthorLeaderboard(
        pk_author_leaderboard_id="lead_1",
        author="meta-llama",
        total_models=15,
        total_downloads=100000,
        total_likes=5000,
        avg_downloads_per_model=6666.6,
        avg_likes_per_model=333.3,
        first_model_created_at=datetime.now(timezone.utc),
        last_model_created_at=datetime.now(timezone.utc),
        rank_by_downloads=1,
        rank_by_likes=1,
    )
    db_session.add(entry)
    await db_session.commit()

    response = await client.get("/api/v1/authors/leaderboard")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) == 1
    assert data[0]["author"] == "meta-llama"
    assert data[0]["rank_by_downloads"] == 1


@pytest.mark.asyncio
async def test_get_author_models(client: AsyncClient, db_session: AsyncSession):
    now = datetime.now(timezone.utc)

    author_pk = "meta-llama-pk"
    author_obj = Author(
        pk_author_id=author_pk,
        author="meta-llama"
    )
    db_session.add(author_obj)

    m1 = ModelMetrics(
        pk_model_version_id="v1_meta",
        model_id="meta-llama/Llama-3-8B",
        fk_author_id=author_pk, 
        downloads=50000,
        likes=2000,
        gated_status="auto",
        is_private=False,
        created_at=now,
        last_modified=now,
        is_current=True,
    )
    m2_old = ModelMetrics(
        pk_model_version_id="v0_meta",
        model_id="meta-llama/Llama-2-7B",
        fk_author_id=author_pk, 
        downloads=10000,
        likes=500,
        gated_status="auto",
        is_private=False,
        created_at=now,
        last_modified=now,
        is_current=False,  
    )
    m3_google = ModelMetrics(
        pk_model_version_id="v1_google",
        model_id="google/gemma-7b",
        fk_author_id="google-pk",
        downloads=30000,
        likes=1500,
        gated_status="manual",
        is_private=False,
        created_at=now,
        last_modified=now,
        is_current=True,
    )
    db_session.add_all([m1, m2_old, m3_google])
    await db_session.commit()

    response = await client.get("/api/v1/authors/meta-llama/models")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) == 1
    assert data[0]["model_id"] == "meta-llama/Llama-3-8B"