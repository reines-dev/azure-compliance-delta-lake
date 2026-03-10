import awswrangler as wr
import pandas as pd

path = "s3://reinesdev-compliance-lake-prd/gold/listas/"
print("Listing Gold Layer partitions and sampling one record per source...")
try:
    df = wr.s3.read_parquet(path=path, dataset=True)
    sources = df['fuente'].unique().tolist()
    print(f"\nActive sources: {sources}\n")
    for src in sorted(sources):
        sample = df[df['fuente'] == src].head(1)
        nombre = sample.iloc[0]['nombre_original']
        tipo = sample.iloc[0]['tipo_lista']
        print(f"[{src:<20}] ({tipo}) -> Sample: '{nombre}'")
except Exception as e:
    print(f"Error: {e}")
