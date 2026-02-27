import os
import pandas as pd
import requests
import io
import logging
import xml.etree.ElementTree as ET

def download_ofac_list() -> pd.DataFrame:
    OFAC_SDN_URL = os.getenv("OFAC_SDN_URL")
    OFAC_ALT_URL = os.getenv("OFAC_ALT_URL")
    
    resp_sdn = requests.get(OFAC_SDN_URL)
    sdn_cols = ["ent_num", "SDN_Name", "SDN_Type", "Program", "Title", "Call_Sign", "Vess_type", "Tonnage", "GRT", "vess_flag", "Vess_owner", "Remarks"]
    df_sdn = pd.read_csv(io.StringIO(resp_sdn.text), names=sdn_cols, index_col=False)
    
    resp_alt = requests.get(OFAC_ALT_URL)
    alt_cols = ["ent_num", "alt_num", "alt_type", "alt_name", "alt_remarks"]
    df_alt = pd.read_csv(io.StringIO(resp_alt.text), names=alt_cols, index_col=False)

    df_main = df_sdn[['ent_num', 'SDN_Name', 'SDN_Type', 'Remarks']].copy()
    df_main.rename(columns={'SDN_Name': 'nombre_raw', 'SDN_Type': 'tipo_entidad', 'Remarks': 'remarks'}, inplace=True)
    
    df_aliases = df_alt[['ent_num', 'alt_name', 'alt_type']].copy()
    df_aliases = df_aliases.merge(df_sdn[['ent_num', 'SDN_Type', 'Remarks']], on='ent_num', how='left')
    df_aliases.rename(columns={'alt_name': 'nombre_raw', 'SDN_Type': 'tipo_entidad', 'Remarks': 'remarks'}, inplace=True)
    df_aliases['remarks'] = df_aliases.apply(lambda x: f"Alias ({x['alt_type']}). " + str(x['remarks']), axis=1)
    
    df_final = pd.concat([df_main, df_aliases[['ent_num', 'nombre_raw', 'tipo_entidad', 'remarks']]], ignore_index=True)
    df_final.rename(columns={'ent_num': 'id_fuente'}, inplace=True)
    return df_final

def download_sat69b_list() -> pd.DataFrame:
    SAT69B_URL = os.getenv("SAT69B_URL")
    SAT69B_ENCODING = os.getenv("SAT69B_ENCODING", "latin1")
    
    response = requests.get(SAT69B_URL)
    if response.status_code != 200:
        return pd.DataFrame([{"id_fuente": "SAT-001", "nombre_raw": "EMPRESA MOCK", "situacion": "Definitivo"}])
    
    df = pd.read_csv(io.StringIO(response.content.decode(SAT69B_ENCODING)), sep=',', quotechar='"')
    df_result = df.iloc[:, [1, 2, 3]] 
    df_result.columns = ['id_fuente', 'nombre_raw', 'situacion']
    return df_result

def download_un_list() -> pd.DataFrame:
    ONU_URL = os.getenv("ONU_URL")
    response = requests.get(ONU_URL)
    root = ET.fromstring(response.content)
    records = []
    for ind in root.findall('.//INDIVIDUAL'):
        name = f"{ind.findtext('FIRST_NAME', '')} {ind.findtext('SECOND_NAME', '')} {ind.findtext('THIRD_NAME', '')}".strip()
        records.append({"id_fuente": ind.findtext('DATAID', 'N/A'), "nombre_raw": name, "tipo_entidad": "Individual", "remarks": ind.findtext('COMMENTS1', '')})
    for ent in root.findall('.//ENTITY'):
        records.append({"id_fuente": ent.findtext('DATAID', 'N/A'), "nombre_raw": ent.findtext('FIRST_NAME', ''), "tipo_entidad": "Entity", "remarks": ent.findtext('COMMENTS1', '')})
    return pd.DataFrame(records)

def download_generic_list(source_name) -> pd.DataFrame:
    url = os.getenv(f"{source_name.upper()}_LIST_URL")
    if not url:
        return pd.DataFrame([{"id_fuente": f"{source_name}-001", "nombre_raw": f"SAMPLE {source_name}", "tipo_entidad": "Generic", "remarks": "Sample"}])
    response = requests.get(url, timeout=30)
    df = pd.read_csv(io.StringIO(response.text))
    df_res = pd.DataFrame()
    df_res['nombre_raw'] = df.iloc[:, 1] if len(df.columns) > 1 else df.iloc[:, 0]
    df_res['id_fuente'] = df.iloc[:, 0].astype(str)
    df_res['tipo_entidad'] = source_name
    df_res['remarks'] = "Sourced from " + source_name
    return df_res
