import os
import json
import boto3
import pytest
from moto import mock_aws
from unittest.mock import patch, MagicMock
from lambdas.ofac_handler import ofac_handler
from lambdas.onu_handler import onu_handler
from lambdas.opensanctions_handler import opensanctions_proxy_handler

@pytest.fixture(autouse=True)
def aws_credentials():
    """Mocked AWS Credentials for moto."""
    os.environ["AWS_ACCESS_KEY_ID"] = "testing"
    os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"
    os.environ["AWS_SECURITY_TOKEN"] = "testing"
    os.environ["AWS_SESSION_TOKEN"] = "testing"
    os.environ["AWS_DEFAULT_REGION"] = "us-east-1"

@pytest.fixture
def mock_s3_env(aws_credentials, monkeypatch):
    with mock_aws():
        monkeypatch.setenv('COMPLIANCE_LAKE_BUCKET', 'test-bucket')
        s3 = boto3.client('s3', region_name='us-east-1')
        s3.create_bucket(Bucket='test-bucket')
        yield s3

@patch('urllib3.PoolManager.request')
def test_all_extractors(mock_request, mock_s3_env):
    # Mock genÃ©rico exitoso
    mock_resp = MagicMock()
    mock_resp.status = 200
    mock_resp.data = b"id,name\n1,TEST DATA"
    mock_request.return_value = mock_resp

    # Test OFAC
    assert ofac_handler({"OFAC_SDN_URL": "http://mock"}, None)['status'] == 'success'
    
    # Test ONU
    assert onu_handler({"ONU_URL": "http://mock"}, None)['status'] == 'success'
    
    # Test OpenSanctions
    assert opensanctions_proxy_handler({"source_id": "fbi_wanted"}, None)['status'] == 'success'

@patch('urllib3.PoolManager.request')
def test_all_extractors_exceptions(mock_request, mock_s3_env, monkeypatch):
    mock_resp = MagicMock()
    mock_resp.status = 500
    mock_request.return_value = mock_resp
    
    with pytest.raises(Exception, match="Failed to download data"):
        ofac_handler({"OFAC_SDN_URL": "http://mock"}, None)
        
    with pytest.raises(Exception, match="Failed to download data"):
        onu_handler({"ONU_URL": "http://mock"}, None)
        
    with pytest.raises(Exception, match="Failed to download data"):
        opensanctions_proxy_handler({"source_id": "fbi"}, None)

def test_missing_payloads(mock_s3_env, monkeypatch):
    with pytest.raises(ValueError, match="OFAC_SDN_URL"):
        ofac_handler({}, None)
        
    with pytest.raises(ValueError, match="ONU_URL"):
        onu_handler({}, None)
        
    with pytest.raises(ValueError, match="source_id"):
        opensanctions_proxy_handler({}, None)
