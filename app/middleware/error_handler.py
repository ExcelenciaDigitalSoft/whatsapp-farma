"""
Global error handler middleware.
"""
from fastapi import Request, status
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from pydantic import ValidationError
import logging
import traceback

logger = logging.getLogger(__name__)


async def error_handler_middleware(request: Request, call_next):
    """
    Global error handler middleware for consistent error responses.

    Catches all exceptions and returns standardized JSON responses.
    """
    try:
        response = await call_next(request)
        return response

    except ValidationError as e:
        # Pydantic validation errors
        logger.warning(f"Validation error: {e}")
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "error": "validation_error",
                "message": "Request validation failed",
                "details": e.errors(),
            }
        )

    except IntegrityError as e:
        # Database integrity errors (unique constraints, foreign keys, etc.)
        logger.error(f"Database integrity error: {e}")
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={
                "error": "integrity_error",
                "message": "Database integrity constraint violated",
                "details": str(e.orig) if hasattr(e, 'orig') else str(e),
            }
        )

    except SQLAlchemyError as e:
        # Other database errors
        logger.error(f"Database error: {e}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": "database_error",
                "message": "Database operation failed",
                "details": str(e) if request.app.state.settings.DEBUG else "Internal server error",
            }
        )

    except Exception as e:
        # Unexpected errors
        logger.error(f"Unexpected error: {e}\n{traceback.format_exc()}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": "internal_server_error",
                "message": "An unexpected error occurred",
                "details": str(e) if request.app.state.settings.DEBUG else "Internal server error",
            }
        )
