import os
import uuid
from typing import List, Dict, Any, Optional
from qdrant_client import QdrantClient
from qdrant_client.http import models
from qdrant_client.http.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue
import numpy as np
from datetime import datetime


class QdrantService:
    """Service for managing Qdrant vector database operations"""
    
    def __init__(self):
        self.client = QdrantClient(
            host=os.getenv("QDRANT_HOST", "localhost"),
            port=int(os.getenv("QDRANT_PORT", "6333"))
        )
        self.collection_name = "ai_memory"
        self.vector_size = 1536  # OpenAI embedding size, adjust based on your embedding model
        
    async def ensure_collection_exists(self):
        """Create collection if it doesn't exist"""
        try:
            collections = self.client.get_collections()
            collection_names = [col.name for col in collections.collections]
            
            if self.collection_name not in collection_names:
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(
                        size=self.vector_size,
                        distance=Distance.COSINE
                    )
                )
                print(f"Created Qdrant collection: {self.collection_name}")
        except Exception as e:
            print(f"Error ensuring collection exists: {e}")
            raise
    
    async def store_embedding(
        self,
        user_id: str,
        text: str,
        embedding: List[float],
        conversation_id: Optional[str] = None,
        source_type: str = "chat",
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Store text embedding in Qdrant with metadata
        
        Args:
            user_id: User ID who owns this memory
            text: Original text content
            embedding: Vector embedding of the text
            conversation_id: Optional conversation ID for grouping
            source_type: Type of content (chat, voice, document, etc.)
            metadata: Additional metadata to store
            
        Returns:
            point_id: Unique ID of stored point
        """
        await self.ensure_collection_exists()
        
        point_id = str(uuid.uuid4())
        
        # Prepare payload with camelCase fields
        payload = {
            "userId": user_id,
            "text": text,
            "conversationId": conversation_id,
            "sourceType": source_type,
            "createdAt": datetime.utcnow().isoformat(),
        }
        
        if metadata:
            payload.update(metadata)
        
        point = PointStruct(
            id=point_id,
            vector=embedding,
            payload=payload
        )
        
        try:
            self.client.upsert(
                collection_name=self.collection_name,
                points=[point]
            )
            return point_id
        except Exception as e:
            print(f"Error storing embedding: {e}")
            raise
    
    async def search_similar(
        self,
        query_embedding: List[float],
        user_id: str,
        limit: int = 10,
        score_threshold: float = 0.7,
        conversation_id: Optional[str] = None,
        source_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for similar embeddings
        
        Args:
            query_embedding: Query vector to search for
            user_id: Filter by user ID
            limit: Maximum number of results
            score_threshold: Minimum similarity score
            conversation_id: Optional filter by conversation
            source_type: Optional filter by source type
            
        Returns:
            List of similar memories with scores and metadata
        """
        await self.ensure_collection_exists()
        
        # Build filter conditions
        must_conditions = [
            FieldCondition(
                key="userId",
                match=MatchValue(value=user_id)
            )
        ]
        
        if conversation_id:
            must_conditions.append(
                FieldCondition(
                    key="conversationId",
                    match=MatchValue(value=conversation_id)
                )
            )
        
        if source_type:
            must_conditions.append(
                FieldCondition(
                    key="sourceType", 
                    match=MatchValue(value=source_type)
                )
            )
        
        search_filter = Filter(
            must=must_conditions
        )
        
        try:
            search_result = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_embedding,
                query_filter=search_filter,
                limit=limit,
                score_threshold=score_threshold
            )
            
            results = []
            for point in search_result:
                results.append({
                    "id": point.id,
                    "score": point.score,
                    "payload": point.payload
                })
            
            return results
        except Exception as e:
            print(f"Error searching embeddings: {e}")
            raise
    
    async def get_conversation_context(
        self,
        user_id: str,
        conversation_id: str,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Get recent conversation context without vector search
        
        Args:
            user_id: User ID
            conversation_id: Conversation ID
            limit: Maximum number of messages
            
        Returns:
            List of conversation messages ordered by creation time
        """
        await self.ensure_collection_exists()
        
        search_filter = Filter(
            must=[
                FieldCondition(
                    key="userId",
                    match=MatchValue(value=user_id)
                ),
                FieldCondition(
                    key="conversationId",
                    match=MatchValue(value=conversation_id)
                )
            ]
        )
        
        try:
            # Use scroll to get all points matching filter
            points, _ = self.client.scroll(
                collection_name=self.collection_name,
                scroll_filter=search_filter,
                limit=limit,
                with_payload=True,
                with_vectors=False
            )
            
            # Sort by creation time
            sorted_points = sorted(
                points,
                key=lambda x: x.payload.get("createdAt", ""),
                reverse=True
            )
            
            results = []
            for point in sorted_points:
                results.append({
                    "id": point.id,
                    "payload": point.payload
                })
            
            return results
        except Exception as e:
            print(f"Error getting conversation context: {e}")
            raise
    
    async def delete_user_data(self, user_id: str) -> bool:
        """
        Delete all data for a specific user (GDPR compliance)
        
        Args:
            user_id: User ID to delete data for
            
        Returns:
            Success status
        """
        await self.ensure_collection_exists()
        
        try:
            self.client.delete(
                collection_name=self.collection_name,
                points_selector=Filter(
                    must=[
                        FieldCondition(
                            key="userId",
                            match=MatchValue(value=user_id)
                        )
                    ]
                )
            )
            return True
        except Exception as e:
            print(f"Error deleting user data: {e}")
            return False


# Global Qdrant service instance
qdrant_service = QdrantService()