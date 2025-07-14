import redis
import logging
from app.settings import Settings

class RedisClient:
    
    """Cliente Redis para gerenciar a blacklist de tokens JWT (versão síncrona)"""

    def __init__(self, redis_url: str = None):
        """
        Inicializa o cliente Redis.
        
        Args:
            redis_url: URL de conexão do Redis. Se não fornecido, usa a configuração padrão.
        """
        settings = Settings()
        self.redis_url = redis_url or settings.REDIS_URL
        self._redis = None

    def _get_connection(self):
        """Obtém uma conexão Redis ou reutiliza a existente"""
        if self._redis is None:
            try:
                self._redis = redis.from_url(self.redis_url, decode_responses=True)
            except Exception as e:
                logging.error(f"Erro ao conectar ao Redis: {e}")
                return None
        return self._redis

    def add_token_to_blacklist(self, jti: str, ttl: int) -> bool:
        redis_conn = self._get_connection()
        if not redis_conn:
            logging.error("Não foi possível adicionar token à blacklist: sem conexão Redis")
            return False
        try:
            key = f"token:blacklist:{jti}"
            redis_conn.setex(key, ttl, "1")
            return True
        except Exception as e:
            logging.error(f"Erro ao adicionar token à blacklist: {e}")
            return False

    def is_token_blacklisted(self, jti: str) -> bool:
        redis_conn = self._get_connection()
        if not redis_conn:
            logging.warning("Não foi possível verificar blacklist: sem conexão Redis")
            return False
        try:
            key = f"token:blacklist:{jti}"
            return bool(redis_conn.exists(key))
        except Exception as e:
            logging.error(f"Erro ao verificar blacklist: {e}")
            return False

    def clear_blacklist(self) -> bool:
        redis_conn = self._get_connection()
        if not redis_conn:
            return False
        try:
            keys = redis_conn.keys("token:blacklist:*")
            if keys:
                redis_conn.delete(*keys)
            return True
        except Exception as e:
            logging.error(f"Erro ao limpar blacklist: {e}")
            return False

    def close(self):
        if self._redis:
            self._redis.close()
            self._redis = None
