import os
import requests
import json
import pandas as pd
from src.services.storage import StorageService

LAKE_BUCKET = "reinesdev-compliance-lake-prd"
DELTA_PATH = "s3://reinesdev-compliance-lake-prd/gold/listas"
API_URL = "https://9m9yj00e81.execute-api.us-east-1.amazonaws.com/prod"
WB_URL = "https://data.opensanctions.org/datasets/latest/wb_debarred/targets.nested.json"

def sync_wb():
    print("🚀 Sincronizando Banco Mundial (Dataset Específico)...")
    storage = StorageService(LAKE_BUCKET, DELTA_PATH)
    
    try:
        resp = requests.get(WB_URL, timeout=60)
        if resp.status_code != 200:
            print(f"❌ Error: {resp.status_code}")
            return

        lines = resp.text.strip().splitlines()
        records = []
        for line in lines:
            if not line: continue
            entity = json.loads(line)
            props = entity.get("properties", {})
            name = props.get("name", ["N/A"])[0]
            
            records.append({
                "id_fuente": entity.get("id", "N/A"),
                "nombre_raw": name,
                "tipo_entidad": "Individual" if entity.get("schema") == "Person" else "Entity",
                "remarks": f"World Bank Debarred. Reason: {', '.join(props.get('notes', []))}"
            })

        df = pd.DataFrame(records)
        print(f"✅ {len(df)} registros encontrados.")
        storage.save_parquet(df, "bronze/worldbank.parquet")
        print("📤 Subido a S3.")
        requests.post(f"{API_URL}/etl/transform/worldbank")
        requests.post(f"{API_URL}/etl/load/worldbank")
        print("✨ AWS Sincronizado.")

    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    sync_wb()
