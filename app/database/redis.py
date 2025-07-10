import redis
import logging
from app.settings import Settings
from typing import Set

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
        self._redis_available = False
        self._in_memory_blacklist: Set[str] = set()  # Fallback para quando Redis não estiver disponível

    def _get_connection(self):
        """Obtém uma conexão Redis ou reutiliza a existente"""
        if self._redis is None:
            try:
                self._redis = redis.from_url(self.redis_url, decode_responses=True)
                # Teste a conexão
                self._redis.ping()
                self._redis_available = True
                logging.info("Conexão Redis estabelecida com sucesso")
            except Exception as e:
                logging.warning(f"Redis não disponível, usando fallback em memória: {e}")
                self._redis_available = False
                return None
        return self._redis if self._redis_available else None

    def add_token_to_blacklist(self, jti: str, ttl: int) -> bool:
        """
        Adiciona um token à blacklist
        
        Args:
            jti: Identificador único do token (JWT ID)
            ttl: Tempo de vida em segundos
            
        Returns:
            True se o token foi adicionado com sucesso, False caso contrário
        """
        redis_conn = self._get_connection()
        if redis_conn:
            try:
                key = f"token:blacklist:{jti}"
                redis_conn.setex(key, ttl, "1")
                logging.debug(f"Token {jti} adicionado à blacklist Redis com TTL {ttl}s")
                return True
            except Exception as e:
                logging.error(f"Erro ao adicionar token à blacklist Redis: {e}")
                # Fallback para memória
                self._in_memory_blacklist.add(jti)
                logging.debug(f"Token {jti} adicionado à blacklist em memória (fallback)")
                return True
        else:
            # Usar blacklist em memória
            self._in_memory_blacklist.add(jti)
            logging.debug(f"Token {jti} adicionado à blacklist em memória")
            return True

    def is_token_blacklisted(self, jti: str) -> bool:
        """
        Verifica se um token está na blacklist
        
        Args:
            jti: Identificador único do token (JWT ID)
            
        Returns:
            True se o token estiver na blacklist, False caso contrário
        """
        redis_conn = self._get_connection()
        if redis_conn:
            try:
                key = f"token:blacklist:{jti}"
                result = bool(redis_conn.exists(key))
                logging.debug(f"Token {jti} verificado no Redis: {'blacklisted' if result else 'válido'}")
                return result
            except Exception as e:
                logging.error(f"Erro ao verificar blacklist Redis: {e}")
                # Fallback para memória
                result = jti in self._in_memory_blacklist
                logging.debug(f"Token {jti} verificado em memória (fallback): {'blacklisted' if result else 'válido'}")
                return result
        else:
            # Usar blacklist em memória
            result = jti in self._in_memory_blacklist
            logging.debug(f"Token {jti} verificado em memória: {'blacklisted' if result else 'válido'}")
            return result

    def clear_blacklist(self) -> bool:
        """
        Limpa toda a blacklist
        
        Returns:
            True se a operação foi bem-sucedida, False caso contrário
        """
        redis_conn = self._get_connection()
        if redis_conn:
            try:
                keys = redis_conn.keys("token:blacklist:*")
                if keys:
                    redis_conn.delete(*keys)
                logging.info("Blacklist Redis limpa com sucesso")
                return True
            except Exception as e:
                logging.error(f"Erro ao limpar blacklist Redis: {e}")
                # Fallback para memória
                self._in_memory_blacklist.clear()
                logging.info("Blacklist em memória limpa com sucesso (fallback)")
                return True
        else:
            # Limpar blacklist em memória
            self._in_memory_blacklist.clear()
            logging.info("Blacklist em memória limpa com sucesso")
            return True

    def close(self):
        """Fecha a conexão Redis"""
        if self._redis:
            try:
                self._redis.close()
                logging.info("Conexão Redis fechada")
            except Exception as e:
                logging.warning(f"Erro ao fechar conexão Redis: {e}")
            finally:
                self._redis = None
                self._redis_available = False

    def get_status(self) -> dict:
        """
        Retorna o status do cliente Redis
        
        Returns:
            Dicionário com informações de status
        """
        return {
            "redis_available": self._redis_available,
            "redis_url": self.redis_url,
            "fallback_blacklist_size": len(self._in_memory_blacklist),
            "using_fallback": not self._redis_available
        }
