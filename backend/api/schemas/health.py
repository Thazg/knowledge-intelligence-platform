from pydantic import BaseModel


class DependencyStatus(BaseModel):
    rag_service: str
    qdrant: str
    ollama: str | None = None
    groq: str | None = None


class ReadinessResponse(BaseModel):
    status: str
    dependencies: DependencyStatus