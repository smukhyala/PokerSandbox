"""Thin wrapper around treys.Evaluator for hand evaluation."""

from __future__ import annotations

from treys import Evaluator

# Module-level evaluator (uses precomputed lookup tables, safe to share)
_evaluator = Evaluator()

# Treys rank class names (1-indexed)
RANK_CLASS_NAMES = {
    1: "Straight Flush",
    2: "Four of a Kind",
    3: "Full House",
    4: "Flush",
    5: "Straight",
    6: "Three of a Kind",
    7: "Two Pair",
    8: "Pair",
    9: "High Card",
}


def evaluate(hole_cards: list[int], board: list[int]) -> int:
    """Evaluate a hand. Returns treys rank (1=best, 7462=worst).

    Requires exactly 2 hole cards and 3-5 board cards.
    """
    return _evaluator.evaluate(board, hole_cards)


def get_rank_class(rank: int) -> int:
    """Get the rank class (1-9) from a treys rank."""
    return _evaluator.get_rank_class(rank)


def get_rank_class_name(rank: int) -> str:
    """Get human-readable hand class name from a treys rank."""
    rank_class = get_rank_class(rank)
    return RANK_CLASS_NAMES.get(rank_class, "Unknown")


def get_rank_percentage(rank: int) -> float:
    """Get percentile (0.0=worst, 1.0=best) from a treys rank.

    treys: rank 1 = best (Royal Flush), 7462 = worst (7-5-4-3-2 offsuit).
    We invert so higher = better.
    """
    return 1.0 - (rank - 1) / 7461
