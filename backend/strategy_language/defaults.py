"""Default strategy presets for common player archetypes."""

from backend.strategy_language.schema import (
    BetSizing, PreflopStrategy, StrategyConfig, StreetStrategy,
)


TAG_DEFAULT = StrategyConfig(
    name="Tight-Aggressive",
    description="Play premium hands aggressively, fold marginal hands",
    tightness=0.75,
    aggression=0.7,
    preflop=PreflopStrategy(
        open_raise_range=3, three_bet_range=1, call_raise_range=3,
        open_size=BetSizing.MEDIUM,
    ),
    flop=StreetStrategy(
        value_bet_threshold=0.65, call_threshold=0.4,
        bluff_frequency=0.15, bet_sizing=BetSizing.MEDIUM,
    ),
    turn=StreetStrategy(
        value_bet_threshold=0.7, call_threshold=0.45,
        bluff_frequency=0.10, bet_sizing=BetSizing.LARGE,
    ),
    river=StreetStrategy(
        value_bet_threshold=0.75, call_threshold=0.5,
        bluff_frequency=0.08, bet_sizing=BetSizing.LARGE,
    ),
    continuation_bet_frequency=0.70,
    fold_to_aggression=0.5,
)

LAG_DEFAULT = StrategyConfig(
    name="Loose-Aggressive",
    description="Play many hands aggressively with frequent bluffs",
    tightness=0.3,
    aggression=0.8,
    preflop=PreflopStrategy(
        open_raise_range=5, three_bet_range=3, call_raise_range=5,
        open_size=BetSizing.LARGE,
    ),
    flop=StreetStrategy(
        value_bet_threshold=0.55, call_threshold=0.3,
        bluff_frequency=0.30, bet_sizing=BetSizing.LARGE,
    ),
    turn=StreetStrategy(
        value_bet_threshold=0.6, call_threshold=0.35,
        bluff_frequency=0.25, bet_sizing=BetSizing.LARGE,
    ),
    river=StreetStrategy(
        value_bet_threshold=0.65, call_threshold=0.4,
        bluff_frequency=0.20, bet_sizing=BetSizing.LARGE,
    ),
    continuation_bet_frequency=0.80,
    fold_to_aggression=0.3,
)

CALLING_STATION_DEFAULT = StrategyConfig(
    name="Calling Station",
    description="Call too much, raise too little, never fold",
    tightness=0.2,
    aggression=0.15,
    preflop=PreflopStrategy(
        open_raise_range=6, three_bet_range=0, call_raise_range=7,
        limp_frequency=0.6,
    ),
    flop=StreetStrategy(
        value_bet_threshold=0.8, call_threshold=0.15,
        bluff_frequency=0.02, bet_sizing=BetSizing.SMALL,
    ),
    turn=StreetStrategy(
        value_bet_threshold=0.8, call_threshold=0.15,
        bluff_frequency=0.01, bet_sizing=BetSizing.SMALL,
    ),
    river=StreetStrategy(
        value_bet_threshold=0.85, call_threshold=0.15,
        bluff_frequency=0.0, bet_sizing=BetSizing.SMALL,
    ),
    continuation_bet_frequency=0.20,
    fold_to_aggression=0.1,
)

NIT_DEFAULT = StrategyConfig(
    name="Nit",
    description="Only play the very best hands, fold everything else",
    tightness=0.95,
    aggression=0.6,
    preflop=PreflopStrategy(
        open_raise_range=1, three_bet_range=0, call_raise_range=1,
    ),
    flop=StreetStrategy(
        value_bet_threshold=0.8, call_threshold=0.6,
        bluff_frequency=0.02, bet_sizing=BetSizing.MEDIUM,
    ),
    turn=StreetStrategy(
        value_bet_threshold=0.85, call_threshold=0.65,
        bluff_frequency=0.01, bet_sizing=BetSizing.LARGE,
    ),
    river=StreetStrategy(
        value_bet_threshold=0.9, call_threshold=0.7,
        bluff_frequency=0.0, bet_sizing=BetSizing.LARGE,
    ),
    continuation_bet_frequency=0.50,
    fold_to_aggression=0.7,
)

PRESETS = {
    "TAG": TAG_DEFAULT,
    "LAG": LAG_DEFAULT,
    "CallingStation": CALLING_STATION_DEFAULT,
    "Nit": NIT_DEFAULT,
}
