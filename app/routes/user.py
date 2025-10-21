from fastapi import FastAPI, HTTPException, Query, APIRouter, Body,status
from pydantic import BaseModel
from app.schemas.user import CreateAccountRequest, CreateAccountResponse
from app.models.user import User, Role, UserStatus
import bcrypt
app = FastAPI()


router = APIRouter(
    prefix="/api/v1/users",
    tags=["Users"]
)

# -------------------------
# Route
# -------------------------
@router.post("/register", response_model=CreateAccountResponse, status_code=status.HTTP_201_CREATED)
async def create_account(payload: CreateAccountRequest):
    # 1️⃣ Check if user already exists
    existing_user = await User.find_one(User.email == payload.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This email is already registered"
        )

    # 2️⃣ Hash the password
    salt_rounds = 12  # or read from config
    hashed_password = bcrypt.hashpw(payload.password.encode("utf-8"), bcrypt.gensalt(salt_rounds)).decode()

    # 3️⃣ Prepare user data
    status_value = UserStatus.ACTIVE if payload.role == Role.USER else UserStatus.PENDING

    user_data = User(
        firstName=payload.firstName,
        lastName=payload.lastName,
        email=payload.email.strip(),
        password=hashed_password,
        role=payload.role,
        status=status_value
    )

    # 4️⃣ Insert user (Beanie handles transaction internally)
    await user_data.insert()

    # 5️⃣ Return structured response
    return CreateAccountResponse(
        id=str(user_data.id),
        name=f"{user_data.firstName} {user_data.lastName}",
        otpSent=True,
        message="You are register successfully!"
    )
@router.get("/")
def get_users(district: str = Query(None), blood_group: str = Query(None)):
    filtered_users = []

    if district:
        filtered_users = [u for u in filtered_users if u["district"].lower() == district.lower()]

    if blood_group:
        filtered_users = [u for u in filtered_users if u["blood_group"].lower() == blood_group.lower()]

    return filtered_users