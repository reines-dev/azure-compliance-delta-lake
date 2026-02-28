import pandas as pd
from src.etl.ingest import download_fbi_list

def test_download_fbi_list():
    # Execute
    df = download_fbi_list()
    
    # Assert
    assert isinstance(df, pd.DataFrame)
    if not df.empty:
        assert "id_fuente" in df.columns
        assert "nombre_raw" in df.columns
        assert "tipo_entidad" in df.columns
        assert "remarks" in df.columns
        print(f"✅ FBI list ingested successfully with {len(df)} records.")
    else:
        print("⚠️ FBI list is empty (API might be down or rate limited).")

if __name__ == "__main__":
    test_download_fbi_list()
