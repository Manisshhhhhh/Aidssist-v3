from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.exception_handlers import request_validation_exception_handler
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

from app.api.analysis import router as analysis_router
from app.api.artifacts import router as artifacts_router
from app.api.audit import router as audit_router
from app.api.auth import router as auth_router
from app.api.backups import router as backups_router
from app.api.charts import router as charts_router
from app.api.chat import router as chat_router
from app.api.datasets import router as datasets_router
from app.api.diagnostics import router as diagnostics_router
from app.api.forecast import router as forecast_router
from app.api.health import router as health_router
from app.api.jobs import router as jobs_router
from app.api.llm import router as llm_router
from app.api.preflight import router as preflight_router
from app.api.report import router as report_router
from app.api.upload import router as upload_router
from app.api.workspaces import router as workspaces_router
from app.core.config import get_settings
from app.core.headers import add_security_headers
from app.core.logging import configure_logging, get_logger
from app.core.maintenance import enforce_maintenance_mode
from app.core.preflight import run_startup_preflight
from app.core.request_context import get_request_id
from app.core.request_id import add_request_context
from app.db.init_db import init_db
from app.services.audit_service import record_event


settings = get_settings()
configure_logging()
logger = get_logger(__name__)

if settings.auth_enabled and "*" in settings.cors_origins:
    raise RuntimeError("Wildcard CORS origins are not allowed when Aidssist API key auth is enabled.")

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    run_startup_preflight()
    yield


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Autonomous data intelligence platform API.",
    lifespan=lifespan,
)

app.middleware("http")(add_request_context)
app.middleware("http")(enforce_maintenance_mode)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_origin_regex=settings.cors_origin_regex,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.middleware("http")(add_security_headers)

app.include_router(health_router)
app.include_router(auth_router)
app.include_router(workspaces_router)
app.include_router(jobs_router)
app.include_router(audit_router)
app.include_router(diagnostics_router)
app.include_router(preflight_router)
app.include_router(backups_router)
app.include_router(upload_router)
app.include_router(datasets_router)
app.include_router(artifacts_router)
app.include_router(analysis_router)
app.include_router(forecast_router)
app.include_router(charts_router)
app.include_router(chat_router)
app.include_router(llm_router)
app.include_router(report_router)


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    request_id = get_request_id()
    if exc.status_code in {401, 403, 429}:
        record_event(
            event_type="security.rate_limited" if exc.status_code == 429 else "security.unauthorized",
            action=f"{request.method} {request.url.path}",
            outcome="denied",
            metadata={"status_code": exc.status_code, "detail": str(exc.detail)},
            request=request,
        )
    headers = dict(exc.headers or {})
    if request_id:
        headers["X-Request-ID"] = request_id
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail, "request_id": request_id},
        headers=headers,
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    response = await request_validation_exception_handler(request, exc)
    request_id = get_request_id()
    if request_id:
        response.headers["X-Request-ID"] = request_id
    return response


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    request_id = get_request_id()
    logger.exception("unhandled request error")
    detail = str(exc) if settings.error_details_enabled else "Internal server error."
    return JSONResponse(
        status_code=500,
        content={"detail": detail, "request_id": request_id},
        headers={"X-Request-ID": request_id} if request_id else None,
    )


@app.get("/")
def root() -> dict[str, str]:
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "docs": "/docs",
        "health": "/health",
    }
