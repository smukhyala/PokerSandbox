"""Hand strength prediction model using Random Forest."""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier

from backend.feature_engineering.features import FEATURE_NAMES
from backend.models.model_store import save_model, load_model_or_none

MODEL_NAME = "hand_strength"

# Equity bucket boundaries
BUCKET_EDGES = [0.0, 0.2, 0.4, 0.6, 0.8, 1.01]
BUCKET_LABELS = ["trash", "weak", "medium", "strong", "monster"]


def equity_to_bucket(equity: float) -> int:
    """Convert equity (0-1) to bucket index (0-4)."""
    for i in range(len(BUCKET_EDGES) - 1):
        if equity < BUCKET_EDGES[i + 1]:
            return i
    return len(BUCKET_LABELS) - 1


def bucket_to_label(bucket: int) -> str:
    return BUCKET_LABELS[bucket]


class HandStrengthModel:
    """Predicts hand strength bucket from game state features."""

    def __init__(self):
        self.model = RandomForestClassifier(
            n_estimators=200,
            max_depth=12,
            min_samples_leaf=20,
            n_jobs=-1,
            random_state=42,
        )
        self._is_trained = False

    def train(self, X: pd.DataFrame, y: pd.Series) -> dict:
        """Train the model.

        Args:
            X: Feature matrix with columns matching FEATURE_NAMES.
            y: Target bucket indices (0-4).

        Returns:
            Dict with training metrics.
        """
        self.model.fit(X, y)
        self._is_trained = True

        train_accuracy = self.model.score(X, y)
        importance = dict(zip(X.columns, self.model.feature_importances_))

        return {
            "train_accuracy": train_accuracy,
            "n_samples": len(X),
            "top_features": sorted(importance.items(), key=lambda x: -x[1])[:10],
        }

    def predict(self, features: dict[str, float]) -> tuple[str, dict[str, float]]:
        """Predict hand strength bucket and class probabilities.

        Args:
            features: 40-feature dict from extract_features().

        Returns:
            Tuple of (predicted_label, {label: probability}).
        """
        if not self._is_trained:
            raise RuntimeError("Model not trained yet")

        X = pd.DataFrame([features])[FEATURE_NAMES]
        bucket = self.model.predict(X)[0]
        probs = self.model.predict_proba(X)[0]

        prob_dict = {}
        for i, label in enumerate(BUCKET_LABELS):
            if i < len(probs):
                prob_dict[label] = float(probs[i])
            else:
                prob_dict[label] = 0.0

        return bucket_to_label(int(bucket)), prob_dict

    def save(self) -> str:
        return save_model(self, MODEL_NAME)

    @classmethod
    def load(cls) -> HandStrengthModel | None:
        return load_model_or_none(MODEL_NAME)
