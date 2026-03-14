"""Simulation endpoint."""

from __future__ import annotations

from fastapi import APIRouter, Request

from backend.agents.calling_station import CallingStationAgent
from backend.agents.config_policy_agent import ConfigPolicyAgent
from backend.agents.lag_agent import LAGAgent
from backend.agents.ml_agent import MLAgent
from backend.agents.random_agent import RandomAgent
from backend.agents.tag_agent import TAGAgent
from backend.api.schemas import HandSummary, SimulateRequest, SimulateResponse
from backend.config import BB_SIZE
from backend.data_generation.simulator import Simulator
from backend.evaluation.profitability import compute_agent_stats
from backend.poker_engine.deck import Deck
from backend.poker_engine.hand_evaluator import get_rank_class_name
from backend.poker_engine.types import Position, Street
from backend.strategy_language.schema import StrategyConfig

router = APIRouter()

STREET_NAMES = {Street.PREFLOP: "preflop", Street.FLOP: "flop", Street.TURN: "turn", Street.RIVER: "river"}


def _get_agent(name: str, strategy_config: dict | None = None, request: Request | None = None):
    """Instantiate an agent by name."""
    name_lower = name.lower()
    if name_lower == "tag":
        return TAGAgent()
    elif name_lower == "lag":
        return LAGAgent()
    elif name_lower == "callingstation":
        return CallingStationAgent()
    elif name_lower == "random":
        return RandomAgent()
    elif name_lower == "mlagent":
        ev = request.app.state.ev_model if request else None
        hs = request.app.state.hand_strength_model if request else None
        return MLAgent(ev_model=ev, hand_strength_model=hs)
    elif name_lower == "custom" and strategy_config:
        try:
            config = StrategyConfig(**strategy_config)
        except Exception as e:
            print(f"StrategyConfig validation error: {e}")
            print(f"Config received: {strategy_config}")
            # Try more lenient parsing
            config = StrategyConfig.model_validate(strategy_config)
        return ConfigPolicyAgent(config)
    else:
        return RandomAgent()


def _build_hand_summaries(result, req) -> list[HandSummary]:
    """Build per-hand summaries from simulation results."""
    summaries = []
    for i, hr in enumerate(result.hand_results):
        # Determine which agent was in which position this hand
        if i % 2 == 0:
            a1_pos, a2_pos = Position.BUTTON, Position.BIG_BLIND
        else:
            a1_pos, a2_pos = Position.BIG_BLIND, Position.BUTTON

        a1_cards = Deck.cards_to_str(hr.player_hands.get(a1_pos, []))
        a2_cards = Deck.cards_to_str(hr.player_hands.get(a2_pos, []))
        board = Deck.cards_to_str(hr.final_board) if hr.final_board else []

        winner_name = None
        if hr.winner == a1_pos:
            winner_name = req.agent_1
        elif hr.winner == a2_pos:
            winner_name = req.agent_2
        else:
            winner_name = "split"

        actions = []
        for a in hr.action_history:
            agent_name = req.agent_1 if a.player == a1_pos else req.agent_2
            actions.append({
                "agent": agent_name,
                "action": a.action_type.value,
                "amount_bb": round(a.amount / BB_SIZE, 1),
                "street": STREET_NAMES.get(a.street, "unknown"),
            })

        hand_class_1 = hr.player_hand_classes.get(a1_pos, "")
        hand_class_2 = hr.player_hand_classes.get(a2_pos, "")

        summaries.append(HandSummary(
            hand_number=i + 1,
            agent_1_cards=a1_cards,
            agent_2_cards=a2_cards,
            board=board,
            agent_1_profit_bb=round(hr.profit.get(a1_pos, 0) / BB_SIZE, 1),
            agent_2_profit_bb=round(hr.profit.get(a2_pos, 0) / BB_SIZE, 1),
            went_to_showdown=hr.went_to_showdown,
            winner=winner_name,
            final_street=STREET_NAMES.get(hr.final_street, "unknown"),
            actions=actions,
        ))
    return summaries


@router.post("/simulate")
async def simulate(req: SimulateRequest, request: Request):
    from fastapi.responses import JSONResponse
    import traceback

    try:
        agent_1 = _get_agent(req.agent_1, req.strategy_config_1, request)
        agent_2 = _get_agent(req.agent_2, req.strategy_config_2, request)

        sim = Simulator(
            agent_1=agent_1,
            agent_2=agent_2,
            num_hands=req.num_hands,
            record_features=False,
            seed=42,
        )
        result = sim.run()

        stats_1 = compute_agent_stats(result, "agent_1")
        stats_2 = compute_agent_stats(result, "agent_2")
        stats_1["agent_name"] = req.agent_1
        stats_2["agent_name"] = req.agent_2

        hand_summaries = _build_hand_summaries(result, req)

        return SimulateResponse(
            num_hands=result.num_hands,
            agent_1_stats=stats_1,
            agent_2_stats=stats_2,
            bankroll_history=result.bankroll_history,
            hand_summaries=hand_summaries,
        )
    except Exception as e:
        traceback.print_exc()
        return JSONResponse(
            status_code=500,
            content={"detail": str(e), "type": type(e).__name__},
        )
