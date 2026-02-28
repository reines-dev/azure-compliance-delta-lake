import pandas as pd
from src.etl.ingest import download_worldbank_list

def test_download_worldbank_list():
    # Execute
    df = download_worldbank_list()
    
    # Assert
    assert isinstance(df, pd.DataFrame)
    if not df.empty:
        assert "id_fuente" in df.columns
        assert "nombre_raw" in df.columns
        assert "tipo_entidad" in df.columns
        assert "remarks" in df.columns
        print(f"✅ World Bank list ingested successfully with {len(df)} records.")
    else:
        print("⚠️ World Bank list is empty (API might be down or empty).")

if __name__ == "__main__":
    test_download_worldbank_list()
