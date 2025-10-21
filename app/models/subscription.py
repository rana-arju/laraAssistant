from beanie import Document, Indexed, Link
from pydantic import Field, ConfigDict, validator
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone
from enum import Enum


class SubscriptionStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    CANCELLED = "cancelled"
    EXPIRED = "expired"
    SUSPENDED = "suspended"


class SubscriptionPlan(str, Enum):
    FREE = "free"
    BASIC = "basic"
    PREMIUM = "premium"
    ENTERPRISE = "enterprise"


class BillingInterval(str, Enum):
    MONTHLY = "monthly"
    YEARLY = "yearly"
    WEEKLY = "weekly"


class Subscription(Document):
    """
    User subscription model for AI services with camelCase fields
    """
    
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_default=True,
        extra="forbid"
    )
    
    userId: Indexed(str) = Field(..., description="User ID owning this subscription")
    planType: SubscriptionPlan = Field(..., description="Subscription plan type")
    status: SubscriptionStatus = Field(default=SubscriptionStatus.ACTIVE, description="Subscription status")
    
    # Billing information
    billingInterval: BillingInterval = Field(default=BillingInterval.MONTHLY, description="Billing frequency")
    amount: float = Field(..., description="Subscription amount", ge=0)
    currency: str = Field(default="USD", description="Currency code")
    
    # Features and limits
    aiChatLimit: Optional[int] = Field(default=None, description="Monthly AI chat limit (null = unlimited)")
    voiceChatLimit: Optional[int] = Field(default=None, description="Monthly voice chat limit")
    schedulingLimit: Optional[int] = Field(default=None, description="Monthly scheduling limit")
    tokensLimit: Optional[int] = Field(default=None, description="Monthly tokens limit")
    
    # Usage tracking
    aiChatUsed: int = Field(default=0, description="AI chats used this period", ge=0)
    voiceChatUsed: int = Field(default=0, description="Voice chats used this period", ge=0)
    schedulingUsed: int = Field(default=0, description="Scheduled items used this period", ge=0)
    tokensUsed: int = Field(default=0, description="Tokens used this period", ge=0)
    
    # Features enabled
    features: List[str] = Field(
        default_factory=list, 
        description="Enabled features list"
    )
    
    # Billing dates
    startDate: datetime = Field(..., description="Subscription start date")
    endDate: Optional[datetime] = Field(default=None, description="Subscription end date")
    currentPeriodStart: datetime = Field(..., description="Current billing period start")
    currentPeriodEnd: datetime = Field(..., description="Current billing period end")
    nextBillingDate: Optional[datetime] = Field(default=None, description="Next billing date")
    
    # Payment information
    paymentMethodId: Optional[str] = Field(default=None, description="Payment method identifier")
    lastPaymentAt: Optional[datetime] = Field(default=None, description="Last successful payment")
    lastPaymentAmount: Optional[float] = Field(default=None, description="Last payment amount")
    failedPaymentAttempts: int = Field(default=0, description="Failed payment attempts", ge=0)
    
    # External service IDs
    stripeSubscriptionId: Optional[str] = Field(default=None, description="Stripe subscription ID")
    stripeCustomerId: Optional[str] = Field(default=None, description="Stripe customer ID")
    
    # Trial information
    trialStart: Optional[datetime] = Field(default=None, description="Trial start date")
    trialEnd: Optional[datetime] = Field(default=None, description="Trial end date")
    isTrialUsed: bool = Field(default=False, description="Whether user has used trial")
    
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
    cancelledAt: Optional[datetime] = Field(default=None, description="Cancellation timestamp")
    suspendedAt: Optional[datetime] = Field(default=None, description="Suspension timestamp")
    
    @validator('endDate')
    def validate_end_date(cls, v, values):
        if v and 'startDate' in values and v <= values['startDate']:
            raise ValueError('End date must be after start date')
        return v
    
    @validator('currentPeriodEnd')
    def validate_current_period_end(cls, v, values):
        if 'currentPeriodStart' in values and v <= values['currentPeriodStart']:
            raise ValueError('Current period end must be after start')
        return v
    
    def is_active(self) -> bool:
        """Check if subscription is currently active"""
        return (
            self.status == SubscriptionStatus.ACTIVE and
            (self.endDate is None or self.endDate > datetime.now(timezone.utc))
        )
    
    def has_feature(self, feature: str) -> bool:
        """Check if subscription includes a specific feature"""
        return feature in self.features
    
    def can_use_ai_chat(self) -> bool:
        """Check if user can use AI chat based on limits"""
        if not self.is_active():
            return False
        if self.aiChatLimit is None:  # Unlimited
            return True
        return self.aiChatUsed < self.aiChatLimit
    
    def can_use_voice_chat(self) -> bool:
        """Check if user can use voice chat based on limits"""
        if not self.is_active():
            return False
        if self.voiceChatLimit is None:  # Unlimited
            return True
        return self.voiceChatUsed < self.voiceChatLimit
    
    def can_schedule(self) -> bool:
        """Check if user can schedule posts/emails based on limits"""
        if not self.is_active():
            return False
        if self.schedulingLimit is None:  # Unlimited
            return True
        return self.schedulingUsed < self.schedulingLimit
    
    class Settings:
        name = "subscriptions"
        
        indexes = [
            "userId",
            "status",
            "planType",
            "endDate",
            "nextBillingDate",
            "createdAt",
            [("userId", 1), ("status", 1)],
            [("status", 1), ("nextBillingDate", 1)],
            [("stripeSubscriptionId", 1)],
            [("stripeCustomerId", 1)],
        ]