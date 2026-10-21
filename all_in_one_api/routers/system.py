from fastapi import APIRouter, Request
from database import db_dependency
from sqlalchemy import select
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
system = APIRouter(
    prefix= "/api/v1/health",
    tags=["health"]
)


@system.get("/")
@limiter.limit("30/minute")
async def health_check(
    request:Request,
    db: db_dependency):

    query = select(1)

    result_raw = await db.execute(query)

    result = result_raw.scalars().first()

    if result:
        return "System is healthy."
    else:
        return "There might be a database error"