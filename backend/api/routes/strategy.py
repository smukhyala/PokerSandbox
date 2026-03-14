"""Strategy parsing endpoint."""

from fastapi import APIRouter

from backend.api.schemas import ParseStrategyRequest, ParseStrategyResponse
from backend.strategy_language.parser import parse_strategy

router = APIRouter()


@router.post("/parse-strategy", response_model=ParseStrategyResponse)
async def parse_strategy_endpoint(req: ParseStrategyRequest):
    result = parse_strategy(req.description)
    return ParseStrategyResponse(
        strategy=result.config.model_dump(),
        matched_keywords=result.matched_keywords,
        confidence=round(result.confidence, 2),
        warnings=result.warnings,
    )
