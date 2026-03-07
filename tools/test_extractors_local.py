import os
import boto3
import json
from moto import mock_aws
import sys

# Agregar la raíz del proyecto al path para encontrar las lambdas
sys.path.append(os.getcwd())

from lambdas.ofac_handler import ofac_handler
from lambdas.onu_handler import onu_handler
from lambdas.sat_handler import sat69b_handler
from lambdas.pep_handler import socrata_pep_handler
from lambdas.opensanctions_handler import opensanctions_proxy_handler

@mock_aws
def test_extractors():
    print("=== Iniciando Pruebas Locales de Extractores ===")
    
    # 1. Setup Mock AWS
    bucket_name = "local-compliance-lake"
    os.environ['COMPLIANCE_LAKE_BUCKET'] = bucket_name
    os.environ['AWS_DEFAULT_REGION'] = "us-east-1"
    
    # Credenciales de Socrata para la prueba
    os.environ['DATOS_GOV_KEY_ID'] = "d6if00d6bulczelcxwh1ofa05"
    os.environ['DATOS_GOV_API_KEY'] = "2we7eyfg1mz7xo1o0bwio1dmva730c4r0m1e958iiwxp60bl4m"
    
    s3 = boto3.client('s3', region_name='us-east-1')
    s3.create_bucket(Bucket=bucket_name)
    print(f"Bucket mock '{bucket_name}' creado.")

    extractors = [
        ("OFAC", ofac_handler, {}),
        ("ONU", onu_handler, {}),
        ("SAT 69B", sat69b_handler, {}),
        ("PEP (Socrata)", socrata_pep_handler, {}),
        ("OpenSanctions (FBI)", opensanctions_proxy_handler, {"source_id": "us_fbi_most_wanted"})
    ]

    for name, handler, event in extractors:
        print(f"\nProbando extractor: {name}...")
        try:
            result = handler(event, None)
            if result['status'] == 'success':
                print(f"  [OK] Exitoso. Bytes: {result.get('records_bytes', 'N/A')}")
                # Verificar que el archivo existe en el bucket mock
                key = result['landing_path'].replace(f"s3://{bucket_name}/", "")
                s3.head_object(Bucket=bucket_name, Key=key)
                print(f"  [OK] Archivo verificado en S3: {key}")
            else:
                print(f"  [FALLO] El status no fue success: {result}")
        except Exception as e:
            print(f"  [ERROR] Excepción ejecutando {name}: {str(e)}")

if __name__ == "__main__":
    test_extractors()
