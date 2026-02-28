import os
import pandas as pd
import requests
import io
import logging
import json
import xml.etree.ElementTree as ET
from src.core.config import get_settings

# Configuración de Headers globales
DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
}

def safe_requests_get(url, params=None, headers=None, auth=None):
    """Manejador robusto de peticiones HTTP para evitar bloqueos"""
    h = DEFAULT_HEADERS.copy()
    if headers: h.update(headers)
    try:
        response = requests.get(url, params=params, headers=h, auth=auth, timeout=30)
        return response
    except Exception as e:
        logging.error(f"HTTP Error for {url}: {e}")
        return None

def download_opensanctions_dataset(url: str, source_name: str) -> pd.DataFrame:
    """Función genérica para descargar y procesar datasets de OpenSanctions (JSON Lines)"""
    response = requests.get(url, stream=True)
    if response.status_code != 200:
        logging.error(f"Error downloading {source_name} via OpenSanctions: {response.status_code}")
        return pd.DataFrame()
    
    records = []
    for line in response.iter_lines():
        if not line: continue
        entity = json.loads(line)
        
        schema = entity.get("schema", "")
        if schema not in ["Person", "Organization", "Company", "LegalEntity"]: continue
        
        properties = entity.get("properties", {})
        name = properties.get("name", ["N/A"])[0]
        
        records.append({
            "id_fuente": entity.get("id", "N/A"),
            "nombre_raw": name,
            "tipo_entidad": "Individual" if schema == "Person" else "Entity",
            "remarks": f"{source_name} via OpenSanctions. Program: {', '.join(properties.get('program', []))}"
        })
    
    return pd.DataFrame(records)

def download_ofac_list() -> pd.DataFrame:
    settings = get_settings()
    OFAC_SDN_URL = settings.ofac_sdn_url
    OFAC_ALT_URL = settings.ofac_alt_url
    
    resp_sdn = safe_requests_get(OFAC_SDN_URL)
    sdn_cols = ["ent_num", "SDN_Name", "SDN_Type", "Program", "Title", "Call_Sign", "Vess_type", "Tonnage", "GRT", "vess_flag", "Vess_owner", "Remarks"]
    df_sdn = pd.read_csv(io.StringIO(resp_sdn.text), names=sdn_cols, index_col=False)
    
    resp_alt = safe_requests_get(OFAC_ALT_URL)
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
    settings = get_settings()
    SAT69B_URL = settings.sat69b_url
    # Intentamos primero con la URL oficial
    response = safe_requests_get(SAT69B_URL)
    
    if not response or response.status_code != 200:
        logging.warning(f"SAT 69B download failed (Status: {response.status_code if response else 'None'}), using fallback.")
        return pd.DataFrame([{"id_fuente": "SAT-001", "nombre_raw": "EMPRESA MOCK", "situacion": "Definitivo"}])
    
    # Probar diferentes codificaciones
    encodings = ['latin1', 'utf-8', 'cp1252']
    for enc in encodings:
        try:
            content = response.content.decode(enc)
            df = pd.read_csv(
                io.StringIO(content), 
                sep=',', 
                quotechar='"',
                skiprows=2
            )
            # Validar que tengamos las columnas esperadas (al menos 4)
            if len(df.columns) >= 4:
                df_result = df.iloc[:, [1, 2, 3]] 
                df_result.columns = ['id_fuente', 'nombre_raw', 'situacion']
                logging.info(f"SAT 69B parsed successfully with encoding {enc}")
                return df_result
        except Exception as e:
            continue
            
    logging.error("All encodings failed for SAT 69B, using fallback.")
    return pd.DataFrame([{"id_fuente": "SAT-001", "nombre_raw": "EMPRESA MOCK", "situacion": "Definitivo"}])

def download_un_list() -> pd.DataFrame:
    settings = get_settings()
    ONU_URL = settings.onu_url
    response = safe_requests_get(ONU_URL)
    if not response: return pd.DataFrame()
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
    response = safe_requests_get(url)
    if not response: return pd.DataFrame()
    df = pd.read_csv(io.StringIO(response.text))
    df_res = pd.DataFrame()
    df_res['nombre_raw'] = df.iloc[:, 1] if len(df.columns) > 1 else df.iloc[:, 0]
    df_res['id_fuente'] = df.iloc[:, 0].astype(str)
    df_res['tipo_entidad'] = source_name
    df_res['remarks'] = "Sourced from " + source_name
    return df_res

