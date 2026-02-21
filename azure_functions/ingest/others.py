import os
import pandas as pd
import requests
import io
import logging
from dotenv import load_dotenv

load_dotenv()

def download_generic_list(source_name) -> pd.DataFrame:
    """
    Descarga listas genéricas basadas en variables de entorno.
    Soporta: UE, DEA, LPB, IRAQ.
    """
    url_env_var = f"{source_name.upper()}_LIST_URL"
    url = os.getenv(url_env_var)
    
    if not url:
        logging.warning(f"No URL found for {source_name}. Returning empty sample.")
        return pd.DataFrame([
            {"id_fuente": f"{source_name}-001", "nombre_raw": f"SAMPLE {source_name} NAME", "tipo_entidad": "Generic", "remarks": "Automated Sample"}
        ])

    logging.info(f"Downloading {source_name} list from {url}")
    try:
        response = requests.get(url, timeout=30)
        if response.status_code == 200:
            # Intentar leer como CSV por defecto
            df = pd.read_csv(io.StringIO(response.text))
            
            # Mapeo básico de columnas (esto debería refinarse por fuente)
            # Buscamos columnas que se parezcan a 'name', 'id', 'remarks'
            df_res = pd.DataFrame()
            df_res['nombre_raw'] = df.iloc[:, 1] if len(df.columns) > 1 else df.iloc[:, 0]
            df_res['id_fuente'] = df.iloc[:, 0].astype(str)
            df_res['tipo_entidad'] = source_name
            df_res['remarks'] = "Sourced from " + source_name
            return df_res
        else:
            raise Exception(f"HTTP {response.status_code}")
    except Exception as e:
        logging.error(f"Error downloading {source_name}: {e}")
        # Retornamos datos de prueba para no romper el flujo
        return pd.DataFrame([{"id_fuente": "ERR", "nombre_raw": f"ERROR_{source_name}", "tipo_entidad": "N/A", "remarks": str(e)}])
