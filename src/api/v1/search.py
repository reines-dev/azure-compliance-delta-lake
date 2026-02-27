from typing import Annotated
from fastapi import APIRouter, Query, Depends, HTTPException
import json
from rapidfuzz import process, fuzz

from src.core.config import get_settings, Settings
from src.api.schemas import SearchResponse, MatchResult
from src.services.storage import StorageService
from src.etl.normalization import normalize_name

router = APIRouter(prefix="/check", tags=["Search"])

# Simple cache in memory
dt_cache = None
df_cache = None

def get_storage() -> StorageService:
    settings = get_settings()
    return StorageService(settings.compliance_lake_bucket, settings.delta_table_path)

StorageDep = Annotated[StorageService, Depends(get_storage)]


@router.get("/", response_model=SearchResponse)
async def check_name(
    name: Annotated[str, Query(min_length=3, description="Nombre exacto o parcial a buscar")],
    storage: StorageDep,
    threshold: Annotated[float, Query(ge=0.0, le=100.0, description="Umbral de similitud")] = 85.0,
    limit: Annotated[int, Query(ge=1, le=100, description="Límite máximo de resultados")] = 20
) -> SearchResponse:

    global dt_cache, df_cache
    
    clean_query = normalize_name(name)
    
    try:
        if dt_cache is None or df_cache is None:
            df_cache = storage.get_delta_table()
            if df_cache is None:
                raise ValueError("No se pudo leer la tabla de Delta Lake")

        if df_cache.empty:
            return SearchResponse(query=name, match_found=False, results=[])

        results = process.extract(
            clean_query, 
            df_cache['nombre_limpio'], 
            scorer=fuzz.token_set_ratio, 
            limit=limit
        )

        matches = []
        for _, score, index in results:
            if score >= threshold:
                row = df_cache.iloc[index]
                matches.append(MatchResult(
                    nombre_original=row["nombre_original"],
                    fuente=row["fuente"],
                    score=round(score, 2),
                    tipo_lista=row["tipo_lista"],
                    metadata=json.loads(row["metadata"])
                ))

        return SearchResponse(
            query=name,
            match_found=len(matches) > 0,
            results=matches
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
