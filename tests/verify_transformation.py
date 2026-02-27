import pandas as pd
import json
from datetime import datetime
from src.etl.normalization import normalize_name

def simulate_transformation(source, raw_data):
    print(f"\n--- Probando Transformación para fuente: {source.upper()} ---")
    df = pd.DataFrame(raw_data)
    
    df_unified = pd.DataFrame()
    df_unified['id_unico'] = df['id_fuente'].astype(str) + f"_{source.upper()}"
    df_unified['nombre_original'] = df['nombre_raw']
    df_unified['nombre_limpio'] = df['nombre_raw'].apply(normalize_name)
    df_unified['fuente'] = source.upper()
    df_unified['tipo_lista'] = "Restrictive" if source == "sat69b" else "SDN"
    df_unified['fecha_carga'] = datetime.utcnow().isoformat()
    
    if source == "ofac":
        df_unified['metadata'] = df.apply(lambda x: json.dumps({
            "tipo_entidad": x.get("tipo_entidad"), 
            "remarks": x.get("Remarks")
        }), axis=1)
    elif source == "sat69b":
        df_unified['metadata'] = df.apply(lambda x: json.dumps({
            "situacion": x.get("situacion")
        }), axis=1)

    print(df_unified[['id_unico', 'nombre_original', 'nombre_limpio', 'fuente', 'metadata']].to_string(index=False))
    return df_unified

if __name__ == "__main__":
    ofac_raw = [
        {"id_fuente": "123", "nombre_raw": "SANTOS, Juan Manuel", "tipo_entidad": "Individual", "Remarks": "Alias: El Santo"},
        {"id_fuente": "456", "nombre_raw": "CARTEL DE LOS SOLES", "tipo_entidad": "Entity", "Remarks": "Sancionado en 2020"}
    ]
    
    sat_raw = [
        {"id_fuente": "SAT-999", "nombre_raw": "SERVICIOS INTEGRALES S.A. DE C.V.", "situacion": "Definitivo"},
        {"id_fuente": "SAT-888", "nombre_raw": "CONSULTORES FANTASMA S.A.S.", "situacion": "Presunto"}
    ]

    simulate_transformation("ofac", ofac_raw)
    simulate_transformation("sat69b", sat_raw)
