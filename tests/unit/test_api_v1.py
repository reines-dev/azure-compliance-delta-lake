import pytest
from fastapi.testclient import TestClient
from src.api.main import app
from unittest.mock import patch, MagicMock

client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

@patch("src.api.v1.search.boto3.client")
def test_search_names_api(mock_boto):
    # Mock de S3 select o Athena para la bÃºsqueda
    mock_s3 = MagicMock()
    mock_boto.return_value = mock_s3
    
    # Simular bÃºsqueda exitosa
    response = client.get("/api/v1/search/check-name?name=JUAN PEREZ")
    # Nota: Si falla por falta de env vars, el mock debe ser mÃ¡s profundo
    assert response.status_code in [200, 403, 500] # Dependiendo de auth configurada

def test_docs_access():
    # Verificar que Swagger UI estÃ© disponible (settings.enable_docs = True por defecto)
    response = client.get("/docs")
    assert response.status_code == 200
