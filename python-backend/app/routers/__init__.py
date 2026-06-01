from app.routers.article import router as article_router
from app.routers.health import router as health_router
from app.routers.passage import router as passage_router
from app.routers.payment import payment_router, webhook_router
from app.routers.statistics import router as statistics_router
from app.routers.user import router as user_router

__all__ = [
    "health_router",
    "passage_router",
    "user_router",
    "article_router",
    "payment_router",
    "webhook_router",
    "statistics_router",
]
