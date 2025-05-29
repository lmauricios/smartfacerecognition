"""
Dependências de segurança para a API.
"""
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from datetime import datetime
from typing import Optional
from utils.security_config import security_settings
from utils.security import SecurityUtils

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

async def get_current_user(token: str = Depends(oauth2_scheme)) -> dict:
    """Obtém o usuário atual a partir do token JWT"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Credenciais inválidas",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(
            token,
            security_settings.JWT_SECRET_KEY,
            algorithms=[security_settings.JWT_ALGORITHM]
        )
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
            
        # Verifica expiração do token
        exp = payload.get("exp")
        if exp is None:
            raise credentials_exception
            
        if datetime.utcnow().timestamp() > exp:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token expirado",
                headers={"WWW-Authenticate": "Bearer"},
            )
            
        return {"username": username, "permissions": payload.get("permissions", [])}
            
    except JWTError:
        raise credentials_exception

async def verify_api_key(api_key: Optional[str] = None) -> bool:
    """Verifica chave de API para autenticação de serviços"""
    if not api_key:
        return False
        
    # Aqui você pode implementar a lógica de verificação da API key
    # Por exemplo, comparar com uma chave armazenada de forma segura
    return SecurityUtils.verify_api_key(api_key)

async def require_permission(required_permission: str, user: dict = Depends(get_current_user)) -> None:
    """Verifica se o usuário tem a permissão necessária"""
    if required_permission not in user.get("permissions", []):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permissão insuficiente"
        )
