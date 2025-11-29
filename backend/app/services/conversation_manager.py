"""
Conversation Manager - Short-term and long-term memory management
"""
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone
import uuid
from app.models.weaviate_client import get_weaviate_client
from app.constants import SHORT_TERM_MEMORY_LIMIT, CollectionNames
from app.config import settings
from app.logger import get_logger

logger = get_logger("conversation_manager")


class ConversationManager:
    """Manages conversation memory (short-term and long-term)."""
    
    def __init__(self):
        # Short-term memory: conversation_id -> list of last N messages
        self._short_term_memory: Dict[str, List[Dict[str, Any]]] = {}
        self._initialized = False
    
    async def initialize(self) -> None:
        """Initialize conversation manager and ensure Weaviate collection exists."""
        if self._initialized:
            return
        
        try:
            # Ensure conversation history collection exists
            await self._ensure_conversation_collection()
            self._initialized = True
            logger.info("✅ Conversation manager initialized")
        except Exception as e:
            logger.error(f"❌ Error initializing conversation manager: {e}")
            raise
    
    async def _ensure_conversation_collection(self) -> None:
        """Ensure ConversationHistory collection exists in Weaviate."""
        try:
            from weaviate.classes.config import Configure, Property, DataType
            
            client = get_weaviate_client()
            collection_name = CollectionNames.CONVERSATION_HISTORY
            
            # client.collections.exists() is synchronous, no await needed
            if client.collections.exists(collection_name):
                logger.debug(f"ℹ️ Collection '{collection_name}' already exists")
                return
            
            # Create collection
            client.collections.create(
                name=collection_name,
                description="Conversation history for long-term memory",
                properties=[
                    Property(name="conversation_id", data_type=DataType.TEXT, description="Conversation UUID"),
                    Property(name="user_id", data_type=DataType.TEXT, description="User ID (optional)"),
                    Property(name="messages", data_type=DataType.TEXT_ARRAY, description="Array of message contents"),
                    Property(name="message_roles", data_type=DataType.TEXT_ARRAY, description="Array of message roles"),
                    Property(name="message_timestamps", data_type=DataType.TEXT_ARRAY, description="Array of message timestamps"),
                    Property(name="created_at", data_type=DataType.TEXT, description="Conversation creation timestamp"),
                    Property(name="updated_at", data_type=DataType.TEXT, description="Last update timestamp"),
                ],
                # No vectorizer needed for conversation history (we can add one later if needed)
            )
            
            logger.info(f"✅ Created collection: {collection_name}")
            
        except Exception as e:
            logger.error(f"❌ Error ensuring conversation collection: {e}")
            raise
    
    def add_message(
        self,
        conversation_id: str,
        role: str,
        content: str,
        message_id: Optional[str] = None,
        image_url: Optional[str] = None,
        image_analysis: Optional[str] = None
    ) -> str:
        """
        Add message to short-term memory.
        
        Args:
            conversation_id: Conversation UUID
            role: Message role ('user' or 'assistant')
            content: Message content
            message_id: Optional message UUID
            image_url: Optional image URL
            image_analysis: Optional image analysis text
            
        Returns:
            Message UUID
        """
        if message_id is None:
            message_id = str(uuid.uuid4())
        
        message = {
            "message_id": message_id,
            "role": role,
            "content": content,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "image_url": image_url,
            "image_analysis": image_analysis,
        }
        
        # Initialize conversation if needed
        if conversation_id not in self._short_term_memory:
            self._short_term_memory[conversation_id] = []
        
        # Add message
        self._short_term_memory[conversation_id].append(message)
        
        # Keep only last N messages
        if len(self._short_term_memory[conversation_id]) > SHORT_TERM_MEMORY_LIMIT:
            self._short_term_memory[conversation_id] = self._short_term_memory[conversation_id][-SHORT_TERM_MEMORY_LIMIT:]
        
        logger.debug(f"✅ Added message to conversation {conversation_id[:8]}... ({len(self._short_term_memory[conversation_id])} messages)")
        
        return message_id
    
    def get_recent_context(self, conversation_id: str) -> List[Dict[str, str]]:
        """
        Get recent conversation context (last N messages).
        
        Args:
            conversation_id: Conversation UUID
            
        Returns:
            List of message dictionaries (role, content)
        """
        if conversation_id not in self._short_term_memory:
            return []
        
        messages = self._short_term_memory[conversation_id]
        
        # Return in format expected by RAG service
        return [
            {
                "role": msg["role"],
                "content": msg["content"]
            }
            for msg in messages
        ]
    
    async def save_conversation(
        self,
        conversation_id: str,
        user_id: Optional[str] = None
    ) -> bool:
        """
        Save conversation to Weaviate (long-term memory).
        
        Args:
            conversation_id: Conversation UUID
            user_id: Optional user ID
            
        Returns:
            True if successful
        """
        try:
            await self.initialize()
            
            if conversation_id not in self._short_term_memory:
                logger.warning(f"⚠️ No messages to save for conversation {conversation_id}")
                return False
            
            messages = self._short_term_memory[conversation_id]
            
            if not messages:
                return False
            
            # Prepare data for Weaviate
            message_contents = [msg["content"] for msg in messages]
            message_roles = [msg["role"] for msg in messages]
            message_timestamps = [msg["timestamp"] for msg in messages]
            
            client = get_weaviate_client()
            collection = client.collections.get(CollectionNames.CONVERSATION_HISTORY)
            
            # Check if conversation already exists
            result = collection.query.fetch_objects(
                where={
                    "path": ["conversation_id"],
                    "operator": "Equal",
                    "valueText": conversation_id
                },
                limit=1
            )
            
            now = datetime.now(timezone.utc).isoformat()
            
            if len(result.objects) > 0:
                # Update existing conversation
                obj_uuid = result.objects[0].uuid
                collection.data.update(
                    uuid=obj_uuid,
                    properties={
                        "messages": message_contents,
                        "message_roles": message_roles,
                        "message_timestamps": message_timestamps,
                        "updated_at": now,
                    }
                )
                logger.debug(f"✅ Updated conversation {conversation_id[:8]}... in Weaviate")
            else:
                # Create new conversation
                collection.data.insert(
                    properties={
                        "conversation_id": conversation_id,
                        "user_id": user_id or "",
                        "messages": message_contents,
                        "message_roles": message_roles,
                        "message_timestamps": message_timestamps,
                        "created_at": now,
                        "updated_at": now,
                    }
                )
                logger.info(f"✅ Saved conversation {conversation_id[:8]}... to Weaviate")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error saving conversation: {e}")
            return False
    
    async def get_conversation_history(
        self,
        conversation_id: str
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Retrieve conversation history from Weaviate.
        
        Args:
            conversation_id: Conversation UUID
            
        Returns:
            List of messages or None if not found
        """
        try:
            await self.initialize()
            
            client = get_weaviate_client()
            collection = client.collections.get(CollectionNames.CONVERSATION_HISTORY)
            
            result = collection.query.fetch_objects(
                where={
                    "path": ["conversation_id"],
                    "operator": "Equal",
                    "valueText": conversation_id
                },
                limit=1,
                return_properties=["messages", "message_roles", "message_timestamps"]
            )
            
            if len(result.objects) == 0:
                return None
            
            obj = result.objects[0]
            messages = obj.properties.get("messages", [])
            roles = obj.properties.get("message_roles", [])
            timestamps = obj.properties.get("message_timestamps", [])
            
            # Reconstruct messages
            history = []
            for i in range(len(messages)):
                history.append({
                    "role": roles[i] if i < len(roles) else "user",
                    "content": messages[i],
                    "timestamp": timestamps[i] if i < len(timestamps) else None,
                })
            
            logger.debug(f"✅ Retrieved {len(history)} messages from conversation {conversation_id[:8]}...")
            return history
            
        except Exception as e:
            logger.error(f"❌ Error retrieving conversation history: {e}")
            return None
    
    def clear_short_term(self, conversation_id: str) -> None:
        """
        Clear short-term memory for a conversation.
        
        Args:
            conversation_id: Conversation UUID
        """
        if conversation_id in self._short_term_memory:
            del self._short_term_memory[conversation_id]
            logger.debug(f"✅ Cleared short-term memory for conversation {conversation_id[:8]}...")
    
    def get_conversation_stats(self, conversation_id: str) -> Dict[str, Any]:
        """
        Get statistics for a conversation.
        
        Args:
            conversation_id: Conversation UUID
            
        Returns:
            Dictionary with statistics
        """
        if conversation_id not in self._short_term_memory:
            return {
                "message_count": 0,
                "user_messages": 0,
                "assistant_messages": 0,
            }
        
        messages = self._short_term_memory[conversation_id]
        
        return {
            "message_count": len(messages),
            "user_messages": sum(1 for msg in messages if msg["role"] == "user"),
            "assistant_messages": sum(1 for msg in messages if msg["role"] == "assistant"),
        }


# Global instance
conversation_manager = ConversationManager()

