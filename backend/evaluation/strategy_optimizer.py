"""Simulation-driven strategy optimization."""

from __future__ import annotations

from dataclasses import dataclass

from backend.agents.calling_station import CallingStationAgent
from backend.agents.config_policy_agent import ConfigPolicyAgent
from backend.agents.lag_agent import LAGAgent
from backend.agents.ml_agent import MLAgent
from backend.agents.random_agent import RandomAgent
from backend.agents.tag_agent import TAGAgent
from backend.evaluation.experiments import run_head_to_head_experiment
from backend.evaluation.leak_detector import StrategyLeak, detect_leaks
from backend.models.model_store import load_model_or_none
from backend.strategy_language.schema import StrategyConfig


@dataclass
class StrategyCandidate:
    """A candidate strategy mutation."""

    name: str
    config: StrategyConfig
    changes: list[dict]
    reason: str


def optimize_strategy(
    config: StrategyConfig,
    leaks: list[StrategyLeak],
    *,
    baselines: list[str],
    num_hands: int,
    seed: int,
    max_candidates: int = 6,
) -> dict:
    """Generate, backtest, and rank strategy mutations."""
    candidates = _generate_candidates(config, leaks)[:max_candidates]
    if not candidates:
        return {
            "attempted": False,
            "reason": "No actionable leaks were detected.",
            "best_config": config.model_dump(),
            "best_score": None,
            "original_score": None,
            "improvement": None,
            "changes": [],
            "candidate_results": [],
        }

    original_results = _run_matchups(config, baselines, num_hands, seed)
    original_leaks = detect_leaks(config, original_results)
    original_score = _score_results(original_results, original_leaks)

    candidate_results = []
    for index, candidate in enumerate(candidates):
        results = _run_matchups(candidate.config, baselines, num_hands, seed + 100 + index * 17)
        candidate_leaks = detect_leaks(candidate.config, results)
        score = _score_results(results, candidate_leaks)
        avg_delta = _avg_delta(results)
        candidate_results.append({
            "name": candidate.name,
            "score": score,
            "avg_delta_bb_per_100": round(avg_delta, 3),
            "remaining_leaks": [leak.to_dict() for leak in candidate_leaks],
            "changes": candidate.changes,
            "reason": candidate.reason,
            "config": candidate.config.model_dump(),
            "matchup_results": results,
        })

    best = max(candidate_results, key=lambda result: result["score"])
    if best["score"] <= original_score:
        return {
            "attempted": True,
            "reason": "No candidate patch improved the original strategy in this seeded search.",
            "best_config": config.model_dump(),
            "best_score": original_score,
            "original_score": original_score,
            "improvement": 0,
            "changes": [],
            "candidate_results": candidate_results,
        }

    return {
        "attempted": True,
        "reason": "Generated candidates from detected leaks and selected the best seeded backtest result.",
        "best_config": best["config"],
        "best_score": best["score"],
        "original_score": original_score,
        "improvement": best["score"] - original_score,
        "changes": best["changes"],
        "candidate_results": candidate_results,
    }


def _generate_candidates(config: StrategyConfig, leaks: list[StrategyLeak]) -> list[StrategyCandidate]:
    candidates: list[StrategyCandidate] = []
    combined_changes: dict[str, float] = {}

    for leak in leaks:
        if not leak.suggested_parameter_changes:
            continue
        candidate_config = config.model_copy(deep=True)
        changes = []
        for path, value in leak.suggested_parameter_changes.items():
            before = _get_param(candidate_config, path)
            _set_param(candidate_config, path, value)
            changes.append({
                "parameter": path,
                "before": before,
                "after": value,
                "reason": leak.leak_type,
            })
            combined_changes[path] = value
        candidates.append(StrategyCandidate(
            name=f"Fix: {leak.leak_type}",
            config=candidate_config,
            changes=changes,
            reason=leak.recommendation,
        ))

    if combined_changes:
        candidate_config = config.model_copy(deep=True)
        changes = []
        for path, value in combined_changes.items():
            before = _get_param(candidate_config, path)
            _set_param(candidate_config, path, value)
            changes.append({
                "parameter": path,
                "before": before,
                "after": value,
                "reason": "Combined leak fixes",
            })
        candidates.insert(0, StrategyCandidate(
            name="Combined leak fixes",
            config=candidate_config,
            changes=changes,
            reason="Apply all compatible leak recommendations together.",
        ))

    candidates.extend(_generic_candidates(config))
    return _dedupe_candidates(candidates)


