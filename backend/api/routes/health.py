"""Health check endpoint."""

from fastapi import APIRouter, Request

from backend.api.schemas import HealthResponse

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health(request: Request):
    state = request.app.state
    return HealthResponse(
        status="ok",
        models_loaded={
            "hand_strength": state.hand_strength_model is not None,
            "opponent_model": state.opponent_model is not None,
            "bluff_detector": state.bluff_detector is not None,
            "ev_model": state.ev_model is not None,
        },
        version="0.1.0",
    )
