"""Calling Station agent: calls too much, rarely raises or folds."""

from __future__ import annotations

import random

from backend.agents.base import Agent
from backend.poker_engine.types import ActionType, GameState


class CallingStationAgent(Agent):
    """Calls almost everything, rarely raises, rarely folds."""

    name = "CallingStation"

    def select_action(self, state: GameState, legal_actions: list[ActionType]) -> ActionType:
        # Almost always call if facing a bet
        if ActionType.CALL in legal_actions:
            # Fold occasionally with very low probability
            if random.random() < 0.05 and ActionType.FOLD in legal_actions:
                return ActionType.FOLD
            return ActionType.CALL

        # Not facing a bet — check most of the time
        if ActionType.CHECK in legal_actions:
            # Occasionally make a small bet
            if random.random() < 0.08:
                if ActionType.BET_SMALL in legal_actions:
                    return ActionType.BET_SMALL
            return ActionType.CHECK

        # Fallback
        if ActionType.FOLD in legal_actions:
            return ActionType.FOLD
        return legal_actions[0]
