"""Betting pattern features derived from action history."""

from __future__ import annotations

from backend.poker_engine.types import Action, ActionType, GameState, Position, Street


def betting_features(state: GameState, perspective: Position) -> dict[str, float]:
    """Extract betting pattern features from the action history.

    Args:
        state: Current game state.
        perspective: Which player's perspective to compute features from.

    Returns:
        Dict of feature name -> value.
    """
    villain = perspective.opponent
    features: dict[str, float] = {}

    all_actions = state.action_history
    street_actions = [a for a in all_actions if a.street == state.current_street]

    # Villain's actions
    villain_all = [a for a in all_actions if a.player == villain]
    villain_street = [a for a in street_actions if a.player == villain]

    # Aggression: (bets + raises) / total actions
    def aggression(actions: list[Action]) -> float:
        if not actions:
            return 0.0
        aggressive = sum(
            1 for a in actions
            if a.action_type in (
                ActionType.BET_SMALL, ActionType.BET_MEDIUM,
                ActionType.BET_LARGE, ActionType.ALL_IN,
            )
        )
        return aggressive / len(actions)

    features["villain_aggression_this_street"] = aggression(villain_street)
    features["villain_aggression_overall"] = aggression(villain_all)

    # Count bets/raises this street
    bet_types = {ActionType.BET_SMALL, ActionType.BET_MEDIUM, ActionType.BET_LARGE, ActionType.ALL_IN}
    bets_this_street = [a for a in street_actions if a.action_type in bet_types]
    features["num_bets_this_street"] = float(len(bets_this_street))
    features["num_raises_this_street"] = float(max(0, len(bets_this_street) - 1))

    # Villain's last bet size as fraction of pot
    villain_bets = [a for a in villain_all if a.action_type in bet_types and a.amount > 0]
    if villain_bets:
        last_bet = villain_bets[-1]
        pot_at_time = max(state.pot, 1)  # approximate
        features["villain_bet_size_last"] = last_bet.amount / pot_at_time
    else:
        features["villain_bet_size_last"] = 0.0

    # Facing a bet
    player = state.players[perspective]
    call_amount = state.current_bet - player.bet_this_street
    features["facing_bet"] = 1.0 if call_amount > 0 else 0.0

    # Bet to pot ratio
    features["bet_to_pot_ratio"] = state.current_bet / max(state.pot, 1)

    # Hero is aggressor (made last bet/raise on previous street)
    hero_actions = [a for a in all_actions if a.player == perspective]
    hero_prev_street_bets = [
        a for a in hero_actions
        if a.street == Street(max(0, state.current_street - 1))
        and a.action_type in bet_types
    ]
    features["hero_is_aggressor"] = 1.0 if hero_prev_street_bets else 0.0

    # Preflop raiser is hero
    preflop_bets = [
        a for a in all_actions
        if a.street == Street.PREFLOP and a.action_type in bet_types
    ]
    features["preflop_raiser_is_hero"] = (
        1.0 if preflop_bets and preflop_bets[0].player == perspective else 0.0
    )

    # Continuation bet opportunity
    is_flop = state.current_street == Street.FLOP
    hero_was_pfr = features["preflop_raiser_is_hero"] == 1.0
    no_actions_yet = len(street_actions) == 0
    features["continuation_bet_opportunity"] = (
        1.0 if is_flop and hero_was_pfr and no_actions_yet else 0.0
    )

    # Check-raise detected: villain checked then raised this street
    check_raise = False
    villain_street_actions = [a.action_type for a in villain_street]
    if len(villain_street_actions) >= 2:
        if villain_street_actions[0] == ActionType.CHECK and villain_street_actions[1] in bet_types:
            check_raise = True
    features["check_raise_detected"] = 1.0 if check_raise else 0.0

    # Total action sequence length
    features["action_sequence_length"] = float(len(all_actions))

    return features
