"""CORS middleware configuration helper."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from configs.settings import get_settings

settings = get_settings()


def setup_cors(app: FastAPI) -> None:
    """Registers standard CORS middleware configuration into the app instance."""
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=settings.cors_allow_credentials,
        allow_methods=["*"],
        allow_headers=["*"],
    )
