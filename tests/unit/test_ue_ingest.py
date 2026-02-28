import pandas as pd
from src.etl.ingest import download_ue_list

def test_download_ue_list():
    # Execute
    df = download_ue_list()
    
    # Assert
    assert isinstance(df, pd.DataFrame)
    if not df.empty:
        assert "id_fuente" in df.columns
        assert "nombre_raw" in df.columns
        assert "tipo_entidad" in df.columns
        assert "remarks" in df.columns
        print(f"✅ UE list ingested successfully with {len(df)} records.")
    else:
        print("⚠️ UE list is empty or service unavailable.")

if __name__ == "__main__":
    test_download_ue_list()
