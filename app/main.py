"""
WhatsApp Pharmacy Assistant - Main FastAPI Application
"""
import os
import time
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.api.v1 import api_router
from app.middleware.auth_middleware import AuthMiddleware
from app.middleware.error_handler import error_handler_middleware

# Set timezone
os.environ["TZ"] = getattr(settings, "timezone", "America/Argentina/Buenos_Aires")
time.tzset()

# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    description="WhatsApp-based pharmacy billing and payment assistant with Mercado Pago integration",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# Store settings in app state
app.state.settings = settings

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=settings.ALLOWED_METHODS,
    allow_headers=settings.ALLOWED_HEADERS,
)

# Error handler middleware
app.middleware("http")(error_handler_middleware)

# Authentication middleware
auth_middleware = AuthMiddleware()
app.middleware("http")(auth_middleware)

# Include API v1 router
app.include_router(api_router)


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "service": settings.APP_NAME,
        "version": "0.1.0",
        "environment": settings.ENVIRONMENT,
        "documentation": {
            "swagger": "/docs",
            "redoc": "/redoc",
            "openapi": "/openapi.json",
        },
        "api_version": "v1",
        "endpoints": {
            "health": "/api/v1/health",
            "clients": "/api/v1/clients",
            "transactions": "/api/v1/transactions",
            "payments": "/api/v1/payments",
        },
    }


@app.on_event("startup")
async def startup_event():
    """Startup event handler."""
    print(f"🚀 {settings.APP_NAME} starting...")
    print(f"📍 Environment: {settings.ENVIRONMENT}")
    print(f"🔗 Database: {settings.DATABASE_URL.split('@')[-1] if '@' in settings.DATABASE_URL else 'configured'}")
    print(f"📱 WhatsApp: {'configured' if settings.CHATTIGO_AUTH_TOKEN else 'not configured'}")
    print(f"💰 Mercado Pago: {'configured' if settings.MERCADOPAGO_ACCESS_TOKEN else 'not configured'}")
    print(f"✅ Application ready!")


@app.on_event("shutdown")
async def shutdown_event():
    """Shutdown event handler."""
    print(f"🛑 {settings.APP_NAME} shutting down...")
