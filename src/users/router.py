from argon2 import PasswordHasher
from fastapi import APIRouter, Depends, status

from src.users.schemas import CreateUserRequest, User, UserResponse
from src.common.database import user_db
from src.users.errors import EmailAlreadyExistsException
from src.auth.router import get_current_user

user_router = APIRouter(prefix="/users", tags=["users"])

@user_router.post("", status_code=status.HTTP_201_CREATED)
def create_user(request: CreateUserRequest) -> UserResponse:
    if any(user.email == request.email for user in user_db):
        raise EmailAlreadyExistsException()

    user_id = max((user.user_id for user in user_db), default=0) + 1
    user = User(
        user_id=user_id,
        email=request.email,
        hashed_password=PasswordHasher().hash(request.password),
        name=request.name,
        phone_number=request.phone_number,
        height=request.height,
        bio=request.bio,
    )
    user_db.append(user)
    return UserResponse(**user.model_dump(exclude={"hashed_password"}))

@user_router.get("/me")
def get_user_info(user: User = Depends(get_current_user)) -> UserResponse:
    return UserResponse(
        user_id=user.user_id,
        email=user.email,
        name=user.name,
        phone_number=user.phone_number,
        height=user.height,
        bio=user.bio,
    )
