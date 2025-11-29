"""
API schemas for chat endpoints
"""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class ChatMessageRequest(BaseModel):
    """Request schema for chat message."""
    conversation_id: str = Field(..., description="Conversation UUID")
    message: str = Field(..., description="User message text", min_length=1)
    user_id: Optional[str] = Field(None, description="Optional user ID")
    
    class Config:
        json_schema_extra = {
            "example": {
                "conversation_id": "123e4567-e89b-12d3-a456-426614174000",
                "message": "What nail color suits fair skin?",
                "user_id": "user_123"
            }
        }


class ChatMessageResponse(BaseModel):
    """Response schema for chat message."""
    conversation_id: str
    message_id: str
    answer: str
    language: str = Field(default="en", description="Detected language code")
    context_sources: List[Dict[str, Any]] = Field(default_factory=list, description="Source documents used")
    image_analyzed: bool = Field(default=False, description="Whether image was analyzed")
    tokens_used: int = Field(default=0, description="Tokens used for generation")
    error: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "conversation_id": "123e4567-e89b-12d3-a456-426614174000",
                "message_id": "msg_123",
                "answer": "For fair skin, I recommend soft pink, nude, or light coral shades...",
                "language": "en",
                "context_sources": [
                    {"title": "Top 5 Fair Skin", "category": "Skin Tone", "score": 0.89}
                ],
                "image_analyzed": False,
                "tokens_used": 250
            }
        }


class ImageUploadRequest(BaseModel):
    """Request schema for image upload with message."""
    conversation_id: str = Field(..., description="Conversation UUID")
    message: Optional[str] = Field(None, description="Optional message text")
    user_id: Optional[str] = Field(None, description="Optional user ID")
    
    class Config:
        json_schema_extra = {
            "example": {
                "conversation_id": "123e4567-e89b-12d3-a456-426614174000",
                "message": "What nail shape and color would suit me?",
                "user_id": "user_123"
            }
        }


class ImageUploadResponse(BaseModel):
    """Response schema for image upload."""
    conversation_id: str
    message_id: str
    answer: str
    image_analysis: Optional[str] = Field(None, description="Image analysis from GPT-5.1 vision")
    language: str = Field(default="en", description="Detected language code")
    context_sources: List[Dict[str, Any]] = Field(default_factory=list)
    tokens_used: int = Field(default=0)
    error: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "conversation_id": "123e4567-e89b-12d3-a456-426614174000",
                "message_id": "msg_123",
                "answer": "Based on your nail image, I recommend...",
                "image_analysis": "The image shows almond-shaped nails with a soft pink polish...",
                "language": "en",
                "context_sources": [],
                "tokens_used": 350
            }
        }


class ConversationCreateRequest(BaseModel):
    """Request schema for creating a new conversation."""
    user_id: Optional[str] = Field(None, description="Optional user ID")


class ConversationCreateResponse(BaseModel):
    """Response schema for conversation creation."""
    conversation_id: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "conversation_id": "123e4567-e89b-12d3-a456-426614174000"
            }
        }


class ConversationHistoryResponse(BaseModel):
    """Response schema for conversation history."""
    conversation_id: str
    messages: List[Dict[str, Any]] = Field(default_factory=list)
    message_count: int = Field(default=0)
    
    class Config:
        json_schema_extra = {
            "example": {
                "conversation_id": "123e4567-e89b-12d3-a456-426614174000",
                "messages": [
                    {"role": "user", "content": "What nail color suits fair skin?"},
                    {"role": "assistant", "content": "For fair skin, I recommend..."}
                ],
                "message_count": 2
            }
        }


class WebSocketMessage(BaseModel):
    """WebSocket message schema."""
    type: str = Field(..., description="Message type: 'message', 'image', 'ping'")
    conversation_id: str = Field(..., description="Conversation UUID")
    message: Optional[str] = Field(None, description="Message text")
    user_id: Optional[str] = Field(None, description="Optional user ID")
    
    class Config:
        json_schema_extra = {
            "example": {
                "type": "message",
                "conversation_id": "123e4567-e89b-12d3-a456-426614174000",
                "message": "What nail color suits fair skin?",
                "user_id": "user_123"
            }
        }

