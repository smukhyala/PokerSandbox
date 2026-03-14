"""Opponent action prediction model using Random Forest."""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier

from backend.feature_engineering.features import FEATURE_NAMES
from backend.models.model_store import save_model, load_model_or_none
from backend.poker_engine.types import ActionType

MODEL_NAME = "opponent_model"

ACTION_LABELS = [a.value for a in ActionType]


class OpponentModel:
    """Predicts the opponent's next action given game state features."""

    def __init__(self):
        self.model = RandomForestClassifier(
            n_estimators=200,
            max_depth=15,
            min_samples_leaf=10,
            n_jobs=-1,
            random_state=42,
        )
        self._is_trained = False

    def train(self, X: pd.DataFrame, y: pd.Series) -> dict:
        """Train on features + action labels.

        Args:
            X: Feature matrix.
            y: Action type strings.
        """
        self.model.fit(X, y)
        self._is_trained = True

        return {
            "train_accuracy": self.model.score(X, y),
            "n_samples": len(X),
            "classes": list(self.model.classes_),
        }

    def predict(self, features: dict[str, float]) -> tuple[str, dict[str, float]]:
        """Predict the opponent's most likely action.

        Returns:
            Tuple of (predicted_action, {action: probability}).
        """
        if not self._is_trained:
            raise RuntimeError("Model not trained")

        X = pd.DataFrame([features])[FEATURE_NAMES]
        action = self.model.predict(X)[0]
        probs = self.model.predict_proba(X)[0]

        prob_dict = {cls: float(p) for cls, p in zip(self.model.classes_, probs)}
        return str(action), prob_dict

    def save(self) -> str:
        return save_model(self, MODEL_NAME)

    @classmethod
    def load(cls) -> OpponentModel | None:
        return load_model_or_none(MODEL_NAME)
