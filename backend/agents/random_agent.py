"""Random agent: selects a uniformly random legal action."""

from __future__ import annotations

import random

from backend.agents.base import Agent
from backend.poker_engine.types import ActionType, GameState


class RandomAgent(Agent):
    name = "Random"

    def select_action(self, state: GameState, legal_actions: list[ActionType]) -> ActionType:
        return random.choice(legal_actions)
