from typing import Optional, List
from datetime import datetime
from enum import Enum
from beanie import Document, Link
from pydantic import EmailStr, Field
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
    id: ObjectId = Field(default_factory=ObjectId, alias="_id")
    firstName: str
    lastName: str
    email: EmailStr
    password: Optional[str] = None
    image: Optional[str] = None
    role: Role = Role.USER
    createdAt: datetime = Field(default_factory=datetime.utcnow)
    updatedAt: datetime = Field(default_factory=datetime.utcnow)
    status: UserStatus = UserStatus.ACTIVE
    isDeleted: bool = False
    stripeCustomerId: Optional[str] = None
    subscriptionId: Optional[str] = None
    subStartDate: Optional[datetime] = None
    subEndDate: Optional[datetime] = None
    subscription: Optional[List[Link[Subscription]]] = []
    bloodQA: Optional[List[Link[BloodQA]]] = []

    class Settings:
        name = "users"

    class Config:
        alias_generator = lambda string: string[0].lower() + string[1:]
        validate_by_name = True
        arbitrary_types_allowed = True
