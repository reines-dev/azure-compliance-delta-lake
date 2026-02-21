import requests
import pytest
import os
from dotenv import load_dotenv

load_dotenv()

# La URL de la API (por defecto puerto 8000)
API_URL = "http://localhost:8000"

def test_api_health_check():
    """Verifica que el servicio API esté arriba."""
    try:
        response = requests.get(f"{API_URL}/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"
    except Exception as e:
        pytest.fail(f"La API no está disponible en {API_URL}: {e}")

def test_check_name_api_response():
    """Verifica que el endpoint de búsqueda responda con el esquema correcto."""
    params = {"name": "SANTOS", "threshold": 50}
    try:
        response = requests.get(f"{API_URL}/check-name", params=params)
        assert response.status_code == 200
        data = response.json()
        assert "query" in data
        assert "match_found" in data
        assert "results" in data
    except Exception as e:
        pytest.fail(f"Error al consultar el endpoint /check-name: {e}")

def test_storage_connectivity():
    """Verifica que las variables de entorno de Azure estén configuradas."""
    assert os.getenv("AZURE_STORAGE_CONNECTION_STRING") is not None
    assert os.getenv("DELTA_TABLE_PATH") is not None
