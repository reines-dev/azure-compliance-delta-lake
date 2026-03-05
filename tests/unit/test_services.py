import os
import pytest
import boto3
import pandas as pd
from moto import mock_aws
from unittest.mock import patch, MagicMock
from src.services.storage import StorageService
from src.etl import pipeline

@pytest.fixture
def storage_service():
    with mock_aws():
        os.environ['AWS_ACCESS_KEY_ID'] = 'testing'
        os.environ['AWS_SECRET_ACCESS_KEY'] = 'testing'
        os.environ['AWS_SECURITY_TOKEN'] = 'testing'
        os.environ['AWS_SESSION_TOKEN'] = 'testing'
        os.environ['AWS_DEFAULT_REGION'] = 'us-east-1'
        
        s3 = boto3.client('s3', region_name='us-east-1')
        s3.create_bucket(Bucket='test-bucket')
        yield StorageService('test-bucket', 's3://test-bucket/gold')

def test_storage_parquet_ops(storage_service):
    df = pd.DataFrame([{"a": 1, "b": 2}])
    key = "test.parquet"
    path = storage_service.save_parquet(df, key)
    assert "s3://" in path
    df_read = storage_service.read_parquet(key)
    assert not df_read.empty

@patch("awswrangler.s3.read_parquet")
def test_storage_delta_table(mock_wr, storage_service):
    df = pd.DataFrame([{"nombre_limpio": "A", "fuente": "F"}])
    mock_wr.return_value = df
    res = storage_service.get_delta_table()
    assert not res.empty

def test_storage_error_handling(storage_service):
    # Forzar error en get_delta_table para cubrir el bloque except
    with patch("awswrangler.s3.read_parquet") as mock_wr:
        mock_wr.side_effect = Exception("S3 Fail")
        with pytest.raises(Exception):
            storage_service.get_delta_table()

def test_pipeline_methods(storage_service):
    assert pipeline.execute_ingest("ofac", storage_service)["status"] == "success"
    assert pipeline.execute_transform("ofac", storage_service)["status"] == "success"
