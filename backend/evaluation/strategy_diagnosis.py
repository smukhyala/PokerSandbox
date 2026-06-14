"""Natural-language strategy diagnosis workflow."""

from __future__ import annotations

from backend.agents.config_policy_agent import ConfigPolicyAgent
from backend.agents.ml_agent import MLAgent
from backend.agents.random_agent import RandomAgent
from backend.agents.tag_agent import TAGAgent
from backend.agents.lag_agent import LAGAgent
from backend.agents.calling_station import CallingStationAgent
from backend.evaluation.experiments import run_head_to_head_experiment
from backend.evaluation.leak_detector import detect_leaks
from backend.evaluation.strategy_optimizer import optimize_strategy
from backend.models.model_store import load_model_or_none
from backend.strategy_language.parser import parse_strategy
from backend.strategy_language.schema import StrategyConfig


DEFAULT_BASELINES = ["TAG", "LAG", "CallingStation", "Random"]


def diagnose_strategy(
    description: str,
    *,
    baselines: list[str] | None = None,
    num_hands: int = 1000,
    seed: int = 42,
    optimize: bool = True,
    max_candidates: int = 6,
) -> dict:
    """Compile a natural-language strategy, stress test it, and detect leaks."""
    parsed = parse_strategy(description)
    return diagnose_config(
        parsed.config,
        baselines=baselines,
        num_hands=num_hands,
        seed=seed,
        optimize=optimize,
        max_candidates=max_candidates,
        matched_keywords=parsed.matched_keywords,
        confidence=round(parsed.confidence, 2),
        warnings=parsed.warnings,
    )


