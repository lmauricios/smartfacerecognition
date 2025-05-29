from fastapi import APIRouter, File, UploadFile, HTTPException, Form, Depends, Security
from typing import List
from services.recognition_service import RecognitionService
from models.schemas import PersonRegistrationResponse, IdentificationResponse, FaceIdentificationResult
from utils.logger_config import log
from api.security_dependencies import get_current_user, require_permission
from utils.security_config import security_settings


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
    current_user: dict = Depends(get_current_user),  # Requer autenticação
    _: None = Depends(lambda: require_permission("register_person"))  # Requer permissão específica
):
    # Validação do tamanho do arquivo
    if await image.read(security_settings.MAX_UPLOAD_SIZE + 1):
        raise HTTPException(status_code=413, detail="Arquivo muito grande")
    await image.seek(0)

    # Validação da extensão
    ext = image.filename.lower().split('.')[-1]
    if f'.{ext}' not in security_settings.ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Tipo de arquivo não permitido")

    log.info("Usuário %s solicitou registro de: %s com imagem: %s",
             current_user["username"], name, image.filename)

    image_bytes = await image.read()
    result = service.register_new_person(name, image_bytes)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@router.post("/identify", response_model=List[FaceIdentificationResult])
async def identify_faces_endpoint(
    image: UploadFile = File(...),
    service: RecognitionService = Depends(get_recognition_service_dependency),
    current_user: dict = Depends(get_current_user),  # Requer autenticação
    _: None = Depends(lambda: require_permission("identify_faces"))  # Requer permissão específica
):
    # Validação do tamanho do arquivo
    if await image.read(security_settings.MAX_UPLOAD_SIZE + 1):
        raise HTTPException(status_code=413, detail="Arquivo muito grande")
    await image.seek(0)

    # Validação da extensão
    ext = image.filename.lower().split('.')[-1]
    if f'.{ext}' not in security_settings.ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Tipo de arquivo não permitido")

    log.info("Usuário %s solicitou identificação de faces na imagem: %s",
             current_user["username"], image.filename)

    image_bytes = await image.read()
    results = service.identify_faces_in_image(image_bytes)
    return results
