import logging

from fastapi import FastAPI, Request, status
from fastapi.exception_handlers import request_validation_exception_handler
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError, OperationalError

from app.config import settings
from app.core.logging import RequestContextMiddleware, configure_logging
from app.database import SessionLocal
from app.routers import applications, auth, profile, scan

configure_logging()
logger = logging.getLogger("signalwork")

app = FastAPI(
    title=settings.app_name,
    description="AI career-intelligence API: skill profiles, job-posting scans, and application tracking.",
    version="1.0.0",
)

app.add_middleware(RequestContextMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(profile.router)
app.include_router(scan.router)
app.include_router(applications.router)


# ---------- Error handling ----------
# FastAPI's default 422 body is fine but inconsistent with our other error
# shapes; normalize it. More importantly: never let a raw DB exception (with
# table/column names, SQL fragments) reach the client — log it, return a
# generic message instead.

@app.exception_handler(RequestValidationError)
async def validation_handler(request: Request, exc: RequestValidationError):
    return await request_validation_exception_handler(request, exc)


@app.exception_handler(IntegrityError)
async def integrity_error_handler(request: Request, exc: IntegrityError):
    logger.warning("integrity_error path=%s detail=%s", request.url.path, str(exc.orig))
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content={"detail": "This record conflicts with an existing one."},
    )


@app.exception_handler(OperationalError)
async def db_unavailable_handler(request: Request, exc: OperationalError):
    logger.error("database_unavailable path=%s detail=%s", request.url.path, str(exc))
    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content={"detail": "Database temporarily unavailable. Try again shortly."},
    )


# ---------- Health checks ----------
@app.get("/health", tags=["meta"])
def health():
    """Liveness probe — process is up. Does not touch the DB."""
    return {"status": "ok", "service": settings.app_name}


@app.get("/health/ready", tags=["meta"])
def readiness():
    """Readiness probe — can this instance actually serve traffic (DB reachable)?"""
    try:
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
    except Exception as exc:  # noqa: BLE001 - readiness probe deliberately broad
        logger.error("readiness_check_failed detail=%s", str(exc))
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"status": "not_ready", "database": "unreachable"},
        )
    return {"status": "ready", "database": "reachable"}
