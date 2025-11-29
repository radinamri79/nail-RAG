"""
Weaviate v4 Client singleton for connection management
"""
from typing import Optional
from weaviate import WeaviateClient, connect_to_local
from weaviate.auth import AuthApiKey
from app.config import settings
from app.logger import get_logger

logger = get_logger("weaviate_client")


class WeaviateClientFactory:
    """
    Singleton factory for creating and managing Weaviate Client.
    
    This factory ensures that:
    - Weaviate clients are created with consistent configuration
    - API key is properly loaded from settings
    - Client instances can be reused
    - Connection health is monitored
    """
    
    _instance: Optional['WeaviateClientFactory'] = None
    _client: Optional[WeaviateClient] = None
    
    def __new__(cls) -> 'WeaviateClientFactory':
        """Implement singleton pattern."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def get_client(self) -> WeaviateClient:
        """
        Get or create a WeaviateClient instance.
        
        Returns:
            WeaviateClient: Configured Weaviate client
            
        Raises:
            ValueError: If Weaviate connection settings are invalid
        """
        if self._client is None:
            self._client = self._create_client()
        
        return self._client
    
    def _create_client(self) -> WeaviateClient:
        """
        Create a new WeaviateClient with proper configuration.
        
        Returns:
            WeaviateClient: Configured client
            
        Raises:
            ValueError: If connection settings are invalid
        """
        try:
            # Build additional headers for OpenAI API key
            additional_headers = {}
            if settings.OPENAI_API_KEY:
                additional_headers["X-OpenAI-Api-Key"] = settings.OPENAI_API_KEY
            
            # Build auth credentials if API key provided
            auth_credentials = None
            if settings.WEAVIATE_API_KEY:
                auth_credentials = AuthApiKey(api_key=settings.WEAVIATE_API_KEY)
            
            # Use connect_to_local for all Docker connections
            # The host parameter supports both 'localhost' and service names like 'weaviate'
            client = connect_to_local(
                host=settings.WEAVIATE_HOST,
                port=settings.WEAVIATE_PORT,
                grpc_port=50051,
                headers=additional_headers if additional_headers else None,
                auth_credentials=auth_credentials,
                skip_init_checks=False
            )
            
            logger.info(f"✅ Weaviate client created successfully: {settings.WEAVIATE_HOST}:{settings.WEAVIATE_PORT}")
            return client
            
        except Exception as e:
            logger.error(f"❌ Failed to create Weaviate client: {e}")
            raise
    
    def health_check(self) -> bool:
        """
        Check Weaviate connection health.
        
        Returns:
            bool: True if healthy, False otherwise
        """
        try:
            client = self.get_client()
            is_ready = client.is_ready()
            
            if is_ready:
                logger.info("✅ Weaviate health check passed")
            else:
                logger.warning("⚠️ Weaviate health check failed: not ready")
            
            return is_ready
            
        except Exception as e:
            logger.error(f"❌ Weaviate health check error: {e}")
            return False
    
    def close(self) -> None:
        """Close the Weaviate client connection."""
        if self._client:
            try:
                self._client.close()
                logger.info("✅ Weaviate client closed")
            except Exception as e:
                logger.error(f"❌ Error closing Weaviate client: {e}")
            finally:
                self._client = None
    
    def reset_client(self) -> None:
        """
        Reset the singleton client instance.
        
        This will force creation of a new client on the next get_client() call.
        """
        self._client = None
        logger.info("🔄 Weaviate client instance reset")


# Singleton instance
_factory = WeaviateClientFactory()


def get_weaviate_client() -> WeaviateClient:
    """
    Get the shared WeaviateClient instance.
    
    This is the main entry point for getting a Weaviate client throughout the application.
    
    Returns:
        WeaviateClient: Configured Weaviate client
        
    Example:
        ```python
        from app.models.weaviate_client import get_weaviate_client
        
        def my_function():
            client = get_weaviate_client()
            collections = client.collections.list_all()
        ```
    """
    return _factory.get_client()


def check_weaviate_health() -> bool:
    """
    Check Weaviate connection health.
    
    Returns:
        bool: True if healthy, False otherwise
    """
    return _factory.health_check()


def close_weaviate_client() -> None:
    """Close the Weaviate client connection."""
    _factory.close()


def reset_weaviate_client() -> None:
    """Reset the shared Weaviate client instance."""
    _factory.reset_client()
