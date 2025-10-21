from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
from enum import Enum
from beanie import Document, Link, Indexed
from pydantic import EmailStr, Field, ConfigDict
from bson import ObjectId

# -------------------------
# Enums
# -------------------------
class Role(str, Enum):
    SUPERADMIN = "SUPERADMIN"
    ADMIN = "ADMIN"
    USER = "USER"
    CONSULTANT = "CONSULTANT"

class UserStatus(str, Enum):
    PENDING = "PENDING"
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    BLOCKED = "BLOCKED"
    AVAILABLE = "AVAILABLE"
    UNAVAILABLE = "UNAVAILABLE"

class PlanStatus(str, Enum):
    COMPLETED = "COMPLETED"
    INCOMPLETED = "INCOMPLETED"

class Currency(str, Enum):
    LYD = "LYD"
    USD = "USD"
    EUR = "EUR"
    GBP = "GBP"

class Language(str, Enum):
    EN = "EN"
    AR = "AR"
    FR = "FR"

class SubscriptionStatus(str, Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    CANCELLED = "CANCELLED"

class SubscriptionPlanType(str, Enum):
    SOLO = "SOLO"
    TEAM = "TEAM"

class ProductInterval(str, Enum):
    MONTHLY = "MONTHLY"
    YEARLY = "YEARLY"
    WEEKLY = "WEEKLY"
    DAILY = "DAILY"

class MembershipStatus(str, Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    SUSPENDED = "SUSPENDED"

class InvitationStatus(str, Enum):
    PENDING = "PENDING"
    ACCEPTED = "ACCEPTED"
    DECLINED = "DECLINED"
    EXPIRED = "EXPIRED"

# -------------------------
# BloodQA Model
# -------------------------
class BloodQA(Document):
    userId: Optional[str] = None
    user: Optional[Link["User"]] = None
    question: str
    answer: str
    language: str  # e.g., "bn-BD"
    isBloodRelated: bool
    rejectedReason: Optional[str] = None
    ip: Optional[str] = None
    ua: Optional[str] = None
    meta: Optional[dict] = None
    createdAt: datetime = Field(default_factory=datetime.utcnow)
    updatedAt: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "bloodqas"

# -------------------------
# Product Model
# -------------------------
class Product(Document):
    name: str
    description: Optional[str] = None
    price: float
    currency: str
    interval: ProductInterval
    subscriptions: Optional[List[Link["Subscription"]]] = []

    class Settings:
        name = "products"

# -------------------------
# Subscription Model
# -------------------------
class Subscription(Document):
    userId: str
    user: Link["User"]
    productId: str
    product: Link[Product]
    moovPaymentId: Optional[str] = None
    status: SubscriptionStatus = SubscriptionStatus.ACTIVE
    amount: float
    currency: str
    startDate: datetime = Field(default_factory=datetime.utcnow)
    currentPeriodStart: datetime = Field(default_factory=datetime.utcnow)
    currentPeriodEnd: datetime
    nextBillingDate: datetime
    lastPaymentAttempt: Optional[datetime] = None
    retryCount: int = 0
    createdAt: datetime = Field(default_factory=datetime.utcnow)
    updatedAt: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "subscriptions"

# -------------------------
# User Model
# -------------------------
class User(Document):
    """
    User model for AI backend with camelCase fields
    """
    
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_default=True,
        extra="forbid",
        arbitrary_types_allowed=True
    )
    
    id: ObjectId = Field(default_factory=ObjectId, alias="_id")
    firstName: str = Field(..., min_length=1, max_length=50)
    lastName: str = Field(..., min_length=1, max_length=50)
    email: Indexed(EmailStr, unique=True) = Field(...)
    password: Optional[str] = Field(default=None)
    avatarUrl: Optional[str] = Field(default=None, alias="image")
    role: Role = Field(default=Role.USER)
    status: UserStatus = Field(default=UserStatus.ACTIVE)
    isDeleted: bool = Field(default=False)
    
    # AI-specific fields
    aiPreferences: Optional[Dict[str, Any]] = Field(default_factory=dict, description="AI chat preferences")
    conversationHistory: Optional[List[str]] = Field(default_factory=list, description="Recent conversation IDs")
    totalTokensUsed: int = Field(default=0, description="Total AI tokens used")
    lastAiInteraction: Optional[datetime] = Field(default=None, description="Last AI chat timestamp")
    
    # Subscription fields
    stripeCustomerId: Optional[str] = Field(default=None)
    subscriptionId: Optional[str] = Field(default=None)
    subscriptionStartDate: Optional[datetime] = Field(default=None, alias="subStartDate")
    subscriptionEndDate: Optional[datetime] = Field(default=None, alias="subEndDate")
    
    # Timestamps
    createdAt: Indexed(datetime) = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    updatedAt: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    lastLoginAt: Optional[datetime] = Field(default=None)
    
    # Relationships
    subscription: Optional[List[Link["Subscription"]]] = Field(default_factory=list)
    bloodQA: Optional[List[Link["BloodQA"]]] = Field(default_factory=list)
    
    class Settings:
        name = "users"
        
        indexes = [
            "email",
            "status", 
            "role",
            "isDeleted",
            "createdAt",
            [("email", 1), ("isDeleted", 1)],
            [("status", 1), ("isDeleted", 1)],
        ]
