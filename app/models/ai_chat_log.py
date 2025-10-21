from beanie import Document, Indexed
from pydantic import Field, ConfigDict
from typing import Dict, Any, Optional
from datetime import datetime, timezone


class AiChatLog(Document):
    """
    AI Chat interaction log with camelCase fields
    Stores user messages, AI responses, and metadata
    """
    
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_default=True,
        extra="forbid"
    )
    
    userId: Indexed(str) = Field(..., description="User ID who initiated the chat")
    conversationId: Indexed(str) = Field(..., description="Conversation ID for grouping messages")
    userMessage: str = Field(..., description="Original user message")
    aiResponse: str = Field(..., description="AI generated response") 
    tokenUsage: Dict[str, int] = Field(default_factory=dict, description="Token usage breakdown")
    model: str = Field(default="unknown", description="AI model used for response")
    createdAt: Indexed(datetime) = Field(
        default_factory=lambda: datetime.now(timezone.utc), 
        description="When the interaction occurred"
    )
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional metadata")
    
    class Settings:
        name = "ai_chat_logs"  # MongoDB collection name
        
        # Additional indexes for compound queries
        indexes = [
            [("userId", 1), ("conversationId", 1)],
            [("userId", 1), ("createdAt", -1)],
            [("conversationId", 1), ("createdAt", -1)],
        ]


class TokenUsage(Document):
    """
    Token usage tracking for billing and analytics
    """
    
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_default=True,
        extra="forbid"
    )
    
    userId: Indexed(str) = Field(..., description="User ID")
    feature: Indexed(str) = Field(..., description="Feature used (ai_chat, voice_chat, etc.)")
    model: str = Field(..., description="AI model used")
    promptTokens: int = Field(default=0, description="Tokens in prompt", ge=0)
    completionTokens: int = Field(default=0, description="Tokens in completion", ge=0)
    totalTokens: int = Field(default=0, description="Total tokens used", ge=0)
    cost: float = Field(default=0.0, description="Estimated cost in USD", ge=0.0)
    createdAt: Indexed(datetime) = Field(
        default_factory=lambda: datetime.now(timezone.utc), 
        description="Usage timestamp"
    )
    conversationId: Optional[str] = Field(default=None, description="Related conversation ID")
    
    class Settings:
        name = "token_usage"
        
        indexes = [
            [("userId", 1), ("feature", 1)],
            [("userId", 1), ("createdAt", -1)],
            [("feature", 1), ("createdAt", -1)],
        ]
