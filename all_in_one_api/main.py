from fastapi import FastAPI
from routers import analytics, author, models, system
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)

app = FastAPI()

app.include_router(models.models_router)
app.include_router(author.authors_router)
app.include_router(analytics.analytics_router)
app.include_router(system.system)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)