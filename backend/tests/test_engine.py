"""Tests for the poker engine."""

import sys
import os

# Ensure project root is on the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

from backend.poker_engine.types import (
    ActionType, GameState, Position, Street,
)
from backend.poker_engine.engine import GameEngine
from backend.poker_engine.deck import Deck
from backend.poker_engine.hand_evaluator import evaluate, get_rank_class_name, get_rank_percentage
from backend.agents.random_agent import RandomAgent


engine = GameEngine()


class TestDeck:
    def test_deal_52_cards(self):
        deck = Deck(seed=42)
        cards = deck.draw(52)
        assert len(cards) == 52
        assert len(set(cards)) == 52  # all unique

    def test_deterministic_with_seed(self):
        d1 = Deck(seed=123)
        d2 = Deck(seed=123)
        assert d1.draw(5) == d2.draw(5)

    def test_card_string_conversion(self):
        card = Deck.str_to_card("Ah")
        assert Deck.card_to_str(card) == "Ah"

    def test_remaining_count(self):
        deck = Deck(seed=1)
        deck.draw(10)
        assert deck.remaining_count == 42


class TestHandEvaluator:
    def test_royal_flush_beats_pair(self):
        board = Deck.str_to_cards(["Ts", "Js", "Qs"])
        royal = Deck.str_to_cards(["Ks", "As"])
        pair = Deck.str_to_cards(["2h", "2d"])
        royal_rank = evaluate(royal, board)
        pair_rank = evaluate(pair, board)
        assert royal_rank < pair_rank  # lower = better in treys

    def test_rank_percentage_range(self):
        board = Deck.str_to_cards(["Ts", "Js", "Qs"])
        hand = Deck.str_to_cards(["Ks", "As"])
        rank = evaluate(hand, board)
        pct = get_rank_percentage(rank)
        assert 0.0 <= pct <= 1.0
        assert pct > 0.99  # royal flush should be near 1.0

    def test_rank_class_name(self):
        board = Deck.str_to_cards(["2s", "7h", "Td"])
        hand = Deck.str_to_cards(["7c", "7d"])
        rank = evaluate(hand, board)
        name = get_rank_class_name(rank)
        assert name == "Three of a Kind"


class TestGameEngine:
    def test_deal_hand_creates_valid_state(self):
        state = engine.deal_hand(seed=42)
        assert len(state.players) == 2
        assert len(state.players[Position.BUTTON].hole_cards) == 2
        assert len(state.players[Position.BIG_BLIND].hole_cards) == 2
        assert state.pot == 3  # SB=1 + BB=2
        assert state.current_bet == 2  # BB=2
        assert state.current_street == Street.PREFLOP
        assert state.actor == Position.BUTTON
        assert not state.is_hand_over

    def test_legal_actions_preflop_btn(self):
        state = engine.deal_hand(seed=42)
        legal = engine.get_legal_actions(state)
        assert ActionType.FOLD in legal
        assert ActionType.CALL in legal
        # Should have at least one bet size
        bet_actions = [a for a in legal if a.value.startswith("bet_") or a == ActionType.ALL_IN]
        assert len(bet_actions) >= 1

    def test_fold_ends_hand(self):
        state = engine.deal_hand(seed=42)
        state = engine.apply_action(state, ActionType.FOLD)
        assert state.is_hand_over
        assert state.winner == Position.BIG_BLIND

    def test_check_check_advances_street(self):
        state = engine.deal_hand(seed=42)
        # BTN calls (limps)
        state = engine.apply_action(state, ActionType.CALL)
        # BB checks (big blind option)
        state = engine.apply_action(state, ActionType.CHECK)
        # Should have advanced to flop
        assert state.current_street == Street.FLOP
        assert len(state.board) == 3

    def test_full_hand_call_down(self):
        """BTN calls preflop, then both check every street to showdown."""
        state = engine.deal_hand(seed=42)
        # Preflop: BTN calls, BB checks
        state = engine.apply_action(state, ActionType.CALL)
        state = engine.apply_action(state, ActionType.CHECK)
        assert state.current_street == Street.FLOP

        # Flop: BB checks, BTN checks
        state = engine.apply_action(state, ActionType.CHECK)
        state = engine.apply_action(state, ActionType.CHECK)
        assert state.current_street == Street.TURN

        # Turn: BB checks, BTN checks
        state = engine.apply_action(state, ActionType.CHECK)
        state = engine.apply_action(state, ActionType.CHECK)
        assert state.current_street == Street.RIVER

        # River: BB checks, BTN checks
        state = engine.apply_action(state, ActionType.CHECK)
        state = engine.apply_action(state, ActionType.CHECK)
        assert state.is_hand_over
        assert len(state.board) == 5

    def test_hand_result_profits_sum_to_zero(self):
        state = engine.deal_hand(seed=42)
        state = engine.apply_action(state, ActionType.FOLD)
        result = engine.get_hand_result(state)
        total_profit = sum(result.profit.values())
        assert total_profit == 0

    def test_all_in_runs_out_board(self):
        state = engine.deal_hand(seed=42)
        state = engine.apply_action(state, ActionType.ALL_IN)
        state = engine.apply_action(state, ActionType.CALL)
        assert state.is_hand_over
        assert len(state.board) == 5  # full board dealt

    def test_play_hand_with_random_agents(self):
        agent1 = RandomAgent()
        agent2 = RandomAgent()
        state, result = engine.play_hand(agent1, agent2, seed=42)
        assert state.is_hand_over
        assert sum(result.profit.values()) == 0

    def test_100_random_hands_complete(self):
        """Stress test: 100 hands between random agents should all complete."""
        agent1 = RandomAgent()
        agent2 = RandomAgent()
        for i in range(100):
            state, result = engine.play_hand(agent1, agent2, seed=i)
            assert state.is_hand_over, f"Hand {i} did not complete"
            assert sum(result.profit.values()) == 0, f"Hand {i} profits don't sum to 0"

    def test_game_state_copy_is_independent(self):
        state = engine.deal_hand(seed=42)
        copy = state.copy()
        copy.pot = 999
        assert state.pot != 999

    def test_bet_and_call_sequence(self):
        state = engine.deal_hand(seed=42)
        # BTN raises
        state = engine.apply_action(state, ActionType.BET_LARGE)
        assert not state.is_hand_over
        assert state.actor == Position.BIG_BLIND
        # BB calls
        state = engine.apply_action(state, ActionType.CALL)
        # Should advance to flop
        assert state.current_street == Street.FLOP

    def test_bet_and_fold_sequence(self):
        state = engine.deal_hand(seed=42)
        # BTN raises
        state = engine.apply_action(state, ActionType.BET_LARGE)
        # BB folds
        state = engine.apply_action(state, ActionType.FOLD)
        assert state.is_hand_over
        assert state.winner == Position.BUTTON

    def test_postflop_bb_acts_first(self):
        state = engine.deal_hand(seed=42)
        state = engine.apply_action(state, ActionType.CALL)
        state = engine.apply_action(state, ActionType.CHECK)
        # Now on flop, BB should act first
        assert state.actor == Position.BIG_BLIND

    def test_1000_hands_no_crash(self):
        """Extended stress test: 1000 hands."""
        agent1 = RandomAgent()
        agent2 = RandomAgent()
        for i in range(1000):
            state, result = engine.play_hand(agent1, agent2, seed=i * 7)
            assert state.is_hand_over
