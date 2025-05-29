"""
Middleware de segurança para a API FastAPI.
"""
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
import time
from typing import Callable, Dict
import logging
from utils.security_config import security_settings

logger = logging.getLogger(__name__)

class SecurityMiddleware(BaseHTTPMiddleware):
    def __init__(
        self,
        app: FastAPI,
        redis_client = None  # Opcional, para rate limiting distribuído
    ):
        super().__init__(app)
        self.rate_limit_window = security_settings.RATE_LIMIT_WINDOW
        self.max_requests = security_settings.MAX_REQUESTS
        self.request_history: Dict[str, list] = {}
        self.redis_client = redis_client

    async def dispatch(
        self, request: Request, call_next: Callable
    ) -> Response:
        # 1. Rate Limiting
        client_ip = request.client.host
        current_time = time.time()
        
        if not self._check_rate_limit(client_ip, current_time):
            return Response(
                content="Rate limit exceeded",
                status_code=429
            )

        # 2. Adiciona headers de segurança
        response = await call_next(request)
        response.headers.update(security_settings.SECURITY_HEADERS)

        # 3. Log de segurança
        self._log_request(request, response)

        return response

    def _check_rate_limit(self, client_ip: str, current_time: float) -> bool:
        """Verifica rate limiting para o IP"""
        if self.redis_client:
            return self._check_rate_limit_redis(client_ip)
        
        if client_ip not in self.request_history:
            self.request_history[client_ip] = []
        
        # Remove requests antigos
        self.request_history[client_ip] = [
            t for t in self.request_history[client_ip]
            if current_time - t < self.rate_limit_window
        ]
        
        if len(self.request_history[client_ip]) >= self.max_requests:
            logger.warning(f"Rate limit exceeded for IP: {client_ip}")
            return False
            
        self.request_history[client_ip].append(current_time)
        return True

    def _check_rate_limit_redis(self, client_ip: str) -> bool:
        """Rate limiting usando Redis para ambientes distribuídos"""
        try:
            pipe = self.redis_client.pipeline()
            key = f"rate_limit:{client_ip}"
            current_time = time.time()
            
            # Remove requests antigos e adiciona o atual
            pipe.zremrangebyscore(
                key,
                0,
                current_time - self.rate_limit_window
            )
            pipe.zadd(key, {str(current_time): current_time})
            pipe.zcard(key)
            pipe.expire(key, self.rate_limit_window)
            _, _, request_count, _ = pipe.execute()
            
            return request_count <= self.max_requests
        except Exception as e:
            logger.error(f"Redis rate limiting error: {e}")
            return True  # Em caso de erro, permite a requisição

    def _log_request(self, request: Request, response: Response) -> None:
        """Log seguro de requisições"""
        log_data = {
            "timestamp": time.time(),
            "client_ip": request.client.host,
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
            "user_agent": request.headers.get("user-agent", "unknown")
        }
        logger.info("Request", extra=log_data)

def setup_security_middleware(app: FastAPI, redis_client=None) -> None:
    """Configura todos os middlewares de segurança"""
    # 1. CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=security_settings.ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # 2. Trusted Hosts
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=security_settings.ALLOWED_HOSTS
    )

    # 3. Middleware de Segurança Personalizado
    app.add_middleware(
        SecurityMiddleware,
        redis_client=redis_client
    )
