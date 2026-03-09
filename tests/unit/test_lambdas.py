import os
import json
import boto3
import pytest
from moto import mock_aws
from unittest.mock import patch, MagicMock
from lambdas.ofac_handler import ofac_handler
from lambdas.onu_handler import onu_handler
from lambdas.pep_handler import socrata_pep_handler
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
def mock_s3_env(aws_credentials):
    with mock_aws():
        os.environ['COMPLIANCE_LAKE_BUCKET'] = 'test-bucket'
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
    
    # Test PEP (also testing auth injection when vars exist)
    os.environ['DATOS_GOV_KEY_ID'] = 'test_key'
    os.environ['DATOS_GOV_API_KEY'] = 'test_secret'
    assert socrata_pep_handler({"PEP_URL": "http://mock"}, None)['status'] == 'success'
    
    # Test PEP Fallback to GET
    mock_resp.status = 500
    mock_resp_get = MagicMock()
    mock_resp_get.status = 200
    mock_resp_get.data = b"id,name\n1,TEST DATA"
    mock_request.side_effect = [mock_resp, mock_resp_get] # First POST fails, GET succeeds
    assert socrata_pep_handler({"PEP_URL": "http://mock"}, None)['status'] == 'success'
    mock_request.side_effect = None # Reset side effect
    mock_request.return_value = mock_resp_get
    
    # Test OpenSanctions
    assert opensanctions_proxy_handler({"source_id": "fbi_wanted"}, None)['status'] == 'success'

@patch('urllib3.PoolManager.request')
def test_all_extractors_exceptions(mock_request, mock_s3_env):
    mock_resp = MagicMock()
    mock_resp.status = 500
    mock_request.return_value = mock_resp
    
    with pytest.raises(Exception, match="Failed to download data"):
        ofac_handler({"OFAC_SDN_URL": "http://mock"}, None)
        
    with pytest.raises(Exception, match="Failed to download data"):
        onu_handler({"ONU_URL": "http://mock"}, None)
        
    with pytest.raises(Exception, match="Failed to download data"):
        opensanctions_proxy_handler({"source_id": "fbi"}, None)
        
    with pytest.raises(Exception, match="Failed to download data"):
        # PEP does two requests if POST fails, both mocking 500 here
        socrata_pep_handler({"PEP_URL": "http://mock"}, None)

def test_missing_payloads(mock_s3_env):
    with pytest.raises(ValueError, match="OFAC_SDN_URL"):
        ofac_handler({}, None)
        
    with pytest.raises(ValueError, match="ONU_URL"):
        onu_handler({}, None)
        
    with pytest.raises(ValueError, match="PEP_URL"):
        socrata_pep_handler({}, None)
        
    with pytest.raises(ValueError, match="source_id"):
        opensanctions_proxy_handler({}, None)
