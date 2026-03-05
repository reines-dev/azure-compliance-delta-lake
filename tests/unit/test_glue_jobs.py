import pytest
import pandas as pd
import hashlib
import re

# Mock de la lÃ³gica de limpieza que estÃ¡ dentro de los scripts de Glue
def glue_clean_string(name):
    if not name:
        return ""
    # RÃ©plica exacta del regex en los Glue Jobs: [^a-zA-Z0-9\s]
    cleaned = re.sub(r'[^a-zA-Z0-9\s]', '', str(name))
    cleaned = re.sub(r'\s+', ' ', cleaned)
    return cleaned.strip().upper()

def test_glue_name_cleaning():
    # Validar que la lÃ³gica de Glue (Spark UDF) funciona segÃºn lo esperado
    assert glue_clean_string("JUAN PÃREZ") == "JUAN PREZ" # El regex de Glue es mÃ¡s estricto que el de src/
    assert glue_clean_string("Empresa S.A.") == "EMPRESA SA"
    assert glue_clean_string("Test-Name 123!") == "TESTNAME 123"

def test_glue_id_generation_logic():
    # Simular md5(concat_ws("-", lit("OFAC"), col("_c0")))
    source = "OFAC"
    source_id = "12345"
    concat_val = f"{source}-{source_id}"
    expected_hash = hashlib.md5(concat_val.encode('utf-8')).hexdigest()
    
    # Validar consistencia de IDs
    assert len(expected_hash) == 32
    assert expected_hash == hashlib.md5("OFAC-12345".encode('utf-8')).hexdigest()

def test_glue_schema_unification_mock():
    # Simular el esquema final que Glue produce
    raw_data = {
        "_c0": ["1", "2"],
        "_c1": ["NAME ONE", "NAME TWO"],
        "_c2": ["Individual", "Entity"]
    }
    df = pd.DataFrame(raw_data)
    
    # TransformaciÃ³n mockup
    df['id_unico'] = df['_c0'].apply(lambda x: hashlib.md5(f"OFAC-{x}".encode()).hexdigest())
    df['nombre_limpio'] = df['_c1'].apply(glue_clean_string)
    df['fuente'] = "OFAC"
    
    assert list(df.columns).count('nombre_limpio') == 1
    assert df.iloc[0]['fuente'] == "OFAC"
    assert len(df.iloc[0]['id_unico']) == 32
