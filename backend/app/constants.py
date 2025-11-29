"""
Constants for Nail RAG Service
"""

# ============================================================================
# Weaviate Collection Names (4 collections for 4 dataset categories)
# ============================================================================

class CollectionNames:
    """Centralized collection names for Weaviate."""
    
    # Nail guide collections (one per dataset category)
    NAIL_COLOR_THEORY = "NailColorTheory"  # Color Theory & Outfit Matching
    NAIL_SKIN_TONE = "NailSkinTone"  # Skin Tone – Nail Color Advice
    NAIL_SEASONAL = "NailSeasonal"  # Seasonal / Occasion-Based Nail Advice
    NAIL_SHAPE = "NailShape"  # Hand / Finger Shape – Nail Shape & Design Advice
    
    # Conversation history collection
    CONVERSATION_HISTORY = "ConversationHistory"
    
    @classmethod
    def get_all_nail_collections(cls) -> list[str]:
        """Get all nail guide collection names."""
        return [
            cls.NAIL_COLOR_THEORY,
            cls.NAIL_SKIN_TONE,
            cls.NAIL_SEASONAL,
            cls.NAIL_SHAPE,
        ]
    
    @classmethod
    def get_collection_for_category(cls, category: str) -> str:
        """Map dataset category to Weaviate collection name."""
        category_mapping = {
            "Color Theory & Outfit Matching (Nail + Clothes)": cls.NAIL_COLOR_THEORY,
            "Skin Tone – Nail Color Advice": cls.NAIL_SKIN_TONE,
            "Seasonal / Occasion-Based Nail Advice": cls.NAIL_SEASONAL,
            "Hand / Finger Shape – Nail Shape & Design Advice": cls.NAIL_SHAPE,
        }
        return category_mapping.get(category, cls.NAIL_COLOR_THEORY)


# ============================================================================
# Conversation and Message Constants
# ============================================================================

# Conversation memory
SHORT_TERM_MEMORY_LIMIT = 10  # Last N messages for short-term memory
CONVERSATION_HISTORY_LIMIT = 8  # Number of previous messages to include in LLM context
CONVERSATION_BATCH_SIZE = 10  # Messages grouped for processing

# Pagination defaults
DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100

# Message processing
MESSAGE_PREVIEW_LENGTH = 100
MESSAGE_PROCESSING_BATCH_SIZE = 100


# ============================================================================
# Search and Retrieval Constants
# ============================================================================

# Search limits
DEFAULT_SEARCH_LIMIT = 10  # Top-k for retrieval
MAX_SEARCH_RESULTS = 25
MIN_SEARCH_RESULTS = 3

# Score thresholds
DEFAULT_SCORE_THRESHOLD = 0.75  # High threshold for quality
similarity_score_threshold = 0.75  # Similarity threshold for search results
HIGH_QUALITY_THRESHOLD = 0.85
EXCELLENT_THRESHOLD = 0.95

# Hybrid search weights
VECTOR_SEARCH_WEIGHT = 0.7  # Vector similarity weight
BM25_SEARCH_WEIGHT = 0.3  # BM25 keyword weight

# Query processing
MAX_QUERY_VARIANTS = 5  # Query expansion variants
OPTIMAL_ANSWER_LENGTH = 100  # Target answer length (words)


# ============================================================================
# Chunking Strategy Constants
# ============================================================================

# Document chunking
MAX_CHUNK_SIZE = 500  # Max tokens per chunk
CHUNK_OVERLAP = 50  # Overlap tokens between chunks
MIN_CHUNK_SIZE = 100  # Minimum chunk size


# ============================================================================
# Vector Database Settings
# ============================================================================

VECTOR_DIMENSION = 1536  # OpenAI text-embedding-3-small dimension
DISTANCE_METRIC = "cosine"  # Vector similarity metric

# ============================================================================
# Cache Settings
# ============================================================================

RESPONSE_CACHE_SIZE = 100  # Maximum cached responses
RESPONSE_CACHE_TTL = 300  # Time to live in seconds (5 minutes)
EMBEDDING_CACHE_SIZE = 1000  # Maximum cached embeddings


# ============================================================================
# Performance Targets
# ============================================================================

# Latency targets (milliseconds)
TARGET_QUERY_LATENCY = 500  # Total query latency
TARGET_RETRIEVAL_TIME = 200  # Retrieval time
TARGET_GENERATION_TIME = 300  # Generation time
TARGET_WEBSOCKET_FIRST_TOKEN = 100  # First token via WebSocket

# Throughput targets
TARGET_BULK_IMPORT_RATE = 1000  # Documents per minute


# ============================================================================
# Cache Settings
# ============================================================================

# Embedding cache
EMBEDDING_CACHE_SIZE = 1000  # LRU cache size
EMBEDDING_CACHE_TTL = 3600  # 1 hour

# Response cache
RESPONSE_CACHE_SIZE = 100  # Number of cached responses
RESPONSE_CACHE_TTL = 300  # 5 minutes


# ============================================================================
# Logging and Debug Constants
# ============================================================================

LOG_MESSAGE_MAX_LENGTH = 100
LOG_CONTEXT_LINES = 50
DEBUG_ENABLED = False
VERBOSE_LOGGING = False


# ============================================================================
# Feature Flags
# ============================================================================

# RAG features
ENHANCED_RAG_ENABLED = True
QUALITY_ASSESSMENT_ENABLED = True
QUERY_EXPANSION_ENABLED = True
CATEGORY_ROUTING_ENABLED = True

# Performance optimizations
CACHING_ENABLED = True
PARALLEL_PROCESSING_ENABLED = True
STREAMING_ENABLED = True

