"""Strategy leak detection from simulated matchup metrics."""

from __future__ import annotations

from dataclasses import dataclass, field

from backend.strategy_language.schema import StrategyConfig


@dataclass
class StrategyLeak:
    """A structured strategy weakness with evidence and suggested fixes."""

    leak_type: str
    severity: str
    evidence: list[str]
    recommendation: str
    suggested_parameter_changes: dict[str, float] = field(default_factory=dict)
    impact_bb_per_100: float | None = None

    def to_dict(self) -> dict:
        return {
            "leak_type": self.leak_type,
            "severity": self.severity,
            "evidence": self.evidence,
            "recommendation": self.recommendation,
            "suggested_parameter_changes": self.suggested_parameter_changes,
            "impact_bb_per_100": self.impact_bb_per_100,
        }


def detect_leaks(
    config: StrategyConfig,
    matchup_results: list[dict],
) -> list[StrategyLeak]:
    """Detect strategy leaks from config settings and baseline comparisons."""
    leaks: list[StrategyLeak] = []
    if not matchup_results:
        return leaks

    avg_stats = _average_strategy_stats(matchup_results)
    worst = min(matchup_results, key=lambda r: r["summary"]["delta_bb_per_100"])
    worst_delta = float(worst["summary"]["delta_bb_per_100"])
    worst_baseline = str(worst["baseline_agent"])

    if config.fold_to_aggression >= 0.65 and _underperforms_vs(matchup_results, "LAG", threshold=-5):
        leaks.append(StrategyLeak(
            leak_type="Over-folding to aggression",
            severity=_severity(worst_delta, high=-25, medium=-10),
            evidence=[
                f"fold_to_aggression is high at {config.fold_to_aggression:.2f}",
                f"Worst matchup is {worst_baseline} at {worst_delta:.1f} BB/100",
                f"Observed fold frequency is {avg_stats['fold_frequency']:.1%}",
            ],
            recommendation=(
                "Defend more often against aggressive opponents by lowering fold-to-aggression "
                "and allowing more medium-strength calls."
            ),
            suggested_parameter_changes={
                "fold_to_aggression": max(0.30, config.fold_to_aggression - 0.20),
                "flop.call_threshold": max(0.20, config.flop.call_threshold - 0.08),
                "turn.call_threshold": max(0.25, config.turn.call_threshold - 0.06),
            },
            impact_bb_per_100=worst_delta,
        ))

    if config.aggression <= 0.35 or (
        config.aggression < 0.55 and avg_stats["bet_frequency"] < 0.18
    ):
        leaks.append(StrategyLeak(
            leak_type="Under-aggression",
            severity=_severity(worst_delta, high=-20, medium=-8),
            evidence=[
                f"aggression is low at {config.aggression:.2f}",
                f"Observed bet frequency is {avg_stats['bet_frequency']:.1%}",
                f"Average aggression factor is {avg_stats['aggression_factor']:.2f}",
            ],
            recommendation=(
                "Increase value betting and selective pressure, especially when checked to, "
                "so the strategy can win more pots without showdown."
            ),
            suggested_parameter_changes={
                "aggression": min(0.75, config.aggression + 0.20),
                "continuation_bet_frequency": min(0.85, config.continuation_bet_frequency + 0.12),
                "flop.value_bet_threshold": max(0.50, config.flop.value_bet_threshold - 0.08),
            },
            impact_bb_per_100=worst_delta if worst_delta < 0 else None,
        ))

    if config.river.bluff_frequency >= 0.22 and _underperforms_vs(
        matchup_results, "CallingStation", threshold=-3
    ):
        leak_delta = _delta_vs(matchup_results, "CallingStation")
        leaks.append(StrategyLeak(
            leak_type="Over-bluffing calling stations",
            severity=_severity(leak_delta, high=-20, medium=-8),
            evidence=[
                f"river bluff frequency is high at {config.river.bluff_frequency:.2f}",
                f"Performance vs CallingStation is {leak_delta:.1f} BB/100",
            ],
            recommendation=(
                "Reduce river bluffing against sticky opponents and shift that range toward "
                "thin value bets."
            ),
            suggested_parameter_changes={
                "river.bluff_frequency": max(0.04, config.river.bluff_frequency - 0.15),
                "river.value_bet_threshold": max(0.50, config.river.value_bet_threshold - 0.08),
            },
            impact_bb_per_100=leak_delta,
        ))

    if avg_stats["showdown_rate"] > 0.48 and avg_stats["showdown_win_rate"] < 0.46:
        leaks.append(StrategyLeak(
            leak_type="Calling too wide",
            severity="medium",
            evidence=[
                f"Showdown rate is high at {avg_stats['showdown_rate']:.1%}",
                f"Showdown win rate is low at {avg_stats['showdown_win_rate']:.1%}",
            ],
            recommendation=(
                "Tighten calling thresholds in marginal spots and fold more dominated bluff-catchers."
            ),
            suggested_parameter_changes={
                "flop.call_threshold": min(0.65, config.flop.call_threshold + 0.08),
                "turn.call_threshold": min(0.70, config.turn.call_threshold + 0.08),
                "river.call_threshold": min(0.75, config.river.call_threshold + 0.10),
            },
            impact_bb_per_100=worst_delta if worst_delta < 0 else None,
        ))

    if (
        _delta_vs(matchup_results, "CallingStation") < 10
        and config.flop.value_bet_threshold > 0.68
        and config.turn.value_bet_threshold > 0.68
    ):
        station_delta = _delta_vs(matchup_results, "CallingStation")
        leaks.append(StrategyLeak(
            leak_type="Not extracting enough value",
            severity=_severity(station_delta, high=-5, medium=10),
            evidence=[
                f"Performance vs CallingStation is only {station_delta:.1f} BB/100",
                f"flop value threshold is {config.flop.value_bet_threshold:.2f}",
                f"turn value threshold is {config.turn.value_bet_threshold:.2f}",
            ],
            recommendation=(
                "Value bet thinner against passive callers and reduce bluff frequency in those matchups."
            ),
            suggested_parameter_changes={
                "flop.value_bet_threshold": max(0.52, config.flop.value_bet_threshold - 0.12),
                "turn.value_bet_threshold": max(0.55, config.turn.value_bet_threshold - 0.10),
                "river.bluff_frequency": max(0.04, config.river.bluff_frequency - 0.06),
            },
            impact_bb_per_100=station_delta,
        ))

    if config.continuation_bet_frequency >= 0.85 and _underperforms_vs(
        matchup_results, "CallingStation", threshold=-3
    ):
        leaks.append(StrategyLeak(
            leak_type="Autopilot continuation betting",
            severity="medium",
            evidence=[
                f"c-bet frequency is very high at {config.continuation_bet_frequency:.2f}",
                "Sticky baselines can punish automatic flop pressure.",
            ],
            recommendation=(
                "Keep frequent c-bets on dry boards, but lower global c-bet frequency so wet boards "
                "and poor-equity spots are checked more often."
            ),
            suggested_parameter_changes={
                "continuation_bet_frequency": max(0.58, config.continuation_bet_frequency - 0.15),
                "flop.bluff_frequency": max(0.06, config.flop.bluff_frequency - 0.08),
            },
            impact_bb_per_100=_delta_vs(matchup_results, "CallingStation"),
        ))

    return _dedupe_leaks(leaks)


