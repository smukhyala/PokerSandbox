"""Pydantic request/response models for the API."""

from __future__ import annotations

from pydantic import BaseModel, Field


class AnalyzeHandRequest(BaseModel):
    hole_cards: list[str] = Field(..., min_length=2, max_length=2, examples=[["Ah", "Kd"]])
    board: list[str] = Field(default=[], max_length=5, examples=[["Ts", "Jh", "Qc"]])
    pot_size_bb: float = Field(3.0, ge=0)
    hero_stack_bb: float = Field(97.0, ge=0)
    villain_stack_bb: float = Field(97.0, ge=0)
    hero_position: str = Field("BTN", pattern="^(BTN|BB)$")
    action_history: list[dict] = Field(default=[])


class AnalyzeHandResponse(BaseModel):
    hand_strength: str
    hand_strength_probs: dict[str, float]
    equity: float
    recommended_action: str
    action_evs: dict[str, float]
    bluff_probability: float | None
    explanation: str


class TrainingScenarioResponse(BaseModel):
    scenario_id: str
    hole_cards: list[str]
    board: list[str]
    pot_size_bb: float
    hero_stack_bb: float
    villain_stack_bb: float
    hero_position: str
    street: str
    action_history: list[dict]
    legal_actions: list[str]
    prompt: str


class GradeScenarioRequest(BaseModel):
    scenario_id: str
    chosen_action: str
    hand_strength_estimate: float = Field(50.0, ge=0, le=100)
    bluff_guess: float = Field(50.0, ge=0, le=100)


class GradeScenarioResponse(BaseModel):
    score: float
    grade: str
    predicted_equity: float
    recommended_action: str
    action_evs: dict[str, float]
    chosen_ev: float
    optimal_ev: float
    ev_loss: float
    bluff_probability: float | None
    explanation: str


class SimulateRequest(BaseModel):
    agent_1: str = Field("TAG", examples=["TAG", "LAG", "CallingStation", "Random", "MLAgent"])
    agent_2: str = Field("Random")
    num_hands: int = Field(1000, ge=10, le=50000)
    strategy_config_1: dict | None = None
    strategy_config_2: dict | None = None


class HandSummary(BaseModel):
    hand_number: int
    agent_1_cards: list[str]
    agent_2_cards: list[str]
    board: list[str]
    agent_1_profit_bb: float
    agent_2_profit_bb: float
    went_to_showdown: bool
    winner: str | None
    final_street: str
    actions: list[dict]


class SimulateResponse(BaseModel):
    num_hands: int
    agent_1_stats: dict
    agent_2_stats: dict
    bankroll_history: list[dict]
    hand_summaries: list[HandSummary]


class ParseStrategyRequest(BaseModel):
    description: str = Field(
        ..., min_length=5, max_length=1000,
        examples=["Play tight preflop, continuation bet dry boards often"],
    )


class ParseStrategyResponse(BaseModel):
    strategy: dict
    matched_keywords: list[str]
    confidence: float
    warnings: list[str]


class HealthResponse(BaseModel):
    status: str
    models_loaded: dict[str, bool]
    version: str
