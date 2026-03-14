"""Simulation engine: runs many hands between agents and collects data."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from backend.agents.base import Agent
from backend.config import BB_SIZE
from backend.feature_engineering.features import extract_features
from backend.poker_engine.engine import GameEngine
from backend.poker_engine.types import ActionType, GameState, HandResult, Position, Street


@dataclass
class DecisionRecord:
    """One training data row: a decision point + outcome."""
    hand_id: str
    features: dict[str, float]
    action_taken: str             # ActionType value
    street: int                   # Street int value
    position: str                 # Position value
    hand_profit: int              # net chips won/lost for the whole hand
    hand_profit_bb: float         # profit in big blinds
    went_to_showdown: bool
    agent_name: str


@dataclass
class SimulationResult:
    """Aggregate results from a simulation run."""
    num_hands: int
    hand_results: list[HandResult]
    decision_records: list[DecisionRecord]
    bankroll_history: list[dict[str, float]]  # [{hand: N, btn: X, bb: Y}, ...]

    @property
    def btn_profit(self) -> int:
        return sum(r.profit.get(Position.BUTTON, 0) for r in self.hand_results)

    @property
    def bb_profit(self) -> int:
        return sum(r.profit.get(Position.BIG_BLIND, 0) for r in self.hand_results)

    @property
    def btn_bb_per_100(self) -> float:
        if self.num_hands == 0:
            return 0.0
        return (self.btn_profit / BB_SIZE) / self.num_hands * 100

    @property
    def bb_bb_per_100(self) -> float:
        if self.num_hands == 0:
            return 0.0
        return (self.bb_profit / BB_SIZE) / self.num_hands * 100

    @property
    def showdown_rate(self) -> float:
        if self.num_hands == 0:
            return 0.0
        return sum(1 for r in self.hand_results if r.went_to_showdown) / self.num_hands


class Simulator:
    """Runs N hands between two agents, optionally collecting decision records."""

    def __init__(
        self,
        agent_1: Agent,
        agent_2: Agent,
        num_hands: int = 1000,
        record_features: bool = True,
        seed: int | None = None,
        alternate_positions: bool = True,
    ):
        self.agent_1 = agent_1
        self.agent_2 = agent_2
        self.num_hands = num_hands
        self.record_features = record_features
        self.seed = seed
        self.alternate_positions = alternate_positions
        self.engine = GameEngine()

    def run(self, progress_callback=None) -> SimulationResult:
        """Run the full simulation.

        Args:
            progress_callback: Optional callable(hand_number, bankroll_1, bankroll_2)
                called after each hand for live updates.

        Returns:
            SimulationResult with all hand results and decision records.
        """
        hand_results: list[HandResult] = []
        decision_records: list[DecisionRecord] = []
        bankroll_history: list[dict[str, float]] = []

        bankroll_1 = 0.0  # cumulative profit for agent_1 in chips
        bankroll_2 = 0.0

        for hand_num in range(self.num_hands):
            hand_seed = (self.seed * 10000 + hand_num) if self.seed is not None else None

            # Alternate positions each hand
            if self.alternate_positions and hand_num % 2 == 1:
                agent_btn, agent_bb = self.agent_2, self.agent_1
                a1_pos, a2_pos = Position.BIG_BLIND, Position.BUTTON
            else:
                agent_btn, agent_bb = self.agent_1, self.agent_2
                a1_pos, a2_pos = Position.BUTTON, Position.BIG_BLIND

            agent_btn.position = Position.BUTTON
            agent_bb.position = Position.BIG_BLIND

            if self.record_features:
                state, result, records = self._play_hand_with_records(
                    agent_btn, agent_bb, hand_seed, a1_pos,
                )
                decision_records.extend(records)
            else:
                state, result = self.engine.play_hand(agent_btn, agent_bb, seed=hand_seed)

            hand_results.append(result)

            # Track bankrolls
            bankroll_1 += result.profit.get(a1_pos, 0)
            bankroll_2 += result.profit.get(a2_pos, 0)

            bankroll_history.append({
                "hand": hand_num + 1,
                "agent_1_bankroll": bankroll_1 / BB_SIZE,
                "agent_2_bankroll": bankroll_2 / BB_SIZE,
            })

            if progress_callback:
                progress_callback(hand_num + 1, bankroll_1 / BB_SIZE, bankroll_2 / BB_SIZE)

        return SimulationResult(
            num_hands=self.num_hands,
            hand_results=hand_results,
            decision_records=decision_records,
            bankroll_history=bankroll_history,
        )

    def _play_hand_with_records(
        self,
        agent_btn: Agent,
        agent_bb: Agent,
        seed: int | None,
        agent_1_pos: Position,
    ) -> tuple[GameState, HandResult, list[DecisionRecord]]:
        """Play a hand while recording features at each decision point."""
        agents = {Position.BUTTON: agent_btn, Position.BIG_BLIND: agent_bb}
        state = self.engine.deal_hand(seed=seed)

        # Collect (position, features, action) at each decision
        raw_records: list[tuple[Position, dict[str, float], str, str]] = []

        max_actions = 100
        action_count = 0

        while not state.is_hand_over and action_count < max_actions:
            legal = self.engine.get_legal_actions(state)
            if not legal:
                break

            actor_pos = state.actor
            agent = agents[actor_pos]

            # Extract features before the action
            features = extract_features(state, actor_pos)

            action = agent.select_action(state, legal)
            if action not in legal:
                action = ActionType.FOLD if ActionType.FOLD in legal else ActionType.CHECK

            raw_records.append((
                actor_pos,
                features,
                action.value,
                agent.name,
            ))

            state = self.engine.apply_action(state, action)
            action_count += 1

        result = self.engine.get_hand_result(state)

        # Backfill profit into records
        records: list[DecisionRecord] = []
        for pos, features, action_val, agent_name in raw_records:
            records.append(DecisionRecord(
                hand_id=result.hand_id,
                features=features,
                action_taken=action_val,
                street=int(features.get("street", 0)),
                position=pos.value,
                hand_profit=result.profit.get(pos, 0),
                hand_profit_bb=result.profit.get(pos, 0) / BB_SIZE,
                went_to_showdown=result.went_to_showdown,
                agent_name=agent_name,
            ))

        return state, result, records
