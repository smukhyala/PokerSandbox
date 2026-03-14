"""EV (expected value) prediction model using Random Forest."""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor

from backend.feature_engineering.features import FEATURE_NAMES
from backend.models.model_store import save_model, load_model_or_none
from backend.poker_engine.types import ActionType

MODEL_NAME = "ev_model"

# Action features: one-hot encoding for the action being evaluated
ACTION_FEATURE_NAMES = [f"action_{a.value}" for a in ActionType]
FULL_FEATURE_NAMES = FEATURE_NAMES + ACTION_FEATURE_NAMES


class EVModel:
    """Predicts the expected value of (state, action) pairs."""

    def __init__(self):
        self.model = RandomForestRegressor(
            n_estimators=300,
            max_depth=15,
            min_samples_leaf=10,
            n_jobs=-1,
            random_state=42,
        )
        self._is_trained = False

    def train(self, X: pd.DataFrame, y: pd.Series) -> dict:
        """Train on features + action one-hot + profit labels.

        Args:
            X: Feature matrix with FULL_FEATURE_NAMES columns.
            y: Target profit in BB.
        """
        self.model.fit(X, y)
        self._is_trained = True

        train_preds = self.model.predict(X)
        mse = float(np.mean((train_preds - y) ** 2))
        mae = float(np.mean(np.abs(train_preds - y)))

        return {
            "train_mse": mse,
            "train_mae": mae,
            "n_samples": len(X),
        }

    def predict_action_evs(
        self, features: dict[str, float], legal_actions: list[ActionType]
    ) -> dict[str, float]:
        """Predict EV for each legal action.

        Args:
            features: 40-feature dict from extract_features().
            legal_actions: List of legal ActionTypes.

        Returns:
            Dict mapping action name -> predicted EV in BB.
        """
        if not self._is_trained:
            raise RuntimeError("Model not trained")

        results = {}
        for action in legal_actions:
            row = dict(features)
            for at in ActionType:
                row[f"action_{at.value}"] = 1.0 if at == action else 0.0
            X = pd.DataFrame([row])[FULL_FEATURE_NAMES]
            ev = float(self.model.predict(X)[0])
            results[action.value] = ev

        return results

    def recommend_action(
        self, features: dict[str, float], legal_actions: list[ActionType]
    ) -> tuple[str, dict[str, float]]:
        """Recommend the best action and return all EVs.

        Returns:
            Tuple of (best_action_name, {action: ev}).
        """
        evs = self.predict_action_evs(features, legal_actions)
        best = max(evs, key=evs.get)
        return best, evs

    def save(self) -> str:
        return save_model(self, MODEL_NAME)

    @classmethod
    def load(cls) -> EVModel | None:
        return load_model_or_none(MODEL_NAME)
