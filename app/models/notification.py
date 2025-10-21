from beanie import Document, Indexed
from pydantic import Field, ConfigDict
from typing import Optional, Dict, Any
from datetime import datetime, timezone
from enum import Enum


class NotificationType(str, Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    SUCCESS = "success"


class NotificationStatus(str, Enum):
    UNREAD = "unread"
    READ = "read"
    DISMISSED = "dismissed"


class NotificationChannel(str, Enum):
    IN_APP = "in_app"
    EMAIL = "email"
    PUSH = "push"
    SMS = "sms"


class Notification(Document):
    """
    Notification model for system and user notifications with camelCase fields
    """
    
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_default=True,
        extra="forbid"
    )
    
    userId: Indexed(str) = Field(..., description="User ID who receives this notification")
    title: str = Field(..., description="Notification title", max_length=100)
    message: str = Field(..., description="Notification message", max_length=500)
    type: NotificationType = Field(default=NotificationType.INFO, description="Notification type")
    status: NotificationStatus = Field(default=NotificationStatus.UNREAD, description="Read status")
    
    # Channel and delivery
    channel: NotificationChannel = Field(default=NotificationChannel.IN_APP, description="Delivery channel")
    priority: int = Field(default=1, description="Priority level (1=low, 5=high)", ge=1, le=5)
    
    # Action and navigation
    actionUrl: Optional[str] = Field(default=None, description="URL to navigate when clicked")
    actionText: Optional[str] = Field(default=None, description="Text for action button")
    
    # Categorization
    category: Optional[str] = Field(default=None, description="Notification category")
    tags: Optional[list] = Field(default_factory=list, description="Tags for filtering")
    
    # Scheduling
    scheduledAt: Optional[datetime] = Field(default=None, description="When to send notification")
    expiresAt: Optional[datetime] = Field(default=None, description="When notification expires")
    
    # Tracking
    sentAt: Optional[datetime] = Field(default=None, description="When notification was sent")
    readAt: Optional[datetime] = Field(default=None, description="When notification was read")
    clickedAt: Optional[datetime] = Field(default=None, description="When notification was clicked")
    
    # Related entities
    relatedEntityType: Optional[str] = Field(default=None, description="Type of related entity")
    relatedEntityId: Optional[str] = Field(default=None, description="ID of related entity")
    
    # Metadata
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional metadata")
    
    # Timestamps
    createdAt: Indexed(datetime) = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Creation timestamp"
    )
    updatedAt: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Last update timestamp"
    )
    
    def mark_as_read(self):
        """Mark notification as read"""
        self.status = NotificationStatus.READ
        self.readAt = datetime.now(timezone.utc)
        self.updatedAt = datetime.now(timezone.utc)
    
    def mark_as_clicked(self):
        """Mark notification as clicked"""
        if self.status == NotificationStatus.UNREAD:
            self.mark_as_read()
        self.clickedAt = datetime.now(timezone.utc)
        self.updatedAt = datetime.now(timezone.utc)
    
    def is_expired(self) -> bool:
        """Check if notification is expired"""
        if not self.expiresAt:
            return False
        return self.expiresAt <= datetime.now(timezone.utc)
    
    class Settings:
        name = "notifications"
        
        indexes = [
            "userId",
            "status",
            "type",
            "channel",
            "category",
            "createdAt",
            "scheduledAt",
            "expiresAt",
            [("userId", 1), ("status", 1)],
            [("userId", 1), ("createdAt", -1)],
            [("status", 1), ("scheduledAt", 1)],
            [("relatedEntityType", 1), ("relatedEntityId", 1)],
        ]