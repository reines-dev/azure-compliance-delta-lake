import logging
from src.services.storage import StorageService

logger = logging.getLogger(__name__)

def execute_ingest(source: str, storage: StorageService):
    """Lógica base de ingesta para la API"""
    logger.info(f"Ejecutando ingesta para fuente: {source}")
    # En esta arquitectura modular, la ingesta real la hacen las Lambdas
    # La API puede disparar validaciones o logs
    return {"status": "success", "source": source, "action": "ingest", "message": "Ingesta iniciada o validada"}

def execute_transform(source: str, storage: StorageService):
    """Lógica base de transformación"""
    logger.info(f"Ejecutando transformación para fuente: {source}")
    # Aquí iría la lógica de normalización pesada si no se usa Glue
    return {"status": "success", "source": source, "action": "transform"}

def execute_load(source: str, storage: StorageService):
    """Lógica base de carga"""
    logger.info(f"Ejecutando carga para fuente: {source}")
    return {"status": "success", "source": source, "action": "load"}
