"""Core poker types: enums, dataclasses, and type aliases."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from enum import Enum, IntEnum
from typing import Optional


class Street(IntEnum):
    PREFLOP = 0
    FLOP = 1
    TURN = 2
    RIVER = 3


class ActionType(str, Enum):
    FOLD = "fold"
    CHECK = "check"
    CALL = "call"
    BET_SMALL = "bet_small"      # ~33% pot
    BET_MEDIUM = "bet_medium"    # ~66% pot
    BET_LARGE = "bet_large"      # ~100% pot
    ALL_IN = "all_in"


class Position(str, Enum):
    BUTTON = "BTN"    # dealer / small blind in heads-up
    BIG_BLIND = "BB"

    @property
    def opponent(self) -> Position:
        return Position.BIG_BLIND if self == Position.BUTTON else Position.BUTTON


@dataclass
class Action:
    player: Position
    action_type: ActionType
    amount: int          # chips committed by this action (0 for fold/check)
    street: Street
    sequence_index: int  # 0-based order within the hand


@dataclass
class PlayerState:
    position: Position
    hole_cards: list[int] = field(default_factory=list)  # treys int encoding
    stack: int = 100
    bet_this_street: int = 0
    total_invested: int = 0
    is_folded: bool = False
    is_all_in: bool = False

    def copy(self) -> PlayerState:
        return PlayerState(
            position=self.position,
            hole_cards=list(self.hole_cards),
            stack=self.stack,
            bet_this_street=self.bet_this_street,
            total_invested=self.total_invested,
            is_folded=self.is_folded,
            is_all_in=self.is_all_in,
        )


@dataclass
class GameState:
    """Complete snapshot of a hand at any point in time."""

    hand_id: str = field(default_factory=lambda: str(uuid.uuid4()))

    players: dict[Position, PlayerState] = field(default_factory=dict)
    board: list[int] = field(default_factory=list)  # treys ints; 0/3/4/5 cards
    deck_remaining: list[int] = field(default_factory=list)

    current_street: Street = Street.PREFLOP
    action_history: list[Action] = field(default_factory=list)

    pot: int = 0
    current_bet: int = 0
    actor: Position = Position.BUTTON
    num_actions_this_street: int = 0

    is_hand_over: bool = False
    winner: Optional[Position] = None

    effective_stack: int = 100  # starting effective stack

    @property
    def active_players(self) -> list[Position]:
        return [p for p, s in self.players.items() if not s.is_folded]

    @property
    def actions_this_street(self) -> list[Action]:
        return [a for a in self.action_history if a.street == self.current_street]

    @property
    def spr(self) -> float:
        """Stack-to-pot ratio for the smaller remaining stack."""
        stacks = [s.stack for s in self.players.values() if not s.is_folded]
        if not stacks or self.pot == 0:
            return float("inf")
        return min(stacks) / self.pot

    def copy(self) -> GameState:
        return GameState(
            hand_id=self.hand_id,
            players={p: s.copy() for p, s in self.players.items()},
            board=list(self.board),
            deck_remaining=list(self.deck_remaining),
            current_street=self.current_street,
            action_history=list(self.action_history),
            pot=self.pot,
            current_bet=self.current_bet,
            actor=self.actor,
            num_actions_this_street=self.num_actions_this_street,
            is_hand_over=self.is_hand_over,
            winner=self.winner,
            effective_stack=self.effective_stack,
        )


@dataclass
class HandResult:
    hand_id: str
    winner: Optional[Position]  # None if split pot
    pot_won: int
    went_to_showdown: bool
    final_board: list[int]
    player_hands: dict[Position, list[int]]
    player_hand_ranks: dict[Position, int]       # treys rank (1=best, 7462=worst)
    player_hand_classes: dict[Position, str]      # "Flush", "Two Pair", etc.
    action_history: list[Action]
    profit: dict[Position, int]                   # bb won/lost per player
    final_street: Street
