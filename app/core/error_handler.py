# app/core/error_handler.py
from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from app.core.logger import logger
from app.core.custom_exceptions import ApiError

def init_error_handlers(app):
    # Handle HTTPException (custom or raised by FastAPI)
    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        logger.warning(f"HTTP error {exc.status_code}: {exc.detail}")
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "success": False,
                "message": exc.detail,
            },
        )

    # Handle validation errors (from Pydantic schemas)
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        logger.warning(f"Validation error: {exc.errors()}")
        return JSONResponse(
            status_code=422,
            content={
                "success": False,
                "message": "Validation failed",
                "errors": exc.errors(),
            },
        )

    # Handle all other unhandled exceptions
    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        logger.error(f"Unhandled error: {exc}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "message": "Internal server error",
            },
        )
    @app.exception_handler(ApiError)
    async def api_error_handler(request: Request, exc: ApiError):
        logger.warning(f"API error {exc.status_code}: {exc.message}")
        return JSONResponse(
            status_code=exc.status_code,
            content={"success": False, "message": exc.message},
        )
