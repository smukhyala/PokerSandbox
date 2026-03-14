"""Monte Carlo equity estimation via random rollouts."""

from __future__ import annotations

import random

from treys import Card

from backend.poker_engine.hand_evaluator import evaluate
from backend.poker_engine.deck import FULL_DECK
from backend.config import DEFAULT_EQUITY_SIMULATIONS


def estimate_equity(
    hole_cards: list[int],
    board: list[int],
    num_simulations: int = DEFAULT_EQUITY_SIMULATIONS,
    seed: int | None = None,
) -> float:
    """Estimate hand equity via Monte Carlo rollout against a random opponent.

    Args:
        hole_cards: Hero's two hole cards (treys ints).
        board: Community cards dealt so far (0-5 treys ints).
        num_simulations: Number of random rollouts.
        seed: Optional random seed for reproducibility.

    Returns:
        Win probability as a float in [0.0, 1.0].
    """
    rng = random.Random(seed)
    known = set(hole_cards) | set(board)
    available = [c for c in FULL_DECK if c not in known]
    cards_to_deal = 5 - len(board)
    wins = 0.0

    for _ in range(num_simulations):
        rng.shuffle(available)
        opp_hand = available[:2]
        new_board_cards = available[2 : 2 + cards_to_deal]
        full_board = board + new_board_cards

        hero_rank = evaluate(hole_cards, full_board)
        opp_rank = evaluate(opp_hand, full_board)

        if hero_rank < opp_rank:
            wins += 1.0
        elif hero_rank == opp_rank:
            wins += 0.5

    return wins / num_simulations


def estimate_equity_vs_range(
    hole_cards: list[int],
    board: list[int],
    opponent_range: list[list[int]],
    num_simulations: int = DEFAULT_EQUITY_SIMULATIONS,
    seed: int | None = None,
) -> float:
    """Estimate equity against a specific opponent range.

    Args:
        hole_cards: Hero's two hole cards.
        board: Community cards.
        opponent_range: List of possible opponent hands (each is a 2-card list).
        num_simulations: Number of rollouts per opponent hand.
        seed: Random seed.

    Returns:
        Average equity across the opponent range.
    """
    if not opponent_range:
        return estimate_equity(hole_cards, board, num_simulations, seed)

    rng = random.Random(seed)
    known_hero = set(hole_cards) | set(board)
    valid_hands = [h for h in opponent_range if not (set(h) & known_hero)]

    if not valid_hands:
        return estimate_equity(hole_cards, board, num_simulations, seed)

    total_wins = 0.0
    total_sims = 0
    cards_to_deal = 5 - len(board)

    for _ in range(num_simulations):
        opp_hand = rng.choice(valid_hands)
        known_all = known_hero | set(opp_hand)
        available = [c for c in FULL_DECK if c not in known_all]
        rng.shuffle(available)

        full_board = board + available[:cards_to_deal]
        hero_rank = evaluate(hole_cards, full_board)
        opp_rank = evaluate(opp_hand, full_board)

        if hero_rank < opp_rank:
            total_wins += 1.0
        elif hero_rank == opp_rank:
            total_wins += 0.5
        total_sims += 1

    return total_wins / max(total_sims, 1)
