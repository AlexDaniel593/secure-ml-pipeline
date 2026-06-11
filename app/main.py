"""Composition root de la aplicación FastAPI.

Responsabilidad única (SRP): crear la instancia de la app, montar
los routers e inicializar el esquema de base de datos.
"""

from fastapi import FastAPI

from app.database import Base, engine
from app.routers import auth, health

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Secure ML Pipeline Demo", version="0.1.0")
app.include_router(health.router)
app.include_router(auth.router)
