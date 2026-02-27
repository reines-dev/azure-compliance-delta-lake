import json
from datetime import datetime
import pandas as pd
from src.core.config import get_settings
from src.etl.normalization import normalize_name
from src.services.storage import StorageService
from src.etl.ingest import download_ofac_list, download_sat69b_list, download_un_list, download_generic_list

def execute_ingest(source: str, storage: StorageService):
    if source == "ofac":
        df = download_ofac_list()
    elif source == "sat69b":
        df = download_sat69b_list()
    elif source == "onu":
        df = download_un_list()
    else:
        df = download_generic_list(source)
    
    path = storage.save_bronze(df, source)
    return {"status": "success", "source": source, "path": path, "records": len(df)}

def execute_transform(source: str, storage: StorageService):
    df = storage.read_bronze(source)
    
    if df.empty:
        return {"status": "error", "message": "Empty Bronze data"}
        
    df_unified = pd.DataFrame()
    id_col = 'id_fuente' if 'id_fuente' in df.columns else df.columns[0]
    df_unified['id_unico'] = df[id_col].astype(str) + f"_{source.upper()}"
    df_unified['nombre_original'] = df['nombre_raw']
    df_unified['nombre_limpio'] = df['nombre_raw'].apply(normalize_name)
    df_unified['fuente'] = source.upper()
    df_unified['tipo_lista'] = "Sanciones" if source in ["onu", "ofac", "ue", "iraq"] else "Restrictiva"
    df_unified['fecha_carga'] = datetime.utcnow().isoformat()
    
    df_unified['metadata'] = df.apply(lambda x: json.dumps({
        "tipo_original": x.get("tipo_entidad", "N/A"), 
        "info_adicional": x.get("remarks", "") or x.get("situacion", "")
    }), axis=1)

    path = storage.save_silver(df_unified, source)
    return {"status": "success", "source": source, "path": path}

def execute_load(source: str, storage: StorageService):
    df_silver = storage.read_silver(source)
    
    if df_silver.empty:
         return {"status": "error", "message": "Empty Silver data"}

    path = storage.write_gold_delta(df_silver, source)
    return {"status": "success", "source": source, "path": path}
