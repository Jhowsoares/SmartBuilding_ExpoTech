"""
Rate Limiting Middleware — SmartBuilding API
Critério OWASP API4 + critério de segurança/performance da avaliação.

Estratégia: sliding window por token JWT (ou IP como fallback).
Armazenamento: Redis com TTL automático — sem vazamento de memória.

Adicione ao main.py:
    from app.middleware.rate_limit import RateLimitMiddleware
    app.add_middleware(RateLimitMiddleware)

Resposta quando limite atingido (RFC 7807):
    HTTP 429 Too Many Requests
    Retry-After: 45
    Content-Type: application/problem+json
    {
        "type": "https://smartbuilding.local/errors/rate-limit-exceeded",
        "title": "Limite de requisições atingido",
        "status": 429,
        "detail": "Você atingiu o limite de 60 requisições por minuto. Tente novamente em 45 segundos.",
        "retry_after": 45
    }
"""
from __future__ import annotations

import json
import time
from typing import Callable

import redis.asyncio as aioredis
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

# ---------------------------------------------------------------------------
# Configuração de limites por perfil de endpoint
# ---------------------------------------------------------------------------

# Formato: { "prefixo_do_path": (requisições, janela_em_segundos) }
RATE_LIMIT_RULES: dict[str, tuple[int, int]] = {
    "/api/v1/auth/login":         (10,  60),   # 10 req/min — protege brute force
    "/api/v1/predictions/train":  (3,  300),   # 3 req/5min — operação cara (ML)
    "/api/v1/sensors/data":       (120,  60),  # 120 req/min — ingestão IoT (alta)
    "/api/v1/":                   (60,   60),  # 60 req/min — padrão geral
}

# Rotas que ficam fora do rate limiting
EXEMPT_PATHS = {"/api/v1/health", "/api/docs", "/api/redoc", "/openapi.json"}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_limit_for_path(path: str) -> tuple[int, int]:
    """Retorna (max_requests, window_seconds) para o path dado."""
    for prefix, limits in RATE_LIMIT_RULES.items():
        if path.startswith(prefix):
            return limits
    return (60, 60)  # fallback


def _extract_identifier(request: Request) -> str:
    """
    Tenta extrair o sub do JWT para contar por usuário.
    Se não houver token, usa IP — mais justo e evita BOLA (API1).
    """
    auth = request.headers.get("Authorization", "")
    if auth.startswith("Bearer "):
        token = auth[7:]
        try:
            # Decodifica sem verificar assinatura só para pegar o sub
            import base64
            payload_b64 = token.split(".")[1]
            # Padding
            payload_b64 += "=" * (-len(payload_b64) % 4)
            payload = json.loads(base64.urlsafe_b64decode(payload_b64))
            return f"user:{payload.get('sub', 'unknown')}"
        except Exception:
            pass
    # Fallback: IP (considera proxy reverso com X-Forwarded-For)
    forwarded = request.headers.get("X-Forwarded-For")
    ip = forwarded.split(",")[0].strip() if forwarded else request.client.host
    return f"ip:{ip}"


def _problem_detail_429(detail: str, retry_after: int) -> dict:
    return {
        "type": "https://smartbuilding.local/errors/rate-limit-exceeded",
        "title": "Limite de requisições atingido",
        "status": 429,
        "detail": detail,
        "retry_after": retry_after,
    }


# ---------------------------------------------------------------------------
# Middleware
# ---------------------------------------------------------------------------

class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Sliding window rate limiter usando Redis.

    Algoritmo: lista de timestamps no Redis com TTL = janela.
    Complexidade: O(n) por request onde n = número de requests na janela.
    Para escala maior, use sorted sets (ZADD/ZREMRANGEBYSCORE).
    """

    def __init__(self, app, redis_url: str = "redis://localhost:6379"):
        super().__init__(app)
        self.redis_url = redis_url
        self._redis: aioredis.Redis | None = None

    async def _get_redis(self) -> aioredis.Redis:
        if self._redis is None:
            self._redis = aioredis.from_url(
                self.redis_url, encoding="utf-8", decode_responses=True
            )
        return self._redis

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        path = request.url.path

        # Rotas isentas
        if path in EXEMPT_PATHS or not path.startswith("/api/"):
            return await call_next(request)

        max_requests, window_seconds = _get_limit_for_path(path)
        identifier = _extract_identifier(request)
        redis_key = f"ratelimit:{identifier}:{path}"

        try:
            redis = await self._get_redis()
            now = time.time()
            window_start = now - window_seconds

            pipe = redis.pipeline()
            # Remove timestamps fora da janela
            pipe.zremrangebyscore(redis_key, 0, window_start)
            # Conta requests na janela atual
            pipe.zcard(redis_key)
            # Adiciona o timestamp atual
            pipe.zadd(redis_key, {str(now): now})
            # Renova o TTL
            pipe.expire(redis_key, window_seconds + 1)
            results = await pipe.execute()

            current_count = results[1]  # zcard antes do zadd

            # Headers de rate limit (informacionais)
            remaining = max(0, max_requests - current_count - 1)
            reset_at = int(now) + window_seconds

            if current_count >= max_requests:
                # Calcula quando o request mais antigo da janela vai expirar
                oldest = await redis.zrange(redis_key, 0, 0, withscores=True)
                retry_after = window_seconds
                if oldest:
                    oldest_ts = oldest[0][1]
                    retry_after = max(1, int(oldest_ts + window_seconds - now))

                detail = (
                    f"Você atingiu o limite de {max_requests} requisições "
                    f"por {window_seconds} segundos. "
                    f"Tente novamente em {retry_after} segundos."
                )
                return JSONResponse(
                    content=_problem_detail_429(detail, retry_after),
                    status_code=429,
                    media_type="application/problem+json",
                    headers={
                        "Retry-After": str(retry_after),
                        "X-RateLimit-Limit": str(max_requests),
                        "X-RateLimit-Remaining": "0",
                        "X-RateLimit-Reset": str(reset_at),
                    },
                )

            response = await call_next(request)
            # Injeta headers de rate limit nas respostas normais
            response.headers["X-RateLimit-Limit"] = str(max_requests)
            response.headers["X-RateLimit-Remaining"] = str(remaining)
            response.headers["X-RateLimit-Reset"] = str(reset_at)
            return response

        except Exception:
            # Se o Redis cair, não derruba a API — fail open com log
            import logging
            logging.getLogger(__name__).warning(
                "Rate limiting indisponível (Redis inacessível) — request permitido."
            )
            return await call_next(request)
