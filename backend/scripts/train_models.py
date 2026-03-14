"""Train all 4 Random Forest models from generated data."""

import sys
import os
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split

from backend.feature_engineering.features import FEATURE_NAMES
from backend.models.hand_strength import HandStrengthModel
from backend.models.opponent_model import OpponentModel
from backend.models.bluff_detector import BluffDetector
from backend.models.ev_model import EVModel, ACTION_FEATURE_NAMES, FULL_FEATURE_NAMES
from backend.poker_engine.types import ActionType
from backend.config import DATA_DIR


def load_data() -> pd.DataFrame:
    path = os.path.join(DATA_DIR, "training_data.csv")
    if not os.path.exists(path):
        raise FileNotFoundError(
            f"Training data not found at {path}. Run generate_data.py first."
        )
    return pd.read_csv(path)


def train_hand_strength(df: pd.DataFrame) -> None:
    """Train hand strength predictor (equity bucket classification)."""
    print("\n=== Training Hand Strength Model ===")

    # Use all rows that have valid features
    X = df[FEATURE_NAMES].copy()
    y = df["equity_bucket"]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    model = HandStrengthModel()
    metrics = model.train(X_train, y_train)
    print(f"  Train accuracy: {metrics['train_accuracy']:.3f}")
    print(f"  Train samples: {metrics['n_samples']}")

    test_accuracy = model.model.score(X_test, y_test)
    print(f"  Test accuracy: {test_accuracy:.3f}")

    top_feats = metrics["top_features"][:5]
    print(f"  Top features: {[(f, f'{v:.3f}') for f, v in top_feats]}")

    path = model.save()
    print(f"  Saved to: {path}")


def train_opponent_model(df: pd.DataFrame) -> None:
    """Train opponent action predictor."""
    print("\n=== Training Opponent Model ===")

    X = df[FEATURE_NAMES].copy()
    y = df["action_taken"]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    model = OpponentModel()
    metrics = model.train(X_train, y_train)
    print(f"  Train accuracy: {metrics['train_accuracy']:.3f}")
    print(f"  Classes: {metrics['classes']}")

    test_accuracy = model.model.score(X_test, y_test)
    print(f"  Test accuracy: {test_accuracy:.3f}")

    path = model.save()
    print(f"  Saved to: {path}")


def train_bluff_detector(df: pd.DataFrame) -> None:
    """Train bluff detection model on betting actions."""
    print("\n=== Training Bluff Detector ===")

    # Only use rows where the action was a bet
    bet_df = df[df["is_bet"] == 1].copy()
    if len(bet_df) < 100:
        print("  Not enough betting actions to train. Skipping.")
        return

    X = bet_df[FEATURE_NAMES].copy()
    y = bet_df["is_bluff"]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    model = BluffDetector()
    metrics = model.train(X_train, y_train)
    print(f"  Train accuracy: {metrics['train_accuracy']:.3f}")
    print(f"  Bluff rate in data: {metrics['bluff_rate']:.2%}")

    test_accuracy = model.model.score(X_test, y_test)
    print(f"  Test accuracy: {test_accuracy:.3f}")

    path = model.save()
    print(f"  Saved to: {path}")


def train_ev_model(df: pd.DataFrame) -> None:
    """Train EV prediction model."""
    print("\n=== Training EV Model ===")

    # Add action one-hot encoding
    for action_type in ActionType:
        col = f"action_{action_type.value}"
        df[col] = (df["action_taken"] == action_type.value).astype(float)

    X = df[FULL_FEATURE_NAMES].copy()
    y = df["hand_profit_bb"]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    model = EVModel()
    metrics = model.train(X_train, y_train)
    print(f"  Train MSE: {metrics['train_mse']:.3f}")
    print(f"  Train MAE: {metrics['train_mae']:.3f}")

    test_preds = model.model.predict(X_test)
    test_mse = float(np.mean((test_preds - y_test) ** 2))
    test_mae = float(np.mean(np.abs(test_preds - y_test)))
    print(f"  Test MSE: {test_mse:.3f}")
    print(f"  Test MAE: {test_mae:.3f}")

    path = model.save()
    print(f"  Saved to: {path}")


def main():
    print("=== Training All Models ===")
    start = time.time()

    df = load_data()
    print(f"Loaded {len(df)} records")

    train_hand_strength(df)
    train_opponent_model(df)
    train_bluff_detector(df)
    train_ev_model(df)

    elapsed = time.time() - start
    print(f"\nAll models trained in {elapsed:.1f}s")


if __name__ == "__main__":
    main()
