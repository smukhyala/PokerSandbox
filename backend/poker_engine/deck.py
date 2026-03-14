"""Deck wrapper around treys for card handling."""

from __future__ import annotations

import random
from treys import Card, Deck as TreysDeck


RANKS = "23456789TJQKA"
SUITS = "shdc"

# Full 52-card deck as treys ints (cached)
FULL_DECK: list[int] = [Card.new(r + s) for r in RANKS for s in SUITS]


class Deck:
    """A shuffled deck of cards using treys integer representation."""

    def __init__(self, seed: int | None = None) -> None:
        self._cards = list(FULL_DECK)
        self._rng = random.Random(seed)
        self._rng.shuffle(self._cards)
        self._index = 0

    def draw(self, n: int = 1) -> list[int]:
        """Draw n cards from the top of the deck."""
        if self._index + n > len(self._cards):
            raise ValueError(f"Cannot draw {n} cards, only {len(self._cards) - self._index} remaining")
        cards = self._cards[self._index : self._index + n]
        self._index += n
        return cards

    @property
    def remaining(self) -> list[int]:
        """Cards remaining in the deck (not yet dealt)."""
        return self._cards[self._index:]

    @property
    def remaining_count(self) -> int:
        return len(self._cards) - self._index

    @staticmethod
    def card_to_str(card: int) -> str:
        """Convert a treys card int to a human-readable string like 'Ah'."""
        return Card.int_to_str(card)

    @staticmethod
    def str_to_card(s: str) -> int:
        """Convert a string like 'Ah' to a treys card int."""
        return Card.new(s)

    @staticmethod
    def cards_to_str(cards: list[int]) -> list[str]:
        return [Card.int_to_str(c) for c in cards]

    @staticmethod
    def str_to_cards(strings: list[str]) -> list[int]:
        return [Card.new(s) for s in strings]
