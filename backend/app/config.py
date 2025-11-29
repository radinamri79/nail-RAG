"""
Configuration settings for Nail RAG Service
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file explicitly
load_dotenv(Path(__file__).parent.parent / ".env")

try:
    from pydantic_settings import BaseSettings
except ImportError:
    from pydantic import BaseSettings


class Settings(BaseSettings):
    """
    Application configuration, loaded from environment variables.
    """
    # Weaviate connection settings
    WEAVIATE_HOST: str = os.getenv("WEAVIATE_HOST", "localhost")
    WEAVIATE_PORT: int = int(os.getenv("WEAVIATE_PORT", "8080"))
    WEAVIATE_SCHEME: str = os.getenv("WEAVIATE_SCHEME", "http")
    WEAVIATE_API_KEY: str = os.getenv("WEAVIATE_API_KEY", "")
    
    # OpenAI API settings
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-5.1")  # GPT-5.1 for chat and vision
    EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
    
    # RAG and AI parameters
    default_confidence_threshold: float = 0.7
    max_contexts_per_query: int = 8  # Retrieve top 8-10 chunks
    similarity_score_threshold: float = 0.75  # High threshold for quality
    max_tokens_response: int = 1000
    temperature_rag: float = 0.7  # For creative responses
    temperature_factual: float = 0.2  # For factual responses
    
    # Vector search parameters
    vector_dimension: int = 1536  # text-embedding-3-small dimension
    weaviate_timeout: float = 30.0
    search_limit_default: int = 10  # Top-k for retrieval
    
    # Weaviate performance tuning
    weaviate_batch_size: int = 50  # Batch size for imports
    weaviate_hnsw_ef_construction: int = 200  # HNSW construction parameter
    weaviate_hnsw_ef: int = 50  # HNSW search parameter
    
    # Embedding optimizations
    embedding_batch_size: int = 100
    embedding_cache_enabled: bool = True
    embedding_cache_ttl: int = 3600  # 1 hour cache
    embedding_cache_size: int = 1000  # LRU cache size
    
    # Generation optimizations
    generation_timeout: float = 30.0
    
    # Bulk import performance tuning
    bulk_batch_size: int = 50
    bulk_max_concurrent_batches: int = 4
    bulk_embedding_batch_size: int = 100
    
    # Prompt file paths (relative to app directory)
    prompt_rag_system: str = "app/prompts/rag_system.txt"
    prompt_multilingual: str = "app/prompts/multilingual.txt"
    prompt_image_analysis: str = "app/prompts/image_analysis.txt"
    prompt_language_detection: str = "app/prompts/language_detection.txt"
    prompt_translate_to_english: str = "app/prompts/translate_to_english.txt"
    prompt_translate_response: str = "app/prompts/translate_response.txt"
    
    # CORS settings
    ALLOWED_ORIGINS: str = os.getenv("ALLOWED_ORIGINS", "*")
    
    # Conversation memory settings
    short_term_memory_limit: int = 10  # Last 10 messages
    conversation_history_collection: str = "ConversationHistory"
    
    # Optimization flags
    CACHING_ENABLED: bool = True
    PARALLEL_PROCESSING_ENABLED: bool = True
    STREAMING_ENABLED: bool = True
    QUERY_EXPANSION_ENABLED: bool = True
    CATEGORY_ROUTING_ENABLED: bool = True
    
    class Config:
        extra = "allow"  # Allow extra fields to prevent validation errors
    
    @property
    def WEAVIATE_URL(self) -> str:
        """Construct Weaviate URL from components"""
        return f"{self.WEAVIATE_SCHEME}://{self.WEAVIATE_HOST}:{self.WEAVIATE_PORT}"
    
    def print_config(self):
        """Debug method to print current configuration"""
        print("=== CONFIGURATION DEBUG ===")
        print(f"WEAVIATE_HOST: {self.WEAVIATE_HOST}")
        print(f"WEAVIATE_PORT: {self.WEAVIATE_PORT}")
        print(f"WEAVIATE_SCHEME: {self.WEAVIATE_SCHEME}")
        print(f"WEAVIATE_URL: {self.WEAVIATE_URL}")
        print(f"WEAVIATE_API_KEY: {'***' if self.WEAVIATE_API_KEY else 'None'}")
        print(f"OPENAI_API_KEY: {'***' if self.OPENAI_API_KEY else 'None'}")
        print(f"OPENAI_MODEL: {self.OPENAI_MODEL}")
        print(f"EMBEDDING_MODEL: {self.EMBEDDING_MODEL}")
        print("==========================")
    
    @property
    def allowed_origins_list(self) -> list[str]:
        """Convert ALLOWED_ORIGINS string to list"""
        if not self.ALLOWED_ORIGINS or self.ALLOWED_ORIGINS.strip() == "":
            return ["*"]
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",") if origin.strip()]


settings = Settings()

