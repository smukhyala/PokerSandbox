"""Bluff detection model using Random Forest."""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier

from backend.feature_engineering.features import FEATURE_NAMES
from backend.models.model_store import save_model, load_model_or_none

MODEL_NAME = "bluff_detector"


class BluffDetector:
    """Predicts whether an opponent's bet is a bluff or value bet."""

    def __init__(self):
        self.model = RandomForestClassifier(
            n_estimators=150,
            max_depth=10,
            min_samples_leaf=20,
            n_jobs=-1,
            random_state=42,
        )
        self._is_trained = False

    def train(self, X: pd.DataFrame, y: pd.Series) -> dict:
        """Train on features + bluff/value labels.

        Args:
            X: Feature matrix.
            y: Binary labels (1=bluff, 0=value).
        """
        self.model.fit(X, y)
        self._is_trained = True

        return {
            "train_accuracy": self.model.score(X, y),
            "n_samples": len(X),
            "bluff_rate": float(y.mean()),
        }

    def predict(self, features: dict[str, float]) -> tuple[bool, float]:
        """Predict if the opponent is bluffing.

        Returns:
            Tuple of (is_bluff, bluff_probability).
        """
        if not self._is_trained:
            raise RuntimeError("Model not trained")

        X = pd.DataFrame([features])[FEATURE_NAMES]
        prediction = self.model.predict(X)[0]
        proba = self.model.predict_proba(X)[0]

        # Index of the bluff class (1)
        bluff_idx = list(self.model.classes_).index(1) if 1 in self.model.classes_ else 0
        bluff_prob = float(proba[bluff_idx])

        return bool(prediction), bluff_prob

    def save(self) -> str:
        return save_model(self, MODEL_NAME)

    @classmethod
    def load(cls) -> BluffDetector | None:
        return load_model_or_none(MODEL_NAME)
