"""FastAPI 主应用入口"""

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.database import database
from app.exceptions import BusinessException, ErrorCode
from app.routers import (
    article_router,
    health_router,
    passage_router,
    payment_router,
    statistics_router,
    user_router,
    webhook_router,
)
from app.utils.session import close_redis, init_redis


@asynccontextmanager
async def lifespan(app: FastAPI):
    await database.connect()
    await init_redis()
    print(f"数据库连接成功: {settings.database_url}")
    print(f"Redis 连接成功: {settings.redis_url}")
    print(
        "配图: "
        f"NANO_BANANA_PROVIDER={settings.nano_banana_provider!r}, "
        f"dashscope_key={'已配置' if (settings.dashscope_api_key or '').strip() else '未配置'}, "
        f"gemini_key={'已配置' if (settings.nano_banana_api_key or '').strip() else '未配置'}"
    )
    print(
        "支付: "
        f"stripe_key={'已配置' if (settings.stripe_api_key or '').strip() else '未配置'}, "
        f"webhook={'已配置' if (settings.stripe_webhook_secret or '').strip() and settings.stripe_webhook_secret != 'whsec_xxx' else '未配置'}"
    )
    yield
    await database.disconnect()
    await close_redis()
    print("应用已关闭")


app = FastAPI(
    title="AI 爆款文章创作器",
    description="基于多智能体编排的 AI 文章创作平台",
    version="0.0.1",
    lifespan=lifespan,
)

# 开发时 Vite 默认 5173，占线时会改用 5174、5175…，用正则避免每次改配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=[],
    allow_origin_regex=r"http://(localhost|127\.0\.0\.1):\d+",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(BusinessException)
async def business_exception_handler(request: Request, exc: BusinessException):
    return JSONResponse(
        status_code=200,
        content={
            "code": exc.error_code.code,
            "data": None,
            "message": exc.message,
        },
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    print(f"未处理的异常: {exc}")
    return JSONResponse(
        status_code=200,
        content={
            "code": ErrorCode.SYSTEM_ERROR.code,
            "data": None,
            "message": f"系统内部异常: {str(exc)}",
        },
    )


app.include_router(health_router, prefix="/api")
app.include_router(user_router, prefix="/api")
app.include_router(article_router, prefix="/api")
app.include_router(passage_router, prefix="/api")
app.include_router(payment_router, prefix="/api")
app.include_router(webhook_router, prefix="/api")
app.include_router(statistics_router, prefix="/api")


@app.get("/")
async def root():
    return {
        "message": "AI 爆款文章创作器 - Python 后端",
        "version": "0.0.1",
        "docs": "/docs",
    }
