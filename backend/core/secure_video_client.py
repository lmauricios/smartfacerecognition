"""
Cliente seguro para streaming de vídeo.
"""
import cv2
import json
import base64
import socket
import struct
import numpy as np
from typing import Optional, Tuple
import logging
from ..utils.security import SecurityUtils

# Configuração de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SecureVideoClient:
    def __init__(self, host: str = "127.0.0.1", port: int = 8080):
        self.host = host
        self.port = port
        self.security = SecurityUtils()
        self.socket: Optional[socket.socket] = None

    def connect(self) -> bool:
        """Estabelece conexão com o servidor"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(30)  # 30 segundos timeout
            self.socket.connect((self.host, self.port))
            logger.info(f"Conectado ao servidor em {self.host}:{self.port}")
            return True
        except Exception as e:
            logger.error(f"Erro ao conectar: {e}")
            return False

    def _decode_frame(self, data: bytes) -> Optional[np.ndarray]:
        """
        Decodifica o frame recebido de forma segura
        """
        try:
            # Decodifica JSON
            data_packet = json.loads(data.decode('utf-8'))
            
            # Verifica HMAC
            hmac = data_packet.pop("hmac", None)
            if not hmac:
                logger.warning("HMAC ausente no pacote")
                return None
            
            # Verifica integridade
            json_for_hmac = json.dumps({k: v for k, v in data_packet.items() if k != "hmac"}).encode('utf-8')
            if not self.security.verify_hmac(json_for_hmac, hmac):
                logger.warning("HMAC inválido - possível adulteração de dados")
                return None
            
            # Decodifica o frame
            frame_data = base64.b64decode(data_packet["frame"])
            nparr = np.frombuffer(frame_data, np.uint8)
            frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            return frame
        except Exception as e:
            logger.error(f"Erro ao decodificar frame: {e}")
            return None

    def receive_stream(self) -> None:
        """Recebe e exibe o stream de vídeo"""
        if not self.socket:
            logger.error("Cliente não conectado")
            return

        data = b""
        payload_size = struct.calcsize("!I")
        
        try:
            while True:
                # Recebe o tamanho do pacote
                while len(data) < payload_size:
                    packet = self.socket.recv(4096)
                    if not packet:
                        raise ConnectionError("Conexão perdida")
                    data += packet

                packed_size = data[:payload_size]
                data = data[payload_size:]
                msg_size = struct.unpack("!I", packed_size)[0]

                # Recebe o pacote completo
                while len(data) < msg_size:
                    packet = self.socket.recv(4096)
                    if not packet:
                        raise ConnectionError("Conexão perdida")
                    data += packet

                frame_data = data[:msg_size]
                data = data[msg_size:]

                # Decodifica e exibe o frame
                frame = self._decode_frame(frame_data)
                if frame is not None:
                    cv2.imshow("Secure Video Stream", frame)
                    
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break

        except (socket.error, ConnectionError) as e:
            logger.error(f"Erro de conexão: {e}")
        except Exception as e:
            logger.error(f"Erro inesperado: {e}")
        finally:
            self.cleanup()

    def cleanup(self) -> None:
        """Libera recursos"""
        if self.socket:
            self.socket.close()
        cv2.destroyAllWindows()
        logger.info("Cliente encerrado")
