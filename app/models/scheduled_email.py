from beanie import Document, Indexed
from pydantic import Field, ConfigDict, EmailStr, validator
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone
from enum import Enum


class EmailStatus(str, Enum):
    SCHEDULED = "scheduled"
    PROCESSING = "processing"
    SENT = "sent"
    FAILED = "failed"
    CANCELLED = "cancelled"
    BOUNCED = "bounced"


class EmailPriority(str, Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"


class EmailTemplate(str, Enum):
    PLAIN = "plain"
    HTML = "html"
    CUSTOM = "custom"


class ScheduledEmail(Document):
    """
    Scheduled email with camelCase fields
    """
    
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_default=True,
        extra="forbid"
    )
    
    scheduleId: str = Field(..., description="Unique schedule identifier")
    userId: Indexed(str) = Field(..., description="User who scheduled the email")
    
    # Email fields
    to: List[EmailStr] = Field(..., description="Recipient email addresses", min_items=1)
    cc: Optional[List[EmailStr]] = Field(default_factory=list, description="CC recipients")
    bcc: Optional[List[EmailStr]] = Field(default_factory=list, description="BCC recipients")
    fromEmail: Optional[EmailStr] = Field(default=None, description="From email address")
    fromName: Optional[str] = Field(default=None, description="From name")
    replyTo: Optional[EmailStr] = Field(default=None, description="Reply-to address")
    
    subject: str = Field(..., description="Email subject", max_length=200)
    body: str = Field(..., description="Email body content")
    htmlBody: Optional[str] = Field(default=None, description="HTML version of email body")
    
    # Scheduling
    scheduledAt: Indexed(datetime) = Field(..., description="When to send the email")
    status: EmailStatus = Field(default=EmailStatus.SCHEDULED, description="Current status")
    priority: EmailPriority = Field(default=EmailPriority.NORMAL, description="Email priority")
    
    # Execution tracking
    sentAt: Optional[datetime] = Field(default=None, description="When email was actually sent")
    attempts: int = Field(default=0, description="Number of send attempts")
    lastAttemptAt: Optional[datetime] = Field(default=None, description="Last attempt timestamp")
    errorMessage: Optional[str] = Field(default=None, description="Last error if any")
    
    # Email service response
    emailServiceId: Optional[str] = Field(default=None, description="ID from email service provider")
    emailServiceResponse: Optional[Dict[str, Any]] = Field(default=None, description="Full service response")
    
    # Template and personalization
    templateId: Optional[str] = Field(default=None, description="Email template ID")
    templateType: EmailTemplate = Field(default=EmailTemplate.PLAIN, description="Template type")
    personalizations: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Template variables")
    
    # Tracking
    trackOpens: bool = Field(default=False, description="Track email opens")
    trackClicks: bool = Field(default=False, description="Track link clicks")
    
    # Attachments
    attachments: Optional[List[Dict[str, str]]] = Field(
        default_factory=list, 
        description="File attachments with filename and path/url"
    )
    
    # Metadata
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional metadata")
    tags: Optional[List[str]] = Field(default_factory=list, description="Internal tags")
    campaignId: Optional[str] = Field(default=None, description="Campaign identifier")
    
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
    
    @validator('subject')
    def validate_subject(cls, v):
        if not v.strip():
            raise ValueError('Subject cannot be empty')
        return v
    
    @validator('body')
    def validate_body(cls, v):
        if not v.strip():
            raise ValueError('Email body cannot be empty')
        return v
    
    class Settings:
        name = "scheduled_emails"
        
        indexes = [
            "userId",
            "status",
            "scheduledAt",
            "priority",
            "createdAt",
            "campaignId",
            [("userId", 1), ("status", 1)],
            [("status", 1), ("scheduledAt", 1)],
            [("status", 1), ("priority", 1)],
            [("userId", 1), ("campaignId", 1)],
        ]