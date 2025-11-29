"""
Chat Service - Integrates RAG, image, multilingual, and conversation services
"""
from typing import Dict, Any, Optional, List, AsyncGenerator
import uuid
from app.services.rag_service import rag_service
from app.services.image_service import image_service
from app.services.multilingual_service import multilingual_service
from app.services.conversation_manager import conversation_manager
from app.constants import CONVERSATION_HISTORY_LIMIT
from app.logger import get_logger

logger = get_logger("chat_service")


class ChatService:
    """Service for handling chat interactions."""
    
    def __init__(self):
        self._initialized = False
    
    async def initialize(self) -> None:
        """Initialize chat service and dependencies."""
        if self._initialized:
            return
        
        try:
            await conversation_manager.initialize()
            self._initialized = True
            logger.info("✅ Chat service initialized")
        except Exception as e:
            logger.error(f"❌ Error initializing chat service: {e}")
            raise
    
    async def process_message(
        self,
        conversation_id: str,
        message: str,
        image_data: Optional[bytes] = None,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Process a chat message and generate response.
        
        Args:
            conversation_id: Conversation UUID
            message: User message text
            image_data: Optional image file bytes
            user_id: Optional user ID
            
        Returns:
            Dictionary with response and metadata
        """
        try:
            await self.initialize()
            
            # Step 1: Detect language
            lang_result = await multilingual_service.detect_language(message)
            detected_language = lang_result["detected_language"]
            logger.info(f"🌐 Detected language: {detected_language}")
            
            # Step 2: Translate to English if needed
            if detected_language != "en":
                translated_query = await multilingual_service.translate_to_english(message, detected_language)
            else:
                translated_query = message
            
            # Step 3: Analyze image if provided
            image_context = None
            if image_data:
                logger.info("🖼️ Analyzing image...")
                image_result = await image_service.analyze_nail_image(image_data, translated_query)
                if image_result.get("analysis"):
                    image_context = image_result["analysis"]
                    logger.info("✅ Image analysis completed")
            
            # Step 4: Get conversation history and message count
            recent_context = conversation_manager.get_recent_context(conversation_id)
            stats = conversation_manager.get_conversation_stats(conversation_id)
            user_message_count = stats.get("user_messages", 0)
            
            # Step 5: Process query with RAG
            logger.info(f"🔍 Processing query with RAG...")
            rag_response = await rag_service.process_query(
                query=translated_query,
                conversation_history=recent_context,
                image_context=image_context,
                language=detected_language,
                user_message_count=user_message_count
            )
            
            answer = rag_response.get("answer", "I apologize, but I couldn't generate a response.")
            
            # Step 6: Translate response back to user's language if needed
            if detected_language != "en":
                answer = await multilingual_service.translate_response(answer, detected_language)
            
            # Step 7: Add messages to conversation
            user_message_id = conversation_manager.add_message(
                conversation_id=conversation_id,
                role="user",
                content=message,
                image_analysis=image_context
            )
            
            assistant_message_id = conversation_manager.add_message(
                conversation_id=conversation_id,
                role="assistant",
                content=answer
            )
            
            # Step 8: Save conversation to long-term memory (async, don't wait)
            # We can do this in background to not block response
            import asyncio
            asyncio.create_task(conversation_manager.save_conversation(conversation_id, user_id))
            
            # Build response
            response = {
                "conversation_id": conversation_id,
                "message_id": assistant_message_id,
                "answer": answer,
                "language": detected_language,
                "context_sources": rag_response.get("context_sources", []),
                "image_analyzed": image_data is not None,
                "tokens_used": rag_response.get("tokens_used", 0),
            }
            
            logger.info(f"✅ Generated response for conversation {conversation_id[:8]}...")
            
            return response
            
        except Exception as e:
            logger.error(f"❌ Error processing message: {e}")
            return {
                "conversation_id": conversation_id,
                "message_id": str(uuid.uuid4()),
                "answer": "I apologize, but I encountered an error processing your message. Please try again.",
                "language": "en",
                "context_sources": [],
                "image_analyzed": False,
                "tokens_used": 0,
                "error": str(e)
            }
    
    async def stream_response(
        self,
        conversation_id: str,
        message: str,
        image_data: Optional[bytes] = None,
        user_id: Optional[str] = None
    ) -> AsyncGenerator[str, None]:
        """
        Stream response tokens as they're generated.
        
        Args:
            conversation_id: Conversation UUID
            message: User message text
            image_data: Optional image file bytes
            user_id: Optional user ID
            
        Yields:
            Response tokens as strings
        """
        try:
            await self.initialize()
            
            # Step 1-3: Same as process_message (detect language, translate, analyze image)
            lang_result = await multilingual_service.detect_language(message)
            detected_language = lang_result["detected_language"]
            
            if detected_language != "en":
                translated_query = await multilingual_service.translate_to_english(message, detected_language)
            else:
                translated_query = message
            
            image_context = None
            if image_data:
                image_result = await image_service.analyze_nail_image(image_data, translated_query)
                if image_result.get("analysis"):
                    image_context = image_result["analysis"]
            
            # Step 4: Get context and generate streaming response
            recent_context = conversation_manager.get_recent_context(conversation_id)
            stats = conversation_manager.get_conversation_stats(conversation_id)
            user_message_count = stats.get("user_messages", 0)
            
            # Retrieve context
            context = await rag_service.retrieve_context(
                query=translated_query,
                limit=8
            )
            
            # Generate streaming response
            from app.utils.openai_client import get_openai_client
            from app.utils.prompt_loader import get_prompt
            
            system_prompt = get_prompt("rag_system")
            formatted_context = rag_service._format_context(context)
            
            system_message = f"""{system_prompt}

## Retrieved Context:
{formatted_context}

## Conversation History:
You have access to the conversation history below. Use it to provide context-aware responses:
- Reference previous topics we discussed when relevant
- Build on information the user shared earlier (skin tone, preferences, occasions, etc.)
- Make the conversation feel continuous and natural
- Remember what the user mentioned in previous messages

## Instructions:
- Answer based on the retrieved context above
- When the retrieved context doesn't fully answer the question, ask thoughtful follow-up questions to better understand the user's needs
- Provide specific, actionable advice with color names, shape recommendations, and styling tips
- Respond in the same language as the user's query (detected: {detected_language})
- Be warm, friendly, and conversational - like chatting with a knowledgeable friend
- This is the user's message number: {user_message_count}
"""
            
            if image_context:
                system_message += f"\n## Image Analysis:\n{image_context}\n"
            
            messages = [
                {"role": "system", "content": system_message}
            ]
            
            if recent_context:
                history_limit = min(CONVERSATION_HISTORY_LIMIT, len(recent_context))
                for msg in recent_context[-history_limit:]:
                    messages.append(msg)
            
            messages.append({"role": "user", "content": translated_query})
            
            # Stream response
            client = get_openai_client()
            full_response = ""
            
            from app.config import settings
            
            async for chunk in client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=messages,
                temperature=settings.temperature_rag,
                max_completion_tokens=settings.max_tokens_response,
                stream=True
            ):
                if chunk.choices[0].delta.content:
                    token = chunk.choices[0].delta.content
                    full_response += token
                    yield token
            
            # Add messages to conversation after streaming completes
            conversation_manager.add_message(
                conversation_id=conversation_id,
                role="user",
                content=message,
                image_analysis=image_context
            )
            
            # Translate if needed
            if detected_language != "en":
                full_response = await multilingual_service.translate_response(full_response, detected_language)
            
            conversation_manager.add_message(
                conversation_id=conversation_id,
                role="assistant",
                content=full_response
            )
            
            # Save conversation
            import asyncio
            asyncio.create_task(conversation_manager.save_conversation(conversation_id, user_id))
            
        except Exception as e:
            logger.error(f"❌ Error streaming response: {e}")
            yield f"Error: {str(e)}"
    
    async def create_conversation(self, user_id: Optional[str] = None) -> str:
        """
        Create a new conversation.
        
        Args:
            user_id: Optional user ID
            
        Returns:
            Conversation UUID
        """
        conversation_id = str(uuid.uuid4())
        logger.info(f"✅ Created new conversation: {conversation_id[:8]}...")
        return conversation_id
    
    async def get_conversation_history(
        self,
        conversation_id: str
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Get conversation history.
        
        Args:
            conversation_id: Conversation UUID
            
        Returns:
            List of messages or None
        """
        # Try short-term first
        recent = conversation_manager.get_recent_context(conversation_id)
        if recent:
            return recent
        
        # Try long-term
        return await conversation_manager.get_conversation_history(conversation_id)
    
    def clear_conversation(self, conversation_id: str) -> None:
        """
        Clear conversation from short-term memory.
        
        Args:
            conversation_id: Conversation UUID
        """
        conversation_manager.clear_short_term(conversation_id)
        logger.info(f"✅ Cleared conversation {conversation_id[:8]}...")


# Global instance
chat_service = ChatService()

