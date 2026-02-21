import os
import azure.functions as func
import logging
import json
import pandas as pd
from datetime import datetime
from azure.identity import DefaultAzureCredential
from deltalake import write_deltalake
from shared.normalization import normalize_name
from azure_functions.ingest.ofac import download_ofac_list
from azure_functions.ingest.sat69b import download_sat69b_list
from azure_functions.ingest.onu import download_un_list
from azure_functions.ingest.others import download_generic_list
from dotenv import load_dotenv

load_dotenv()

app = func.FunctionApp()

def get_storage_options():
    conn_str = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
    if conn_str:
        return {"connection_string": conn_str}
    return {"azure_storage_use_managed_identity": "true"}

# --- ENDPOINT DE INGESTA DINÁMICO ---
@app.function_name(name="ingest_step")
@app.route(route="etl/ingest/{source}", methods=["POST"])
def ingest_step(req: func.HttpRequest) -> func.HttpResponse:
    source = req.route_params.get('source').lower()
    try:
        logging.info(f"Ingesting {source.upper()} list...")
        
        if source == "ofac":
            df_raw = download_ofac_list()
        elif source == "sat69b":
            df_raw = download_sat69b_list()
        elif source == "onu":
            df_raw = download_un_list()
        else:
            # Para UE, DEA, LPB, IRAQ usamos el descargador genérico
            df_raw = download_generic_list(source)
            
        path = os.path.join(os.getenv("BASE_STORAGE_PATH"), f"bronze/{source}_raw.parquet")
        df_raw.to_parquet(path, storage_options=get_storage_options())
        
        return func.HttpResponse(json.dumps({
            "status": f"Bronze {source.upper()} loaded", 
            "records": len(df_raw),
            "path": path
        }), status_code=200)
    except Exception as e:
        logging.error(f"Error in Ingest {source}: {str(e)}")
        return func.HttpResponse(str(e), status_code=500)

# --- ENDPOINT DE TRANSFORMACIÓN DINÁMICO ---
@app.function_name(name="transform_step")
@app.route(route="etl/transform/{source}", methods=["POST"])
def transform_step(req: func.HttpRequest) -> func.HttpResponse:
    source = req.route_params.get('source').lower()
    try:
        logging.info(f"Transforming {source.upper()} data...")
        bronze_path = os.path.join(os.getenv("BASE_STORAGE_PATH"), f"bronze/{source}_raw.parquet")
        df = pd.read_parquet(bronze_path, storage_options=get_storage_options())
        
        df_unified = pd.DataFrame()
        # Usamos la primera columna como ID si no existe id_fuente explícito
        id_col = 'id_fuente' if 'id_fuente' in df.columns else df.columns[0]
        df_unified['id_unico'] = df[id_col].astype(str) + f"_{source.upper()}"
        df_unified['nombre_original'] = df['nombre_raw']
        df_unified['nombre_limpio'] = df['nombre_raw'].apply(normalize_name)
        df_unified['fuente'] = source.upper()
        df_unified['tipo_lista'] = "Sanciones" if source in ["onu", "ofac", "ue", "iraq"] else "Restrictiva"
        df_unified['fecha_carga'] = datetime.utcnow().isoformat()
        
        # Metadata unificada (combina posibles columnas de remarks o situacion)
        df_unified['metadata'] = df.apply(lambda x: json.dumps({
            "tipo_original": x.get("tipo_entidad", "N/A"), 
            "info_adicional": x.get("remarks", "") or x.get("Remarks", "") or x.get("situacion", "")
        }), axis=1)

        silver_path = os.path.join(os.getenv("BASE_STORAGE_PATH"), f"silver/{source}_clean.parquet")
        df_unified.to_parquet(silver_path, storage_options=get_storage_options())
        
        return func.HttpResponse(json.dumps({"status": f"Silver {source.upper()} loaded", "path": silver_path}), status_code=200)
    except Exception as e:
        return func.HttpResponse(str(e), status_code=500)

# --- ENDPOINT DE CARGA (GOLD / DELTA LAKE) ---
@app.function_name(name="load_step")
@app.route(route="etl/load/{source}", methods=["POST"])
def load_step(req: func.HttpRequest) -> func.HttpResponse:
    source = req.route_params.get('source').lower()
    try:
        logging.info(f"Loading {source.upper()} to Delta Lake...")
        silver_path = os.path.join(os.getenv("BASE_STORAGE_PATH"), f"silver/{source}_clean.parquet")
        df_silver = pd.read_parquet(silver_path, storage_options=get_storage_options())
        
        # Carga final en Delta Lake con reemplazo selectivo por fuente
        write_deltalake(
            os.getenv("DELTA_TABLE_PATH"), 
            df_silver, 
            mode="overwrite", 
            partition_by=["fuente"], 
            predicate=f"fuente = '{source.upper()}'",
            storage_options=get_storage_options()
        )
        
        return func.HttpResponse(json.dumps({"status": f"Gold {source.upper()} loaded", "records": len(df_silver)}), status_code=200)
    except Exception as e:
        return func.HttpResponse(str(e), status_code=500)
