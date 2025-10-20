from pydantic import BaseModel, EmailStr
from typing import Optional
from app.models.user import  Role


# -------------------------
# Request schema
# -------------------------
class CreateAccountRequest(BaseModel):
    firstName: str
    lastName: str
    email: EmailStr
    password: str
    role: Optional[Role] = Role.USER
    fcmToken: Optional[str] = None

# -------------------------
# Response schema
# -------------------------
class CreateAccountResponse(BaseModel):
    id: str
    name: str
    otpSent: bool = True
    message: str
    type: str = "register"