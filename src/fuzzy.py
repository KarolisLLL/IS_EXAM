"""Maža, aiškinama fuzzy tipo rizikos taisyklių sistema be papildomos bibliotekos."""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, ClassifierMixin


def _series(frame: pd.DataFrame, name: str, default: float | str) -> pd.Series:
    if name in frame.columns:
        return frame[name]
    return pd.Series([default] * len(frame), index=frame.index)


def _linear_membership(values: pd.Series, low: float, high: float) -> np.ndarray:
    numeric = pd.to_numeric(values, errors="coerce").fillna((low + high) / 2)
    return np.clip((numeric.to_numpy() - low) / (high - low), 0.0, 1.0)


def _category_risk(values: pd.Series, mapping: dict[str, float], fallback: float) -> np.ndarray:
    normalised = values.astype(str).str.strip().str.lower()
    return normalised.map(mapping).fillna(fallback).to_numpy(dtype=float)


class FuzzyRiskClassifier(ClassifierMixin, BaseEstimator):
    """Aiškinamas rizikos balas iš kredito sumos, trukmės ir dviejų kategorijų.

    Tai nėra pilnas ekspertinės sistemos pakaitalas. Ji reikalinga kaip nedidelis
    palyginamas fuzzy kandidatas, kurio taisykles galima aptarti gynimo metu.
    """

    def __init__(self, base_risk: float = 0.08):
        self.base_risk = base_risk

    def fit(self, X: pd.DataFrame, y: pd.Series):
        self.classes_ = np.array([0, 1])
        self.training_bad_rate_ = float(np.mean(y))
        return self

    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        if not isinstance(X, pd.DataFrame):
            raise TypeError("FuzzyRiskClassifier laukia pandas DataFrame įvesties.")
        duration = _linear_membership(_series(X, "duration", 24), 6, 48)
        amount = _linear_membership(_series(X, "credit_amount", 2500), 1000, 8000)
        checking = _category_risk(_series(X, "checking_status", "unknown"), {
            "<0": 1.0, "a11": 1.0,
            "0<=x<200": 0.65, "a12": 0.65,
            ">=200": 0.25, "a13": 0.25,
            "no checking": 0.40, "a14": 0.40,
        }, 0.55)
        savings = _category_risk(_series(X, "savings_status", "unknown"), {
            "<100": 0.85, "a61": 0.85,
            "100<=x<500": 0.60, "a62": 0.60,
            "500<=x<1000": 0.40, "a63": 0.40,
            ">=1000": 0.20, "a64": 0.20,
            "no known savings": 0.50, "a65": 0.50,
        }, 0.55)
        risk = self.base_risk + 0.26 * duration + 0.29 * amount + 0.27 * checking + 0.18 * savings
        bad_probability = np.clip(risk, 0.01, 0.99)
        return np.column_stack((1.0 - bad_probability, bad_probability))

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        return (self.predict_proba(X)[:, 1] >= 0.5).astype(int)
