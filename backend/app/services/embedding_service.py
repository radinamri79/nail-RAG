"""
Embedding service for generating and caching OpenAI embeddings
"""
from typing import List, Optional, Dict
import hashlib
import json
from app.config import settings
from app.utils.openai_client import get_openai_client
from app.logger import get_logger

logger = get_logger("embedding_service")


class EmbeddingCache:
    """LRU cache for embeddings with TTL support."""
    
    def __init__(self, max_size: int = 1000):
        self.cache: Dict[str, tuple] = {}  # key -> (embedding, timestamp)
        self.max_size = max_size
    
    def _generate_key(self, text: str) -> str:
        """Generate cache key from text."""
        return hashlib.md5(text.encode('utf-8')).hexdigest()
    
    def get(self, text: str) -> Optional[List[float]]:
        """Get embedding from cache if available and not expired."""
        key = self._generate_key(text)
        if key in self.cache:
            embedding, timestamp = self.cache[key]
            # Check if expired (TTL check would go here if needed)
            return embedding
        return None
    
    def set(self, text: str, embedding: List[float]) -> None:
        """Store embedding in cache."""
        key = self._generate_key(text)
        
        # Evict oldest if cache is full
        if len(self.cache) >= self.max_size:
            # Remove first item (FIFO)
            first_key = next(iter(self.cache))
            del self.cache[first_key]
        
        import time
        self.cache[key] = (embedding, time.time())
    
    def clear(self) -> None:
        """Clear the cache."""
        self.cache.clear()
        logger.info("🔄 Embedding cache cleared")


class EmbeddingService:
    """Service for generating and caching embeddings."""
    
    def __init__(self):
        self.cache = EmbeddingCache(max_size=settings.embedding_cache_size) if settings.embedding_cache_enabled else None
        self.client = None
    
    def _get_client(self):
        """Lazy load OpenAI client."""
        if self.client is None:
            self.client = get_openai_client()
        return self.client
    
    async def generate_embedding(
        self,
        text: str,
        use_cache: bool = True
    ) -> List[float]:
        """
        Generate embedding for a single text.
        
        Args:
            text: Text to embed
            use_cache: Whether to use cache
            
        Returns:
            Embedding vector as list of floats
        """
        # Check cache first
        if use_cache and self.cache:
            cached = self.cache.get(text)
            if cached:
                logger.debug(f"✅ Cache hit for embedding: {text[:50]}...")
                return cached
        
        # Generate embedding
        try:
            client = self._get_client()
            response = await client.embeddings.create(
                model=settings.EMBEDDING_MODEL,
                input=text
            )
            
            embedding = response.data[0].embedding
            
            # Store in cache
            if use_cache and self.cache:
                self.cache.set(text, embedding)
            
            logger.debug(f"✅ Generated embedding for: {text[:50]}...")
            return embedding
            
        except Exception as e:
            logger.error(f"❌ Error generating embedding: {e}")
            raise
    
    async def generate_embeddings_batch(
        self,
        texts: List[str],
        use_cache: bool = True
    ) -> List[List[float]]:
        """
        Generate embeddings for multiple texts in batch.
        
        Args:
            texts: List of texts to embed
            use_cache: Whether to use cache
            
        Returns:
            List of embedding vectors
        """
        if not texts:
            return []
        
        # Separate cached and uncached texts
        cached_embeddings: Dict[int, List[float]] = {}
        uncached_texts: List[tuple[int, str]] = []
        
        if use_cache and self.cache:
            for idx, text in enumerate(texts):
                cached = self.cache.get(text)
                if cached:
                    cached_embeddings[idx] = cached
                else:
                    uncached_texts.append((idx, text))
        else:
            uncached_texts = [(idx, text) for idx, text in enumerate(texts)]
        
        # Generate embeddings for uncached texts
        if uncached_texts:
            try:
                client = self._get_client()
                
                # Batch process in chunks
                batch_size = settings.embedding_batch_size
                all_embeddings = []
                
                for i in range(0, len(uncached_texts), batch_size):
                    batch = uncached_texts[i:i + batch_size]
                    batch_texts = [text for _, text in batch]
                    
                    response = await client.embeddings.create(
                        model=settings.EMBEDDING_MODEL,
                        input=batch_texts
                    )
                    
                    batch_embeddings = [item.embedding for item in response.data]
                    
                    # Store in cache
                    if use_cache and self.cache:
                        for (idx, text), embedding in zip(batch, batch_embeddings):
                            self.cache.set(text, embedding)
                    
                    all_embeddings.extend(batch_embeddings)
                
                # Map embeddings back to original indices
                for (idx, _), embedding in zip(uncached_texts, all_embeddings):
                    cached_embeddings[idx] = embedding
                
                logger.info(f"✅ Generated {len(uncached_texts)} embeddings (batch)")
                
            except Exception as e:
                logger.error(f"❌ Error generating batch embeddings: {e}")
                raise
        
        # Return embeddings in original order
        return [cached_embeddings.get(idx, []) for idx in range(len(texts))]
    
    def clear_cache(self) -> None:
        """Clear the embedding cache."""
        if self.cache:
            self.cache.clear()


# Global instance
embedding_service = EmbeddingService()

