"""
HTTP routes for chat and image upload
"""
from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from typing import Optional
from app.schemas.chat import (
    ChatMessageRequest,
    ChatMessageResponse,
    ImageUploadResponse,
    ConversationCreateRequest,
    ConversationCreateResponse,
    ConversationHistoryResponse
)
from app.services.chat_service import chat_service
from app.logger import get_logger

logger = get_logger("chat_routes")

router = APIRouter(prefix="/api/chat", tags=["chat"])


@router.post("/conversation", response_model=ConversationCreateResponse)
async def create_conversation(request: ConversationCreateRequest) -> ConversationCreateResponse:
    """
    Create a new conversation.
    
    Returns:
        Conversation UUID
    """
    try:
        conversation_id = await chat_service.create_conversation(request.user_id)
        return ConversationCreateResponse(conversation_id=conversation_id)
    except Exception as e:
        logger.error(f"❌ Error creating conversation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/message", response_model=ChatMessageResponse)
async def send_message(request: ChatMessageRequest) -> ChatMessageResponse:
    """
    Send a chat message and get response.
    
    Returns:
        Chat response with answer and metadata
    """
    try:
        response = await chat_service.process_message(
            conversation_id=request.conversation_id,
            message=request.message,
            image_data=None,
            user_id=request.user_id
        )
        
        return ChatMessageResponse(**response)
        
    except Exception as e:
        logger.error(f"❌ Error processing message: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/image", response_model=ImageUploadResponse)
async def upload_image(
    conversation_id: str = Form(...),
    message: Optional[str] = Form(None),
    user_id: Optional[str] = Form(None),
    image: UploadFile = File(...)
) -> ImageUploadResponse:
    """
    Upload an image with optional message and get RAG response.
    
    Args:
        conversation_id: Conversation UUID
        message: Optional message text
        user_id: Optional user ID
        image: Image file (JPEG, PNG, WebP)
        
    Returns:
        Response with image analysis and RAG answer
    """
    try:
        # Validate image file
        if image.content_type not in ['image/jpeg', 'image/png', 'image/webp']:
            raise HTTPException(
                status_code=400,
                detail="Invalid image format. Supported: JPEG, PNG, WebP"
            )
        
        # Read image data
        image_data = await image.read()
        
        if len(image_data) == 0:
            raise HTTPException(status_code=400, detail="Empty image file")
        
        # Process message with image
        response = await chat_service.process_message(
            conversation_id=conversation_id,
            message=message or "Analyze this nail image and provide advice.",
            image_data=image_data,
            user_id=user_id
        )
        
        return ImageUploadResponse(**response)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error processing image: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/conversation/{conversation_id}/history", response_model=ConversationHistoryResponse)
async def get_conversation_history(conversation_id: str) -> ConversationHistoryResponse:
    """
    Get conversation history.
    
    Args:
        conversation_id: Conversation UUID
        
    Returns:
        Conversation history with messages
    """
    try:
        history = await chat_service.get_conversation_history(conversation_id)
        
        if history is None:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        return ConversationHistoryResponse(
            conversation_id=conversation_id,
            messages=history,
            message_count=len(history)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error retrieving conversation history: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/conversation/{conversation_id}")
async def clear_conversation(conversation_id: str) -> dict:
    """
    Clear conversation from short-term memory.
    
    Args:
        conversation_id: Conversation UUID
        
    Returns:
        Success message
    """
    try:
        chat_service.clear_conversation(conversation_id)
        return {"message": "Conversation cleared", "conversation_id": conversation_id}
    except Exception as e:
        logger.error(f"❌ Error clearing conversation: {e}")
        raise HTTPException(status_code=500, detail=str(e))

