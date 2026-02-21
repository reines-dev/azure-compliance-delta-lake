import os
import pandas as pd
import json
from datetime import datetime
from dotenv import load_dotenv
from shared.normalization import normalize_name

load_dotenv()

def get_storage_options():
    conn_str = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
    if conn_str:
        return {"connection_string": conn_str}
    return {"azure_storage_use_managed_identity": "true"}

def transform_all():
    base_path = os.getenv("BASE_STORAGE_PATH")
    storage_options = get_storage_options()
    sources = ["ofac", "sat69b", "onu"]

    print("--- Iniciando Transformacion (Bronze -> Silver) ---")
    print(f"Base Path: {base_path}")

    for source in sources:
        try:
            print(f"Transformando fuente: {source.upper()}...")
            
            # 1. Leer de Bronze
            bronze_path = os.path.join(base_path, f"bronze/{source}_raw.parquet")
            df = pd.read_parquet(bronze_path, storage_options=storage_options, engine="pyarrow")
            
            # 2. Aplicar logica de transformacion
            df_unified = pd.DataFrame()
            
            # Identificar ID original (evitar errores de columna)
            id_col = 'id_fuente' if 'id_fuente' in df.columns else df.columns[0]
            df_unified['id_unico'] = df[id_col].astype(str) + f"_{source.upper()}"
            
            # Nombres y Normalizacion
            df_unified['nombre_original'] = df['nombre_raw']
            df_unified['nombre_limpio'] = df['nombre_raw'].apply(normalize_name)
            
            # Clasificacion
            df_unified['fuente'] = source.upper()
            df_unified['tipo_lista'] = "Sanciones" if source in ["onu", "ofac"] else "Restrictiva"
            df_unified['fecha_carga'] = datetime.utcnow().isoformat()
            
            # Metadata Dinamica
            def build_metadata(row):
                return json.dumps({
                    "tipo_original": row.get("tipo_entidad", "N/A"), 
                    "info_adicional": row.get("remarks", "") or row.get("Remarks", "") or row.get("situacion", "")
                })

            df_unified['metadata'] = df.apply(build_metadata, axis=1)

            # 3. Guardar en Silver
            silver_path = os.path.join(base_path, f"silver/{source}_clean.parquet")
            print(f"   Salvando {len(df_unified)} registros en {silver_path}...")
            df_unified.to_parquet(silver_path, storage_options=storage_options, engine="pyarrow")
            print(f"   OK: {source.upper()} transformado.")
            
        except Exception as e:
            print(f"   ERROR en {source.upper()}: {e}")

if __name__ == "__main__":
    transform_all()
