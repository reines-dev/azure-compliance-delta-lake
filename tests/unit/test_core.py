import pytest
from src.etl.normalization import normalize_name
from src.core.config import get_settings

def test_normalization_logic():
    # Casos base
    assert normalize_name("Empresa S.A.") == "EMPRESA"
    assert normalize_name("JUAN PÉREZ") == "JUAN PEREZ"
    # La lÃ³gica elimina sufijos como Co, Inc, LLC
    assert normalize_name("García & Co!!!") == "GARCIA"
    
    # Casos borde
    assert normalize_name("") == ""
    assert normalize_name(None) == ""
    assert normalize_name("   ") == ""

def test_settings_load():
    settings = get_settings()
    assert settings.compliance_lake_bucket is not None
    assert isinstance(settings.enable_docs, bool)
