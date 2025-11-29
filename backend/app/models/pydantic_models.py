"""
Pydantic v2 models for data validation and serialization
"""
from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field


class NailGuideDocument(BaseModel):
    """Base document model from the nail guides dataset."""
    id: int
    category: str
    title: str
    content: str
    questions: List[str] = Field(default_factory=list)
    answers: List[str] = Field(default_factory=list)
    
    class Config:
        """Pydantic v2 config."""
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 1,
                "category": "Color Theory & Outfit Matching (Nail + Clothes)",
                "title": "Match Any Outfit",
                "content": "Nail Polish Colors That Match Any Outfit...",
                "questions": ["Which neutral nail shades pair best with bold prints?"],
                "answers": ["Neutral shades like nude, beige, ivory..."]
            }
        }


class ChunkMetadata(BaseModel):
    """Metadata for document chunks."""
    chunk_index: int
    total_chunks: int
    source_doc_id: int
    source_title: str
    source_category: str
    chunk_start: Optional[int] = None  # Character position
    chunk_end: Optional[int] = None


class WeaviateNailGuide(BaseModel):
    """Model for Weaviate objects with vector field."""
    id: Optional[str] = None  # Weaviate UUID
    document_id: int
    category: str
    title: str
    content: str  # Chunked content
    questions: List[str] = Field(default_factory=list)
    answers: List[str] = Field(default_factory=list)
    chunk_metadata: Optional[ChunkMetadata] = None
    vector: Optional[List[float]] = None  # Embedding vector
    
    class Config:
        """Pydantic v2 config."""
        from_attributes = True


class ConversationMessage(BaseModel):
    """Chat message model."""
    role: str = Field(..., description="Message role: 'user' or 'assistant'")
    content: str = Field(..., description="Message content")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    message_id: Optional[str] = None
    image_url: Optional[str] = None  # If message includes image
    image_analysis: Optional[str] = None  # GPT-5.1 vision analysis
    
    class Config:
        """Pydantic v2 config."""
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class ConversationHistory(BaseModel):
    """Conversation context model for long-term storage."""
    conversation_id: str
    user_id: Optional[str] = None
    messages: List[ConversationMessage] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        """Pydantic v2 config."""
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