def _generic_candidates(config: StrategyConfig) -> list[StrategyCandidate]:
    candidates = []

    balanced = config.model_copy(deep=True)
    changes = [
        _change(balanced, "fold_to_aggression", _move_toward(balanced.fold_to_aggression, 0.50, 0.12), "Normalize defense frequency"),
        _change(balanced, "river.bluff_frequency", _move_toward(balanced.river.bluff_frequency, 0.10, 0.08), "Reduce river spew risk"),
        _change(balanced, "flop.value_bet_threshold", _move_toward(balanced.flop.value_bet_threshold, 0.60, 0.08), "Value bet less narrowly"),
    ]
    candidates.append(StrategyCandidate(
        name="Balanced correction",
        config=balanced,
        changes=changes,
        reason="Move extreme parameters toward a more robust baseline.",
    ))

    exploit_station = config.model_copy(deep=True)
    changes = [
        _change(exploit_station, "river.bluff_frequency", max(0.04, exploit_station.river.bluff_frequency - 0.12), "Reduce bluffs against callers"),
        _change(exploit_station, "turn.value_bet_threshold", max(0.54, exploit_station.turn.value_bet_threshold - 0.10), "Value bet thinner"),
        _change(exploit_station, "river.value_bet_threshold", max(0.55, exploit_station.river.value_bet_threshold - 0.10), "Value bet thinner"),
    ]
    candidates.append(StrategyCandidate(
        name="Anti-calling-station adjustment",
        config=exploit_station,
        changes=changes,
        reason="Improve performance against passive callers by reducing bluffs and increasing value extraction.",
    ))

    return candidates


def _run_matchups(
    config: StrategyConfig,
    baselines: list[str],
    num_hands: int,
    seed: int,
) -> list[dict]:
    results = []
    for index, baseline_name in enumerate(baselines):
        experiment = run_head_to_head_experiment(
            lambda strategy_config=config: ConfigPolicyAgent(strategy_config),
            lambda name=baseline_name: _make_baseline_agent(name),
            agent_1_name=config.name,
            agent_2_name=baseline_name,
            num_hands=num_hands,
            seed=seed + index,
            name=f"optimize_vs_{baseline_name.lower()}",
        )
        results.append({
            "baseline_agent": baseline_name,
            "seed": seed + index,
            "agent_1_stats": experiment.agent_1_stats,
            "agent_2_stats": experiment.agent_2_stats,
            "summary": experiment.summary,
        })
    return results


def _make_baseline_agent(name: str):
    name_lower = name.lower()
    if name_lower == "tag":
        return TAGAgent()
    if name_lower == "lag":
        return LAGAgent()
    if name_lower == "callingstation":
        return CallingStationAgent()
    if name_lower == "random":
        return RandomAgent()
    if name_lower == "mlagent":
        return MLAgent(
            ev_model=load_model_or_none("ev_model"),
            hand_strength_model=load_model_or_none("hand_strength"),
        )
    return RandomAgent()


def _score_results(results: list[dict], leaks: list[StrategyLeak]) -> int:
    avg_delta = _avg_delta(results)
    score = 60 + avg_delta / 4
    score -= sum({"high": 15, "medium": 8, "low": 3}.get(leak.severity, 0) for leak in leaks)
    if any(leak.severity == "high" for leak in leaks):
        score = min(score, 70)
    elif any(leak.severity == "medium" for leak in leaks):
        score = min(score, 85)
    elif any(leak.severity == "low" for leak in leaks):
        score = min(score, 95)
    return max(0, min(100, round(score)))


def _avg_delta(results: list[dict]) -> float:
    return sum(float(result["summary"]["delta_bb_per_100"]) for result in results) / max(len(results), 1)


def _change(config: StrategyConfig, path: str, value: float, reason: str) -> dict:
    before = _get_param(config, path)
    _set_param(config, path, value)
    return {"parameter": path, "before": before, "after": value, "reason": reason}


def _get_param(config: StrategyConfig, path: str):
    target = config
    for part in path.split("."):
        target = getattr(target, part)
    return target


def _set_param(config: StrategyConfig, path: str, value):
    parts = path.split(".")
    target = config
    for part in parts[:-1]:
        target = getattr(target, part)
    setattr(target, parts[-1], value)


def _move_toward(current: float, target: float, step: float) -> float:
    if current < target:
        return min(target, current + step)
    return max(target, current - step)


def _dedupe_candidates(candidates: list[StrategyCandidate]) -> list[StrategyCandidate]:
    seen = set()
    deduped = []
    for candidate in candidates:
        key = tuple(
            (change["parameter"], round(float(change["after"]), 3))
            for change in candidate.changes
        )
        if key in seen:
            continue
        seen.add(key)
        deduped.append(candidate)
    return deduped
