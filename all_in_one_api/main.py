from fastapi import FastAPI, Request
from sqlalchemy import select
from database import db_dependency
from routers import analytics, author, models, health
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)

app = FastAPI()
app.state.limiter = limiter

app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.include_router(models.models_router)
app.include_router(author.authors_router)
app.include_router(analytics.analytics_router)
app.include_router(health.health_router)