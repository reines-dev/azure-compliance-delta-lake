from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException
from src.api.schemas import ETLResponse
from src.services.storage import StorageService
from src.core.config import get_settings
from src.etl import pipeline

router = APIRouter(prefix="/etl", tags=["ETL Pipeline"])

def get_storage() -> StorageService:
    settings = get_settings()
    return StorageService(settings.compliance_lake_bucket, settings.delta_table_path)

StorageDep = Annotated[StorageService, Depends(get_storage)]

@router.post("/ingest/{source}")
async def ingest_source(source: str, storage: StorageDep):
    try:
        result = pipeline.execute_ingest(source, storage)
        return result
    except Exception as e:
        import traceback
        return {"status": "error", "source": source, "message": str(e), "traceback": traceback.format_exc()}

@router.post("/transform/{source}")
async def transform_source(source: str, storage: StorageDep):
    try:
        result = pipeline.execute_transform(source, storage)
        return result
    except Exception as e:
        import traceback
        return {"status": "error", "source": source, "message": str(e), "traceback": traceback.format_exc()}

@router.post("/load/{source}")
async def load_source(source: str, storage: StorageDep):
    try:
        result = pipeline.execute_load(source, storage)
        return result
    except Exception as e:
        import traceback
        return {"status": "error", "source": source, "message": str(e), "traceback": traceback.format_exc()}