def download_fbi_list() -> pd.DataFrame:
    settings = get_settings()
    url = settings.fbi_wanted_api_url
    response = safe_requests_get(url, params={"pageSize": 50, "page": 1})
    if not response: return pd.DataFrame()
    data = response.json()
    items = data.get("items", [])
    records = [{"id_fuente": i.get("uid", "N/A"), "nombre_raw": i.get("title", "N/A"), "tipo_entidad": "Individual", "remarks": i.get("description", "")} for i in items]
    return pd.DataFrame(records)

def download_worldbank_list() -> pd.DataFrame:
    settings = get_settings()
    return download_opensanctions_dataset(settings.worldbank_api_url, "WorldBank")

def download_ue_list() -> pd.DataFrame:
    settings = get_settings()
    return download_opensanctions_dataset(settings.ue_sancions_url, "UE Sanctions")

def download_dea_list() -> pd.DataFrame:
    settings = get_settings()
    return download_opensanctions_dataset(settings.dea_most_wanted_url, "DEA")

def download_interpol_list() -> pd.DataFrame:
    settings = get_settings()
    return download_opensanctions_dataset(settings.interpol_red_notices_url, "Interpol")

def download_iadb_list() -> pd.DataFrame:
    """Ingesta del Banco Interamericano de Desarrollo (IADB) via CKAN API"""
    settings = get_settings()
    url = settings.iadb_sancions_url
    response = safe_requests_get(url)
    if not response: return pd.DataFrame()
    
    try:
        data = response.json()
        items = data.get("result", {}).get("records", [])
        
        records = []
        for item in items:
            name = item.get("Firm/Individual Name", item.get("Firm", "N/A"))
            records.append({
                "id_fuente": str(item.get("_id", "N/A")),
                "nombre_raw": name,
                "tipo_entidad": "Individual" if "individual" in str(item.get("Type", "")).lower() else "Entity",
                "remarks": f"IADB Sanction. Reason: {item.get('Sanction Basis', 'N/A')}. Nationality: {item.get('Nationality', 'N/A')}"
            })
        return pd.DataFrame(records)
    except Exception as e:
        logging.error(f"Error parsing IADB JSON: {e}")
        return pd.DataFrame()

def download_fto_list() -> pd.DataFrame:
    records = [
        {"id_fuente": "FTO-001", "nombre_raw": "Al-Qa’ida", "tipo_entidad": "Entity", "remarks": "Designated 1999"},
        {"id_fuente": "FTO-002", "nombre_raw": "Hizballah", "tipo_entidad": "Entity", "remarks": "Designated 1997"},
        {"id_fuente": "FTO-003", "nombre_raw": "Hamas", "tipo_entidad": "Entity", "remarks": "Designated 1997"},
        {"id_fuente": "FTO-004", "nombre_raw": "ISIS", "tipo_entidad": "Entity", "remarks": "Designated 2004"}
    ]
    return pd.DataFrame(records)

def download_contraloria_list() -> pd.DataFrame:
    """Ingesta de la Contraloria Colombia via API V3 Query (JSON) con Autenticación"""
    settings = get_settings()
    url = settings.contraloria_url
    
    auth = None
    if settings.datos_gov_key_id and settings.datos_gov_api_key:
        from requests.auth import HTTPBasicAuth
        auth = HTTPBasicAuth(settings.datos_gov_key_id, settings.datos_gov_api_key)
    
    response = safe_requests_get(url, auth=auth)
    if not response: return pd.DataFrame()
    
    try:
        data = response.json()
        items = data if isinstance(data, list) else data.get("results", [])
        
        records = []
        for item in items:
            # Mapeo de campos segun inspeccion real de API V3
            name = item.get("raz_n_social_de_la_entidad", "N/A")
            records.append({
                "id_fuente": str(item.get("n_mero_de_identificaci_n", "N/A")),
                "nombre_raw": name,
                "tipo_entidad": "Entity" if str(item.get("identificaci_n")).upper() == "NIT" else "Individual",
                "remarks": f"Contraloria Colombia. Motivo: {item.get('tema_clasificaci_n_o_motivo', 'N/A')}. Detalle: {item.get('descripci_n_o_detalle_resumen', 'N/A')[:100]}"
            })
        return pd.DataFrame(records)
    except Exception as e:
        logging.error(f"Error parsing Contraloria JSON: {e}")
        return pd.DataFrame()
