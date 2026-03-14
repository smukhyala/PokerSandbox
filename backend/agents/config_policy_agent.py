"""Config-driven policy agent: makes decisions based on a StrategyConfig."""

from __future__ import annotations

import random

from backend.agents.base import Agent
from backend.feature_engineering.features import extract_features, preflop_hand_group
from backend.poker_engine.types import ActionType, GameState, Street
from backend.strategy_language.schema import BetSizing, StrategyConfig


class ConfigPolicyAgent(Agent):
    """Agent driven by a structured StrategyConfig schema."""

    def __init__(self, config: StrategyConfig):
        self.config = config
        self.name = f"Config:{config.name}"

    def select_action(self, state: GameState, legal_actions: list[ActionType]) -> ActionType:
        if state.current_street == Street.PREFLOP:
            return self._preflop(state, legal_actions)
        return self._postflop(state, legal_actions)

    def _preflop(self, state: GameState, legal: list[ActionType]) -> ActionType:
        player = state.players[self.position]
        hand_group = preflop_hand_group(player.hole_cards)
        pf = self.config.preflop
        facing_raise = ActionType.FOLD in legal

        if facing_raise:
            # Facing a raise
            if hand_group <= pf.three_bet_range:
                return self._sized_bet(legal, pf.open_size)
            elif hand_group <= pf.call_raise_range:
                return ActionType.CALL
            else:
                return ActionType.FOLD
        else:
            # First to act or facing a limp
            if hand_group <= pf.open_raise_range:
                if random.random() < pf.limp_frequency:
                    return ActionType.CALL if ActionType.CALL in legal else ActionType.CHECK
                return self._sized_bet(legal, pf.open_size)
            else:
                if ActionType.CHECK in legal:
                    return ActionType.CHECK
                return ActionType.FOLD

    def _postflop(self, state: GameState, legal: list[ActionType]) -> ActionType:
        features = extract_features(state, self.position)
        hand_strength = features["hand_rank_normalized"]
        facing_bet = features["facing_bet"] == 1.0
        is_cbet_spot = features["continuation_bet_opportunity"] == 1.0

        street_strat = self.config.get_street_strategy(int(state.current_street))

        # C-bet logic
        if is_cbet_spot and not facing_bet:
            if random.random() < self.config.continuation_bet_frequency:
                return self._sized_bet(legal, street_strat.bet_sizing)

        # Position adjustment
        pos_bonus = 0.0
        if features["is_in_position"] == 1.0:
            pos_bonus = self.config.positional_awareness * 0.1

        effective_strength = hand_strength + pos_bonus

        if effective_strength >= street_strat.value_bet_threshold:
            # Value bet
            return self._sized_bet(legal, street_strat.bet_sizing)
        elif effective_strength >= street_strat.call_threshold:
            # Medium hand
            if facing_bet:
                # Fold-to-aggression check
                if random.random() < self.config.fold_to_aggression * 0.3:
                    return ActionType.FOLD if ActionType.FOLD in legal else ActionType.CALL
                return ActionType.CALL
            return ActionType.CHECK if ActionType.CHECK in legal else ActionType.CALL
        else:
            # Weak hand — potential bluff
            if facing_bet:
                return ActionType.FOLD if ActionType.FOLD in legal else ActionType.CALL
            if random.random() < street_strat.bluff_frequency:
                return self._sized_bet(legal, street_strat.bluff_sizing)
            return ActionType.CHECK if ActionType.CHECK in legal else ActionType.FOLD

    def _sized_bet(self, legal: list[ActionType], sizing: BetSizing) -> ActionType:
        """Select a bet action matching the desired sizing."""
        sizing_map = {
            BetSizing.SMALL: [ActionType.BET_SMALL, ActionType.BET_MEDIUM, ActionType.BET_LARGE],
            BetSizing.MEDIUM: [ActionType.BET_MEDIUM, ActionType.BET_SMALL, ActionType.BET_LARGE],
            BetSizing.LARGE: [ActionType.BET_LARGE, ActionType.BET_MEDIUM, ActionType.BET_SMALL],
        }
        for action in sizing_map.get(sizing, []):
            if action in legal:
                return action
        if ActionType.ALL_IN in legal:
            return ActionType.ALL_IN
        if ActionType.CALL in legal:
            return ActionType.CALL
        if ActionType.CHECK in legal:
            return ActionType.CHECK
        return ActionType.FOLD
