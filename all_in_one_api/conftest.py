import sys
from pathlib import Path

API_DIR = Path(__file__).resolve().parent.parent
if str(API_DIR) not in sys.path:
    sys.path.insert(0, str(API_DIR))

from httpx import ASGITransport, AsyncClient
from sqlalchemy import event, text
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from database import Base, get_db
import pytest
from data_models import (
    AuthorLeaderboard,
    ModelMetrics,
    fct_model_version, 
    author_leaderboard_version)

import pytest_asyncio
from main import app
from datetime import datetime

TEST_DB_URL = "sqlite+aiosqlite:///all_in_one_api/:memory:"

test_engine = create_async_engine(
    url=TEST_DB_URL,
    echo= False)

TestingSessionLocal = async_sessionmaker(
    class_=AsyncSession,
    autoflush = False, 
    bind = test_engine,
    expire_on_commit=False)

@event.listens_for(Base.metadata, "before_create")
def disable_schemas_for_sqlite(target, connection, **kw):
    if connection.dialect.name == "sqlite":
        for table in target.tables.values():
            table.schema = None

@pytest_asyncio.fixture(scope="function")
async def db_session():
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with TestingSessionLocal() as session:
        yield session

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest_asyncio.fixture(scope="function")
async def client(db_session: AsyncSession):
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()

@pytest_asyncio.fixture
async def author():
     
    author = AuthorLeaderboard(
        pk_author_leaderboard_id="test_pk_id",
        author="test_author",
        total_models=20,
        total_downloads=50,
        total_likes=100,
        avg_downloads_per_model=2.5,
        avg_likes_per_model=5,
        first_model_created_at= datetime(2022,3,2,23,29,5),
        last_model_created_at= datetime(2023,3,4,16,15,32),
        rank_by_downloads= 6,
        rank_by_likes= 3
        )

    async with TestingSessionLocal() as db:
        db.add(author)
        await db.commit()

    yield author

    async with test_engine.begin() as conn:
        await conn.execute(text(f"DELETE FROM mart_author_leaderboard_v{author_leaderboard_version}"))

@pytest_asyncio.fixture
async def model_v1():
    model_v1 = ModelMetrics(
        pk_model_version_id="test_pk_id1",
        model_id = "test_model1",
        fk_author_id = "author",
        downloads = 10,
        likes = 100,
        pipeline_tag = "pipeline",
        library_name = "library",
        license = "license",
        base_model = "base_model1",
        gated_status = "False",
        is_private = False,
        created_at = datetime(2022,3,2,23,29,5),
        last_modified = datetime(2023,3,2,23,29,5),
        is_current = True,
        dbt_updated_at = datetime(2023,3,2,23,29,5),
        dbt_valid_from = datetime(2023,3,2,23,29,5),
        dbt_valid_to = None
        )

    

    model_v3 = ModelMetrics(
            pk_model_version_id="test_pk_id3",
            model_id = "test_model3",
            fk_author_id = "author",
            downloads = 23,
            likes = 113,
            pipeline_tag = "",
            library_name = "",
            license = "license",
            base_model = "base_model3",
            gated_status = "manual",
            is_private = False,
            created_at = datetime(2022,3,2,23,29,5),
            last_modified = datetime(2025,3,2,23,29,5),
            is_current = False,
            dbt_updated_at = datetime(2025,3,2,23,29,5),
            dbt_valid_from = datetime(2022,3,2,23,29,5),
            dbt_valid_to = datetime(2025,3,2,23,29,5)
            )

    async with TestingSessionLocal() as db:
        db.add(model_v1)
        await db.commit()

    yield model_v1

    async with test_engine.begin() as conn:
        await conn.execute(text(f"DELETE FROM fct_model_metrics_v{fct_model_version}"))

@pytest_asyncio.fixture
async def model_v2():
    model_v2 = ModelMetrics(
            pk_model_version_id="test_pk_id2",
            model_id = "test_model2",
            fk_author_id = "author",
            downloads = 15,
            likes = 90,
            pipeline_tag = "pipeline",
            library_name = "library",
            license = "",
            base_model = "base_model2",
            gated_status = "auto",
            is_private = False,
            created_at = datetime(2022,6,2,23,29,5),
            last_modified = datetime(2023,3,1,23,29,5),
            is_current = True,
            dbt_updated_at = datetime(2023,3,1,23,29,5),
            dbt_valid_from = datetime(2023,3,1,23,29,5),
            dbt_valid_to = None
            )
   
    async with TestingSessionLocal() as db:
        db.add(model_v2)
        await db.commit()

    yield model_v2

    async with test_engine.begin() as conn:
        await conn.execute(text(f"DELETE FROM fct_model_metrics_v{fct_model_version}"))


@pytest_asyncio.fixture
async def model_v3():
    model_v3 = ModelMetrics(
            pk_model_version_id="test_pk_id3",
            model_id = "test_model3",
            fk_author_id = "author",
            downloads = 23,
            likes = 113,
            pipeline_tag = "",
            library_name = "",
            license = "license",
            base_model = "base_model3",
            gated_status = "manual",
            is_private = False,
            created_at = datetime(2022,3,2,23,29,5),
            last_modified = datetime(2025,3,2,23,29,5),
            is_current = False,
            dbt_updated_at = datetime(2025,3,2,23,29,5),
            dbt_valid_from = datetime(2022,3,2,23,29,5),
            dbt_valid_to = datetime(2025,3,2,23,29,5)
            )

    async with TestingSessionLocal() as db:
        db.add(model_v3)
        await db.commit()

    yield model_v3

    async with test_engine.begin() as conn:
        await conn.execute(text(f"DELETE FROM fct_model_metrics_v{fct_model_version}"))
