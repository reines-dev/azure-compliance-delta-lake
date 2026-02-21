import pytest
import json
import pandas as pd
from datetime import datetime
from shared.normalization import normalize_name

def transform_logic(df, source):
    """Réplica de la lógica de transformación para pruebas."""
    df_unified = pd.DataFrame()
    df_unified['id_unico'] = df['id_fuente'].astype(str) + f"_{source.upper()}"
    df_unified['nombre_original'] = df['nombre_raw']
    df_unified['nombre_limpio'] = df['nombre_raw'].apply(normalize_name)
    df_unified['fuente'] = source.upper()
    df_unified['tipo_lista'] = "Restrictive" if source == "sat69b" else "SDN"
    
    if source == "ofac":
        df_unified['metadata'] = df.apply(lambda x: json.dumps({
            "tipo_entidad": x.get("tipo_entidad"), 
            "remarks": x.get("Remarks")
        }), axis=1)
    elif source == "sat69b":
        df_unified['metadata'] = df.apply(lambda x: json.dumps({
            "situacion": x.get("situacion")
        }), axis=1)
    return df_unified

def test_ofac_transformation():
    raw_data = [{"id_fuente": "1", "nombre_raw": "TEST NAME", "tipo_entidad": "Individual", "Remarks": "None"}]
    df = pd.DataFrame(raw_data)
    result = transform_logic(df, "ofac")
    
    assert result.iloc[0]['id_unico'] == "1_OFAC"
    assert result.iloc[0]['nombre_limpio'] == "TEST NAME"
    assert "tipo_entidad" in json.loads(result.iloc[0]['metadata'])

def test_sat69b_transformation():
    raw_data = [{"id_fuente": "RFC123", "nombre_raw": "EMPRESA S.A.", "situacion": "Definitivo"}]
    df = pd.DataFrame(raw_data)
    result = transform_logic(df, "sat69b")
    
    assert result.iloc[0]['id_unico'] == "RFC123_SAT69B"
    assert result.iloc[0]['nombre_limpio'] == "EMPRESA"
    assert json.loads(result.iloc[0]['metadata'])["situacion"] == "Definitivo"
