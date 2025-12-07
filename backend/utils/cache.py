"""
Sistema de cache com Redis para respostas LLM e API externa.
"""
import os
import json
import hashlib
from typing import Optional, Any
import redis
from backend.utils.logger import setup_logger

logger = setup_logger(__name__)


class RedisCache:
    """Cliente Redis para caching."""

    def __init__(self):
        self.enabled = os.getenv("REDIS_ENABLED", "true").lower() == "true"

        if not self.enabled:
            logger.info("Redis cache desabilitado")
            self.client = None
            return

        host = os.getenv("REDIS_HOST", "localhost")
        port = int(os.getenv("REDIS_PORT", 6379))

        try:
            self.client = redis.Redis(
                host=host,
                port=port,
                db=0,
                decode_responses=True,
                socket_connect_timeout=5
            )
            self.client.ping()
            logger.info(f"Redis conectado: {host}:{port}")
        except Exception as e:
            logger.error(f"Falha ao conectar Redis: {e}")
            self.enabled = False
            self.client = None

    def _make_key(self, prefix: str, data: str) -> str:
        """Gera chave única baseada em hash."""
        hash_obj = hashlib.sha256(data.encode())
        return f"{prefix}:{hash_obj.hexdigest()[:16]}"

    def get(self, key: str) -> Optional[Any]:
        """Busca valor do cache."""
        if not self.enabled or not self.client:
            return None

        try:
            value = self.client.get(key)
            if value:
                logger.debug(f"Cache HIT: {key}")
                return json.loads(value)
            logger.debug(f"Cache MISS: {key}")
            return None
        except Exception as e:
            logger.error(f"Erro ao ler cache: {e}")
            return None

    def set(self, key: str, value: Any, ttl: int = 600) -> bool:
        """Salva valor no cache com TTL."""
        if not self.enabled or not self.client:
            return False

        try:
            self.client.setex(
                key,
                ttl,
                json.dumps(value)
            )
            logger.debug(f"Cache SET: {key} (TTL={ttl}s)")
            return True
        except Exception as e:
            logger.error(f"Erro ao salvar cache: {e}")
            return False

    def delete(self, key: str) -> bool:
        """Remove chave do cache."""
        if not self.enabled or not self.client:
            return False

        try:
            self.client.delete(key)
            return True
        except Exception as e:
            logger.error(f"Erro ao deletar cache: {e}")
            return False

    def increment_metric(self, metric_name: str) -> int:
        """Incrementa métrica (contador)."""
        if not self.enabled or not self.client:
            return 0

        try:
            return self.client.incr(f"metric:{metric_name}")
        except Exception as e:
            logger.error(f"Erro ao incrementar métrica: {e}")
            return 0

    def get_metric(self, metric_name: str) -> int:
        """Obtém valor da métrica."""
        if not self.enabled or not self.client:
            return 0

        try:
            value = self.client.get(f"metric:{metric_name}")
            return int(value) if value else 0
        except Exception as e:
            logger.error(f"Erro ao ler métrica: {e}")
            return 0


cache = RedisCache()
