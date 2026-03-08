import awswrangler as wr
import json

# Read the raw Socrata PEP JSON from S3 Landing
bucket = "reinesdev-compliance-lake-prd"
key = "landing/listas/pep/fecha_carga=2026-03-08/pep_colombia.json"
import boto3, io
s3 = boto3.client('s3')
obj = s3.get_object(Bucket=bucket, Key=key)
raw = obj['Body'].read()
data = json.loads(raw)

print("Type:", type(data))
if isinstance(data, dict):
    print("Top-level keys:", list(data.keys()))
    for k, v in data.items():
        print(f"  {k}: {type(v).__name__}")
elif isinstance(data, list):
    print("List length:", len(data))
    print("First record keys:", list(data[0].keys()) if data else "empty")
