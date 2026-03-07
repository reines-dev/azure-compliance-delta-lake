import os
# ComplianceGuard - API Entry Point
# Reorganized into modular structure for production stability.
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.api.v1 import search, etl
from src.core.config import get_settings

settings = get_settings()

# Detectar si estamos en AWS Lambda para ajustar el root_path del stage (/prod)
# Mangum suele inyectar esto, pero lo forzamos si es necesario para Swagger
root_path = "/prod" if os.getenv("AWS_LAMBDA_FUNCTION_NAME") else ""

app = FastAPI(
    title="ComplianceGuard Multi-Cloud API",
    description="""
    ### Sistema de Prevención de Lavado de Activos y Sanciones.
    
    Esta API permite realizar búsquedas inteligentes sobre múltiples listas de control.
    """,
    version="1.1.0",
    openapi_tags=[
        {"name": "Search", "description": "Búsqueda Fuzzy Match"},
        {"name": "System", "description": "Salud del servicio"}
    ],
    docs_url="/docs" if settings.enable_docs else None,
    redoc_url="/redoc" if settings.enable_docs else None,
    openapi_url="/openapi.json" if settings.enable_docs else None,
    root_path=root_path
)

# Configuración de CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluir Rutas
app.include_router(search.router)

# ETL Router: Se incluye pero se oculta de Swagger para mantener la API "limpia"
app.include_router(etl.router, include_in_schema=False)

@app.get("/health", tags=["System"])
async def health_check():
    return {"status": "healthy", "engine": "FastAPI", "version": "1.1.0"}
