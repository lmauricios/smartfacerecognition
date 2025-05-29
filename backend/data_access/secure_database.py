"""
Gerenciador seguro de conexões com banco de dados.
"""
import os
import logging
from typing import Optional, Dict, Any
import psycopg2
from psycopg2.extras import RealDictCursor
from ..utils.security import SecurityUtils

# Configuração de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SecureDatabaseManager:
    def __init__(self):
        self.security = SecurityUtils()
        self._conn = None
        self._setup_connection_params()

    def _setup_connection_params(self) -> None:
        """Configura parâmetros de conexão de forma segura"""
        self.db_config = {
            "host": os.getenv("DB_HOST", "localhost"),
            "database": os.getenv("DB_NAME", "reconhecimento_facial"),
            "user": os.getenv("DB_USER"),
            "password": os.getenv("DB_PASS"),
            "sslmode": "require",  # Força conexão SSL
            "connect_timeout": 10
        }

        # Valida configurações críticas
        if not all([self.db_config["user"], self.db_config["password"]]):
            raise ValueError("Credenciais de banco de dados não configuradas")

    def get_connection(self) -> Optional[psycopg2.extensions.connection]:
        """Obtém conexão com o banco de dados de forma segura"""
        if self._conn is None or self._conn.closed:
            try:
                self._conn = psycopg2.connect(**self.db_config)
                self._conn.autocommit = False  # Força uso explícito de transações
                logger.info("Nova conexão com banco de dados estabelecida")
            except psycopg2.Error as e:
                logger.error(f"Erro ao conectar ao banco de dados: {e}")
                raise

        return self._conn

    def execute_query(self, query: str, params: tuple = None, fetch: bool = True) -> Optional[list]:
        """Executa query de forma segura"""
        conn = self.get_connection()
        result = None

        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query, params)
                if fetch:
                    result = cur.fetchall()
                conn.commit()
                return result
        except psycopg2.Error as e:
            conn.rollback()
            logger.error(f"Erro ao executar query: {e}")
            raise
        except Exception as e:
            conn.rollback()
            logger.error(f"Erro inesperado: {e}")
            raise

    def close(self) -> None:
        """Fecha conexão de forma segura"""
        if self._conn and not self._conn.closed:
            self._conn.close()
            logger.info("Conexão com banco de dados fechada")

    def __enter__(self) -> 'SecureDatabaseManager':
        """Suporte a context manager"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Garante que a conexão seja fechada"""
        self.close()

    def add_person(self, name: str, face_encoding: bytes) -> bool:
        """Adiciona pessoa de forma segura"""
        try:
            # Criptografa o encoding facial
            encrypted_encoding = self.security.encrypt_data(face_encoding)
            
            query = """
                INSERT INTO pessoas (nome_pessoa, face_encoding)
                VALUES (%s, %s)
                ON CONFLICT (nome_pessoa) 
                DO UPDATE SET face_encoding = EXCLUDED.face_encoding
            """
            self.execute_query(query, (name, encrypted_encoding), fetch=False)
            logger.info(f"Pessoa {name} adicionada/atualizada com sucesso")
            return True
        except Exception as e:
            logger.error(f"Erro ao adicionar pessoa: {e}")
            return False

    def get_all_people(self) -> list:
        """Obtém todas as pessoas de forma segura"""
        try:
            query = "SELECT nome_pessoa, face_encoding FROM pessoas"
            results = self.execute_query(query)
            
            # Descriptografa os encodings
            for row in results:
                if row["face_encoding"]:
                    row["face_encoding"] = self.security.decrypt_data(row["face_encoding"])
            
            return results
        except Exception as e:
            logger.error(f"Erro ao obter pessoas: {e}")
            return []
