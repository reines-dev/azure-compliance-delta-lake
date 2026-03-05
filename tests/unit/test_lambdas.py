import os
import json
import boto3
import pytest
from moto import mock_aws
from unittest.mock import patch, MagicMock
from lambdas.ofac_handler import ofac_handler
from lambdas.onu_handler import onu_handler
from lambdas.sat_handler import sat69b_handler
from lambdas.pep_handler import socrata_pep_handler
from lambdas.opensanctions_handler import opensanctions_proxy_handler

@pytest.fixture
def mock_s3_env():
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
    assert ofac_handler({}, None)['status'] == 'success'
    
    # Test ONU
    assert onu_handler({}, None)['status'] == 'success'
    
    # Test SAT
    assert sat69b_handler({}, None)['status'] == 'success'
    
    # Test PEP
    assert socrata_pep_handler({}, None)['status'] == 'success'
    
    # Test OpenSanctions
    assert opensanctions_proxy_handler({"source_id": "fbi_wanted"}, None)['status'] == 'success'
