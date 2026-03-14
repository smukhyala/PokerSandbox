"""Strategy configuration schema for poker agents."""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field, model_validator


class BetSizing(str, Enum):
    SMALL = "small"
    MEDIUM = "medium"
    LARGE = "large"


class StreetStrategy(BaseModel):
    """Strategy parameters for a single post-flop street."""

    value_bet_threshold: float = Field(
        0.7, ge=0.0, le=1.0,
        description="Minimum hand strength to bet for value",
    )
    call_threshold: float = Field(
        0.4, ge=0.0, le=1.0,
        description="Minimum hand strength to call a bet",
    )
    bet_sizing: BetSizing = Field(
        BetSizing.MEDIUM,
        description="Default bet size when value betting",
    )
    bluff_sizing: BetSizing = Field(
        BetSizing.SMALL,
        description="Bet size when bluffing",
    )
    bluff_frequency: float = Field(
        0.15, ge=0.0, le=1.0,
        description="Probability of bluffing with a weak hand",
    )
    draw_aggression: float = Field(
        0.5, ge=0.0, le=1.0,
        description="How aggressively to play draws (0=passive, 1=always semi-bluff)",
    )

    @model_validator(mode="after")
    def call_below_value(self):
        if self.call_threshold > self.value_bet_threshold:
            self.call_threshold = self.value_bet_threshold
        return self


class PreflopStrategy(BaseModel):
    """Preflop-specific strategy parameters."""

    open_raise_range: int = Field(
        3, ge=0, le=7,
        description="Max hand group to open-raise (0=tightest, 7=any two cards)",
    )
    three_bet_range: int = Field(
        1, ge=0, le=7,
        description="Max hand group to 3-bet with",
    )
    call_raise_range: int = Field(
        4, ge=0, le=7,
        description="Max hand group to call a raise with",
    )
    open_size: BetSizing = Field(
        BetSizing.MEDIUM,
        description="Open raise sizing",
    )
    limp_frequency: float = Field(
        0.0, ge=0.0, le=1.0,
        description="Frequency of limping instead of raising (0=never)",
    )


class StrategyConfig(BaseModel):
    """Complete strategy configuration for a poker agent."""

    name: str = Field("Custom Strategy", max_length=50)
    description: str = Field("", max_length=1000)

    tightness: float = Field(
        0.5, ge=0.0, le=1.0,
        description="0=very loose, 1=very tight",
    )
    aggression: float = Field(
        0.5, ge=0.0, le=1.0,
        description="0=very passive, 1=very aggressive",
    )

    preflop: PreflopStrategy = Field(default_factory=PreflopStrategy)
    flop: StreetStrategy = Field(default_factory=StreetStrategy)
    turn: StreetStrategy = Field(default_factory=StreetStrategy)
    river: StreetStrategy = Field(default_factory=StreetStrategy)

    continuation_bet_frequency: float = Field(
        0.65, ge=0.0, le=1.0,
        description="C-bet frequency when was preflop raiser",
    )
    fold_to_aggression: float = Field(
        0.5, ge=0.0, le=1.0,
        description="Tendency to fold facing bets (0=never, 1=easily)",
    )
    positional_awareness: float = Field(
        0.5, ge=0.0, le=1.0,
        description="How much to adjust play based on position",
    )

    def get_street_strategy(self, street_val: int) -> StreetStrategy:
        """Get the StreetStrategy for a given street integer."""
        mapping = {1: self.flop, 2: self.turn, 3: self.river}
        return mapping.get(street_val, self.flop)
