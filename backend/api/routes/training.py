"""Training scenario endpoints."""

from __future__ import annotations

import random
import uuid

from fastapi import APIRouter, Request

from backend.api.schemas import (
    GradeScenarioRequest, GradeScenarioResponse,
    TrainingScenarioResponse,
)
from backend.config import BB_SIZE
from backend.data_generation.monte_carlo import estimate_equity
from backend.feature_engineering.features import extract_features
from backend.poker_engine.deck import Deck
from backend.poker_engine.engine import GameEngine
from backend.poker_engine.types import ActionType, GameState, PlayerState, Position, Street

router = APIRouter()
engine = GameEngine()


def _generate_scenario() -> tuple[str, GameState, str]:
    """Generate a random training scenario.

    Returns:
        Tuple of (scenario_id, game_state, prompt_text).
    """
    state = engine.deal_hand(seed=random.randint(0, 999999))

    # Randomly advance through some actions to create an interesting spot
    num_preflop_actions = random.choice([1, 2, 3])
    action_choices = [
        ActionType.CALL, ActionType.BET_SMALL, ActionType.BET_MEDIUM,
        ActionType.CHECK, ActionType.BET_LARGE,
    ]

    for _ in range(num_preflop_actions):
        if state.is_hand_over:
            break
        legal = engine.get_legal_actions(state)
        if not legal:
            break
        # Pick a non-fold action to keep the hand going
        non_fold = [a for a in legal if a != ActionType.FOLD]
        if not non_fold:
            break
        action = random.choice(non_fold)
        state = engine.apply_action(state, action)

    # Build prompt
    hero_pos = state.actor
    hero = state.players[hero_pos]
    hero_cards_str = Deck.cards_to_str(hero.hole_cards)
    board_str = Deck.cards_to_str(state.board) if state.board else "no board yet"
    street_name = state.current_street.name.lower()

    prompt = (
        f"You hold {hero_cards_str[0]} {hero_cards_str[1]} "
        f"on the {street_name}. "
    )
    if state.board:
        prompt += f"Board: {' '.join(Deck.cards_to_str(state.board))}. "
    prompt += f"Pot is {state.pot / BB_SIZE:.1f} BB. "

    call_amount = max(0, state.current_bet - hero.bet_this_street)
    if call_amount > 0:
        prompt += f"You face a bet of {call_amount / BB_SIZE:.1f} BB. "
    prompt += "What do you do?"

    scenario_id = str(uuid.uuid4())
    return scenario_id, state, prompt


@router.get("/training-scenario", response_model=TrainingScenarioResponse)
async def get_training_scenario(request: Request):
    scenario_id, state, prompt = _generate_scenario()

    hero_pos = state.actor
    hero = state.players[hero_pos]
    legal = engine.get_legal_actions(state)

    # Store scenario for grading
    request.app.state.scenarios[scenario_id] = state

    return TrainingScenarioResponse(
        scenario_id=scenario_id,
        hole_cards=Deck.cards_to_str(hero.hole_cards),
        board=Deck.cards_to_str(state.board),
        pot_size_bb=state.pot / BB_SIZE,
        hero_stack_bb=hero.stack / BB_SIZE,
        villain_stack_bb=state.players[hero_pos.opponent].stack / BB_SIZE,
        hero_position=hero_pos.value,
        street=state.current_street.name.lower(),
        action_history=[
            {"player": a.player.value, "action": a.action_type.value, "amount": a.amount / BB_SIZE}
            for a in state.action_history
        ],
        legal_actions=[a.value for a in legal],
        prompt=prompt,
    )


@router.post("/grade-scenario", response_model=GradeScenarioResponse)
async def grade_scenario(req: GradeScenarioRequest, request: Request):
    state = request.app.state.scenarios.get(req.scenario_id)
    if state is None:
        # Generate a fresh scenario for grading
        _, state, _ = _generate_scenario()

    hero_pos = state.actor
    features = extract_features(state, hero_pos)

    # Equity
    hero = state.players[hero_pos]
    equity = estimate_equity(hero.hole_cards, state.board, num_simulations=500)

    # Action EVs
    legal = engine.get_legal_actions(state)
    ev_model = request.app.state.ev_model
    if ev_model:
        action_evs = ev_model.predict_action_evs(features, legal)
    else:
        action_evs = {a.value: 0.0 for a in legal}

    # Find optimal
    optimal_action = max(action_evs, key=action_evs.get)
    optimal_ev = action_evs.get(optimal_action, 0.0)
    chosen_ev = action_evs.get(req.chosen_action, action_evs.get("fold", 0.0))
    ev_loss = max(0, optimal_ev - chosen_ev)

    # Grade based on EV loss
    if ev_loss < 0.5:
        grade, score = "A", 95
    elif ev_loss < 1.5:
        grade, score = "B", 80
    elif ev_loss < 3.0:
        grade, score = "C", 65
    elif ev_loss < 5.0:
        grade, score = "D", 45
    else:
        grade, score = "F", 20

    # Adjust score based on equity estimate accuracy
    equity_diff = abs(req.hand_strength_estimate / 100 - equity)
    score -= int(equity_diff * 20)
    score = max(0, min(100, score))

    # Bluff probability
    bluff_prob = None
    bd = request.app.state.bluff_detector
    if bd and features.get("facing_bet", 0) == 1.0:
        _, bluff_prob = bd.predict(features)

    # Explanation
    explanation = _build_grade_explanation(
        req.chosen_action, optimal_action, equity, ev_loss, bluff_prob
    )

    return GradeScenarioResponse(
        score=score,
        grade=grade,
        predicted_equity=round(equity, 3),
        recommended_action=optimal_action,
        action_evs={k: round(v, 2) for k, v in action_evs.items()},
        chosen_ev=round(chosen_ev, 2),
        optimal_ev=round(optimal_ev, 2),
        ev_loss=round(ev_loss, 2),
        bluff_probability=round(bluff_prob, 3) if bluff_prob is not None else None,
        explanation=explanation,
    )


def _build_grade_explanation(
    chosen: str, optimal: str, equity: float,
    ev_loss: float, bluff_prob: float | None,
) -> str:
    parts = []
    if chosen == optimal:
        parts.append(f"Great choice! {chosen.replace('_', ' ').title()} is the recommended action.")
    else:
        parts.append(
            f"The recommended action was {optimal.replace('_', ' ')} "
            f"(you chose {chosen.replace('_', ' ')}). "
            f"EV loss: {ev_loss:.1f} BB."
        )

    parts.append(f"Your hand equity is approximately {equity:.0%}.")

    if bluff_prob is not None and bluff_prob > 0.5:
        parts.append(
            f"The opponent's line is likely a bluff ({bluff_prob:.0%}), "
            "so calling may have been profitable here."
        )

    return " ".join(parts)
