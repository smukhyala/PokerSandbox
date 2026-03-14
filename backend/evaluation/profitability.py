"""Agent profitability and simulation statistics."""

from __future__ import annotations

from backend.config import BB_SIZE
from backend.data_generation.simulator import SimulationResult
from backend.poker_engine.types import ActionType, Position


def compute_agent_stats(result: SimulationResult, agent_position_label: str = "agent_1") -> dict:
    """Compute detailed statistics for an agent from simulation results.

    Args:
        result: SimulationResult from a simulation run.
        agent_position_label: "agent_1" or "agent_2"

    Returns:
        Dict of stat name -> value.
    """
    is_agent_1 = agent_position_label == "agent_1"
    hand_results = result.hand_results
    n = len(hand_results)
    if n == 0:
        return {}

    # Profit
    total_profit = 0
    hands_won = 0
    showdowns = 0
    showdown_wins = 0
    folds = 0
    bets = 0
    calls = 0
    checks = 0
    total_actions = 0

    for i, hr in enumerate(hand_results):
        # Determine this agent's position for this hand
        if is_agent_1:
            pos = Position.BUTTON if i % 2 == 0 else Position.BIG_BLIND
        else:
            pos = Position.BIG_BLIND if i % 2 == 0 else Position.BUTTON

        profit = hr.profit.get(pos, 0)
        total_profit += profit
        if profit > 0:
            hands_won += 1

        if hr.went_to_showdown:
            showdowns += 1
            if hr.winner == pos:
                showdown_wins += 1

        # Action counts
        for action in hr.action_history:
            if action.player == pos:
                total_actions += 1
                if action.action_type == ActionType.FOLD:
                    folds += 1
                elif action.action_type == ActionType.CALL:
                    calls += 1
                elif action.action_type == ActionType.CHECK:
                    checks += 1
                elif action.action_type in (
                    ActionType.BET_SMALL, ActionType.BET_MEDIUM,
                    ActionType.BET_LARGE, ActionType.ALL_IN,
                ):
                    bets += 1

    aggressive = bets
    passive = calls + checks

    return {
        "total_hands": n,
        "total_profit_bb": total_profit / BB_SIZE,
        "bb_per_100": (total_profit / BB_SIZE) / n * 100 if n else 0,
        "win_rate": hands_won / n if n else 0,
        "showdown_rate": showdowns / n if n else 0,
        "showdown_win_rate": showdown_wins / showdowns if showdowns else 0,
        "aggression_factor": aggressive / max(passive, 1),
        "fold_frequency": folds / max(total_actions, 1),
        "bet_frequency": bets / max(total_actions, 1),
        "call_frequency": calls / max(total_actions, 1),
        "hands_won": hands_won,
    }
