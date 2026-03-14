"""Board texture features derived from community cards."""

from __future__ import annotations

from collections import Counter
from treys import Card


def _get_rank(card: int) -> int:
    """Extract rank (0=2, 12=A) from treys card int."""
    return Card.get_rank_int(card)


def _get_suit(card: int) -> int:
    """Extract suit from treys card int."""
    return Card.get_suit_int(card)


def board_texture_features(board: list[int], hole_cards: list[int]) -> dict[str, float]:
    """Extract board texture features.

    Args:
        board: List of treys card ints on the board (0-5 cards).
        hole_cards: Player's two hole cards as treys ints.

    Returns:
        Dict of feature name -> value.
    """
    features: dict[str, float] = {}

    features["board_num_cards"] = float(len(board))

    if not board:
        # No board cards yet (preflop)
        features["board_pair_present"] = 0.0
        features["board_trips_present"] = 0.0
        features["board_flush_possible"] = 0.0
        features["board_flush_draw"] = 0.0
        features["board_straight_possible"] = 0.0
        features["board_high_card_rank"] = 0.0
        features["board_wetness"] = 0.0
        features["board_overcards_to_hero"] = 0.0
        features["made_hand_on_board"] = 0.0
        return features

    board_ranks = [_get_rank(c) for c in board]
    board_suits = [_get_suit(c) for c in board]
    hero_ranks = [_get_rank(c) for c in hole_cards]

    rank_counts = Counter(board_ranks)
    suit_counts = Counter(board_suits)

    # Pair / trips on board
    features["board_pair_present"] = 1.0 if any(v >= 2 for v in rank_counts.values()) else 0.0
    features["board_trips_present"] = 1.0 if any(v >= 3 for v in rank_counts.values()) else 0.0

    # Flush possible: 3+ of any suit on board
    features["board_flush_possible"] = 1.0 if any(v >= 3 for v in suit_counts.values()) else 0.0

    # Flush draw: 2 board cards match a suit of one of hero's hole cards
    hero_suits = [_get_suit(c) for c in hole_cards]
    has_flush_draw = False
    for hs in hero_suits:
        matching_board = sum(1 for bs in board_suits if bs == hs)
        if matching_board >= 2:
            has_flush_draw = True
            break
    features["board_flush_draw"] = 1.0 if has_flush_draw else 0.0

    # Straight possible: check if 3+ ranks within a 5-rank window
    unique_ranks = sorted(set(board_ranks))
    straight_possible = False
    for i in range(len(unique_ranks)):
        window = [r for r in unique_ranks if unique_ranks[i] <= r <= unique_ranks[i] + 4]
        if len(window) >= 3:
            straight_possible = True
            break
    # Also check ace-low: A-2-3-4-5
    if 12 in unique_ranks:  # Ace
        low_ranks = [r for r in unique_ranks if r <= 3]
        if len(low_ranks) >= 2:
            straight_possible = True
    features["board_straight_possible"] = 1.0 if straight_possible else 0.0

    features["board_high_card_rank"] = float(max(board_ranks))

    # Wetness: composite of flush/straight/pair potential
    features["board_wetness"] = (
        features["board_flush_possible"]
        + features["board_straight_possible"]
        + features["board_pair_present"]
    ) / 3.0

    # Overcards: board cards higher than hero's best hole card
    hero_best = max(hero_ranks) if hero_ranks else 0
    features["board_overcards_to_hero"] = float(sum(1 for r in board_ranks if r > hero_best))

    # Made hand on board: simplified — 1 if any hero hole card pairs the board
    hero_hits_board = any(hr in board_ranks for hr in hero_ranks)
    features["made_hand_on_board"] = 1.0 if hero_hits_board else 0.0

    return features
