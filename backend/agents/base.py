"""Base agent interface for poker agents."""

from __future__ import annotations

from abc import ABC, abstractmethod

from backend.poker_engine.types import ActionType, GameState, HandResult, Position


class Agent(ABC):
    """Abstract base class for all poker agents."""

    name: str = "BaseAgent"
    position: Position = Position.BUTTON  # set by simulator before each hand

    @abstractmethod
    def select_action(self, state: GameState, legal_actions: list[ActionType]) -> ActionType:
        """Choose an action given the current game state and legal actions."""
        ...

    def observe_result(self, result: HandResult) -> None:
        """Optional callback after a hand completes. Override for learning agents."""
        pass

    def reset(self) -> None:
        """Reset per-session state. Override if agent maintains state across hands."""
        pass
