"""Strategy parsing endpoint."""

from fastapi import APIRouter, Request

from backend.agents.config_policy_agent import ConfigPolicyAgent
from backend.api.routes.simulate import _get_agent
from backend.api.schemas import (
    ParseStrategyRequest,
    ParseStrategyResponse,
    StrategyDiagnoseRequest,
    StrategyDiagnoseResponse,
    StrategyExperimentRequest,
    StrategyExperimentResponse,
)
from backend.evaluation.experiments import run_head_to_head_experiment
from backend.evaluation.strategy_diagnosis import diagnose_config, diagnose_strategy
from backend.strategy_language.schema import StrategyConfig
from backend.strategy_language.parser import parse_strategy

router = APIRouter()


@router.post("/parse-strategy", response_model=ParseStrategyResponse)
async def parse_strategy_endpoint(req: ParseStrategyRequest):
    result = parse_strategy(req.description)
    return ParseStrategyResponse(
        strategy=result.config.model_dump(),
        matched_keywords=result.matched_keywords,
        confidence=round(result.confidence, 2),
        warnings=result.warnings,
    )


@router.post("/strategy-experiment", response_model=StrategyExperimentResponse)
async def strategy_experiment(req: StrategyExperimentRequest, request: Request):
    """Parse a natural-language strategy and benchmark it against a baseline agent."""
    parsed = parse_strategy(req.description)
    config = parsed.config
    baseline = req.baseline_agent

    experiment = run_head_to_head_experiment(
        lambda: ConfigPolicyAgent(config),
        lambda: _get_agent(baseline, request=request),
        agent_1_name=config.name,
        agent_2_name=baseline,
        num_hands=req.num_hands,
        seed=req.seed,
        name="natural_language_strategy_experiment",
    )

    insights = _build_product_insights(
        req.description,
        baseline,
        experiment.agent_1_stats,
        experiment.agent_2_stats,
        experiment.summary,
    )

    return StrategyExperimentResponse(
        parsed_strategy=config.model_dump(),
        matched_keywords=parsed.matched_keywords,
        confidence=round(parsed.confidence, 2),
        warnings=parsed.warnings,
        baseline_agent=baseline,
        num_hands=req.num_hands,
        seed=req.seed,
        agent_1_stats=experiment.agent_1_stats,
        agent_2_stats=experiment.agent_2_stats,
        bankroll_history=experiment.bankroll_history,
        summary=experiment.summary,
        product_insights=insights,
    )


@router.post("/strategy-diagnose", response_model=StrategyDiagnoseResponse)
async def strategy_diagnose(req: StrategyDiagnoseRequest):
    """Compile a natural-language strategy, stress test it, and detect leaks."""
    if req.strategy_config:
        return diagnose_config(
            StrategyConfig(**req.strategy_config),
            baselines=req.baselines,
            num_hands=req.num_hands,
            seed=req.seed,
            optimize=req.optimize,
            max_candidates=req.max_candidates,
            matched_keywords=["patched config"],
            confidence=1.0,
            warnings=[],
        )

    return diagnose_strategy(
        req.description,
        baselines=req.baselines,
        num_hands=req.num_hands,
        seed=req.seed,
        optimize=req.optimize,
        max_candidates=req.max_candidates,
    )


def _build_product_insights(
    description: str,
    baseline: str,
    strategy_stats: dict,
    baseline_stats: dict,
    summary: dict,
) -> list[str]:
    """Convert experiment metrics into concise user-facing observations."""
    insights = []
    delta = float(summary["delta_bb_per_100"])
    if delta >= 0:
        insights.append(
            f"The parsed strategy outperformed {baseline} by {delta:.1f} BB/100 in this seeded run."
        )
    else:
        insights.append(
            f"The parsed strategy underperformed {baseline} by {abs(delta):.1f} BB/100 in this seeded run."
        )

    aggression_delta = strategy_stats["aggression_factor"] - baseline_stats["aggression_factor"]
    if aggression_delta > 0.2:
        insights.append("The strategy played materially more aggressively than the baseline.")
    elif aggression_delta < -0.2:
        insights.append("The strategy played materially more passively than the baseline.")

    fold_delta = strategy_stats["fold_frequency"] - baseline_stats["fold_frequency"]
    if fold_delta > 0.05:
        insights.append("It folded more often, which may reduce variance but can surrender equity.")
    elif fold_delta < -0.05:
        insights.append("It folded less often, creating a stickier profile against pressure.")

    if strategy_stats["showdown_rate"] > baseline_stats["showdown_rate"] + 0.05:
        insights.append("It reached showdown more often, so river and calling thresholds drive results.")

    if not insights:
        insights.append(f"Experiment completed for: {description}")
    return insights
