"""
RAG Service - Core retrieval and generation logic
"""
from typing import List, Dict, Any, Optional
import asyncio
from app.services.weaviate_service import weaviate_service
from app.services.category_routing_service import category_routing_service
from app.services.response_cache_service import response_cache_service
from app.utils.openai_client import get_openai_client
from app.utils.prompt_loader import get_prompt
from app.config import settings
from app.constants import (
    DEFAULT_SEARCH_LIMIT,
    similarity_score_threshold,
    MAX_QUERY_VARIANTS,
    CONVERSATION_HISTORY_LIMIT
)
from app.logger import get_logger

logger = get_logger("rag_service")


class RAGService:
    """Service for Retrieval-Augmented Generation."""
    
    def __init__(self):
        self.client = None
    
    def _get_client(self):
        """Lazy load OpenAI client."""
        if self.client is None:
            self.client = get_openai_client()
        return self.client
    
    async def retrieve_context(
        self,
        query: str,
        collection_names: Optional[List[str]] = None,
        limit: int = DEFAULT_SEARCH_LIMIT,
        similarity_threshold: float = similarity_score_threshold,
        use_query_expansion: bool = True,
        image_context: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieve relevant context from Weaviate collections with optimizations.
        
        Args:
            query: User query
            collection_names: Collections to search (None = all 4, or use routing)
            limit: Number of results to retrieve
            similarity_threshold: Minimum similarity score
            use_query_expansion: Whether to use query expansion
            image_context: Optional image analysis context for routing
            
        Returns:
            List of relevant context chunks with metadata (reranked)
        """
        try:
            logger.debug(f"🔍 Retrieving context for query: {query[:50]}...")
            
            # Step 1: Route to relevant collections if not specified
            if collection_names is None and settings.CATEGORY_ROUTING_ENABLED:
                collection_names = await category_routing_service.route_query(query, image_context)
                logger.debug(f"📍 Routed to {len(collection_names)} collections")
            
            # Step 2: Expand query if enabled
            queries_to_search = [query]
            if use_query_expansion and settings.QUERY_EXPANSION_ENABLED:
                try:
                    expanded = await self.expand_query(query)
                    queries_to_search = expanded[:MAX_QUERY_VARIANTS]
                    logger.debug(f"🔀 Expanded query to {len(queries_to_search)} variants")
                except Exception as e:
                    logger.warning(f"⚠️ Query expansion failed: {e}, using original query")
            
            # Step 3: Search with all query variants in parallel
            all_results = []
            search_tasks = []
            
            for search_query in queries_to_search:
                search_tasks.append(
                    weaviate_service.search_similar(
                        query=search_query,
                        collection_names=collection_names,
                        limit=limit * 2,  # Get more results for reranking
                        similarity_threshold=similarity_threshold
                    )
                )
            
            results_list = await asyncio.gather(*search_tasks, return_exceptions=True)
            
            # Combine results
            for results in results_list:
                if isinstance(results, Exception):
                    logger.error(f"❌ Search error: {results}")
                    continue
                all_results.extend(results)
            
            # Step 4: Rerank results
            reranked = self._rerank_results(all_results, query)
            
            # Step 5: Filter and return top results
            top_results = reranked[:limit]
            logger.info(f"✅ Retrieved {len(top_results)} context chunks (from {len(all_results)} candidates)")
            
            return top_results
            
        except Exception as e:
            logger.error(f"❌ Error retrieving context: {e}")
            return []
    
    def _rerank_results(
        self,
        results: List[Dict[str, Any]],
        query: str
    ) -> List[Dict[str, Any]]:
        """
        Rerank results by relevance to query.
        
        Args:
            results: List of search results
            query: Original query
            
        Returns:
            Reranked results
        """
        if not results:
            return []
        
        # Remove duplicates by document_id and chunk_index
        seen = set()
        unique_results = []
        for result in results:
            key = (result.get("document_id"), result.get("chunk_index"))
            if key not in seen:
                seen.add(key)
                unique_results.append(result)
        
        # Enhanced scoring: combine similarity score with query relevance
        query_lower = query.lower()
        query_words = set(query_lower.split())
        
        for result in unique_results:
            score = result.get("score", 0)
            content = result.get("content", "").lower()
            title = result.get("source_title", "").lower()
            
            # Boost score if query words appear in title
            title_matches = sum(1 for word in query_words if word in title)
            if title_matches > 0:
                score += 0.1 * title_matches
            
            # Boost score if query words appear in content
            content_matches = sum(1 for word in query_words if word in content)
            if content_matches > 0:
                score += 0.05 * min(content_matches, 5)  # Cap at 5 matches
            
            # Update score
            result["reranked_score"] = min(score, 1.0)  # Cap at 1.0
        
        # Sort by reranked score
        unique_results.sort(key=lambda x: x.get("reranked_score", x.get("score", 0)), reverse=True)
        
        return unique_results
    
    def _format_context(self, results: List[Dict[str, Any]]) -> str:
        """
        Format retrieved context for GPT-5.1 prompt.
        
        Args:
            results: List of search results
            
        Returns:
            Formatted context string
        """
        if not results:
            return "No relevant context found."
        
        context_parts = []
        for idx, result in enumerate(results, 1):
            context_parts.append(f"""
[Context {idx}]
Source: {result.get('source_title', 'Unknown')}
Category: {result.get('category', 'Unknown')}
Content: {result.get('content', '')}
Score: {result.get('score', 0):.3f}
""")
        
        return "\n".join(context_parts)
    
    async def generate_response(
        self,
        query: str,
        context: List[Dict[str, Any]],
        conversation_history: Optional[List[Dict[str, str]]] = None,
        image_context: Optional[str] = None,
        language: str = "en",
        user_message_count: int = 0
    ) -> Dict[str, Any]:
        """
        Generate response using GPT-5.1 with retrieved context.
        
        Args:
            query: User query
            context: Retrieved context chunks
            conversation_history: Previous conversation messages
            image_context: Image analysis context (if image provided)
            language: Response language (en, fi, sv)
            user_message_count: Number of user messages in conversation (for greeting logic)
            
        Returns:
            Dictionary with response and metadata
        """
        try:
            # Load RAG system prompt
            system_prompt = get_prompt("rag_system")
            
            # Format context
            formatted_context = self._format_context(context)
            
            # Build conversation messages
            messages = []
            
            # System prompt with context
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
- Respond in the same language as the user's query (detected: {language})
- Be warm, friendly, and conversational - like chatting with a knowledgeable friend
- This is the user's message number: {user_message_count}
"""
            
            if image_context:
                system_message += f"\n## Image Analysis:\n{image_context}\n"
            
            messages.append({"role": "system", "content": system_message})
            
            # Add conversation history (last N messages for context)
            if conversation_history:
                history_limit = min(CONVERSATION_HISTORY_LIMIT, len(conversation_history))
                for msg in conversation_history[-history_limit:]:
                    messages.append({
                        "role": msg.get("role", "user"),
                        "content": msg.get("content", "")
                    })
            
            # Add current query
            messages.append({"role": "user", "content": query})
            
            # Generate response
            client = self._get_client()
            response = await client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=messages,
                temperature=settings.temperature_rag,
                max_completion_tokens=settings.max_tokens_response,
                stream=False
            )
            
            answer = response.choices[0].message.content
            
            # Validate answer quality
            quality_score = self._validate_answer_quality(answer, context, query)
            
            logger.info(f"✅ Generated response ({len(answer)} chars, quality: {quality_score:.2f})")
            
            return {
                "answer": answer,
                "context_count": len(context),
                "model": settings.OPENAI_MODEL,
                "tokens_used": response.usage.total_tokens if response.usage else 0,
                "quality_score": quality_score,
            }
            
        except Exception as e:
            logger.error(f"❌ Error generating response: {e}")
            return {
                "answer": "I apologize, but I encountered an error generating a response. Please try again.",
                "context_count": len(context),
                "error": str(e)
            }
    
    async def process_query(
        self,
        query: str,
        collection_names: Optional[List[str]] = None,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        image_context: Optional[str] = None,
        language: str = "en",
        user_message_count: int = 0,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        Main entry point: retrieve context and generate response with optimizations.
        
        Args:
            query: User query
            collection_names: Collections to search (None = all 4, or use routing)
            conversation_history: Previous conversation messages
            image_context: Image analysis context
            language: Response language
            user_message_count: Number of user messages (for greeting logic)
            use_cache: Whether to use response cache
            
        Returns:
            Complete response with answer and metadata
        """
        try:
            # Check cache first
            if use_cache and settings.CACHING_ENABLED:
                cache_key_context = None
                if conversation_history:
                    # Use last 2 messages as context for cache key
                    cache_key_context = "|".join([
                        msg.get("content", "")[:50]
                        for msg in conversation_history[-2:]
                    ])
                
                cached = response_cache_service.get(query, cache_key_context)
                if cached:
                    logger.info(f"✅ Cache hit for query: {query[:50]}...")
                    return cached
            
            # Step 1: Retrieve context (with optimizations)
            context = await self.retrieve_context(
                query=query,
                collection_names=collection_names,
                limit=settings.max_contexts_per_query,
                use_query_expansion=settings.QUERY_EXPANSION_ENABLED,
                image_context=image_context
            )
            
            # Step 2: Generate response
            response = await self.generate_response(
                query=query,
                context=context,
                conversation_history=conversation_history,
                image_context=image_context,
                language=language,
                user_message_count=user_message_count
            )
            
            # Add context metadata
            response["context_sources"] = [
                {
                    "title": r.get("source_title"),
                    "category": r.get("category"),
                    "score": r.get("reranked_score", r.get("score", 0))
                }
                for r in context[:5]  # Top 5 sources
            ]
            
            # Cache response
            if use_cache and settings.CACHING_ENABLED:
                cache_key_context = None
                if conversation_history:
                    cache_key_context = "|".join([
                        msg.get("content", "")[:50]
                        for msg in conversation_history[-2:]
                    ])
                response_cache_service.set(query, response, cache_key_context)
            
            return response
            
        except Exception as e:
            logger.error(f"❌ Error processing query: {e}")
            return {
                "answer": "I apologize, but I encountered an error. Please try again.",
                "error": str(e)
            }
    
    async def expand_query(self, query: str) -> List[str]:
        """
        Generate query variants for better retrieval.
        
        Args:
            query: Original query
            
        Returns:
            List of query variants
        """
        try:
            client = self._get_client()
            
            prompt = f"""Generate 3-5 alternative phrasings or expansions of this query for better search results:
Query: {query}

Return only the alternative queries, one per line, without numbering or bullets."""

            response = await client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": "You are a query expansion assistant. Generate alternative phrasings for search queries."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_completion_tokens=1000
            )
            
            variants = [
                line.strip()
                for line in response.choices[0].message.content.split('\n')
                if line.strip() and not line.strip().startswith(('1.', '2.', '3.', '-', '*'))
            ]
            
            # Include original query
            all_queries = [query] + variants[:4]  # Max 5 total
            
            logger.debug(f"✅ Generated {len(variants)} query variants")
            return all_queries
            
        except Exception as e:
            logger.warning(f"⚠️ Query expansion failed: {e}, using original query")
            return [query]
    
    def _validate_answer_quality(
        self,
        answer: str,
        context: List[Dict[str, Any]],
        query: str
    ) -> float:
        """
        Validate answer quality and return score (0.0 to 1.0).
        
        Args:
            answer: Generated answer
            context: Retrieved context
            query: Original query
            
        Returns:
            Quality score between 0.0 and 1.0
        """
        if not answer or not context:
            return 0.0
        
        score = 1.0
        
        # Check for "I don't know" patterns
        uncertainty_patterns = [
            "i don't know",
            "i'm not sure",
            "i cannot",
            "i'm unable",
            "no information",
            "not available"
        ]
        answer_lower = answer.lower()
        for pattern in uncertainty_patterns:
            if pattern in answer_lower:
                score -= 0.3
                break
        
        # Check if answer references context (mentions titles or categories)
        if context:
            context_titles = [r.get("source_title", "").lower() for r in context[:3]]
            context_categories = [r.get("category", "").lower() for r in context[:3]]
            
            references_context = False
            for title in context_titles:
                if title and any(word in answer_lower for word in title.split()[:3]):  # Check first 3 words
                    references_context = True
                    break
            
            if not references_context:
                score -= 0.2
        
        # Check answer length (too short might be incomplete)
        word_count = len(answer.split())
        if word_count < 20:
            score -= 0.2
        elif word_count > 500:
            score -= 0.1  # Too long might be verbose
        
        # Ensure score is between 0 and 1
        return max(0.0, min(1.0, score))


# Global instance
rag_service = RAGService()

