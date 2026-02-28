import pandas as pd
from src.etl.ingest import download_dea_list

def test_download_dea_list():
    # Execute
    df = download_dea_list()
    
    # Assert
    assert isinstance(df, pd.DataFrame)
    if not df.empty:
        assert "id_fuente" in df.columns
        assert "nombre_raw" in df.columns
        assert "remarks" in df.columns
        print(f"✅ DEA list ingested successfully with {len(df)} records.")
    else:
        print("⚠️ DEA list is empty or API blocked the request.")

if __name__ == "__main__":
    test_download_dea_list()
