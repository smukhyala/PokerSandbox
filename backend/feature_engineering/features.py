"""Main feature extraction: converts a GameState into a flat feature dictionary."""

from __future__ import annotations

from treys import Card

from backend.poker_engine.types import GameState, Position, Street
from backend.poker_engine.hand_evaluator import evaluate, get_rank_class, get_rank_percentage
from backend.feature_engineering.board_texture import board_texture_features
from backend.feature_engineering.betting_features import betting_features


# Preflop hand grouping (Sklansky-inspired)
# Group 0 = premium, Group 7 = trash
# Indexed by (high_rank, low_rank, suited) where suited=1 or 0
_HAND_GROUP_CACHE: dict[tuple[int, int, int], int] = {}


def _init_hand_groups() -> None:
    """Build the preflop hand group lookup table."""
    # Group 0: AA, KK, QQ, AKs
    premium_pairs = {(12, 12), (11, 11), (10, 10)}
    premium_suited = {(12, 11)}

    # Group 1: JJ, TT, AKo, AQs
    g1_pairs = {(9, 9), (8, 8)}
    g1_suited = {(12, 10)}
    g1_offsuit = {(12, 11)}

    # Group 2: 99, 88, AJs, ATs, KQs
    g2_pairs = {(7, 7), (6, 6)}
    g2_suited = {(12, 9), (12, 8), (11, 10)}

    # Group 3: 77, 66, AJo, KJs, QJs
    g3_pairs = {(5, 5), (4, 4)}
    g3_suited = {(11, 9), (10, 9)}
    g3_offsuit = {(12, 9)}

    # Group 4: 55, 44, ATo, KJo, QJo, JTs
    g4_pairs = {(3, 3), (2, 2)}
    g4_suited = {(9, 8)}
    g4_offsuit = {(12, 8), (11, 9), (10, 9)}

    # Group 5: 33, 22, suited connectors 89s-56s, A2s-A9s
    g5_pairs = {(1, 1), (0, 0)}
    g5_suited = set()
    for r in range(0, 8):  # A2s through A9s
        g5_suited.add((12, r))
    for r in range(4, 7):  # 56s through 89s
        g5_suited.add((r + 1, r))

    # Group 6: suited gappers, offsuit broadways
    g6_suited = set()
    for r in range(3, 8):  # gappers like T8s, 97s
        g6_suited.add((r + 2, r))
    g6_offsuit = {(11, 10), (11, 8), (10, 8)}

    for high in range(13):
        for low in range(high + 1):
            for suited in (0, 1):
                pair = (high, low)
                key = (high, low, suited)
                if high == low:
                    # Pocket pair
                    if pair in premium_pairs:
                        _HAND_GROUP_CACHE[key] = 0
                    elif pair in g1_pairs:
                        _HAND_GROUP_CACHE[key] = 1
                    elif pair in g2_pairs:
                        _HAND_GROUP_CACHE[key] = 2
                    elif pair in g3_pairs:
                        _HAND_GROUP_CACHE[key] = 3
                    elif pair in g4_pairs:
                        _HAND_GROUP_CACHE[key] = 4
                    elif pair in g5_pairs:
                        _HAND_GROUP_CACHE[key] = 5
                    else:
                        _HAND_GROUP_CACHE[key] = 6
                elif suited == 1:
                    if pair in premium_suited:
                        _HAND_GROUP_CACHE[key] = 0
                    elif pair in g1_suited:
                        _HAND_GROUP_CACHE[key] = 1
                    elif pair in g2_suited:
                        _HAND_GROUP_CACHE[key] = 2
                    elif pair in g3_suited:
                        _HAND_GROUP_CACHE[key] = 3
                    elif pair in g4_suited:
                        _HAND_GROUP_CACHE[key] = 4
                    elif pair in g5_suited:
                        _HAND_GROUP_CACHE[key] = 5
                    elif pair in g6_suited:
                        _HAND_GROUP_CACHE[key] = 6
                    else:
                        _HAND_GROUP_CACHE[key] = 7
                else:
                    # Offsuit
                    if pair in g1_offsuit:
                        _HAND_GROUP_CACHE[key] = 1
                    elif pair in g3_offsuit:
                        _HAND_GROUP_CACHE[key] = 3
                    elif pair in g4_offsuit:
                        _HAND_GROUP_CACHE[key] = 4
                    elif pair in g6_offsuit:
                        _HAND_GROUP_CACHE[key] = 6
                    else:
                        _HAND_GROUP_CACHE[key] = 7


_init_hand_groups()


