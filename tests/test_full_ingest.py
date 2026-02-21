import os
import pandas as pd
from dotenv import load_dotenv
from azure_functions.ingest.ofac import download_ofac_list
from azure_functions.ingest.sat69b import download_sat69b_list
from azure_functions.ingest.onu import download_un_list
from azure_functions.ingest.others import download_generic_list

load_dotenv()

def get_storage_options():
    conn_str = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
    if conn_str:
        return {"connection_string": conn_str}
    return {"azure_storage_use_managed_identity": "true"}

def test_ingest_all():
    base_path = os.getenv("BASE_STORAGE_PATH")
    storage_options = get_storage_options()

    print(f"--- Iniciando ingesta local ---")
    print(f"Destino: {base_path}")

    # OFAC
    try:
        print("Procesando OFAC...")
        df = download_ofac_list()
        path = os.path.join(base_path, "bronze/ofac_raw.parquet")
        df.to_parquet(path, storage_options=storage_options, engine="pyarrow")
        print(f"OK: {len(df)} registros.")
    except Exception as e:
        print(f"ERROR OFAC: {e}")

    # SAT69B
    try:
        print("Procesando SAT69B...")
        df = download_sat69b_list()
        path = os.path.join(base_path, "bronze/sat69b_raw.parquet")
        df.to_parquet(path, storage_options=storage_options, engine="pyarrow")
        print(f"OK: {len(df)} registros.")
    except Exception as e:
        print(f"ERROR SAT69B: {e}")

    # ONU
    try:
        print("Procesando ONU...")
        df = download_un_list()
        path = os.path.join(base_path, "bronze/onu_raw.parquet")
        df.to_parquet(path, storage_options=storage_options, engine="pyarrow")
        print(f"OK: {len(df)} registros.")
    except Exception as e:
        print(f"ERROR ONU: {e}")

if __name__ == "__main__":
    test_ingest_all()
