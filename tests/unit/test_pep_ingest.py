import os
import json
import boto3
from moto import mock_s3
from cloud.aws.lambda_extract.pep_handler import socrata_pep_handler

@mock_s3
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
    assert 's3://test-bucket/landing/listas/pep/' in response['landing_path']
    assert response['records_bytes'] > 0
    
    # Verify S3 Object creation
    s3_key = response['landing_path'].replace('s3://test-bucket/', '')
    body = conn.get_object(Bucket='test-bucket', Key=s3_key)['Body'].read()
    assert len(body) == response['records_bytes']
    print("✅ PEP lambda extracted and saved raw metadata to Mock S3 Landing Zone successfully.")
    
if __name__ == "__main__":
    test_pep_lambda_extract()
