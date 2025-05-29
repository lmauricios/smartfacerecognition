from fastapi import APIRouter, File, UploadFile, HTTPException, Form, Depends
from typing import List
from services.recognition_service import RecognitionService
from models.schemas import PersonRegistrationResponse, IdentificationResponse, FaceIdentificationResult
from utils.logger_config import log


# Esta função seria chamada em main.py para injetar a dependência
def get_recognition_service_dependency(
    service: RecognitionService = Depends(lambda: app_dependencies.recognition_service),
):
    return service


router = APIRouter()


# Placeholder para dependências injetadas. Será configurado em main.py
class AppDependencies:
    recognition_service: RecognitionService = None


app_dependencies = AppDependencies()


@router.post("/register", response_model=PersonRegistrationResponse)
async def register_person_endpoint(
    name: str = Form(...),
    image: UploadFile = File(...),
    service: RecognitionService = Depends(get_recognition_service_dependency),
):
    log.info("Recebida requisição para registrar: %s com imagem: %s", name, image.filename)
    image_bytes = await image.read()
    result = service.register_new_person(name, image_bytes)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@router.post("/identify", response_model=List[FaceIdentificationResult])  # Ajustado para retornar lista diretamente
async def identify_faces_endpoint(
    image: UploadFile = File(...), service: RecognitionService = Depends(get_recognition_service_dependency)
):
    log.info("Recebida requisição para identificar faces na imagem: %s", image.filename)
    image_bytes = await image.read()
    results = service.identify_faces_in_image(image_bytes)
    # Se results for uma lista vazia ou contiver um erro/info, o cliente lida com isso.
    return results
