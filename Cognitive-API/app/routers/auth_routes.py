from fastapi import APIRouter
from ..models.user_models import UserRegister, UserLogin
from ..services.auth_service import register_user, login_user

router = APIRouter(prefix="/auth", tags=["Auth"])

@router.post("/register")
def register(data: UserRegister):
    return register_user(data)


@router.post("/login")
def login(data: UserLogin):
    return login_user(data)