from data_access.database_manager import DatabaseManager
from core.face_processor import FaceProcessor
from utils.logger_config import log
import numpy as np
import cv2

class RecognitionService:
    def __init__(self, db_manager: DatabaseManager, face_processor: FaceProcessor):
        self.db_manager = db_manager
        self.face_processor = face_processor

    def register_new_person(self, name: str, image_bytes: bytes) -> dict:
        """Registra uma nova pessoa. A imagem é usada para extrair o encoding."""
        log.info(f"Tentando registrar nova pessoa: {name}")
        # A lógica de extração de encoding e salvamento já está no DatabaseManager
        # Se você quiser separar e ter o encoding aqui, pode chamar
        # encodings = self.face_processor.get_face_encodings_from_image_bytes(image_bytes)
        # e depois passar o encoding para o db_manager.
        # Por simplicidade, o db_manager.add_person já faz isso.
        
        success = self.db_manager.add_person(name, image_bytes)
        if success:
            log.info(f"Pessoa '{name}' registrada com sucesso.")
            return {"message": f"Pessoa '{name}' registrada com sucesso."}
        else:
            log.error(f"Falha ao registrar pessoa '{name}'. Verifique os logs para detalhes.")
            return {"error": f"Falha ao registrar pessoa '{name}'. A imagem pode não conter uma face detectável ou houve um erro no banco."}

    def identify_faces_in_image(self, image_bytes: bytes) -> list:
        """Identifica faces em uma imagem comparando com o banco de dados."""
        log.info("Iniciando identificação de faces na imagem.")
        
        nparr = np.frombuffer(image_bytes, np.uint8)
        frame_bgr = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        if frame_bgr is None: # Se a imagem não puder ser decodificada
            log.error("Não foi possível decodificar a imagem para identificação.")
            return [] # Retorna lista vazia, o cliente pode interpretar isso ou você pode levantar HTTPException na rota

        known_encodings, known_names = self.db_manager.get_known_faces()
        if not known_encodings: # Se não houver faces conhecidas no banco
            log.warning("Nenhum encoding conhecido no banco para comparação.")
            return [] # Retorna lista vazia

        results = self.face_processor.recognize_faces_in_frame(
            frame_bgr=frame_bgr,
            known_encodings=known_encodings,
            known_names=known_names
        )
        log.info(f"Identificação concluída. Encontrados {len(results)} resultados.")
        return results