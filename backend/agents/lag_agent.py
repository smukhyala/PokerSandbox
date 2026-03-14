"""Loose-Aggressive (LAG) rule-based agent."""

from __future__ import annotations

import random

from backend.agents.base import Agent
from backend.feature_engineering.features import preflop_hand_group, extract_features
from backend.poker_engine.types import ActionType, GameState, Street


class LAGAgent(Agent):
    """Plays many hands aggressively. Wide range, frequent bluffs."""

    name = "LAG"

    def select_action(self, state: GameState, legal_actions: list[ActionType]) -> ActionType:
        player = state.players[self.position]
        hand_group = preflop_hand_group(player.hole_cards)

        if state.current_street == Street.PREFLOP:
            return self._preflop(hand_group, legal_actions, state)
        else:
            return self._postflop(state, legal_actions)

    def _preflop(self, hand_group: int, legal: list[ActionType], state: GameState) -> ActionType:
        facing_raise = ActionType.FOLD in legal

        if hand_group <= 5:
            # Play most hands — raise
            return self._best_raise(legal, prefer_large=(hand_group <= 2))
        elif hand_group <= 6:
            if facing_raise:
                # Call light
                return ActionType.CALL if ActionType.CALL in legal else ActionType.FOLD
            return self._best_raise(legal, prefer_large=False)
        else:
            # Trash hands: sometimes raise as a bluff
            if random.random() < 0.2:
                return self._best_raise(legal, prefer_large=False)
            if facing_raise:
                return ActionType.FOLD
            return ActionType.CHECK if ActionType.CHECK in legal else ActionType.FOLD

    def _postflop(self, state: GameState, legal: list[ActionType]) -> ActionType:
        features = extract_features(state, self.position)
        hand_strength = features["hand_rank_normalized"]
        facing_bet = features["facing_bet"] == 1.0

        if hand_strength >= 0.6:
            return self._best_raise(legal, prefer_large=True)
        elif hand_strength >= 0.35:
            if facing_bet:
                return ActionType.CALL
            # Bet aggressively even with medium hands
            return self._best_raise(legal, prefer_large=False)
        else:
            # Weak: bluff frequently (~30%)
            if facing_bet:
                if random.random() < 0.15:
                    return self._best_raise(legal, prefer_large=True)
                return ActionType.FOLD
            if ActionType.CHECK in legal:
                if random.random() < 0.30:
                    return self._best_raise(legal, prefer_large=True)
                return ActionType.CHECK
            return ActionType.FOLD

    def _best_raise(self, legal: list[ActionType], prefer_large: bool) -> ActionType:
        if prefer_large:
            for a in [ActionType.BET_LARGE, ActionType.BET_MEDIUM, ActionType.BET_SMALL]:
                if a in legal:
                    return a
        else:
            for a in [ActionType.BET_MEDIUM, ActionType.BET_LARGE, ActionType.BET_SMALL]:
                if a in legal:
                    return a
        if ActionType.CALL in legal:
            return ActionType.CALL
        if ActionType.CHECK in legal:
            return ActionType.CHECK
        return ActionType.FOLD
