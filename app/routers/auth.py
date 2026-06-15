"""Endpoints HTTP de autenticación (register y login).

Responsabilidad única (SRP): adaptar peticiones/respuestas HTTP y
delegar la lógica a `AuthService`.
"""

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import Token, UserCreate, UserOut
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register(data: UserCreate, db: Session = Depends(get_db)) -> UserOut:
    user = AuthService.register(db, data)
    return UserOut.model_validate(user)


@router.post("/login", response_model=Token)
def login(data: UserCreate, db: Session = Depends(get_db)) -> Token:
    return AuthService.login(db, data.email, data.password)
