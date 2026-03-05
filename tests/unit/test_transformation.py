import pytest
import json
import pandas as pd
import hashlib
from datetime import datetime
from src.etl.normalization import normalize_name

def transform_mock_logic(df, source):
    """
    RÃ©plica mockup de la lÃ³gica de transformaciÃ³n PySpark usada en AWS Glue.
    """
    df_unified = pd.DataFrame()

    def _md5_id(id_val):
        s = f"{source.upper()}-{id_val}"
        return hashlib.md5(s.encode('utf-8')).hexdigest()

    df_unified['id_unico'] = df['id_fuente'].apply(lambda x: _md5_id(str(x)))
    df_unified['nombre_original'] = df['nombre_raw']
    df_unified['nombre_limpio'] = df['nombre_raw'].apply(normalize_name)
    df_unified['fuente'] = source.upper()

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
    else:
        df_unified['metadata'] = "{}"
        
    return df_unified

def test_ofac_transformation():
    raw_data = [{"id_fuente": "123", "nombre_raw": "TEST NAME", "tipo_entidad": "Individual", "Remarks": "None"}]
    df = pd.DataFrame(raw_data)
    result = transform_mock_logic(df, "ofac")

    expected_md5 = hashlib.md5("OFAC-123".encode('utf-8')).hexdigest()
    assert result.iloc[0]['id_unico'] == expected_md5
    assert result.iloc[0]['nombre_limpio'] == "TEST NAME"
    assert result.iloc[0]['tipo_lista'] == "OFAC_SANCIONES"

def test_sat69b_transformation():
    raw_data = [{"id_fuente": "RFC123", "nombre_raw": "EMPRESA S.A.", "situacion": "Definitivo"}]
    df = pd.DataFrame(raw_data)
    result = transform_mock_logic(df, "sat69b")

    expected_md5 = hashlib.md5("SAT69B-RFC123".encode('utf-8')).hexdigest()
    assert result.iloc[0]['id_unico'] == expected_md5
    # La lÃ³gica de normalizaciÃ³n elimina sufijos corporativos (S.A.)
    assert result.iloc[0]['nombre_limpio'] == "EMPRESA" 
    assert result.iloc[0]['tipo_lista'] == "SAT69B_RESTRICTIVA"

def test_pep_transformation():
    raw_data = [{"id_fuente": "123456", "nombre_raw": "JUAN PEREZ", "tipo_entidad": "Individual", "remarks": "PEP Cargo"}]
    df = pd.DataFrame(raw_data)
    result = transform_mock_logic(df, "pep")

    expected_md5 = hashlib.md5("PEP-123456".encode('utf-8')).hexdigest()
    assert result.iloc[0]['id_unico'] == expected_md5
    assert result.iloc[0]['nombre_limpio'] == "JUAN PEREZ"
    assert result.iloc[0]['tipo_lista'] == "PEP_COLOMBIA"
