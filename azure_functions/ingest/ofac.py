import os
import pandas as pd
import requests
import io
import logging
from dotenv import load_dotenv

load_dotenv()

OFAC_SDN_URL = os.getenv("OFAC_SDN_URL")
OFAC_ALT_URL = os.getenv("OFAC_ALT_URL")

def download_ofac_list() -> pd.DataFrame:
    """
    Descarga y consolida la lista SDN y sus Alias (ALT) de la OFAC.
    """
    logging.info("Downloading OFAC SDN and ALT lists...")
    
    # 1. Descargar SDN (Entidades principales)
    resp_sdn = requests.get(OFAC_SDN_URL)
    if resp_sdn.status_code != 200:
        raise Exception(f"Failed to download SDN list: {resp_sdn.status_code}")
    
    sdn_cols = ["ent_num", "SDN_Name", "SDN_Type", "Program", "Title", "Call_Sign", "Vess_type", "Tonnage", "GRT", "vess_flag", "Vess_owner", "Remarks"]
    df_sdn = pd.read_csv(io.StringIO(resp_sdn.text), names=sdn_cols, index_col=False)
    
    # 2. Descargar ALT (Alias / A.K.A)
    resp_alt = requests.get(OFAC_ALT_URL)
    if resp_alt.status_code != 200:
        logging.warning("Failed to download ALT list. Proceeding with SDN only.")
        df_alt = pd.DataFrame(columns=["ent_num", "alt_name", "alt_type"])
    else:
        alt_cols = ["ent_num", "alt_num", "alt_type", "alt_name", "alt_remarks"]
        df_alt = pd.read_csv(io.StringIO(resp_alt.text), names=alt_cols, index_col=False)

    # 3. Preparar SDN como registros base
    df_main = df_sdn[['ent_num', 'SDN_Name', 'SDN_Type', 'Remarks']].copy()
    df_main.rename(columns={'SDN_Name': 'nombre_raw', 'SDN_Type': 'tipo_entidad', 'Remarks': 'remarks'}, inplace=True)
    
    # 4. Preparar ALT como registros adicionales
    # Cruzamos con SDN para obtener el tipo de entidad y los remarks originales
    df_aliases = df_alt[['ent_num', 'alt_name', 'alt_type']].copy()
    df_aliases = df_aliases.merge(df_sdn[['ent_num', 'SDN_Type', 'Remarks']], on='ent_num', how='left')
    df_aliases.rename(columns={'alt_name': 'nombre_raw', 'SDN_Type': 'tipo_entidad', 'Remarks': 'remarks'}, inplace=True)
    
    # Añadimos el tipo de alias a los remarks
    df_aliases['remarks'] = df_aliases.apply(lambda x: f"Alias ({x['alt_type']}). " + str(x['remarks']), axis=1)
    
    # 5. Consolidar todo en un solo DataFrame
    df_final = pd.concat([df_main, df_aliases[['ent_num', 'nombre_raw', 'tipo_entidad', 'remarks']]], ignore_index=True)
    
    # Renombrar para el flujo ETL estándar
    df_final.rename(columns={'ent_num': 'id_fuente'}, inplace=True)
    
    logging.info(f"Consolidated OFAC list: {len(df_final)} entries (Main + Aliases).")
    return df_final
