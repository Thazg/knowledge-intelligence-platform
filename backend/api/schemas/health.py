from __future__ import annotations

from pydantic import BaseModel


class DependencyStatus(BaseModel):
    rag_service: str
    qdrant: str
    ollama: str


class ReadinessResponse(BaseModel):
    status: str
    dependencies: DependencyStatus