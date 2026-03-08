import boto3, json

s3 = boto3.client('s3')
bucket = "reinesdev-compliance-lake-prd"
key = "landing/listas/pep/fecha_carga=2026-03-08/pep_colombia.json"
obj = s3.get_object(Bucket=bucket, Key=key)
raw = json.loads(obj['Body'].read())

print("Type:", type(raw).__name__)
if isinstance(raw, dict):
    print("Keys:", list(raw.keys()))
    for k, v in raw.items():
        print(f"  {k}: {type(v).__name__}")
elif isinstance(raw, list):
    print("First record keys:", list(raw[0].keys())[:10] if raw else "empty")
    print("Sample record:", json.dumps(raw[0], ensure_ascii=False)[:300])
