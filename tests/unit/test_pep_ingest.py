import os
import json
import boto3
import pytest
from moto import mock_aws
from lambdas.pep_handler import socrata_pep_handler

@mock_aws
def test_pep_lambda_extract():
    # Setup mock S3
    os.environ['COMPLIANCE_LAKE_BUCKET'] = 'test-bucket'
    # Use a small controlled dataset for testing to avoid heavy downloads
    os.environ['PEP_URL'] = 'https://raw.githubusercontent.com/OAI/OpenAPI-Specification/main/examples/v2.0/json/petstore.json'

    conn = boto3.client('s3', region_name='us-east-1')
    conn.create_bucket(Bucket='test-bucket')

    # Execute Lambda Handler
    response = socrata_pep_handler({}, None)

    # Assert
    assert response['status'] == 'success'
    assert response['source'] == 'pep'