def preflop_hand_group(hole_cards: list[int]) -> int:
    """Return hand group 0-7 for two hole cards."""
    r1 = Card.get_rank_int(hole_cards[0])
    r2 = Card.get_rank_int(hole_cards[1])
    s1 = Card.get_suit_int(hole_cards[0])
    s2 = Card.get_suit_int(hole_cards[1])
    high, low = max(r1, r2), min(r1, r2)
    suited = 1 if s1 == s2 else 0
    return _HAND_GROUP_CACHE.get((high, low, suited), 7)


def extract_features(state: GameState, perspective: Position) -> dict[str, float]:
    """Extract the full 40-feature vector from a game state.

    Args:
        state: Current game state.
        perspective: Which player's features to extract.

    Returns:
        Dict mapping feature names to float values.
    """
    player = state.players[perspective]
    opponent = state.players[perspective.opponent]
    features: dict[str, float] = {}

    hole_cards = player.hole_cards
    board = state.board

    # ---- Card strength features (8) ----
    r1 = Card.get_rank_int(hole_cards[0])
    r2 = Card.get_rank_int(hole_cards[1])
    s1 = Card.get_suit_int(hole_cards[0])
    s2 = Card.get_suit_int(hole_cards[1])

    if len(board) >= 3:
        rank = evaluate(hole_cards, board)
        features["hand_rank_normalized"] = get_rank_percentage(rank)
        features["hand_rank_class"] = float(get_rank_class(rank))
    else:
        # Preflop: use hand group as proxy (0=best, 7=worst -> normalize)
        group = preflop_hand_group(hole_cards)
        features["hand_rank_normalized"] = 1.0 - (group / 7.0)
        features["hand_rank_class"] = 0.0  # N/A preflop

    features["hole_card_rank_high"] = float(max(r1, r2))
    features["hole_card_rank_low"] = float(min(r1, r2))
    features["hole_cards_suited"] = 1.0 if s1 == s2 else 0.0
    features["hole_cards_connected"] = 1.0 if abs(r1 - r2) == 1 else 0.0
    features["hole_cards_pair"] = 1.0 if r1 == r2 else 0.0
    features["preflop_hand_group"] = float(preflop_hand_group(hole_cards))

    # ---- Board texture features (10) ----
    board_feats = board_texture_features(board, hole_cards)
    features.update(board_feats)

    # ---- Position and street features (4) ----
    features["street"] = float(state.current_street)

    # In heads-up: BTN is in position post-flop (acts last), out of position preflop
    if state.current_street == Street.PREFLOP:
        features["is_in_position"] = 1.0 if perspective == Position.BIG_BLIND else 0.0
    else:
        features["is_in_position"] = 1.0 if perspective == Position.BUTTON else 0.0

    features["position_is_btn"] = 1.0 if perspective == Position.BUTTON else 0.0
    features["num_actions_this_street"] = float(state.num_actions_this_street)

    # ---- Pot and stack features (6) ----
    from backend.config import BB_SIZE
    features["pot_size_bb"] = state.pot / BB_SIZE
    features["hero_stack_bb"] = player.stack / BB_SIZE
    features["villain_stack_bb"] = opponent.stack / BB_SIZE
    features["spr"] = min(player.stack, opponent.stack) / max(state.pot, 1)
    call_amount = max(0, state.current_bet - player.bet_this_street)
    features["pot_odds"] = call_amount / max(state.pot + call_amount, 1)
    features["hero_invested_bb"] = player.total_invested / BB_SIZE

    # ---- Betting pattern features (12) ----
    bet_feats = betting_features(state, perspective)
    features.update(bet_feats)

    return features


# Ordered list of all feature names (for consistent DataFrame columns)
FEATURE_NAMES: list[str] = [
    # Card (8)
    "hand_rank_normalized", "hand_rank_class",
    "hole_card_rank_high", "hole_card_rank_low",
    "hole_cards_suited", "hole_cards_connected", "hole_cards_pair",
    "preflop_hand_group",
    # Board (10)
    "board_num_cards", "board_pair_present", "board_trips_present",
    "board_flush_possible", "board_flush_draw", "board_straight_possible",
    "board_high_card_rank", "board_wetness", "board_overcards_to_hero",
    "made_hand_on_board",
    # Position/Street (4)
    "street", "is_in_position", "position_is_btn", "num_actions_this_street",
    # Pot/Stack (6)
    "pot_size_bb", "hero_stack_bb", "villain_stack_bb", "spr", "pot_odds",
    "hero_invested_bb",
    # Betting (12)
    "villain_aggression_this_street", "villain_aggression_overall",
    "num_bets_this_street", "num_raises_this_street",
    "villain_bet_size_last", "facing_bet", "bet_to_pot_ratio",
    "hero_is_aggressor", "preflop_raiser_is_hero",
    "continuation_bet_opportunity", "check_raise_detected",
    "action_sequence_length",
]
