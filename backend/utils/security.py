"""
Módulo de segurança para o sistema de reconhecimento facial.
"""
import base64
import hashlib
import hmac
import os
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

import jwt
from cryptography.fernet import Fernet
from fastapi import HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from passlib.context import CryptContext

# Configurações de segurança
SECRET_KEY = os.getenv("SECRET_KEY", os.urandom(32).hex())
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Contexto para hash de senhas
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Sistema de token
security = HTTPBearer()

# Chave para criptografia de dados sensíveis
ENCRYPTION_KEY = Fernet.generate_key()
fernet = Fernet(ENCRYPTION_KEY)

class SecurityUtils:
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verifica se a senha está correta."""
        return pwd_context.verify(plain_password, hashed_password)

    @staticmethod
    def get_password_hash(password: str) -> str:
        """Gera hash da senha."""
        return pwd_context.hash(password)

    @staticmethod
    def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        """Cria um token JWT."""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt

    @staticmethod
    def verify_token(credentials: HTTPAuthorizationCredentials = Security(security)) -> Dict[str, Any]:
        """Verifica se o token JWT é válido."""
        try:
            payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
            if datetime.fromtimestamp(payload["exp"]) < datetime.utcnow():
                raise HTTPException(status_code=401, detail="Token expirado")
            return payload
        except jwt.JWTError:
            raise HTTPException(status_code=401, detail="Token inválido")

    @staticmethod
    def encrypt_data(data: bytes) -> bytes:
        """Criptografa dados sensíveis."""
        return fernet.encrypt(data)

    @staticmethod
    def decrypt_data(encrypted_data: bytes) -> bytes:
        """Descriptografa dados sensíveis."""
        return fernet.decrypt(encrypted_data)

    @staticmethod
    def generate_hmac(data: bytes, key: bytes = None) -> str:
        """Gera um HMAC para verificar integridade dos dados."""
        if key is None:
            key = SECRET_KEY.encode()
        return hmac.new(key, data, hashlib.sha256).hexdigest()

    @staticmethod
    def verify_hmac(data: bytes, signature: str, key: bytes = None) -> bool:
        """Verifica se o HMAC é válido."""
        if key is None:
            key = SECRET_KEY.encode()
        expected = hmac.new(key, data, hashlib.sha256).hexdigest()
        return hmac.compare_digest(signature, expected)

def setup_security() -> None:
    """Configura as variáveis de ambiente necessárias para segurança."""
    if not os.getenv("SECRET_KEY"):
        os.environ["SECRET_KEY"] = os.urandom(32).hex()
    
    if not os.getenv("ENCRYPTION_KEY"):
        os.environ["ENCRYPTION_KEY"] = base64.urlsafe_b64encode(os.urandom(32)).decode()
