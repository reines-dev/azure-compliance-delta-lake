import pandas as pd
from src.etl.ingest import download_interpol_list

def test_download_interpol_list():
    # Execute
    df = download_interpol_list()
    
    # Assert
    assert isinstance(df, pd.DataFrame)
    if not df.empty:
        assert "id_fuente" in df.columns
        assert "nombre_raw" in df.columns
        print(f"✅ Interpol list ingested successfully with {len(df)} records.")
    else:
        print("⚠️ Interpol list is empty or API unavailable.")

if __name__ == "__main__":
    test_download_interpol_list()
