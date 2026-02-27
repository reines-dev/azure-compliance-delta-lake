import logging
from src.core.config import get_settings
from src.services.storage import StorageService
from src.etl.pipeline import execute_ingest, execute_transform, execute_load

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def get_storage_service() -> StorageService:
    settings = get_settings()
    return StorageService(settings.compliance_lake_bucket, settings.delta_table_path)

def ingest_handler(event, context):
    source = event.get('source', 'ofac').lower()
    logger.info(f"Ingesting {source.upper()}...")
    storage = get_storage_service()
    return execute_ingest(source, storage)

def transform_handler(event, context):
    source = event.get('source', 'ofac').lower()
    logger.info(f"Transforming {source.upper()}...")
    storage = get_storage_service()
    return execute_transform(source, storage)

def load_handler(event, context):
    source = event.get('source', 'ofac').lower()
    logger.info(f"Loading {source.upper()} to Gold DeltaLake...")
    storage = get_storage_service()
    return execute_load(source, storage)
