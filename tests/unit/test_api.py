import pytest
from fastapi.testclient import TestClient
from src.api.main import app
from unittest.mock import patch, MagicMock
import pandas as pd

client = TestClient(app)

def test_api_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

@patch("src.api.v1.search.get_storage")
@patch("awswrangler.s3.read_parquet")
def test_search_endpoint(mock_wr, mock_get_storage):
    # Mock profundo para evitar llamadas reales a S3
    df = pd.DataFrame([
        {"nombre_original": "JUAN PEREZ", "nombre_limpio": "JUAN PEREZ", "fuente": "TEST", "tipo_lista": "L1", "metadata": "{}"}
    ])
    mock_wr.return_value = df
    
    mock_storage = MagicMock()
    mock_storage.get_delta_table.return_value = df
    mock_get_storage.return_value = mock_storage
    
    # Simular bÃºsqueda
    response = client.get("/check/?name=JUAN")
    assert response.status_code == 200
    assert response.json()["match_found"] is True

@patch("src.api.v1.etl.pipeline")
def test_etl_endpoints(mock_pipeline):
    mock_pipeline.execute_ingest.return_value = {"status": "success"}
    mock_pipeline.execute_transform.return_value = {"status": "success"}
    mock_pipeline.execute_load.return_value = {"status": "success"}
    
    resp_ingest = client.post("/etl/ingest/ofac")
    assert resp_ingest.status_code == 200
