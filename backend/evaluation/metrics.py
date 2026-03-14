"""Model evaluation metrics."""

from __future__ import annotations

import numpy as np
from sklearn.metrics import (
    accuracy_score, classification_report, confusion_matrix,
    mean_absolute_error, mean_squared_error,
)


def classification_metrics(y_true, y_pred, labels=None) -> dict:
    """Compute classification metrics."""
    acc = accuracy_score(y_true, y_pred)
    cm = confusion_matrix(y_true, y_pred, labels=labels)
    report = classification_report(y_true, y_pred, labels=labels, output_dict=True, zero_division=0)

    return {
        "accuracy": acc,
        "confusion_matrix": cm.tolist(),
        "classification_report": report,
    }


def regression_metrics(y_true, y_pred) -> dict:
    """Compute regression metrics."""
    mse = mean_squared_error(y_true, y_pred)
    mae = mean_absolute_error(y_true, y_pred)
    rmse = np.sqrt(mse)

    return {
        "mse": float(mse),
        "mae": float(mae),
        "rmse": float(rmse),
    }
