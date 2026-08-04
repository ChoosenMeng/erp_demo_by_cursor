import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.router import api_router
from app.core.config import get_settings
from app.core.exceptions import AppError
from app.core.logging import setup_logging
from app.core.response import fail, ok

logger = logging.getLogger(__name__)
settings = get_settings()


# Ensure finance hooks are active even when TestClient skips lifespan
from app.modules.finance.hooks import register_finance_hooks

register_finance_hooks()


@asynccontextmanager
async def lifespan(_app: FastAPI):
    setup_logging(settings.debug)
    register_finance_hooks()
    logger.info("Starting %s (%s)", settings.app_name, settings.app_env)
    yield
    logger.info("Shutting down %s", settings.app_name)


app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(AppError)
async def app_error_handler(_request: Request, exc: AppError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content=fail(exc.message, code=exc.code, data=exc.details),
    )


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(_request: Request, exc: StarletteHTTPException) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content=fail(str(exc.detail), code=exc.status_code * 100),
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    _request: Request, exc: RequestValidationError
) -> JSONResponse:
    return JSONResponse(
        status_code=422,
        content=fail("参数校验失败", code=42200, data=exc.errors()),
    )


@app.get("/")
def root() -> dict:
    return ok(
        {
            "name": settings.app_name,
            "docs": "/docs",
            "health": "/api/v1/health",
        }
    )


app.include_router(api_router)
