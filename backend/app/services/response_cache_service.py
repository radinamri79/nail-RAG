"""
Response Cache Service - Cache frequent queries and responses
"""
from typing import Optional, Dict, Any
import hashlib
import json
import time
from app.config import settings
from app.constants import RESPONSE_CACHE_SIZE, RESPONSE_CACHE_TTL
from app.logger import get_logger

logger = get_logger("response_cache")


class ResponseCache:
    """LRU cache for query responses with TTL."""
    
    def __init__(self, max_size: int = RESPONSE_CACHE_SIZE, ttl: int = RESPONSE_CACHE_TTL):
        self.cache: Dict[str, tuple] = {}  # key -> (response, timestamp)
        self.max_size = max_size
        self.ttl = ttl  # Time to live in seconds
    
    def _generate_key(self, query: str, conversation_context: Optional[str] = None) -> str:
        """Generate cache key from query and optional context."""
        cache_string = query
        if conversation_context:
            cache_string += f"|{conversation_context}"
        return hashlib.md5(cache_string.encode('utf-8')).hexdigest()
    
    def get(
        self,
        query: str,
        conversation_context: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Get response from cache if available and not expired."""
        key = self._generate_key(query, conversation_context)
        
        if key in self.cache:
            response, timestamp = self.cache[key]
            
            # Check if expired
            if time.time() - timestamp < self.ttl:
                logger.debug(f"✅ Cache hit for query: {query[:50]}...")
                return response
            else:
                # Remove expired entry
                del self.cache[key]
        
        return None
    
    def set(
        self,
        query: str,
        response: Dict[str, Any],
        conversation_context: Optional[str] = None
    ) -> None:
        """Store response in cache."""
        key = self._generate_key(query, conversation_context)
        
        # Evict oldest if cache is full
        if len(self.cache) >= self.max_size:
            # Remove oldest entry (first in dict)
            first_key = next(iter(self.cache))
            del self.cache[first_key]
            logger.debug(f"🔄 Evicted cache entry: {first_key[:8]}...")
        
        self.cache[key] = (response, time.time())
        logger.debug(f"✅ Cached response for query: {query[:50]}...")
    
    def clear(self) -> None:
        """Clear the cache."""
        self.cache.clear()
        logger.info("🔄 Response cache cleared")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        return {
            "size": len(self.cache),
            "max_size": self.max_size,
            "ttl": self.ttl
        }


class ResponseCacheService:
    """Service for caching query responses."""
    
    def __init__(self):
        self.cache = ResponseCache() if settings.CACHING_ENABLED else None
    
    def get(
        self,
        query: str,
        conversation_context: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Get cached response if available."""
        if not self.cache:
            return None
        return self.cache.get(query, conversation_context)
    
    def set(
        self,
        query: str,
        response: Dict[str, Any],
        conversation_context: Optional[str] = None
    ) -> None:
        """Store response in cache."""
        if self.cache:
            self.cache.set(query, response, conversation_context)
    
    def clear(self) -> None:
        """Clear the cache."""
        if self.cache:
            self.cache.clear()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        if self.cache:
            return self.cache.get_stats()
        return {"enabled": False}


# Global instance
response_cache_service = ResponseCacheService()

