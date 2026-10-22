from fastapi import APIRouter, Request
from database import db_dependency
from sqlalchemy import select
from slowapi import Limiter
from slowapi.util import get_remote_address


health_router = APIRouter(
    prefix="/api/v1/health",
    tags=["health"]
)
limiter = Limiter(key_func=get_remote_address)

@health_router.get("/")
@limiter.limit("30/minute")
async def health_check(
    request:Request,
    db: db_dependency):

    query = select(1)

    result_raw = await db.execute(query)

    result = result_raw.scalars().first()

    if result:
        return {"status": "healthy"}