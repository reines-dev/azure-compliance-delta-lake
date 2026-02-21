import os
import json
import re
import logging
from fastapi import FastAPI, HTTPException, Query
from deltalake import DeltaTable
from rapidfuzz import process, fuzz
from shared.normalization import normalize_name
from dotenv import load_dotenv
import pandas as pd

load_dotenv()

app = FastAPI(
    title="Compliance Search API",
    description="API para consulta de listas restrictivas (OFAC, SAT69B, ONU) con Fuzzy Matching"
)

def get_storage_config():
    """
    Configura las opciones de almacenamiento para Delta Lake.
    """
    conn_str = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
    if conn_str:
        # Extraer credenciales para el motor de Rust (delta-rs)
        acc_name = re.search(r"AccountName=([^;]+)", conn_str).group(1)
        acc_key = re.search(r"AccountKey=([^;]+)", conn_str).group(1)
        
        # Inyectar en el entorno para el driver interno
        os.environ["AZURE_STORAGE_ACCOUNT"] = acc_name
        os.environ["AZURE_STORAGE_KEY"] = acc_key
        
        return {
            "azure_storage_account_name": acc_name,
            "azure_storage_account_key": acc_key,
            "azure_storage_use_managed_identity": "false"
        }
    return {"azure_storage_use_managed_identity": "true"}

DEFAULT_THRESHOLD = float(os.getenv("DEFAULT_SEARCH_THRESHOLD", "85.0"))
DEFAULT_LIMIT = int(os.getenv("DEFAULT_SEARCH_LIMIT", "5"))

@app.get("/health")
def health_check():
    return {"status": "healthy", "timestamp": pd.Timestamp.now().isoformat()}

@app.get("/check-name")
def check_name(
    name: str = Query(..., description="Nombre o razon social a consultar"),
    threshold: float = Query(DEFAULT_THRESHOLD, description="Umbral de coincidencia (0-100)"),
    source: str = Query(None, description="Filtrar por fuente (ej: OFAC, ONU)"),
    limit: int = Query(DEFAULT_LIMIT, description="Numero maximo de resultados")
):
    try:
        clean_name = normalize_name(name)
        if not clean_name:
            return {"query": name, "match_found": False, "results": []}

        delta_path = os.getenv("DELTA_TABLE_PATH")
        
        # Leer la tabla Delta
        dt = DeltaTable(delta_path, storage_options=get_storage_config())
        df = dt.to_pandas()

        if df.empty:
            return {"query": name, "match_found": False, "results": []}

        if source:
            df = df[df['fuente'].str.upper() == source.upper()]

        # Fuzzy Matching
        results = process.extract(
            clean_name, 
            df['nombre_limpio'], 
            scorer=fuzz.WRatio, 
            limit=limit
        )

        matches = []
        for match_str, score, index in results:
            if score >= threshold:
                row = df.iloc[index]
                meta = row["metadata"]
                if isinstance(meta, str):
                    try: meta = json.loads(meta)
                    except: pass

                matches.append({
                    "nombre_original": row["nombre_original"],
                    "nombre_encontrado": match_str,
                    "fuente": row["fuente"],
                    "tipo_lista": row["tipo_lista"],
                    "score": round(score, 2),
                    "metadata": meta
                })

        return {
            "query": name,
            "clean_query": clean_name,
            "match_found": len(matches) > 0,
            "results": matches
        }

    except Exception as e:
        logging.error(f"API Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
