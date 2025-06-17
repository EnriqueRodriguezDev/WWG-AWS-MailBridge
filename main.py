# app/main.py

import uvicorn
import logging
from fastapi import FastAPI, Request, status, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, ORJSONResponse
from fastapi.openapi.utils import get_openapi

from app.api.v1.api import api_router
from app.core.config import settings
from app.api.v1.endpoints.auth_controller import router as auth_router
from app.api.v1.endpoints.credentials_controller import router as credentials_router

# Logging básico
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("mailbridge")

app = FastAPI(
    title="MailBridge API",
    version="0.1.0",
    docs_url="/docs",        # Swagger UI
    redoc_url="/redoc",      # Redoc
    openapi_url="/openapi.json",
    default_response_class=ORJSONResponse
)

# CORS (ajusta allow_origins según tu necesidad)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Handler de errores de validación para devolver un JSON limpio
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": exc.errors()},
    )

# Include API routes#
app.include_router(api_router, prefix=settings.API_V1_PREFIX)


# Health check
@app.get("/health", tags=["Health"], summary="Health check")
async def health_check():
    return {"status": "ok", "service": "MailBridge", "version": "1"}#app.version}

# Personalizamos el esquema OpenAPI (opcional)
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title="MailBridge WorldWide Group & SMS AWS SQS Service", #app.title,
        version='1.0', #app.version,
        description="API para administrar credenciales de AWS y tokens, comprimir y optimizar PDFs, subirlos a un bucket de S3 y encolar correos en SQS para envío vía SES.",
        routes=app.routes,
    )
    openapi_schema["openapi"] = "3.0.2"
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.HOST if hasattr(settings, "HOST") else "0.0.0.0",
        port=settings.PORT if hasattr(settings, "PORT") else 8000,
        reload=getattr(settings, "DEBUG", True),
    )
