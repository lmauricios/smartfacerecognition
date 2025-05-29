"""
Configurações centralizadas de segurança para todo o sistema.
"""
import os
import secrets
from dataclasses import dataclass
from typing import Dict, Any
from datetime import timedelta

@dataclass
class SecuritySettings:
    # Configurações JWT
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", secrets.token_urlsafe(32))
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE: timedelta = timedelta(minutes=30)
    
    # Configurações de Hash
    PASSWORD_HASH_ALGORITHM: str = "bcrypt"
    BCRYPT_ROUNDS: int = 12
    
    # Configurações de Rate Limiting
    RATE_LIMIT_WINDOW: int = 60  # segundos
    MAX_REQUESTS: int = 100
    
    # Configurações de Banco de dados
    DB_ENCRYPT_KEY: str = os.getenv("DB_ENCRYPT_KEY", secrets.token_urlsafe(32))
    
    # Configurações de Rede
    ALLOWED_HOSTS: list = ["127.0.0.1", "localhost"]
    ALLOWED_ORIGINS: list = ["http://localhost:3000"]
    
    # Configurações SSL/TLS
    SSL_CERT_FILE: str = "certs/cert.pem"
    SSL_KEY_FILE: str = "certs/key.pem"
    
    # Configurações de Upload
    MAX_UPLOAD_SIZE: int = 10 * 1024 * 1024  # 10MB
    ALLOWED_EXTENSIONS: set = {".jpg", ".jpeg", ".png"}
    
    # Configurações de Logs
    LOG_CONFIG: Dict[str, Any] = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "standard": {
                "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
            },
        },
        "handlers": {
            "default": {
                "level": "INFO",
                "formatter": "standard",
                "class": "logging.StreamHandler",
            },
            "file": {
                "level": "INFO",
                "formatter": "standard",
                "class": "logging.FileHandler",
                "filename": "app.log",
                "mode": "a",
            },
        },
        "loggers": {
            "": {  # root logger
                "handlers": ["default", "file"],
                "level": "INFO",
                "propagate": True
            },
        }
    }
    
    # Configurações de Segurança HTTP
    SECURITY_HEADERS: Dict[str, str] = {
        "X-Frame-Options": "DENY",
        "X-Content-Type-Options": "nosniff",
        "X-XSS-Protection": "1; mode=block",
        "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
        "Content-Security-Policy": "default-src 'self'",
    }
    
    # Configurações de Cache
    CACHE_TYPE: str = "redis"
    CACHE_REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    
    # Configurações de Session
    SESSION_TYPE: str = "filesystem"
    SESSION_FILE_DIR: str = "/tmp/flask_session"
    SESSION_PERMANENT: bool = False
    PERMANENT_SESSION_LIFETIME: timedelta = timedelta(minutes=30)
    
    # Configurações de Cookies
    COOKIE_SECURE: bool = True
    COOKIE_HTTPONLY: bool = True
    COOKIE_SAMESITE: str = "Strict"
    
    @classmethod
    def load_from_env(cls) -> 'SecuritySettings':
        """Carrega configurações do ambiente"""
        return cls(
            JWT_SECRET_KEY=os.getenv("JWT_SECRET_KEY", secrets.token_urlsafe(32)),
            DB_ENCRYPT_KEY=os.getenv("DB_ENCRYPT_KEY", secrets.token_urlsafe(32)),
            ALLOWED_HOSTS=os.getenv("ALLOWED_HOSTS", "127.0.0.1,localhost").split(","),
            ALLOWED_ORIGINS=os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(","),
        )

# Instância global das configurações de segurança
security_settings = SecuritySettings.load_from_env()
