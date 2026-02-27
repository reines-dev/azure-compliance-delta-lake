from typing import Any
from pydantic import BaseModel, Field


class MatchResult(BaseModel):
    nombre_original: str
    fuente: str
    score: float = Field(..., description="Similitud porcentual (0.0 a 100.0)")
    tipo_lista: str
    metadata: dict[str, Any] = Field(default_factory=dict, description="Metadata anidada (ej. info_adicional)")


class SearchResponse(BaseModel):
    query: str
    match_found: bool
    results: list[MatchResult] = Field(default_factory=list)
