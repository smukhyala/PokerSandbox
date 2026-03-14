"""FastAPI application factory."""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.models.hand_strength import HandStrengthModel
from backend.models.opponent_model import OpponentModel
from backend.models.bluff_detector import BluffDetector
from backend.models.ev_model import EVModel
from backend.models.model_store import load_model_or_none


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load ML models on startup."""
    print("Loading models...")
    app.state.hand_strength_model = load_model_or_none("hand_strength")
    app.state.ev_model = load_model_or_none("ev_model")
    app.state.opponent_model = load_model_or_none("opponent_model")
    app.state.bluff_detector = load_model_or_none("bluff_detector")
    app.state.scenarios = {}  # in-memory scenario store

    loaded = {
        "hand_strength": app.state.hand_strength_model is not None,
        "ev_model": app.state.ev_model is not None,
        "opponent_model": app.state.opponent_model is not None,
        "bluff_detector": app.state.bluff_detector is not None,
    }
    print(f"Models loaded: {loaded}")
    yield


def create_app() -> FastAPI:
    app = FastAPI(
        title="PokerLab",
        description="ML-driven poker training and simulation platform",
        version="0.1.0",
        lifespan=lifespan,
    )

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Import and include routers
    from backend.api.routes.health import router as health_router
    from backend.api.routes.analyze import router as analyze_router
    from backend.api.routes.training import router as training_router
    from backend.api.routes.simulate import router as simulate_router
    from backend.api.routes.strategy import router as strategy_router

    app.include_router(health_router, prefix="/api", tags=["health"])
    app.include_router(analyze_router, prefix="/api", tags=["analysis"])
    app.include_router(training_router, prefix="/api", tags=["training"])
    app.include_router(simulate_router, prefix="/api", tags=["simulation"])
    app.include_router(strategy_router, prefix="/api", tags=["strategy"])

    return app
