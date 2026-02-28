import boto3
import os
from dotenv import load_dotenv

load_dotenv()
BUCKET = "reinesdev-compliance-lake-prd"

def clean_lake():
    print(f"🧹 Iniciando limpieza profunda del bucket: {BUCKET}")
    s3 = boto3.resource('s3')
    bucket = s3.Bucket(BUCKET)
    
    prefixes = ['bronze/', 'silver/', 'gold/']
    
    for prefix in prefixes:
        print(f"   Eliminando prefijo: {prefix}...")
        bucket.objects.filter(Prefix=prefix).delete()
    
    print("✅ Data Lake purgado exitosamente.")

if __name__ == "__main__":
    clean_lake()
