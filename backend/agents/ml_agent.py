"""ML-based agent: uses trained models to make decisions."""

from __future__ import annotations

from backend.agents.base import Agent
from backend.feature_engineering.features import extract_features
from backend.models.ev_model import EVModel
from backend.models.hand_strength import HandStrengthModel
from backend.poker_engine.types import ActionType, GameState


class MLAgent(Agent):
    """Agent that uses trained ML models for decision-making.

    Uses the EV model as the primary decision driver: for each legal action,
    predicts the expected value and picks the action with the highest EV.
    """

    name = "MLAgent"

    def __init__(
        self,
        ev_model: EVModel | None = None,
        hand_strength_model: HandStrengthModel | None = None,
    ):
        self.ev_model = ev_model
        self.hand_strength_model = hand_strength_model

    def select_action(self, state: GameState, legal_actions: list[ActionType]) -> ActionType:
        if self.ev_model is None or not self.ev_model._is_trained:
            # Fallback: check/call
            if ActionType.CHECK in legal_actions:
                return ActionType.CHECK
            if ActionType.CALL in legal_actions:
                return ActionType.CALL
            return legal_actions[0]

        features = extract_features(state, self.position)
        best_action_name, evs = self.ev_model.recommend_action(features, legal_actions)

        # Convert action name back to ActionType
        for action in legal_actions:
            if action.value == best_action_name:
                return action

        return legal_actions[0]
