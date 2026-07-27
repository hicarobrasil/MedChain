import redis
import logging
from app.settings import Settings

class RedisClient:
    
    """Cliente Redis para gerenciar a blacklist de tokens JWT (versao sincrona)"""

    def __init__(self, redis_url: str = None):
        """
        Inicializa o cliente Redis.
        
        Args:
            redis_url: URL de conexao do Redis. Se nao fornecido, usa a configuracao padrao.
        """
        settings = Settings()
        self.redis_url = redis_url or settings.REDIS_URL
        self._redis = None

    def _get_connection(self):
        """Obtem uma conexao Redis ou reutiliza a existente"""
        if self._redis is None:
            urls = [self.redis_url]
            # Ambiente local (uvicorn fora do Docker): hostname "redis" nao resolve
            if self.redis_url and ("@redis:" in self.redis_url or "://redis:" in self.redis_url):
                urls.append(
                    self.redis_url.replace("@redis:", "@localhost:").replace("://redis:", "://localhost:")
                )
            last_err = None
            for url in urls:
                try:
                    client = redis.from_url(url, decode_responses=True, socket_connect_timeout=1)
                    client.ping()
                    self._redis = client
                    self.redis_url = url
                    return self._redis
                except Exception as e:
                    last_err = e
                    continue
            logging.error(f"Erro ao conectar ao Redis: {last_err}")
            return None
        return self._redis

    def add_token_to_blacklist(self, jti: str, ttl: int) -> bool:
        redis_conn = self._get_connection()
        if not redis_conn:
            logging.error("Nao foi possivel adicionar token à blacklist: sem conexao Redis")
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
            logging.warning("Nao foi possivel verificar blacklist: sem conexao Redis")
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
