"""Tight-Aggressive (TAG) rule-based agent."""

from __future__ import annotations

import random

from backend.agents.base import Agent
from backend.feature_engineering.features import preflop_hand_group, extract_features
from backend.poker_engine.types import ActionType, GameState, Street


class TAGAgent(Agent):
    """Plays premium hands aggressively, folds marginal hands."""

    name = "TAG"

    def select_action(self, state: GameState, legal_actions: list[ActionType]) -> ActionType:
        player = state.players[self.position]
        hand_group = preflop_hand_group(player.hole_cards)

        if state.current_street == Street.PREFLOP:
            return self._preflop(hand_group, legal_actions, state)
        else:
            return self._postflop(state, legal_actions)

    def _preflop(self, hand_group: int, legal: list[ActionType], state: GameState) -> ActionType:
        facing_raise = ActionType.FOLD in legal  # FOLD only available when facing a bet

        if hand_group <= 1:
            # Premium: raise big
            return self._best_raise(legal, prefer_large=True)
        elif hand_group <= 3:
            if facing_raise:
                return ActionType.CALL
            return self._best_raise(legal, prefer_large=False)
        elif hand_group <= 4:
            if facing_raise:
                # Call small raises, fold to big ones
                call_amount = state.current_bet - state.players[self.position].bet_this_street
                if call_amount <= state.pot * 0.5:
                    return ActionType.CALL
                return ActionType.FOLD
            return self._best_raise(legal, prefer_large=False)
        else:
            if facing_raise:
                return ActionType.FOLD
            if ActionType.CHECK in legal:
                return ActionType.CHECK
            return ActionType.FOLD

    def _postflop(self, state: GameState, legal: list[ActionType]) -> ActionType:
        features = extract_features(state, self.position)
        hand_strength = features["hand_rank_normalized"]
        facing_bet = features["facing_bet"] == 1.0

        if hand_strength >= 0.75:
            # Strong hand: bet/raise for value
            return self._best_raise(legal, prefer_large=True)
        elif hand_strength >= 0.55:
            # Medium hand: bet small or call
            if facing_bet:
                return ActionType.CALL
            return self._best_raise(legal, prefer_large=False)
        elif hand_strength >= 0.35:
            # Marginal: check/call small bets
            if facing_bet:
                # Call if bet is small relative to pot
                pot_odds = features["pot_odds"]
                if pot_odds < 0.25:
                    return ActionType.CALL
                return ActionType.FOLD
            return ActionType.CHECK if ActionType.CHECK in legal else ActionType.FOLD
        else:
            # Weak: check/fold, occasional bluff
            if facing_bet:
                return ActionType.FOLD
            if ActionType.CHECK in legal:
                # Bluff ~12% of the time
                if random.random() < 0.12:
                    return self._best_raise(legal, prefer_large=False)
                return ActionType.CHECK
            return ActionType.FOLD

    def _best_raise(self, legal: list[ActionType], prefer_large: bool) -> ActionType:
        if prefer_large:
            for a in [ActionType.BET_LARGE, ActionType.BET_MEDIUM, ActionType.BET_SMALL]:
                if a in legal:
                    return a
        else:
            for a in [ActionType.BET_MEDIUM, ActionType.BET_SMALL, ActionType.BET_LARGE]:
                if a in legal:
                    return a
        if ActionType.CALL in legal:
            return ActionType.CALL
        if ActionType.CHECK in legal:
            return ActionType.CHECK
        return ActionType.FOLD
