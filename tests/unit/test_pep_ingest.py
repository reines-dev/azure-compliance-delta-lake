import os
import json
import boto3
import pytest
from moto import mock_aws
from lambdas.pep_handler import socrata_pep_handler
from unittest.mock import patch, MagicMock

@mock_aws
def test_pep_lambda_extract():
    # Setup mock S3
    os.environ['COMPLIANCE_LAKE_BUCKET'] = 'test-bucket'
    os.environ['PEP_URL'] = 'https://mock-url.com/data.json'

    s3 = boto3.client('s3', region_name='us-east-1')
    s3.create_bucket(Bucket='test-bucket')

    # Mock de la respuesta HTTP para evitar el 404 y descargas reales
    with patch('urllib3.PoolManager.request') as mock_request:
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.data = json.dumps([{"id": "1", "name": "JUAN PEREZ"}]).encode('utf-8')
        mock_request.return_value = mock_response

        # Execute Lambda Handler
        response = socrata_pep_handler({}, None)

    # Assert
    assert response['status'] == 'success'
    assert response['source'] == 'pep'
    
    # Verificar que el archivo se subió a S3
    objects = s3.list_objects(Bucket='test-bucket')
    assert 'landing/listas/pep/' in objects['Contents'][0]['Key']
