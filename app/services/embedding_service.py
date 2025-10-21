from typing import List, Optional
from app.services.ai_service import ai_service


class EmbeddingService:
    """Service for generating text embeddings"""
    
    def __init__(self):
        self.ai_service = ai_service
    
    async def get_embedding(self, text: str) -> Optional[List[float]]:
        """
        Generate embedding for text
        
        Args:
            text: Text to embed
            
        Returns:
            Embedding vector or None if failed
        """
        if not text or not text.strip():
            return None
            
        return await self.ai_service.generate_embedding(text.strip())
    
    async def get_embeddings_batch(self, texts: List[str]) -> List[Optional[List[float]]]:
        """
        Generate embeddings for multiple texts
        
        Args:
            texts: List of texts to embed
            
        Returns:
            List of embedding vectors (None for failed embeddings)
        """
        embeddings = []
        for text in texts:
            embedding = await self.get_embedding(text)
            embeddings.append(embedding)
        return embeddings


# Global embedding service instance
embedding_service = EmbeddingService()