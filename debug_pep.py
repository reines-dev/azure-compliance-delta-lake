import awswrangler as wr
import pandas as pd

# Buscar Gustavo Petro en la partición PEP de Athena/S3
bucket = "reinesdev-compliance-lake-prd"
path = f"s3://{bucket}/gold/listas/"
print(f"Descargando tabla Gold desde {path}...")
try:
    df = wr.s3.read_parquet(
        path=path,
        dataset=True
    )
    df_pep = df[df['fuente'] == 'PEP']
    print(f"Total registros PEP en DB: {len(df_pep)}")
    
    # Buscar Petro
    petros = df_pep[df_pep['nombre_limpio'].str.contains('PETRO', case=False, na=False)]
    print(f"Encontrados en PEP parecidos a PETRO: {len(petros)}")
    if not petros.empty:
        print(petros[['nombre_original', 'nombre_limpio']].head(10).to_string())
    else:
        print("Misterio: No hay ningún Petro en PEP.")
except Exception as e:
    print(f"Error: {e}")
