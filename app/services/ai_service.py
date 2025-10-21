import os
from openai import AsyncOpenAI
from typing import Dict, Any, Optional
try:
    import whisper
except ImportError:
    whisper = None
import tempfile


class AIService:
    """Service for AI operations including chat completion and transcription"""
    
    def __init__(self):
        # TODO: Configure your AI provider API keys in environment variables
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.openai_client = None
        if self.openai_api_key:
            self.openai_client = AsyncOpenAI(api_key=self.openai_api_key)
        
        # Load Whisper model for transcription (you can use OpenAI API instead)
        self.whisper_model = None
        self.use_openai_whisper = os.getenv("USE_OPENAI_WHISPER", "true").lower() == "true"
    
    async def chat_completion(
        self,
        message: str,
        context: str = "",
        user_id: str = "",
        model: str = "gpt-3.5-turbo",
        max_tokens: int = 1000,
        temperature: float = 0.7
    ) -> Dict[str, Any]:
        """
        Generate AI chat completion
        
        Args:
            message: User message
            context: Additional context from memory/conversation
            user_id: User ID for logging
            model: AI model to use
            max_tokens: Maximum response tokens
            temperature: Response randomness
            
        Returns:
            Dict with text, token_usage, and model info
        """
        try:
            # Build system prompt with context
            system_prompt = "You are Lara, a helpful AI assistant."
            if context:
                system_prompt += f"\\n\\nRelevant context:\\n{context}"
            
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": message}
            ]
            
            if self.openai_client:
                # Use OpenAI API
                response = await self.openai_client.chat.completions.create(
                    model=model,
                    messages=messages,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    user=user_id  # For OpenAI usage tracking
                )
                
                return {
                    "text": response.choices[0].message.content,
                    "token_usage": {
                        "prompt_tokens": response.usage.prompt_tokens,
                        "completion_tokens": response.usage.completion_tokens,
                        "total_tokens": response.usage.total_tokens
                    },
                    "model": response.model
                }
            else:
                # TODO: Implement other AI providers (Anthropic, Cohere, local models, etc.)
                # Fallback response for development
                return {
                    "text": f"Echo: {message} (AI service not configured - set OPENAI_API_KEY)",
                    "token_usage": {
                        "prompt_tokens": len(message.split()),
                        "completion_tokens": 10,
                        "total_tokens": len(message.split()) + 10
                    },
                    "model": "mock"
                }
                
        except Exception as e:
            print(f"AI completion error: {e}")
            # Return fallback response
            return {
                "text": "I'm sorry, I'm experiencing technical difficulties. Please try again later.",
                "token_usage": {"prompt_tokens": 0, "completion_tokens": 15, "total_tokens": 15},
                "model": "error"
            }
    
    async def transcribe_audio(self, audio_file_path: str) -> Optional[str]:
        """
        Transcribe audio file using Whisper
        
        Args:
            audio_file_path: Path to audio file
            
        Returns:
            Transcribed text or None if failed
        """
        try:
            if self.use_openai_whisper and self.openai_client:
                # Use OpenAI Whisper API
                with open(audio_file_path, "rb") as audio_file:
                    response = await self.openai_client.audio.transcriptions.create(
                        model="whisper-1",
                        file=audio_file,
                        response_format="text"
                    )
                return response.strip()
            else:
                # Use local Whisper model
                if not self.whisper_model:
                    self.whisper_model = whisper.load_model("base")  # You can use "small", "medium", "large"
                
                result = self.whisper_model.transcribe(audio_file_path)
                return result["text"].strip()
                
        except Exception as e:
            print(f"Transcription error: {e}")
            return None
    
    async def generate_embedding(self, text: str, model: str = "text-embedding-ada-002") -> Optional[list]:
        """
        Generate text embedding
        
        Args:
            text: Text to embed
            model: Embedding model
            
        Returns:
            Embedding vector or None if failed
        """
        try:
            if self.openai_client:
                response = await self.openai_client.embeddings.create(
                    input=text,
                    model=model
                )
                return response.data[0].embedding
            else:
                # TODO: Implement other embedding providers (Cohere, HuggingFace, etc.)
                # Return mock embedding for development
                import random
                return [random.random() for _ in range(1536)]  # Mock 1536-dim vector
                
        except Exception as e:
            print(f"Embedding error: {e}")
            return None


# Global AI service instance
ai_service = AIService()