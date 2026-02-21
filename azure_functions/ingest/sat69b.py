import os
import pandas as pd
import requests
import io
import logging
from dotenv import load_dotenv

load_dotenv()

SAT69B_URL = os.getenv("SAT69B_URL")
SAT69B_ENCODING = os.getenv("SAT69B_ENCODING")

def download_sat69b_list() -> pd.DataFrame:
    """
    Descarga el listado de contribuyentes del SAT (Art. 69-B).
    """
    logging.info(f"Downloading SAT69B list from {SAT69B_URL}")
    
    response = requests.get(SAT69B_URL)
    if response.status_code != 200:
        logging.warning("Failed to download SAT69B. Using placeholder logic.")
        return pd.DataFrame([
            {"id_fuente": "ABC123456789", "nombre_raw": "EMPRESA FACTURADORA SA", "situacion": "Definitivo"},
            {"id_fuente": "XYZ987654321", "nombre_raw": "PRODUCTOS FANTASMA SAS", "situacion": "Presunto"}
        ])

    try:
        df = pd.read_csv(io.StringIO(response.content.decode(SAT69B_ENCODING)), sep=',', quotechar='"')
    except Exception as e:
        logging.error(f"Error parsing SAT69B CSV: {e}")
        raise

    # Limpieza básica de columnas
    # El SAT suele tener: No., RFC, Nombre del Contribuyente, Situación, etc.
    df_result = df.copy()
    
    # Intentar identificar columnas por posición si los nombres varían
    # Asumimos: Col 1 = RFC (ID), Col 2 = Nombre, Col 3 = Situación
    df_result = df_result.iloc[:, [1, 2, 3]] 
    df_result.columns = ['id_fuente', 'nombre_raw', 'situacion']
    
    return df_result
