import boto3, io

s3 = boto3.client('s3')
obj = s3.get_object(Bucket='reinesdev-compliance-lake-prd', Key='landing/listas/sat/fecha_carga=2026-03-08/definitivo.csv')
content = obj['Body'].read().decode('latin-1', errors='replace')
print(f"File size: {len(content)} chars")
print("First 800 chars:")
print(content[:800])
