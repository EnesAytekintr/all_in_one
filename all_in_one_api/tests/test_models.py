import pytest
from datetime import datetime, timezone
from httpx import AsyncClient
from fastapi import status
from sqlalchemy.ext.asyncio import AsyncSession

from data_models import ModelMetrics


@pytest.mark.asyncio
async def test_get_models_pagination_and_filters(client: AsyncClient, db_session: AsyncSession):
    now = datetime.now(timezone.utc)
    m1 = ModelMetrics(
        pk_model_version_id="v1",
        model_id="meta-llama/Llama-3-8B",
        fk_author_id="meta",
        downloads=1000,
        likes=100,
        pipeline_tag="text-generation",
        library_name="transformers",
        license="llama3",
        gated_status="auto",
        is_private=False,
        created_at=now,
        last_modified=now,
        is_current=True,
    )
    m2 = ModelMetrics(
        pk_model_version_id="v2",
        model_id="bert-base-uncased",
        fk_author_id="google",
        downloads=5000,
        likes=300,
        pipeline_tag="fill-mask",
        library_name="transformers",
        license="apache-2.0",
        gated_status="false",
        is_private=False,
        created_at=now,
        last_modified=now,
        is_current=True,
    )
    db_session.add_all([m1, m2])
    await db_session.commit()

    res_filter = await client.get("/api/v1/models/?pipeline_tag=fill-mask")
    assert res_filter.status_code == status.HTTP_200_OK
    data_filter = res_filter.json()
    assert len(data_filter) == 1
    assert data_filter[0]["model_id"] == "bert-base-uncased"

    res_page = await client.get("/api/v1/models/?limit=1&offset=0")
    assert res_page.status_code == status.HTTP_200_OK
    assert len(res_page.json()) == 1


@pytest.mark.asyncio
async def test_top_downloads_descending_order(client: AsyncClient, db_session: AsyncSession):
    now = datetime.now(timezone.utc)
    m_low = ModelMetrics(
        pk_model_version_id="1", model_id="low-model", fk_author_id="a",
        downloads=10, likes=1, gated_status="false", is_private=False,
        created_at=now, last_modified=now, is_current=True
    )
    m_high = ModelMetrics(
        pk_model_version_id="2", model_id="high-model", fk_author_id="b",
        downloads=99999, likes=500, gated_status="false", is_private=False,
        created_at=now, last_modified=now, is_current=True
    )
    db_session.add_all([m_low, m_high])
    await db_session.commit()

    response = await client.get("/api/v1/models/top/downloads?limit=10")
    assert response.status_code == status.HTTP_200_OK
    items = response.json()
    assert items[0]["model_id"] == "high-model"
    assert items[0]["downloads"] == 99999


@pytest.mark.asyncio
async def test_get_model_by_id_success_and_404(client: AsyncClient, db_session: AsyncSession):
    now = datetime.now(timezone.utc)
    m = ModelMetrics(
        pk_model_version_id="v_target", model_id="target-model", fk_author_id="auth",
        downloads=500, likes=50, gated_status="false", is_private=False,
        created_at=now, last_modified=now, is_current=True
    )
    db_session.add(m)
    await db_session.commit()

    res_ok = await client.get("/api/v1/models/target-model")
    assert res_ok.status_code == status.HTTP_200_OK
    assert res_ok.json()["model_id"] == "target-model"

    res_fail = await client.get("/api/v1/models/non-existing-model")
    assert res_fail.status_code == status.HTTP_404_NOT_FOUND

@pytest.mark.asyncio
async def test_top_likes_descending_order(client: AsyncClient, db_session: AsyncSession):
    now = datetime.now(timezone.utc)
    m_low = ModelMetrics(
        pk_model_version_id="1", model_id="low-likes", fk_author_id="a",
        downloads=100, likes=5, gated_status="false", is_private=False,
        created_at=now, last_modified=now, is_current=True
    )
    m_high = ModelMetrics(
        pk_model_version_id="2", model_id="high-likes", fk_author_id="b",
        downloads=50, likes=9999, gated_status="false", is_private=False,
        created_at=now, last_modified=now, is_current=True
    )
    db_session.add_all([m_low, m_high])
    await db_session.commit()

    response = await client.get("/api/v1/models/top/likes?limit=10")
    assert response.status_code == status.HTTP_200_OK
    items = response.json()
    assert items[0]["model_id"] == "high-likes"
    assert items[0]["likes"] == 9999

@pytest.mark.asyncio
async def test_get_models_scd2_only_returns_current(client: AsyncClient, db_session: AsyncSession):
    now = datetime.now(timezone.utc)
    m_old = ModelMetrics(
        pk_model_version_id="scd_old_v1",
        model_id="deepseek-ai/DeepSeek-V3",
        fk_author_id="deepseek-pk",
        downloads=1000,
        likes=50,
        gated_status="false",
        is_private=False,
        created_at=now,
        last_modified=now,
        is_current=False, 
    )
    m_new = ModelMetrics(
        pk_model_version_id="scd_new_v2",
        model_id="deepseek-ai/DeepSeek-V3",
        fk_author_id="deepseek-pk",
        downloads=50000,
        likes=2500,
        gated_status="false",
        is_private=False,
        created_at=now,
        last_modified=now,
        is_current=True,  
    )
    db_session.add_all([m_old, m_new])
    await db_session.commit()

    response = await client.get("/api/v1/models/")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()

    assert len(data) == 1
    assert data[0]["pk_model_version_id"] == "scd_new_v2"
    assert data[0]["downloads"] == 50000


@pytest.mark.asyncio
async def test_get_model_by_id_with_slash_path(client: AsyncClient, db_session: AsyncSession):
    now = datetime.now(timezone.utc)
    m = ModelMetrics(
        pk_model_version_id="v_slash",
        model_id="meta-llama/Meta-Llama-3-70B",
        fk_author_id="meta-pk",
        downloads=75000,
        likes=3200,
        gated_status="auto",
        is_private=False,
        created_at=now,
        last_modified=now,
        is_current=True,
    )
    db_session.add(m)
    await db_session.commit()

    response = await client.get("/api/v1/models/meta-llama/Meta-Llama-3-70B")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["model_id"] == "meta-llama/Meta-Llama-3-70B"
    assert data["downloads"] == 75000


@pytest.mark.asyncio
async def test_get_models_invalid_pagination_parameters(client: AsyncClient):
    res_zero = await client.get("/api/v1/models/?limit=0")
    assert res_zero.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT

    res_overflow = await client.get("/api/v1/models/?limit=50000")
    assert res_overflow.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT

    res_neg_offset = await client.get("/api/v1/models/?offset=-1")
    assert res_neg_offset.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT