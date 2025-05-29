"""
Módulo de transmissão de vídeo seguro usando JSON em vez de pickle.
"""
import cv2
import json
import base64
import socket
import struct
import numpy as np
from typing import Optional, Tuple, Dict
from dataclasses import dataclass
import logging
from ..utils.security import SecurityUtils

# Configuração de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class StreamConfig:
    host: str = "127.0.0.1"  # Apenas conexões locais
    port: int = 8080
    frame_width: int = 640
    frame_height: int = 480
    quality: int = 90  # Qualidade JPEG (0-100)
    max_clients: int = 1
    timeout: int = 30

class SecureVideoStream:
    def __init__(self, config: StreamConfig):
        self.config = config
        self.security = SecurityUtils()
        self._setup_socket()
        self._setup_camera()

    def _setup_socket(self) -> None:
        """Configura o socket com parâmetros seguros"""
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.settimeout(self.config.timeout)
        self.socket.bind((self.config.host, self.config.port))
        self.socket.listen(self.config.max_clients)
        logger.info(f"Socket configurado em {self.config.host}:{self.config.port}")

    def _setup_camera(self) -> None:
        """Configura a câmera com parâmetros seguros"""
        self.camera = cv2.VideoCapture(0)
        self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, self.config.frame_width)
        self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, self.config.frame_height)
        if not self.camera.isOpened():
            raise RuntimeError("Não foi possível inicializar a câmera")
        logger.info("Câmera inicializada com sucesso")

    def _encode_frame(self, frame: np.ndarray) -> Tuple[Dict, bytes]:
        """
        Codifica o frame de forma segura usando JSON e base64
        """
        # Comprime o frame como JPEG
        _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, self.config.quality])
        # Converte para base64
        frame_base64 = base64.b64encode(buffer).decode('utf-8')
        
        # Cria o pacote de dados
        data_packet = {
            "frame": frame_base64,
            "timestamp": str(cv2.getTickCount()),
            "width": frame.shape[1],
            "height": frame.shape[0],
        }
        
        # Gera HMAC para verificar integridade
        json_data = json.dumps(data_packet).encode('utf-8')
        hmac = self.security.generate_hmac(json_data)
        
        # Adiciona HMAC ao pacote
        data_packet["hmac"] = hmac
        
        # Serializa o pacote completo
        final_json = json.dumps(data_packet).encode('utf-8')
        return data_packet, final_json

    def serve_forever(self) -> None:
        """Inicia o servidor de streaming"""
        logger.info("Iniciando servidor de streaming...")
        try:
            while True:
                try:
                    client_socket, addr = self.socket.accept()
                    logger.info(f"Cliente conectado: {addr}")
                    self._handle_client(client_socket)
                except socket.timeout:
                    continue
                except Exception as e:
                    logger.error(f"Erro ao aceitar conexão: {e}")
        except KeyboardInterrupt:
            logger.info("Servidor interrompido pelo usuário")
        finally:
            self.cleanup()

    def _handle_client(self, client_socket: socket.socket) -> None:
        """Gerencia uma conexão de cliente"""
        try:
            while True:
                ret, frame = self.camera.read()
                if not ret:
                    logger.warning("Falha ao capturar frame")
                    continue

                try:
                    # Codifica o frame de forma segura
                    _, encoded_data = self._encode_frame(frame)
                    
                    # Envia o tamanho dos dados
                    size = len(encoded_data)
                    client_socket.sendall(struct.pack("!I", size))
                    
                    # Envia os dados
                    client_socket.sendall(encoded_data)
                except (socket.error, struct.error) as e:
                    logger.error(f"Erro na transmissão: {e}")
                    break
        except Exception as e:
            logger.error(f"Erro ao processar cliente: {e}")
        finally:
            client_socket.close()
            logger.info("Conexão com cliente encerrada")

    def cleanup(self) -> None:
        """Libera recursos"""
        if hasattr(self, 'camera'):
            self.camera.release()
        if hasattr(self, 'socket'):
            self.socket.close()
        logger.info("Recursos liberados")