def _average_strategy_stats(matchup_results: list[dict]) -> dict[str, float]:
    keys = [
        "bb_per_100",
        "win_rate",
        "showdown_rate",
        "showdown_win_rate",
        "aggression_factor",
        "fold_frequency",
        "bet_frequency",
        "call_frequency",
    ]
    return {
        key: sum(float(r["agent_1_stats"].get(key, 0.0)) for r in matchup_results) / len(matchup_results)
        for key in keys
    }


def _underperforms_vs(matchup_results: list[dict], baseline: str, threshold: float) -> bool:
    return _delta_vs(matchup_results, baseline) < threshold


def _delta_vs(matchup_results: list[dict], baseline: str) -> float:
    for result in matchup_results:
        if str(result["baseline_agent"]).lower() == baseline.lower():
            return float(result["summary"]["delta_bb_per_100"])
    return 0.0


def _severity(value: float, *, high: float, medium: float) -> str:
    if value <= high:
        return "high"
    if value <= medium:
        return "medium"
    return "low"


def _dedupe_leaks(leaks: list[StrategyLeak]) -> list[StrategyLeak]:
    seen = set()
    deduped = []
    for leak in leaks:
        if leak.leak_type in seen:
            continue
        seen.add(leak.leak_type)
        deduped.append(leak)
    severity_rank = {"high": 0, "medium": 1, "low": 2}
    return sorted(deduped, key=lambda leak: severity_rank.get(leak.severity, 3))
