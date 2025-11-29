"""
Category Routing Service - Route queries to most relevant collections
"""
from typing import List, Optional
from app.utils.openai_client import get_openai_client
from app.constants import CollectionNames
from app.config import settings
from app.logger import get_logger

logger = get_logger("category_routing")


class CategoryRoutingService:
    """Service for routing queries to relevant collections."""
    
    def __init__(self):
        self.client = None
        self._enabled = True
    
    def _get_client(self):
        """Lazy load OpenAI client."""
        if self.client is None:
            self.client = get_openai_client()
        return self.client
    
    async def route_query(
        self,
        query: str,
        image_context: Optional[str] = None
    ) -> List[str]:
        """
        Route query to 1-2 most relevant collections.
        
        Args:
            query: User query
            image_context: Optional image analysis context
            
        Returns:
            List of collection names to search
        """
        if not self._enabled:
            # Return all collections if routing disabled
            return CollectionNames.get_all_nail_collections()
        
        try:
            # Build classification prompt
            collections_info = {
                CollectionNames.NAIL_COLOR_THEORY: "Color theory, outfit matching, nail polish colors that match clothes",
                CollectionNames.NAIL_SKIN_TONE: "Skin tone advice, nail colors for different skin tones, undertones",
                CollectionNames.NAIL_SEASONAL: "Seasonal nail colors, occasion-based advice, holiday themes",
                CollectionNames.NAIL_SHAPE: "Nail shapes, finger shape advice, nail design based on hand shape"
            }
            
            collections_list = "\n".join([
                f"- {name}: {desc}"
                for name, desc in collections_info.items()
            ])
            
            prompt = f"""Classify this nail design query into 1-2 most relevant categories:

Query: {query}
{('Image context: ' + image_context) if image_context else ''}

Available categories:
{collections_list}

Respond with ONLY the category name(s) separated by commas (e.g., "NailColorTheory, NailSkinTone" or just "NailSeasonal").
If unsure, return all categories separated by commas."""

            client = self._get_client()
            response = await client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": "You are a query classifier. Return only category names."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,  # Low temperature for consistent classification
                max_completion_tokens=100
            )
            
            result = response.choices[0].message.content.strip()
            
            # Parse result
            selected_collections = []
            for collection_name in CollectionNames.get_all_nail_collections():
                if collection_name in result:
                    selected_collections.append(collection_name)
            
            # If no collections found or all found, return all
            if not selected_collections or len(selected_collections) == len(CollectionNames.get_all_nail_collections()):
                logger.debug(f"⚠️ Routing returned all collections for query: {query[:50]}...")
                return CollectionNames.get_all_nail_collections()
            
            logger.debug(f"✅ Routed query to {len(selected_collections)} collections: {selected_collections}")
            return selected_collections
            
        except Exception as e:
            logger.warning(f"⚠️ Category routing failed: {e}, using all collections")
            return CollectionNames.get_all_nail_collections()
    
    def enable(self):
        """Enable category routing."""
        self._enabled = True
        logger.info("✅ Category routing enabled")
    
    def disable(self):
        """Disable category routing (use all collections)."""
        self._enabled = False
        logger.info("⚠️ Category routing disabled")


# Global instance
category_routing_service = CategoryRoutingService()

