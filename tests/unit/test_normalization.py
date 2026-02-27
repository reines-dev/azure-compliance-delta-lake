import pytest
from src.etl.normalization import normalize_name

def test_normalize_basic_case():
    assert normalize_name("Empresa S.A.") == "EMPRESA"

def test_normalize_accents():
    assert normalize_name("Joaquín ÁvIla") == "JOAQUIN AVILA"

def test_normalize_corporate_suffixes():
    assert normalize_name("Tech Solutions S.A.S. S.A. LLC") == "TECH SOLUTIONS"

def test_normalize_special_characters():
    assert normalize_name("García & Hijos!! (2024)") == "GARCIA HIJOS 2024"

def test_normalize_empty():
    assert normalize_name("") == ""
    assert normalize_name(None) == ""

def test_normalize_whitespace():
    assert normalize_name("  Nombre   con   espacios  ") == "NOMBRE CON ESPACIOS"
