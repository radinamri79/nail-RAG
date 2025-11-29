"""
Weaviate service for collection management, chunking, import, and search
"""
from typing import List, Dict, Any, Optional
import asyncio
from weaviate.classes.config import Configure, Property, DataType
from weaviate.classes.query import MetadataQuery
from app.models.weaviate_client import get_weaviate_client
from app.models.pydantic_models import NailGuideDocument
from app.constants import CollectionNames, MAX_CHUNK_SIZE, CHUNK_OVERLAP, VECTOR_SEARCH_WEIGHT, BM25_SEARCH_WEIGHT
from app.config import settings
from app.logger import get_logger

logger = get_logger("weaviate_service")


class WeaviateService:
    """Service for managing Weaviate collections and operations."""
    
    def __init__(self):
        self.client = None
        self._initialized = False
    
    def _get_client(self):
        """Lazy load Weaviate client."""
        if self.client is None:
            self.client = get_weaviate_client()
        return self.client
    
    async def create_collections(self) -> bool:
        """
        Create all 4 nail guide collections with proper schema.
        
        Returns:
            bool: True if all collections created successfully
        """
        try:
            client = self._get_client()
            collections = CollectionNames.get_all_nail_collections()
            
            for collection_name in collections:
                await self._create_collection(client, collection_name)
            
            logger.info(f"✅ Created {len(collections)} Weaviate collections")
            self._initialized = True
            return True
            
        except Exception as e:
            logger.error(f"❌ Error creating collections: {e}")
            return False
    
    async def _create_collection(self, client, collection_name: str) -> None:
        """Create a single collection with schema."""
        try:
            # Check if collection already exists
            if await client.collections.exists(collection_name):
                logger.info(f"ℹ️ Collection '{collection_name}' already exists")
                return
            
            # Create collection with OpenAI vectorizer
            client.collections.create(
                name=collection_name,
                description=f"Nail guide documents for {collection_name}",
                properties=[
                    Property(name="document_id", data_type=DataType.INT, description="Original document ID"),
                    Property(name="category", data_type=DataType.TEXT, description="Document category"),
                    Property(name="title", data_type=DataType.TEXT, description="Document title"),
                    Property(name="content", data_type=DataType.TEXT, description="Chunked content"),
                    Property(name="questions", data_type=DataType.TEXT_ARRAY, description="Related questions"),
                    Property(name="answers", data_type=DataType.TEXT_ARRAY, description="Related answers"),
                    Property(name="chunk_index", data_type=DataType.INT, description="Chunk index within document"),
                    Property(name="total_chunks", data_type=DataType.INT, description="Total chunks in document"),
                    Property(name="source_title", data_type=DataType.TEXT, description="Source document title"),
                ],
                vectorizer_config=Configure.Vectorizer.text2vec_openai(
                    model=settings.EMBEDDING_MODEL,
                    properties=["content", "title"]  # Vectorize content and title
                ),
                vector_index_config=Configure.VectorIndex.hnsw(
                    distance_metric="cosine",
                    max_indexing_threads=4
                ),
            )
            
            logger.info(f"✅ Created collection: {collection_name}")
            
        except Exception as e:
            logger.error(f"❌ Error creating collection '{collection_name}': {e}")
            raise
    
    async def ensure_collections_exist(self) -> bool:
        """
        Ensure all collections exist, create if missing.
        
        Returns:
            bool: True if all collections exist
        """
        try:
            client = self._get_client()
            collections = CollectionNames.get_all_nail_collections()
            
            for collection_name in collections:
                if not await client.collections.exists(collection_name):
                    await self._create_collection(client, collection_name)
            
            self._initialized = True
            return True
            
        except Exception as e:
            logger.error(f"❌ Error ensuring collections exist: {e}")
            return False
    
    def chunk_document(self, document: NailGuideDocument) -> List[Dict[str, Any]]:
        """
        Split document content into semantic chunks.
        
        Strategy:
        - Split by paragraphs
        - Max 500 tokens per chunk
        - 50 token overlap between chunks
        - Preserve metadata
        
        Args:
            document: Document to chunk
            
        Returns:
            List of chunk dictionaries
        """
        chunks = []
        content = document.content
        
        # Simple paragraph-based chunking
        paragraphs = content.split('\n\n')
        current_chunk = ""
        chunk_index = 0
        
        for para in paragraphs:
            para = para.strip()
            if not para:
                continue
            
            # Estimate tokens (rough: 1 token ≈ 4 characters)
            para_tokens = len(para) // 4
            
            # If adding this paragraph exceeds max size, finalize current chunk
            if current_chunk and (len(current_chunk) + len(para)) // 4 > MAX_CHUNK_SIZE:
                chunks.append({
                    "content": current_chunk.strip(),
                    "chunk_index": chunk_index,
                    "document_id": document.id,
                    "category": document.category,
                    "title": document.title,
                    "questions": document.questions,
                    "answers": document.answers,
                })
                chunk_index += 1
                
                # Start new chunk with overlap (last 50 tokens of previous chunk)
                overlap_text = current_chunk[-CHUNK_OVERLAP * 4:] if len(current_chunk) > CHUNK_OVERLAP * 4 else ""
                current_chunk = overlap_text + "\n\n" + para
            else:
                current_chunk += "\n\n" + para if current_chunk else para
        
        # Add final chunk
        if current_chunk.strip():
            chunks.append({
                "content": current_chunk.strip(),
                "chunk_index": chunk_index,
                "document_id": document.id,
                "category": document.category,
                "title": document.title,
                "questions": document.questions,
                "answers": document.answers,
            })
        
        # Add total_chunks to all chunks
        total_chunks = len(chunks)
        for chunk in chunks:
            chunk["total_chunks"] = total_chunks
            chunk["source_title"] = document.title
        
        logger.debug(f"✅ Chunked document {document.id} into {total_chunks} chunks")
        return chunks
    
    async def check_document_exists(self, document_id: int, collection_name: str) -> bool:
        """
        Check if a document already exists in Weaviate.
        
        Args:
            document_id: Document ID to check
            collection_name: Collection name
            
        Returns:
            bool: True if document exists
        """
        try:
            client = self._get_client()
            collection = client.collections.get(collection_name)
            
            # Query by document_id
            result = collection.query.fetch_objects(
                where={
                    "path": ["document_id"],
                    "operator": "Equal",
                    "valueInt": document_id
                },
                limit=1,
                return_metadata=MetadataQuery(creation_time=True)
            )
            
            return len(result.objects) > 0
            
        except Exception as e:
            logger.error(f"❌ Error checking document existence: {e}")
            return False
    
    async def import_document(
        self,
        document: NailGuideDocument,
        collection_name: str
    ) -> bool:
        """
        Import a single document (chunked) into Weaviate.
        
        Args:
            document: Document to import
            collection_name: Target collection name
            
        Returns:
            bool: True if successful
        """
        try:
            # Check if already exists
            if await self.check_document_exists(document.id, collection_name):
                logger.debug(f"ℹ️ Document {document.id} already exists, skipping")
                return True
            
            # Chunk document
            chunks = self.chunk_document(document)
            
            if not chunks:
                logger.warning(f"⚠️ No chunks generated for document {document.id}")
                return False
            
            # Import chunks
            client = self._get_client()
            collection = client.collections.get(collection_name)
            
            # Batch import
            batch_size = settings.weaviate_batch_size
            for i in range(0, len(chunks), batch_size):
                batch = chunks[i:i + batch_size]
                
                with collection.batch.dynamic() as batch_client:
                    for chunk in batch:
                        batch_client.add_object(
                            properties={
                                "document_id": chunk["document_id"],
                                "category": chunk["category"],
                                "title": chunk["title"],
                                "content": chunk["content"],
                                "questions": chunk.get("questions", []),
                                "answers": chunk.get("answers", []),
                                "chunk_index": chunk["chunk_index"],
                                "total_chunks": chunk["total_chunks"],
                                "source_title": chunk["source_title"],
                            }
                        )
            
            logger.info(f"✅ Imported document {document.id} ({len(chunks)} chunks) into {collection_name}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error importing document {document.id}: {e}")
            return False
    
    async def search_similar(
        self,
        query: str,
        collection_names: Optional[List[str]] = None,
        limit: int = 10,
        similarity_threshold: float = 0.75
    ) -> List[Dict[str, Any]]:
        """
        Hybrid search across collections (vector + BM25).
        
        Args:
            query: Search query
            collection_names: Collections to search (None = all 4)
            limit: Number of results per collection
            similarity_threshold: Minimum similarity score
            
        Returns:
            List of search results with metadata
        """
        if collection_names is None:
            collection_names = CollectionNames.get_all_nail_collections()
        
        try:
            client = self._get_client()
            all_results = []
            
            # Search all collections in parallel
            tasks = []
            for collection_name in collection_names:
                tasks.append(
                    self._search_collection(client, collection_name, query, limit, similarity_threshold)
                )
            
            results_list = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Combine and rank results
            for results in results_list:
                if isinstance(results, Exception):
                    logger.error(f"❌ Search error: {results}")
                    continue
                all_results.extend(results)
            
            # Sort by score (descending)
            all_results.sort(key=lambda x: x.get("score", 0), reverse=True)
            
            # Return top results
            top_results = all_results[:limit]
            logger.debug(f"✅ Found {len(top_results)} results for query: {query[:50]}...")
            
            return top_results
            
        except Exception as e:
            logger.error(f"❌ Error in search_similar: {e}")
            return []
    
    async def _search_collection(
        self,
        client,
        collection_name: str,
        query: str,
        limit: int,
        similarity_threshold: float
    ) -> List[Dict[str, Any]]:
        """Search a single collection using hybrid search."""
        try:
            collection = client.collections.get(collection_name)
            
            # Hybrid search (vector + BM25)
            result = collection.query.hybrid(
                query=query,
                alpha=VECTOR_SEARCH_WEIGHT,  # 0.7 for vector, 0.3 for BM25
                limit=limit,
                return_metadata=MetadataQuery(
                    score=True,
                    explain_score=True
                ),
                return_properties=["document_id", "category", "title", "content", "questions", "answers", "chunk_index", "total_chunks", "source_title"]
            )
            
            results = []
            for obj in result.objects:
                score = obj.metadata.score if obj.metadata and obj.metadata.score else 0
                
                if score >= similarity_threshold:
                    results.append({
                        "collection": collection_name,
                        "document_id": obj.properties.get("document_id"),
                        "category": obj.properties.get("category"),
                        "title": obj.properties.get("title"),
                        "content": obj.properties.get("content"),
                        "questions": obj.properties.get("questions", []),
                        "answers": obj.properties.get("answers", []),
                        "chunk_index": obj.properties.get("chunk_index"),
                        "total_chunks": obj.properties.get("total_chunks"),
                        "source_title": obj.properties.get("source_title"),
                        "score": score,
                        "uuid": str(obj.uuid),
                    })
            
            return results
            
        except Exception as e:
            logger.error(f"❌ Error searching collection '{collection_name}': {e}")
            return []


# Global instance
weaviate_service = WeaviateService()

