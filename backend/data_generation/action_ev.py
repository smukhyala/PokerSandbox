"""Action EV estimation via Monte Carlo rollout."""

from __future__ import annotations

import random

from backend.poker_engine.engine import GameEngine
from backend.poker_engine.types import ActionType, GameState, Position
from backend.agents.calling_station import CallingStationAgent
from backend.config import BB_SIZE


def estimate_action_ev(
    state: GameState,
    action: ActionType,
    perspective: Position,
    num_rollouts: int = 100,
    seed: int | None = None,
) -> float:
    """Estimate the EV of taking an action by rolling out the rest of the hand.

    Uses a CallingStation as the default opponent policy for rollouts.
    The hero uses check/call after the initial action.

    Args:
        state: Current game state.
        action: The action to evaluate.
        perspective: Which player's EV to compute.
        num_rollouts: Number of rollout simulations.
        seed: Random seed.

    Returns:
        Average profit in BB for taking this action.
    """
    engine = GameEngine()
    rng = random.Random(seed)
    total_profit = 0.0

    for i in range(num_rollouts):
        rollout_state = state.copy()

        # Randomize the deck for remaining cards
        rng.shuffle(rollout_state.deck_remaining)

        # Apply the action
        rollout_state = engine.apply_action(rollout_state, action)

        # Play out the rest with simple policies
        opp_agent = CallingStationAgent()
        opp_agent.position = perspective.opponent
        hero_agent = CallingStationAgent()  # hero also plays passively after initial action
        hero_agent.position = perspective

        agents = {perspective: hero_agent, perspective.opponent: opp_agent}
        max_actions = 50
        action_count = 0

        while not rollout_state.is_hand_over and action_count < max_actions:
            legal = engine.get_legal_actions(rollout_state)
            if not legal:
                break
            agent = agents[rollout_state.actor]
            chosen = agent.select_action(rollout_state, legal)
            if chosen not in legal:
                chosen = ActionType.CHECK if ActionType.CHECK in legal else ActionType.FOLD
            rollout_state = engine.apply_action(rollout_state, chosen)
            action_count += 1

        if rollout_state.is_hand_over:
            result = engine.get_hand_result(rollout_state)
            total_profit += result.profit.get(perspective, 0)

    return (total_profit / max(num_rollouts, 1)) / BB_SIZE


def estimate_all_action_evs(
    state: GameState,
    legal_actions: list[ActionType],
    perspective: Position,
    num_rollouts: int = 100,
    seed: int | None = None,
) -> dict[str, float]:
    """Estimate EV for all legal actions.

    Returns:
        Dict mapping action name -> EV in BB.
    """
    evs = {}
    for action in legal_actions:
        ev = estimate_action_ev(state, action, perspective, num_rollouts, seed)
        evs[action.value] = ev
    return evs
