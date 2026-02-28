import os
import requests
import json
import pandas as pd
from src.services.storage import StorageService
from dotenv import load_dotenv

# Forzar carga de variables antes de instanciar nada
load_dotenv()

# Configuración explícita para evitar errores de detección
LAKE_BUCKET = "reinesdev-compliance-lake-prd"
DELTA_PATH = "s3://reinesdev-compliance-lake-prd/gold/listas"
API_URL = "https://9m9yj00e81.execute-api.us-east-1.amazonaws.com/prod"
OS_URL = "https://data.opensanctions.org/datasets/latest/default/entities.ftm.json"

def ingest_worldbank_only():
    print("🚀 Iniciando Ingesta Optimizada del Banco Mundial...")
    
    # Instanciar con parámetros hardcoded para el script de herramientas
    storage = StorageService(LAKE_BUCKET, DELTA_PATH)
    print(f"📡 Modo AWS detectado: {storage.is_aws}")
    
    records = []
    print("📥 Descargando dataset global...")
    
    try:
        response = requests.get(OS_URL, stream=True, timeout=60)
        for line in response.iter_lines():
            if not line: continue
            entity = json.loads(line)
            
            # Filtro por mención de Banco Mundial
            props = entity.get("properties", {})
            program = " ".join(props.get("program", [])).lower()
            
            if "world bank" in program or "worldbank" in program:
                name = props.get("name", ["N/A"])[0]
                records.append({
                    "id_fuente": entity.get("id", "N/A"),
                    "nombre_raw": name,
                    "tipo_entidad": "Individual" if entity.get("schema") == "Person" else "Entity",
                    "remarks": f"World Bank Sanction via OpenSanctions. Program: {program}"
                })

        if not records:
            print("⚠️ No se encontraron registros en este fragmento.")
            return

        df = pd.DataFrame(records)
        print(f"✅ Total filtrado: {len(df)} registros.")

        # Subir a Bronze en S3
        key = "bronze/worldbank.parquet"
        print(f"📤 Subiendo a: {LAKE_BUCKET}/{key}...")
        storage.save_parquet(df, key)
        print("✅ Subida exitosa.")

        # Disparar Transform y Load en AWS
        print("⚙️ Disparando Transformación y Carga en AWS...")
        requests.post(f"{API_URL}/etl/transform/worldbank")
        requests.post(f"{API_URL}/etl/load/worldbank")
        
        print("✨ Proceso completado.")

    except Exception as e:
        print(f"❌ Error durante el proceso: {e}")

if __name__ == "__main__":
    ingest_worldbank_only()
