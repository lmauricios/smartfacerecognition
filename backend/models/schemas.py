from pydantic import BaseModel
from typing import List, Optional


class PersonRegistrationResponse(BaseModel):
    message: Optional[str] = None
    error: Optional[str] = None


class FaceIdentificationResult(BaseModel):
    name: str
    box: List[int]  # [startX, startY, endX, endY]
    similarity: float


class IdentificationResponse(BaseModel):
    results: List[FaceIdentificationResult]
    info: Optional[str] = None
    error: Optional[str] = None


# Adicione outros schemas conforme necessário
