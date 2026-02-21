import os
import pandas as pd
from deltalake import write_deltalake
from dotenv import load_dotenv
import re

load_dotenv()

def load_to_gold():
    conn_str = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
    delta_path = os.getenv("DELTA_TABLE_PATH")
    base_path = os.getenv("BASE_STORAGE_PATH")
    
    acc_name = re.search(r"AccountName=([^;]+)", conn_str).group(1)
    acc_key = re.search(r"AccountKey=([^;]+)", conn_str).group(1)
    
    storage_options = {
        "azure_storage_account_name": acc_name,
        "azure_storage_account_key": acc_key
    }

    sources = ["ofac", "sat69b", "onu"]

    print("--- Iniciando Carga Final Atómica ---")

    for source in sources:
        try:
            print(f"Cargando {source.upper()}...")
            silver_path = os.path.join(base_path, f"silver/{source}_clean.parquet")
            df = pd.read_parquet(silver_path, storage_options={"connection_string": conn_str}, engine="pyarrow")
            
            # Usar predicate para sobreescribir solo la partición de la fuente actual
            write_deltalake(
                delta_path,
                df,
                mode="overwrite",
                partition_by=["fuente"],
                predicate=f"fuente = '{source.upper()}'",
                storage_options=storage_options
            )
            print(f"   OK: {len(df)} registros integrados.")
            
        except Exception as e:
            print(f"   ERROR en {source.upper()}: {e}")

if __name__ == "__main__":
    load_to_gold()
