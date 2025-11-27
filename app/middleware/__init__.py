"""
Middleware for request processing, authentication, and error handling.
"""
from app.middleware.auth_middleware import AuthMiddleware
from app.middleware.error_handler import error_handler_middleware

__all__ = ["AuthMiddleware", "error_handler_middleware"]
