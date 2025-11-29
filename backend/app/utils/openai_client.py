"""
Centralized OpenAI client factory for GPT-5.1 and vision capabilities
"""
from typing import Optional
from openai import AsyncOpenAI
from app.config import settings
from app.logger import get_logger

logger = get_logger("openai_client")


class OpenAIClientFactory:
    """
    Singleton factory for creating and managing OpenAI clients.
    
    This factory ensures that:
    - OpenAI clients are created with consistent configuration
    - API key is properly loaded from settings
    - Client instances can be reused when appropriate
    - Supports GPT-5.1 for chat and vision
    """
    
    _instance: Optional['OpenAIClientFactory'] = None
    _client: Optional[AsyncOpenAI] = None
    
    def __new__(cls) -> 'OpenAIClientFactory':
        """Implement singleton pattern."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def get_client(self) -> AsyncOpenAI:
        """
        Get or create an AsyncOpenAI client instance.
        
        Returns:
            AsyncOpenAI: Configured OpenAI client
            
        Raises:
            ValueError: If OpenAI API key is not configured
        """
        if self._client is None:
            self._client = self._create_client()
        
        return self._client
    
    def _create_client(self) -> AsyncOpenAI:
        """
        Create a new AsyncOpenAI client with proper configuration.
        
        Returns:
            AsyncOpenAI: Configured client
            
        Raises:
            ValueError: If OpenAI API key is not configured
        """
        if not settings.OPENAI_API_KEY:
            raise ValueError(
                "OpenAI API key is not configured. Please set OPENAI_API_KEY in your environment variables."
            )
        
        try:
            client = AsyncOpenAI(
                api_key=settings.OPENAI_API_KEY,
                timeout=settings.generation_timeout,
                max_retries=3,
            )
            
            logger.info(f"✅ OpenAI client created successfully (Model: {settings.OPENAI_MODEL})")
            return client
            
        except Exception as e:
            logger.error(f"❌ Failed to create OpenAI client: {e}")
            raise
    
    def create_new_client(self) -> AsyncOpenAI:
        """
        Create a new OpenAI client instance (bypassing singleton).
        
        Use this when you need a fresh client instance with potentially
        different configuration.
        
        Returns:
            AsyncOpenAI: New configured client
        """
        return self._create_client()
    
    def reset_client(self) -> None:
        """
        Reset the singleton client instance.
        
        This will force creation of a new client on the next get_client() call.
        """
        self._client = None
        logger.info("🔄 OpenAI client instance reset")


# Singleton instance
_factory = OpenAIClientFactory()


def get_openai_client() -> AsyncOpenAI:
    """
    Get the shared OpenAI client instance.
    
    This is the main entry point for getting an OpenAI client throughout the application.
    
    Returns:
        AsyncOpenAI: Configured OpenAI client
        
    Example:
        ```python
        from app.utils.openai_client import get_openai_client
        
        async def my_function():
            client = get_openai_client()
            response = await client.chat.completions.create(
                model="gpt-5.1",
                messages=[{"role": "user", "content": "Hello"}]
            )
        ```
    """
    return _factory.get_client()


def create_new_openai_client() -> AsyncOpenAI:
    """
    Create a new OpenAI client instance.
    
    Use this when you need a fresh client instance instead of the shared one.
    
    Returns:
        AsyncOpenAI: New configured client
    """
    return _factory.create_new_client()


def reset_openai_client() -> None:
    """
    Reset the shared OpenAI client instance.
    
    This will force creation of a new client on the next get_openai_client() call.
    """
    _factory.reset_client()

