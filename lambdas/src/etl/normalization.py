import re
import unicodedata

def normalize_name(name) -> str:
    """
    Normaliza nombres y razones sociales:
    - Conversión a mayúsculas.
    - Eliminación de acentos.
    - Eliminación de caracteres especiales.
    - Eliminación de 'stop words' corporativas (S.A., SAS, LLC, etc.).
    """
    if not name or not isinstance(name, str):
        return ""

    # 1. Convertir a mayúsculas
    name = name.upper()

    # 2. Eliminar acentos
    name = ''.join(
        c for c in unicodedata.normalize('NFD', name)
        if unicodedata.category(c) != 'Mn'
    )

    # 3. Eliminar caracteres especiales (mantener solo letras, números y espacios)
    name = re.sub(r'[^A-Z0-9\s]', '', name)

    # 4. Eliminar "stop words" corporativas comunes
    stop_words = [
        r'\bS\s?A\b', r'\bS\s?A\s?S\b', r'\bL\s?L\s?C\b', r'\bINC\b', 
        r'\bCORP\b', r'\bS\s?R\s?L\b', r'\bLTDA\b', r'\bCO\b', r'\bPLC\b'
    ]
    for word in stop_words:
        name = re.sub(word, '', name)

    # 5. Limpiar espacios extras
    name = re.sub(r'\s+', ' ', name).strip()

    return name
