from fastapi import FastAPI
from contextlib import asynccontextmanager

from api.routes import router as api_router, app_dependencies  # Importa as dependências
from api.security_middleware import setup_security_middleware
from data_access.database_manager import DatabaseManager
from core.face_processor import FaceProcessor
from services.recognition_service import RecognitionService
from utils.logger_config import log
from utils.security_config import security_settings
import logging.config

# Configura logging seguro
logging.config.dictConfig(security_settings.LOG_CONFIG)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Código de inicialização
    log.info("Iniciando aplicação FastAPI...")
    db_manager = DatabaseManager()
    face_processor = FaceProcessor(model_dir="face_detector")  # Garanta que este diretório exista relativo a main.py

    # Injeta as dependências
    app_dependencies.recognition_service = RecognitionService(db_manager, face_processor)

    log.info("Dependências da aplicação inicializadas.")
    yield
    # Código de limpeza
    log.info("Encerrando aplicação FastAPI...")
    db_manager.close_connection()  # Fecha a conexão com o BD ao encerrar


# Inicializa FastAPI com configurações de segurança
app = FastAPI(
    title="Face Recognition API",
    version="0.1.0",
    docs_url=None if security_settings.COOKIE_SECURE else "/docs",  # Desativa Swagger em produção
    redoc_url=None if security_settings.COOKIE_SECURE else "/redoc"
)

# Configura middlewares de segurança
setup_security_middleware(app)

# Inclui rotas da API
app.include_router(api_router, prefix="/api/v1")

log.info("Aplicação FastAPI configurada com medidas de segurança e pronta para iniciar.")
