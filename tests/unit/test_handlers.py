import os
import pytest
import boto3
from moto import mock_aws
from unittest.mock import patch, MagicMock
from lambdas.ofac_handler import ofac_handler
from lambdas.onu_handler import onu_handler
from lambdas.sat_handler import sat69b_handler
from lambdas.opensanctions_handler import opensanctions_proxy_handler

@pytest.fixture
def aws_setup():
    with mock_aws():
        os.environ['COMPLIANCE_LAKE_BUCKET'] = 'test-bucket'
        s3 = boto3.client('s3', region_name='us-east-1')
        s3.create_bucket(Bucket='test-bucket')
        yield s3

@patch('urllib3.PoolManager.request')
def test_ofac_handler(mock_request, aws_setup):
    mock_response = MagicMock()
    mock_response.status = 200
    mock_response.data = b"id,name\n1,TEST OFAC"
    mock_request.return_value = mock_response

    response = ofac_handler({}, None)
    assert response['status'] == 'success'
    assert response['source'] == 'ofac'

@patch('urllib3.PoolManager.request')
def test_onu_handler(mock_request, aws_setup):
    mock_response = MagicMock()
    mock_response.status = 200
    mock_response.data = b"<root><test>ONU DATA</test></root>"
    mock_request.return_value = mock_response

    response = onu_handler({}, None)
    assert response['status'] == 'success'
    assert response['source'] == 'onu'

@patch('urllib3.PoolManager.request')
def test_sat_handler(mock_request, aws_setup):
    mock_response = MagicMock()
    mock_response.status = 200
    mock_response.data = b"rfc,nombre\nABC123,TEST SAT"
    mock_request.return_value = mock_response

    response = sat69b_handler({}, None)
    assert response['status'] == 'success'
    assert response['source'] == 'sat69b'

@patch('urllib3.PoolManager.request')
def test_opensanctions_handler(mock_request, aws_setup):
    mock_response = MagicMock()
    mock_response.status = 200
    mock_response.data = json_data = b'{"entities": []}'
    mock_request.return_value = mock_response

    response = opensanctions_proxy_handler({"source_id": "fbi_wanted"}, None)
    assert response['status'] == 'success'
