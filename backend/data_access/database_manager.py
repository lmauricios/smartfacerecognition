import psycopg2
from psycopg2 import sql
from psycopg2.extras import RealDictCursor
import numpy as np
import cv2  # Para decodificar imagem para obter encoding
import face_recognition  # Para obter encoding

from utils.config import settings
from utils.logger_config import log


class DatabaseManager:
    def __init__(self):
        self.db_config = {
            "host": settings.DB_HOST,
            "database": settings.DB_NAME,
            "user": settings.DB_USER,
            "password": settings.DB_PASS,
        }
        self._conn = None

    def _get_connection(self):
        if self._conn is None or self._conn.closed:
            try:
                self._conn = psycopg2.connect(**self.db_config)
                log.info("Nova conexão com o banco de dados estabelecida.")
            except psycopg2.Error as e:
                log.error(f"Erro ao conectar ao PostgreSQL: {e}")
                raise  # Re-levanta a exceção para ser tratada pelo chamador
        return self._conn

    def close_connection(self):
        if self._conn and not self._conn.closed:
            self._conn.close()
            log.info("Conexão com o banco de dados fechada.")

    def add_person(self, name: str, image_bytes: bytes) -> bool:
        """
        Adiciona uma pessoa ao banco de dados, extraindo o encoding facial da imagem.
        A imagem original não é armazenada, apenas o encoding.
        """
        try:
            nparr = np.frombuffer(image_bytes, np.uint8)
            img_bgr = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            if img_bgr is None:
                log.error(f"Não foi possível decodificar a imagem para {name}.")
                return False

            img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
            encodings = face_recognition.face_encodings(img_rgb)

            if not encodings:
                log.warning(f"Nenhum encoding facial encontrado na imagem para {name}.")
                return False

            # Usar o primeiro encoding encontrado
            face_encoding_binary = psycopg2.Binary(encodings[0].tobytes())

            conn = self._get_connection()
            with conn.cursor() as cur:
                # Modifique a tabela 'pessoas' para armazenar 'face_encoding' (bytea) em vez de 'foto'
                # Ex: ALTER TABLE pessoas DROP COLUMN foto;
                #     ALTER TABLE pessoas ADD COLUMN face_encoding BYTEA;
                cur.execute(
                    "INSERT INTO pessoas (nome_pessoa, face_encoding) VALUES (%s, %s) ON CONFLICT (nome_pessoa) DO UPDATE SET face_encoding = EXCLUDED.face_encoding",
                    (name, face_encoding_binary),
                )
                conn.commit()
            log.info(f"Pessoa '{name}' adicionada/atualizada no banco de dados com novo encoding.")
            return True
        except psycopg2.Error as e:
            log.error(f"Erro de banco de dados ao adicionar pessoa '{name}': {e}")
            if self._conn:
                self._conn.rollback()
        except Exception as e:
            log.error(f"Erro inesperado ao adicionar pessoa '{name}': {e}")
        return False

    def get_known_faces(self) -> tuple[list, list]:
        """Carrega encodings e nomes de faces conhecidas do banco de dados."""
        known_encodings = []
        known_names = []
        try:
            conn = self._get_connection()
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("SELECT nome_pessoa, face_encoding FROM pessoas WHERE face_encoding IS NOT NULL")
                pessoas = cur.fetchall()
                for pessoa in pessoas:
                    # O encoding é armazenado como bytes de um array numpy.
                    # Precisamos reconstruir o array numpy.
                    # Assumindo que o encoding tem 128 dimensões e é float64.
                    encoding_array = np.frombuffer(pessoa["face_encoding"], dtype=np.float64)
                    known_encodings.append(encoding_array)
                    known_names.append(pessoa["nome_pessoa"])
            log.info(f"Carregados {len(known_encodings)} encodings conhecidos do banco.")
        except psycopg2.Error as e:
            log.error(f"Erro ao buscar encodings do banco: {e}")
        except Exception as e:
            log.error(f"Erro inesperado ao carregar encodings: {e}")
        return known_encodings, known_names

    def delete_person(self, name: str) -> bool:
        # Implementação similar a add_person, mas com DELETE
        # Retorna True se deletado, False caso contrário
        # ... (a ser implementado se necessário para a API)
        log.warning("Funcionalidade delete_person não totalmente implementada no DatabaseManager.")
        return False
