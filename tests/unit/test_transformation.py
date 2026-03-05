import pytest
import json
import pandas as pd
import hashlib
from datetime import datetime
from src.etl.normalization import normalize_name

def transform_mock_logic(df, source):
    """
    Réplica mockup de la lógica de transformación PySpark usada en AWS Glue.
    (El test real e2e pasará por Glue en AWS)
    """
    df_unified = pd.DataFrame()
    
    # Simula el md5(concat_ws("-", fuente, id)) de Glue
    def _md5_id(id_val):
        s = f"{source.upper()}-{id_val}"
        return hashlib.md5(s.encode('utf-8')).hexdigest()
        
    df_unified['id_unico'] = df['id_fuente'].apply(lambda x: _md5_id(str(x)))
    df_unified['nombre_original'] = df['nombre_raw']
    df_unified['nombre_limpio'] = df['nombre_raw'].apply(normalize_name)
    df_unified['fuente'] = source.upper()
    
    # Tipos de lista simplificados en PySpark script para ONU, OFAC, etc.
    if source in ["onu", "ofac", "ue", "iraq", "fbi"]:
        df_unified['tipo_lista'] = f"{source.upper()}_SANCIONES"
    elif source == "pep":
        df_unified['tipo_lista'] = "PEP_COLOMBIA"
    elif source == "sat69b":
         df_unified['tipo_lista'] = "SAT69B_RESTRICTIVA"
    else:
        df_unified['tipo_lista'] = "GENERAL"
    
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
    raw_data = [{"id_fuente": "123", "nombre_raw": "TEST NAME", "tipo_entidad": "Individual", "Remarks": "None"}]
    df = pd.DataFrame(raw_data)
    result = transform_mock_logic(df, "ofac")
    
    expected_md5 = hashlib.md5("OFAC-123".encode('utf-8')).hexdigest()
    assert result.iloc[0]['id_unico'] == expected_md5
    assert result.iloc[0]['nombre_limpio'] == "TEST NAME"
    assert result.iloc[0]['tipo_lista'] == "OFAC_SANCIONES"
    assert "tipo_entidad" in json.loads(result.iloc[0]['metadata'])

def test_sat69b_transformation():
    raw_data = [{"id_fuente": "RFC123", "nombre_raw": "EMPRESA S.A.", "situacion": "Definitivo"}]
    df = pd.DataFrame(raw_data)
    result = transform_mock_logic(df, "sat69b")
    
    expected_md5 = hashlib.md5("SAT69B-RFC123".encode('utf-8')).hexdigest()
    assert result.iloc[0]['id_unico'] == expected_md5
    assert result.iloc[0]['nombre_limpio'] == "EMPRESA SA" # Asumiendo normalize_name quita puntos
    assert result.iloc[0]['tipo_lista'] == "SAT69B_RESTRICTIVA"
    assert json.loads(result.iloc[0]['metadata'])["situacion"] == "Definitivo"

def test_pep_transformation():
    raw_data = [{"id_fuente": "123456", "nombre_raw": "JUAN PEREZ", "tipo_entidad": "Individual", "remarks": "PEP Cargo"}]
    df = pd.DataFrame(raw_data)
    result = transform_mock_logic(df, "pep")
    
    expected_md5 = hashlib.md5("PEP-123456".encode('utf-8')).hexdigest()
    assert result.iloc[0]['id_unico'] == expected_md5
    assert result.iloc[0]['nombre_limpio'] == "JUAN PEREZ"
    assert result.iloc[0]['tipo_lista'] == "PEP_COLOMBIA"
