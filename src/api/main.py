"""
Perfil Municípios Brasileiros — API REST
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.core.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    yield
    # Shutdown


app = FastAPI(
    title="Perfil Municípios Brasileiros",
    description="API de dados municipais consolidados de 40+ fontes públicas",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health():
    return {"status": "ok", "version": "0.1.0"}


# Registrar routers conforme forem criados:
# from src.api.routers import municipios, eleicoes, emendas, financas
# app.include_router(municipios.router, prefix="/api/v1")
