"""Lógica de negocio de autenticación.

Responsabilidad única (SRP): reglas de registro e inicio de sesión.
No conoce HTTP, sólo recibe y devuelve datos de dominio. La capa
de routers es quien traduce excepciones a respuestas HTTP.
"""

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models import User
from app.schemas import ChangePassword, Token, UserCreate
from app.security import create_access_token, hash_password, verify_password


class AuthService:

    @staticmethod
    def get_by_email(db: Session, email: str) -> User | None:
        return db.query(User).filter(User.email == email).first()

    @staticmethod
    def register(db: Session, data: UserCreate) -> User:
        if AuthService.get_by_email(db, data.email) is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="El email ya está registrado",
            )
        user = User(
            email=data.email,
            hashed_password=hash_password(data.password),
            full_name=data.full_name,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def authenticate(db: Session, email: str, password: str) -> User:
        user = AuthService.get_by_email(db, email)
        if user is None or not verify_password(password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Credenciales inválidas",
            )
        return user

    @staticmethod
    def login(db: Session, email: str, password: str) -> Token:
        user = AuthService.authenticate(db, email, password)
        access_token = create_access_token(subject=user.email)
        return Token(access_token=access_token)

    @staticmethod
    def change_password(db: Session, user: User, data: ChangePassword) -> dict[str, str]:
        if not verify_password(data.old_password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="La contraseña actual no es correcta",
            )
        user.hashed_password = hash_password(data.new_password)
        db.commit()
        return {"detail": "Contraseña actualizada exitosamente"}
