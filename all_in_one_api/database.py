from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from fastapi import Depends
from typing import Annotated
from dotenv import load_dotenv
from collections.abc import AsyncGenerator
import os

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/hf_models_db")
IS_DEBUG = os.getenv("IS_DEBUG", "False").lower() in ("true", "1", "t")

engine = create_async_engine(
    DATABASE_URL, 
    echo=IS_DEBUG,
    pool_size=10,
    max_overflow=20,
    pool_timeout=30,
    pool_recycle=1800,
    pool_pre_ping=True
    )

class Base(DeclarativeBase):
    pass

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    autoflush=False,
    expire_on_commit=False
)

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise

db_dependency = Annotated[AsyncSession, Depends(get_db)]