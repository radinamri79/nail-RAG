"""
WebSocket routes for streaming chat
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Optional
import json
from app.services.chat_service import chat_service
from app.logger import get_logger

logger = get_logger("websocket_routes")

router = APIRouter(tags=["websocket"])


class ConnectionManager:
    """Manages WebSocket connections."""
    
    def __init__(self):
        self.active_connections: dict[str, WebSocket] = {}
    
    async def connect(self, websocket: WebSocket, conversation_id: str):
        """Accept WebSocket connection."""
        await websocket.accept()
        self.active_connections[conversation_id] = websocket
        logger.info(f"✅ WebSocket connected: {conversation_id[:8]}...")
    
    def disconnect(self, conversation_id: str):
        """Remove WebSocket connection."""
        if conversation_id in self.active_connections:
            del self.active_connections[conversation_id]
            logger.info(f"✅ WebSocket disconnected: {conversation_id[:8]}...")
    
    async def send_message(self, conversation_id: str, message: dict):
        """Send message to specific connection."""
        if conversation_id in self.active_connections:
            websocket = self.active_connections[conversation_id]
            try:
                await websocket.send_json(message)
            except Exception as e:
                logger.error(f"❌ Error sending WebSocket message: {e}")
                self.disconnect(conversation_id)


# Global connection manager
connection_manager = ConnectionManager()


@router.websocket("/ws/chat/{conversation_id}")
async def websocket_chat(websocket: WebSocket, conversation_id: str):
    """
    WebSocket endpoint for streaming chat responses.
    
    Args:
        websocket: WebSocket connection
        conversation_id: Conversation UUID
    """
    await connection_manager.connect(websocket, conversation_id)
    
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            
            try:
                message_data = json.loads(data)
                message_type = message_data.get("type", "message")
                message_text = message_data.get("message", "")
                user_id = message_data.get("user_id")
                image_data_base64 = message_data.get("image_data")  # Base64 encoded image
                
                if message_type == "ping":
                    # Respond to ping
                    await websocket.send_json({"type": "pong"})
                    continue
                
                if not message_text and not image_data_base64:
                    await websocket.send_json({
                        "type": "error",
                        "message": "Message or image required"
                    })
                    continue
                
                # Decode image if provided
                image_data = None
                if image_data_base64:
                    import base64
                    try:
                        image_data = base64.b64decode(image_data_base64)
                    except Exception as e:
                        logger.error(f"❌ Error decoding image: {e}")
                        await websocket.send_json({
                            "type": "error",
                            "message": "Invalid image data"
                        })
                        continue
                
                # Send start signal
                await websocket.send_json({
                    "type": "start",
                    "conversation_id": conversation_id
                })
                
                # Stream response
                full_response = ""
                async for token in chat_service.stream_response(
                    conversation_id=conversation_id,
                    message=message_text or "Analyze this nail image.",
                    image_data=image_data,
                    user_id=user_id
                ):
                    full_response += token
                    await websocket.send_json({
                        "type": "token",
                        "token": token,
                        "conversation_id": conversation_id
                    })
                
                # Send completion signal
                await websocket.send_json({
                    "type": "complete",
                    "conversation_id": conversation_id,
                    "full_response": full_response
                })
                
            except json.JSONDecodeError:
                await websocket.send_json({
                    "type": "error",
                    "message": "Invalid JSON format"
                })
            except Exception as e:
                logger.error(f"❌ Error processing WebSocket message: {e}")
                await websocket.send_json({
                    "type": "error",
                    "message": str(e)
                })
                
    except WebSocketDisconnect:
        connection_manager.disconnect(conversation_id)
        logger.info(f"✅ WebSocket disconnected: {conversation_id[:8]}...")
    except Exception as e:
        logger.error(f"❌ WebSocket error: {e}")
        connection_manager.disconnect(conversation_id)
        raise


@router.get("/ws/health")
async def websocket_health():
    """Health check for WebSocket service."""
    return {
        "status": "ok",
        "active_connections": len(connection_manager.active_connections)
    }

