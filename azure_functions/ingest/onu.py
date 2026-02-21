import os
import pandas as pd
import requests
import xml.etree.ElementTree as ET
import io
import logging
from dotenv import load_dotenv

load_dotenv()

ONU_LIST_URL = os.getenv("ONU_LIST_URL", "https://scsanctions.un.org/resources/xml/en/consolidated.xml")

def download_un_list() -> pd.DataFrame:
    """
    Descarga la lista consolidada de sanciones de la ONU (XML).
    """
    logging.info(f"Downloading UN list from {ONU_LIST_URL}")
    response = requests.get(ONU_LIST_URL)
    if response.status_code != 200:
        logging.warning("Failed to download UN list. Using placeholder.")
        return pd.DataFrame([{"id_fuente": "UN-001", "nombre_raw": "AL-QAIDA", "tipo_entidad": "Group", "remarks": "Global Terrorist"}])

    # Parsear XML de la ONU
    root = ET.fromstring(response.content)
    records = []
    
    # La ONU divide en INDIVIDUALS y ENTITIES
    for ind in root.findall('.//INDIVIDUAL'):
        name = f"{ind.findtext('FIRST_NAME', '')} {ind.findtext('SECOND_NAME', '')} {ind.findtext('THIRD_NAME', '')}".strip()
        records.append({
            "id_fuente": ind.findtext('DATAID', 'N/A'),
            "nombre_raw": name,
            "tipo_entidad": "Individual",
            "remarks": ind.findtext('COMMENTS1', '')
        })
    
    for ent in root.findall('.//ENTITY'):
        records.append({
            "id_fuente": ent.findtext('DATAID', 'N/A'),
            "nombre_raw": ent.findtext('FIRST_NAME', ''),
            "tipo_entidad": "Entity",
            "remarks": ent.findtext('COMMENTS1', '')
        })
        
    return pd.DataFrame(records)
