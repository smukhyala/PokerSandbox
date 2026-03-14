"""Save and load trained model artifacts."""

from __future__ import annotations

import os
from typing import Any

import joblib

from backend.config import ARTIFACTS_DIR


def save_model(model: Any, name: str) -> str:
    """Save a model to the artifacts directory.

    Args:
        model: The trained model object.
        name: Filename without extension (e.g., 'hand_strength').

    Returns:
        Path to the saved file.
    """
    os.makedirs(ARTIFACTS_DIR, exist_ok=True)
    path = os.path.join(ARTIFACTS_DIR, f"{name}.joblib")
    joblib.dump(model, path)
    return path


def load_model(name: str) -> Any:
    """Load a model from the artifacts directory.

    Args:
        name: Filename without extension.

    Returns:
        The loaded model object.

    Raises:
        FileNotFoundError: If the model file doesn't exist.
    """
    path = os.path.join(ARTIFACTS_DIR, f"{name}.joblib")
    if not os.path.exists(path):
        raise FileNotFoundError(f"Model not found: {path}")
    return joblib.load(path)


def load_model_or_none(name: str) -> Any | None:
    """Load a model, returning None if not found."""
    try:
        return load_model(name)
    except FileNotFoundError:
        return None


def model_exists(name: str) -> bool:
    """Check if a model artifact exists."""
    path = os.path.join(ARTIFACTS_DIR, f"{name}.joblib")
    return os.path.exists(path)
