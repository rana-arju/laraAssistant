from beanie import Document, Indexed
from pydantic import Field, ConfigDict, validator
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone
from enum import Enum


class SocialPlatform(str, Enum):
    TWITTER = "twitter"
    FACEBOOK = "facebook"
    INSTAGRAM = "instagram"
    LINKEDIN = "linkedin"
    TIKTOK = "tiktok"


class PostStatus(str, Enum):
    SCHEDULED = "scheduled"
    PROCESSING = "processing"
    PUBLISHED = "published"
    FAILED = "failed"
    CANCELLED = "cancelled"


class PostContent(Document):
    """
    Content structure for social media posts
    """
    
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_default=True,
        extra="forbid"
    )
    
    text: str = Field(..., description="Post text content", max_length=2000)
    imageUrls: Optional[List[str]] = Field(default_factory=list, description="Image URLs for the post")
    videoUrls: Optional[List[str]] = Field(default_factory=list, description="Video URLs for the post")
    hashtags: Optional[List[str]] = Field(default_factory=list, description="Hashtags to include")
    mentions: Optional[List[str]] = Field(default_factory=list, description="User mentions")


class ScheduledPost(Document):
    """
    Scheduled social media post with camelCase fields
    """
    
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_default=True,
        extra="forbid"
    )
    
    scheduleId: str = Field(..., description="Unique schedule identifier")
    userId: Indexed(str) = Field(..., description="User who scheduled the post")
    platform: SocialPlatform = Field(..., description="Target social media platform")
    content: PostContent = Field(..., description="Post content")
    
    scheduledAt: Indexed(datetime) = Field(..., description="When to publish the post")
    status: PostStatus = Field(default=PostStatus.SCHEDULED, description="Current status")
    
    # Execution tracking
    publishedAt: Optional[datetime] = Field(default=None, description="When post was actually published")
    attempts: int = Field(default=0, description="Number of publish attempts")
    lastAttemptAt: Optional[datetime] = Field(default=None, description="Last attempt timestamp")
    errorMessage: Optional[str] = Field(default=None, description="Last error if any")
    
    # Social media response
    platformPostId: Optional[str] = Field(default=None, description="ID from social platform")
    platformResponse: Optional[Dict[str, Any]] = Field(default=None, description="Full platform response")
    
    # Metadata
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional metadata")
    tags: Optional[List[str]] = Field(default_factory=list, description="Internal tags")
    
    # Timestamps
    createdAt: Indexed(datetime) = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Creation timestamp"
    )
    updatedAt: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Last update timestamp"
    )
    
    @validator('scheduledAt')
    def validate_scheduled_at(cls, v):
        if v <= datetime.now(timezone.utc):
            raise ValueError('Scheduled time must be in the future')
        return v
    
    class Settings:
        name = "scheduled_posts"
        
        indexes = [
            "userId",
            "platform",
            "status",
            "scheduledAt",
            "createdAt",
            [("userId", 1), ("status", 1)],
            [("status", 1), ("scheduledAt", 1)],
            [("userId", 1), ("platform", 1)],
        ]