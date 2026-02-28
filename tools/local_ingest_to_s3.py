import os
import requests
import pandas as pd
import boto3
from dotenv import load_dotenv
from src.etl import ingest
from src.services.storage import StorageService

# Cargar variables de entorno
load_dotenv()

# Configuración
LAKE_BUCKET = os.getenv("COMPLIANCE_LAKE_BUCKET", "reinesdev-compliance-lake-prd")
DELTA_PATH = os.getenv("DELTA_TABLE_PATH")
API_BASE_URL = "https://9m9yj00e81.execute-api.us-east-1.amazonaws.com/prod"

# Fuentes que suelen fallar desde AWS Lambda por bloqueos de IP
BLOCKED_SOURCES = ["worldbank", "ue", "dea", "interpol", "contraloria"]

def run_local_ingest():
    print(f"🚀 Iniciando Ingesta Local para fuentes bloqueadas en AWS...")
    print(f"📦 Destino: S3 Bucket {LAKE_BUCKET}")
    
    storage = StorageService(LAKE_BUCKET, DELTA_PATH)
    
    for source in BLOCKED_SOURCES:
        print(f"\n--- Procesando: {source.upper()} ---")
        try:
            # 1. Descarga Local
            print(f"[{source}] Descargando datos...", end=" ", flush=True)
            if source == "worldbank": df = ingest.download_worldbank_list()
            elif source == "ue": df = ingest.download_ue_list()
            elif source == "dea": df = ingest.download_dea_list()
            elif source == "interpol": df = ingest.download_interpol_list()
            elif source == "contraloria": df = ingest.download_contraloria_list()
            else: df = pd.DataFrame()
            
            if df.empty:
                print("❌ Fallo: Datos vacíos")
                continue
            
            print(f"✅ {len(df)} registros.")

            # 2. Subida Directa a S3
            key = f"bronze/{source}.parquet"
            print(f"[{source}] Subiendo a S3 ({key})...", end=" ", flush=True)
            storage.save_parquet(df, key)
            print("✅ OK")

            # 3. Disparar Transformación y Carga en la Nube
            print(f"[{source}] Disparando Transformación en AWS...", end=" ", flush=True)
            r_trans = requests.post(f"{API_BASE_URL}/etl/transform/{source}")
            print(f"✅ {r_trans.status_code}")

            print(f"[{source}] Disparando Carga Gold en AWS...", end=" ", flush=True)
            r_load = requests.post(f"{API_BASE_URL}/etl/load/{source}")
            print(f"✅ {r_load.status_code}")

        except Exception as e:
            print(f"❌ ERROR: {e}")

    print("\n✨ Proceso de sincronización finalizado.")
    print("🔄 Refrescando caché de la API...")
    requests.get(f"{API_BASE_URL}/check/", params={"name": "REFRESH", "refresh": "True"})

if __name__ == "__main__":
    run_local_ingest()
