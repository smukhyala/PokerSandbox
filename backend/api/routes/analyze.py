"""Hand analysis endpoint."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Request

from backend.api.schemas import AnalyzeHandRequest, AnalyzeHandResponse
from backend.config import BB_SIZE
from backend.data_generation.monte_carlo import estimate_equity
from backend.feature_engineering.features import extract_features
from backend.models.hand_strength import BUCKET_LABELS, equity_to_bucket
from backend.poker_engine.deck import Deck
from backend.poker_engine.types import (
    Action, ActionType, GameState, PlayerState, Position, Street,
)

router = APIRouter()


def _build_state_from_request(req: AnalyzeHandRequest) -> GameState:
    """Reconstruct a GameState from the API request."""
    hole_cards = Deck.str_to_cards(req.hole_cards)
    board = Deck.str_to_cards(req.board) if req.board else []

    # Map all positions to BTN (in position) or BB (out of position) for the heads-up engine
    in_position_seats = {"BTN", "CO", "SB"}
    hero_pos = Position.BUTTON if req.hero_position in in_position_seats else Position.BIG_BLIND
    villain_pos = hero_pos.opponent

    # Determine street from board length
    street = {0: Street.PREFLOP, 3: Street.FLOP, 4: Street.TURN, 5: Street.RIVER}.get(
        len(board), Street.PREFLOP
    )

    hero = PlayerState(
        position=hero_pos,
        hole_cards=hole_cards,
        stack=int(req.hero_stack_bb * BB_SIZE),
        bet_this_street=0,
        total_invested=int((100 - req.hero_stack_bb) * BB_SIZE) if req.hero_stack_bb < 100 else 0,
    )
    villain = PlayerState(
        position=villain_pos,
        hole_cards=[0, 0],  # unknown
        stack=int(req.villain_stack_bb * BB_SIZE),
    )

    # Parse action history to determine current_bet
    current_bet = 0
    for ah in req.action_history:
        amt = ah.get("amount", 0)
        if amt > current_bet:
            current_bet = int(amt * BB_SIZE)

    state = GameState(
        hand_id=str(uuid.uuid4()),
        players={hero_pos: hero, villain_pos: villain},
        board=board,
        current_street=street,
        pot=int(req.pot_size_bb * BB_SIZE),
        current_bet=current_bet,
        actor=hero_pos,
    )
    return state


@router.post("/analyze-hand", response_model=AnalyzeHandResponse)
async def analyze_hand(req: AnalyzeHandRequest, request: Request):
    state = _build_state_from_request(req)
    in_position_seats = {"BTN", "CO", "SB"}
    hero_pos = Position.BUTTON if req.hero_position in in_position_seats else Position.BIG_BLIND
    features = extract_features(state, hero_pos)

    # Equity via Monte Carlo (this is the ground truth)
    hole_cards = Deck.str_to_cards(req.hole_cards)
    board = Deck.str_to_cards(req.board) if req.board else []
    equity = estimate_equity(hole_cards, board, num_simulations=1000)

    # Hand strength bucket derived from actual equity, not the RF model
    strength_bucket = equity_to_bucket(equity)
    strength_label = BUCKET_LABELS[strength_bucket]

    # RF model probabilities (informational)
    hs_model = request.app.state.hand_strength_model
    if hs_model:
        _, strength_probs = hs_model.predict(features)
    else:
        strength_probs = {}

    # Action EVs
    ev_model = request.app.state.ev_model
    from backend.poker_engine.engine import GameEngine
    engine = GameEngine()
    legal = engine.get_legal_actions(state)
    if ev_model:
        action_evs = ev_model.predict_action_evs(features, legal)
        best_action = max(action_evs, key=action_evs.get)
    else:
        action_evs = {a.value: 0.0 for a in legal}
        best_action = "check" if ActionType.CHECK in legal else "call"

    # Bluff detection
    bluff_prob = None
    bd_model = request.app.state.bluff_detector
    if bd_model and features.get("facing_bet", 0) == 1.0:
        _, bluff_prob = bd_model.predict(features)

    # Explanation
    explanation = _build_explanation(
        strength_label, equity, best_action, action_evs, bluff_prob, features
    )

    return AnalyzeHandResponse(
        hand_strength=strength_label,
        hand_strength_probs=strength_probs,
        equity=round(equity, 3),
        recommended_action=best_action,
        action_evs={k: round(v, 2) for k, v in action_evs.items()},
        bluff_probability=round(bluff_prob, 3) if bluff_prob is not None else None,
        explanation=explanation,
    )


def _build_explanation(
    strength: str, equity: float, best_action: str,
    evs: dict, bluff_prob: float | None, features: dict,
) -> str:
    """Build a human-readable explanation of the analysis."""
    parts = []

    parts.append(f"Your hand is classified as '{strength}' with {equity:.0%} equity against a random hand.")

    if best_action in ("bet_large", "bet_medium"):
        parts.append(f"The recommended action is {best_action.replace('_', ' ')} for value — your hand is strong enough to build the pot.")
    elif best_action == "bet_small":
        parts.append("A small bet is recommended — this balances value and protection.")
    elif best_action == "call":
        parts.append("Calling is recommended — your hand has enough equity to continue but isn't strong enough to raise.")
    elif best_action == "fold":
        parts.append("Folding is recommended — your hand equity doesn't justify the cost of continuing.")
    elif best_action == "check":
        parts.append("Checking is recommended — your hand is marginal and benefits from pot control.")

    if bluff_prob is not None:
        if bluff_prob > 0.6:
            parts.append(f"The opponent's line looks bluff-heavy ({bluff_prob:.0%} bluff probability).")
        elif bluff_prob < 0.3:
            parts.append(f"The opponent's line looks value-heavy ({1-bluff_prob:.0%} value probability).")

    spr = features.get("spr", 0)
    if spr < 3:
        parts.append("The stack-to-pot ratio is low, favoring commitment with strong hands.")

    if features.get("is_in_position", 0) == 1.0:
        parts.append("You have position, which gives you an informational advantage.")
    else:
        parts.append("You are out of position and must act first post-flop, so play more cautiously.")

    return " ".join(parts)
