"""Endpoints HTTP de autenticación (register y login).

Responsabilidad única (SRP): adaptar peticiones/respuestas HTTP y
delegar la lógica a `AuthService`.
"""

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.models import User

from app.database import get_db
from app.schemas import ChangePassword, Token, UserCreate, UserOut
from app.security import get_current_user
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register(data: UserCreate, db: Session = Depends(get_db)) -> UserOut:
    user = AuthService.register(db, data)
    return UserOut.model_validate(user)


@router.post("/login", response_model=Token)
def login(data: UserCreate, db: Session = Depends(get_db)) -> Token:
    return AuthService.login(db, data.email, data.password)


@router.patch("/me/password")
def change_password(
    data: ChangePassword,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, str]:
    return AuthService.change_password(db, current_user, data)
