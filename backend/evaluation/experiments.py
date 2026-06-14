"""Reusable strategy experiment helpers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from backend.agents.base import Agent
from backend.data_generation.simulator import Simulator
from backend.evaluation.profitability import compute_agent_stats


@dataclass
class ExperimentResult:
    """Result from a head-to-head agent experiment."""

    name: str
    num_hands: int
    seed: int
    agent_1_name: str
    agent_2_name: str
    agent_1_stats: dict
    agent_2_stats: dict
    bankroll_history: list[dict[str, float]]
    summary: dict[str, float | str | bool]


def run_head_to_head_experiment(
    agent_1_factory: Callable[[], Agent],
    agent_2_factory: Callable[[], Agent],
    *,
    agent_1_name: str,
    agent_2_name: str,
    num_hands: int,
    seed: int = 42,
    name: str = "head_to_head",
) -> ExperimentResult:
    """Run a reproducible head-to-head agent experiment."""
    simulator = Simulator(
        agent_1=agent_1_factory(),
        agent_2=agent_2_factory(),
        num_hands=num_hands,
        record_features=False,
        seed=seed,
    )
    result = simulator.run()

    agent_1_stats = compute_agent_stats(result, "agent_1")
    agent_2_stats = compute_agent_stats(result, "agent_2")
    agent_1_stats["agent_name"] = agent_1_name
    agent_2_stats["agent_name"] = agent_2_name

    delta_bb_per_100 = agent_1_stats["bb_per_100"] - agent_2_stats["bb_per_100"]
    summary: dict[str, float | str | bool] = {
        "winner": agent_1_name if delta_bb_per_100 >= 0 else agent_2_name,
        "agent_1_bb_per_100": round(agent_1_stats["bb_per_100"], 3),
        "agent_2_bb_per_100": round(agent_2_stats["bb_per_100"], 3),
        "delta_bb_per_100": round(delta_bb_per_100, 3),
        "agent_1_total_profit_bb": round(agent_1_stats["total_profit_bb"], 3),
        "agent_2_total_profit_bb": round(agent_2_stats["total_profit_bb"], 3),
        "agent_1_outperformed": delta_bb_per_100 >= 0,
    }

    return ExperimentResult(
        name=name,
        num_hands=num_hands,
        seed=seed,
        agent_1_name=agent_1_name,
        agent_2_name=agent_2_name,
        agent_1_stats=agent_1_stats,
        agent_2_stats=agent_2_stats,
        bankroll_history=result.bankroll_history,
        summary=summary,
    )
