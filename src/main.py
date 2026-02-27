from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.api.v1 import search
from src.core.config import get_settings

app = FastAPI(
    title="ComplianceGuard Multi-Cloud API",
    description="Motor de búsqueda de Listas de Control basado en Delta Lake (Serverless)",
    version="1.0.0"
)

# Configuración de CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # En producción se recomienda restringir a dominios específicos
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluir Rutas (Modularidad)
app.include_router(search.router)

@app.get("/health", tags=["System"])
async def health_check():
    return {"status": "healthy", "engine": "FastAPI"}