def diagnose_config(
    config: StrategyConfig,
    *,
    baselines: list[str] | None = None,
    num_hands: int = 1000,
    seed: int = 42,
    optimize: bool = True,
    max_candidates: int = 6,
    matched_keywords: list[str] | None = None,
    confidence: float = 1.0,
    warnings: list[str] | None = None,
) -> dict:
    """Stress test an already compiled strategy config and detect leaks."""
    baseline_names = baselines or DEFAULT_BASELINES
    matchup_results = []

    for index, baseline_name in enumerate(baseline_names):
        experiment = run_head_to_head_experiment(
            lambda strategy_config=config: ConfigPolicyAgent(strategy_config),
            lambda name=baseline_name: _make_baseline_agent(name),
            agent_1_name=config.name,
            agent_2_name=baseline_name,
            num_hands=num_hands,
            seed=seed + index,
            name=f"diagnose_vs_{baseline_name.lower()}",
        )
        matchup_results.append({
            "baseline_agent": baseline_name,
            "seed": seed + index,
            "agent_1_stats": experiment.agent_1_stats,
            "agent_2_stats": experiment.agent_2_stats,
            "summary": experiment.summary,
        })

    leaks = detect_leaks(config, matchup_results)
    score = _diagnosis_score(matchup_results, leaks)
    worst_matchup = min(matchup_results, key=lambda r: r["summary"]["delta_bb_per_100"])
    optimization = None
    if optimize:
        optimization = optimize_strategy(
            config,
            leaks,
            baselines=baseline_names,
            num_hands=max(10, num_hands // 2),
            seed=seed + 1000,
            max_candidates=max_candidates,
        )

    return {
        "parsed_strategy": config.model_dump(),
        "matched_keywords": matched_keywords or [],
        "confidence": confidence,
        "warnings": warnings or [],
        "num_hands_per_matchup": num_hands,
        "baselines": baseline_names,
        "matchup_results": matchup_results,
        "leaks": [leak.to_dict() for leak in leaks],
        "aggregate_score": score,
        "worst_matchup": {
            "baseline_agent": worst_matchup["baseline_agent"],
            "delta_bb_per_100": worst_matchup["summary"]["delta_bb_per_100"],
        },
        "optimization": optimization,
        "detailed_feedback": _detailed_feedback(score, matchup_results, leaks, optimization),
        "summary": _summary_text(score, leaks, worst_matchup),
    }


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


def _diagnosis_score(matchup_results: list[dict], leaks: list) -> int:
    avg_delta = sum(float(r["summary"]["delta_bb_per_100"]) for r in matchup_results) / len(matchup_results)
    score = 60 + avg_delta / 4
    score -= sum({"high": 15, "medium": 8, "low": 3}.get(leak.severity, 0) for leak in leaks)
    if any(leak.severity == "high" for leak in leaks):
        score = min(score, 70)
    elif any(leak.severity == "medium" for leak in leaks):
        score = min(score, 85)
    elif any(leak.severity == "low" for leak in leaks):
        score = min(score, 95)
    return max(0, min(100, round(score)))


def _summary_text(score: int, leaks: list, worst_matchup: dict) -> str:
    worst_name = worst_matchup["baseline_agent"]
    worst_delta = float(worst_matchup["summary"]["delta_bb_per_100"])
    if not leaks:
        return (
            f"Strategy score {score}/100. No major leaks triggered in this stress test. "
            f"Worst matchup was {worst_name} at {worst_delta:.1f} BB/100."
        )
    top = leaks[0]
    return (
        f"Strategy score {score}/100. Top leak: {top.leak_type}. "
        f"Worst matchup was {worst_name} at {worst_delta:.1f} BB/100."
    )


def _detailed_feedback(
    score: int,
    matchup_results: list[dict],
    leaks: list,
    optimization: dict | None,
) -> list[str]:
    avg_delta = sum(float(r["summary"]["delta_bb_per_100"]) for r in matchup_results) / len(matchup_results)
    best = max(matchup_results, key=lambda r: r["summary"]["delta_bb_per_100"])
    worst = min(matchup_results, key=lambda r: r["summary"]["delta_bb_per_100"])
    avg_bet = sum(float(r["agent_1_stats"].get("bet_frequency", 0)) for r in matchup_results) / len(matchup_results)
    avg_fold = sum(float(r["agent_1_stats"].get("fold_frequency", 0)) for r in matchup_results) / len(matchup_results)
    avg_showdown = sum(float(r["agent_1_stats"].get("showdown_rate", 0)) for r in matchup_results) / len(matchup_results)

    feedback = [
        (
            f"Overall score is {score}/100 because the strategy averaged {avg_delta:.1f} big blinds "
            "per 100 hands across the selected baselines. Positive numbers mean the compiled strategy "
            "won in simulation; negative numbers mean the baseline exploited it."
        ),
        (
            f"Best matchup was {best['baseline_agent']} at "
            f"{float(best['summary']['delta_bb_per_100']):.1f} big blinds per 100 hands, while worst "
            f"matchup was {worst['baseline_agent']} at "
            f"{float(worst['summary']['delta_bb_per_100']):.1f}. The gap between those two tells you "
            "whether the strategy is robust or only works against one opponent type."
        ),
        (
            f"Behaviorally, it bet {avg_bet:.1%} of the time, folded {avg_fold:.1%} of the time, "
            f"and reached showdown {avg_showdown:.1%} of hands. Those rates matter because profit is not "
            "just hand strength; it also depends on pressure, defense, and whether the strategy reaches "
            "showdown with hands that can actually win."
        ),
    ]

    if leaks:
        top = leaks[0]
        feedback.append(
            f"The most important leak is '{top.leak_type}'. This is bad because the simulation found "
            f"evidence that this behavior costs performance in at least one matchup: {'; '.join(top.evidence)}."
        )
        feedback.append(
            f"Recommended fix: {top.recommendation} The suggested parameter patch is not arbitrary; it moves "
            "the strategy toward the behavior that would directly address the measured leak."
        )
    else:
        feedback.append(
            "No major leak rule fired. That does not prove the strategy is optimal; it means this simulation "
            "did not find a strong, obvious exploit pattern with the current baselines and sample size."
        )

    if optimization and optimization.get("attempted"):
        improvement = optimization.get("improvement")
        if improvement and improvement > 0:
            feedback.append(
                f"The optimizer found a patch that improved the score by {improvement} points in a seeded "
                "candidate search. Treat that as a recommended experiment, not a mathematical proof."
            )
        else:
            feedback.append(
                "The optimizer tested candidate patches but did not find one that beat the original in this "
                "seeded run, so the safest recommendation is to inspect the leak evidence before applying changes."
            )

    return feedback
