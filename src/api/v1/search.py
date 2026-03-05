from typing import Annotated, Optional
from fastapi import APIRouter, Query, Depends, HTTPException
import json
from rapidfuzz import process, fuzz
import logging

from src.core.config import get_settings
from src.api.schemas import SearchResponse, MatchResult
from src.services.storage import StorageService
from src.etl.normalization import normalize_name

router = APIRouter(prefix="/check", tags=["Search"])

# Variable global para cachear la tabla en la Lambda
df_cache = None

def get_storage() -> StorageService:
    settings = get_settings()
    return StorageService(settings.compliance_lake_bucket, settings.delta_table_path)

StorageDep = Annotated[StorageService, Depends(get_storage)]

@router.get("/debug/count")
async def debug_count(storage: StorageDep):
    global df_cache
    if df_cache is None:
        df_cache = storage.get_delta_table()
    
    if df_cache is None or df_cache.empty:
        return {"status": "empty"}
        
    counts = df_cache.groupby('fuente').size().to_dict()
    return {"status": "success", "counts": counts, "total": len(df_cache)}

@router.get("/", response_model=SearchResponse)
async def check_name(
    name: Annotated[str, Query(min_length=3)],
    storage: StorageDep,
    threshold: float = 85.0,
    limit: int = 20,
    refresh: bool = False,
    source: Optional[str] = Query(None, description="Filtrar por fuente (ej: CONTRALORIA, OFAC)")
) -> SearchResponse:

    global df_cache
    
    # Si Refresh o si NO hay cache, AND no me piden fuente especifica, cargo todo en memoria.
    # SI me piden fuente específica (source != None), leo solo la partición. 
    # Optimizazción: El particionado Parquet s3 pushdown es brutalmente rápido por awswrangler.
    
    df_search = None
    
    if source:
        # Búsqueda dedicada a una partición específica. (Ahorra muchísima RAM para Requests filtrados)
        try:
            df_search = storage.get_delta_table(source_filter=source)
        except Exception as e:
             import logging
             logging.error(f"Error reading partition {source}: {e}")
             import pandas as pd
             df_search = pd.DataFrame()
             
    else:
        # Búsqueda global (Carga completa)
        if df_cache is None or refresh:
            df_cache = storage.get_delta_table()
        df_search = df_cache

    if df_search is None or df_search.empty:
        return SearchResponse(query=name, match_found=False, results=[])

    try:
        clean_query = normalize_name(name)
        choices = df_search['nombre_limpio'].tolist()
        
        results = process.extract(
            clean_query, 
            choices, 
            scorer=fuzz.token_set_ratio, 
            limit=limit,
            score_cutoff=threshold
        )

        matches = []
        for _, score, index in results:
            row = df_cache.iloc[index]
            
            meta_dict = {}
            try:
                meta_dict = json.loads(row['metadata'])
            except (json.JSONDecodeError, TypeError):
                meta_dict = {"raw": row['metadata']}

            matches.append(MatchResult(
                nombre_original=row['nombre_original'],
                fuente=row['fuente'],
                score=round(score, 2),
                tipo_lista=row['tipo_lista'],
                metadata=meta_dict
            ))

        return SearchResponse(
            query=name,
            match_found=len(matches) > 0,
            results=matches
        )

    except Exception as e:
        logging.error(f"Search error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
