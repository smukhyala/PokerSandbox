"""Evaluate trained models and strategy baselines.

Writes a JSON report to backend/artifacts/evaluation_report.json.
"""

from __future__ import annotations

import json
import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

import pandas as pd
from sklearn.model_selection import train_test_split

from backend.agents.calling_station import CallingStationAgent
from backend.agents.lag_agent import LAGAgent
from backend.agents.ml_agent import MLAgent
from backend.agents.random_agent import RandomAgent
from backend.agents.tag_agent import TAGAgent
from backend.config import ARTIFACTS_DIR, DATA_DIR
from backend.evaluation.experiments import run_head_to_head_experiment
from backend.evaluation.metrics import classification_metrics, regression_metrics
from backend.feature_engineering.features import FEATURE_NAMES
from backend.models.ev_model import FULL_FEATURE_NAMES
from backend.models.model_store import load_model_or_none
from backend.poker_engine.types import ActionType


def _load_training_data() -> pd.DataFrame:
    path = os.path.join(DATA_DIR, "training_data.csv")
    if not os.path.exists(path):
        raise FileNotFoundError(f"Missing training data at {path}. Run generate_data.py first.")
    return pd.read_csv(path)


def _top_feature_importances(model, feature_names: list[str], limit: int = 15) -> list[dict]:
    estimator = getattr(model, "model", None)
    importances = getattr(estimator, "feature_importances_", None)
    if importances is None:
        return []
    ranked = sorted(zip(feature_names, importances), key=lambda item: item[1], reverse=True)
    return [
        {"feature": feature, "importance": round(float(importance), 6)}
        for feature, importance in ranked[:limit]
    ]


def evaluate_models(df: pd.DataFrame) -> dict:
    """Evaluate available trained model artifacts on a held-out split."""
    report: dict[str, dict] = {}
    _, test_df = train_test_split(df, test_size=0.2, random_state=42)

    hand_strength = load_model_or_none("hand_strength")
    if hand_strength is not None and "equity_bucket" in test_df:
        X = test_df[FEATURE_NAMES]
        y = test_df["equity_bucket"]
        preds = hand_strength.model.predict(X)
        report["hand_strength"] = {
            **classification_metrics(y, preds),
            "top_features": _top_feature_importances(hand_strength, FEATURE_NAMES),
        }

    opponent_model = load_model_or_none("opponent_model")
    if opponent_model is not None:
        X = test_df[FEATURE_NAMES]
        y = test_df["action_taken"]
        preds = opponent_model.model.predict(X)
        labels = sorted(test_df["action_taken"].dropna().unique().tolist())
        report["opponent_action"] = {
            **classification_metrics(y, preds, labels=labels),
            "top_features": _top_feature_importances(opponent_model, FEATURE_NAMES),
        }

    bluff_detector = load_model_or_none("bluff_detector")
    if bluff_detector is not None and "is_bet" in test_df:
        bet_df = test_df[test_df["is_bet"] == 1]
        if len(bet_df) > 0:
            X = bet_df[FEATURE_NAMES]
            y = bet_df["is_bluff"]
            preds = bluff_detector.model.predict(X)
            report["bluff_detector"] = {
                **classification_metrics(y, preds, labels=[0, 1]),
                "top_features": _top_feature_importances(bluff_detector, FEATURE_NAMES),
                "bet_rows": int(len(bet_df)),
            }

    ev_model = load_model_or_none("ev_model")
    if ev_model is not None:
        ev_df = test_df.copy()
        for action_type in ActionType:
            col = f"action_{action_type.value}"
            if col not in ev_df:
                ev_df[col] = (ev_df["action_taken"] == action_type.value).astype(float)
        X = ev_df[FULL_FEATURE_NAMES]
        y = ev_df["hand_profit_bb"]
        preds = ev_model.model.predict(X)
        report["ev_model"] = {
            **regression_metrics(y, preds),
            "top_features": _top_feature_importances(ev_model, FULL_FEATURE_NAMES),
        }

    return report


def evaluate_agent_backtests(num_hands: int = 2000) -> dict:
    """Backtest ML/rule-based agents against fixed baselines."""
    ev_model = load_model_or_none("ev_model")
    hand_strength = load_model_or_none("hand_strength")

    experiments = [
        (
            "tag_vs_random",
            "TAG",
            "Random",
            lambda: TAGAgent(),
            lambda: RandomAgent(),
        ),
        (
            "lag_vs_random",
            "LAG",
            "Random",
            lambda: LAGAgent(),
            lambda: RandomAgent(),
        ),
        (
            "tag_vs_calling_station",
            "TAG",
            "CallingStation",
            lambda: TAGAgent(),
            lambda: CallingStationAgent(),
        ),
    ]

    if ev_model is not None:
        experiments.append((
            "mlagent_vs_tag",
            "MLAgent",
            "TAG",
            lambda: MLAgent(ev_model=ev_model, hand_strength_model=hand_strength),
            lambda: TAGAgent(),
        ))
        experiments.append((
            "mlagent_vs_lag",
            "MLAgent",
            "LAG",
            lambda: MLAgent(ev_model=ev_model, hand_strength_model=hand_strength),
            lambda: LAGAgent(),
        ))

    results = {}
    for name, agent_1_name, agent_2_name, agent_1_factory, agent_2_factory in experiments:
        experiment = run_head_to_head_experiment(
            agent_1_factory,
            agent_2_factory,
            agent_1_name=agent_1_name,
            agent_2_name=agent_2_name,
            num_hands=num_hands,
            seed=42,
            name=name,
        )
        results[name] = {
            "num_hands": experiment.num_hands,
            "seed": experiment.seed,
            "agent_1_stats": experiment.agent_1_stats,
            "agent_2_stats": experiment.agent_2_stats,
            "summary": experiment.summary,
        }
    return results


def main() -> None:
    os.makedirs(ARTIFACTS_DIR, exist_ok=True)
    started = time.time()
    df = _load_training_data()

    report = {
        "generated_at_unix": int(time.time()),
        "dataset": {
            "rows": int(len(df)),
            "columns": list(df.columns),
        },
        "models": evaluate_models(df),
        "agent_backtests": evaluate_agent_backtests(),
        "notes": [
            "EV labels use final hand profit from simulated agents, not counterfactual solver EV.",
            "Backtests are seeded and intended for regression comparisons, not proof of game-theoretic optimality.",
        ],
        "elapsed_seconds": round(time.time() - started, 2),
    }

    path = os.path.join(ARTIFACTS_DIR, "evaluation_report.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    print(f"Wrote evaluation report to {path}")


if __name__ == "__main__":
    main()
