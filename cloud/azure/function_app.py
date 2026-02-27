import azure.functions as func
from src.main import app

# Adaptador ASGI nativo de Azure Functions V2 para montar FastAPI completo
# Todo el ruteo interno (/check, /health) será manejado por FastAPI
fastapi_app = func.AsgiFunctionApp(
    app=app, 
    http_auth_level=func.AuthLevel.FUNCTION
)
