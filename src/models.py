"""Modelių kūrimas ir paprasta hiperparametrų paieškos erdvė."""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.calibration import CalibratedClassifierCV
from sklearn.dummy import DummyClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.neural_network import MLPClassifier
from sklearn.pipeline import Pipeline
from sklearn.svm import SVC

from .fuzzy import FuzzyRiskClassifier
from .preprocess import make_preprocessor


TUNABLE_MODELS = {"logistic", "svm", "mlp"}


def build_model(
    name: str,
    frame: pd.DataFrame,
    seed: int,
    drop_sensitive_features: bool,
    mlp_max_iter: int,
):
    if name == "fuzzy":
        return FuzzyRiskClassifier()
    if name == "majority":
        estimator = DummyClassifier(strategy="most_frequent")
    elif name == "reject_all":
        estimator = DummyClassifier(strategy="constant", constant=1)
    elif name == "logistic":
        estimator = LogisticRegression(max_iter=1000, solver="liblinear", random_state=seed)
    elif name == "svm":
        # Transformacijos mokomos atskirai ir kiekviename kalibracijos skaidyme.
        return CalibratedClassifierCV(
            estimator=Pipeline([
                ("preprocessor", make_preprocessor(frame, drop_sensitive_features)),
                ("model", SVC(kernel="rbf", random_state=seed)),
            ]),
            method="sigmoid",
            cv=3,
            ensemble=False,
        )
    elif name == "mlp":
        estimator = MLPClassifier(
            max_iter=mlp_max_iter,
            early_stopping=True,
            random_state=seed,
        )
    else:
        raise ValueError(f"Nežinomas modelis: {name}")
    return Pipeline([
        ("preprocessor", make_preprocessor(frame, drop_sensitive_features)),
        ("model", estimator),
    ])


def parameter_space(name: str) -> dict[str, list]:
    if name == "logistic":
        return {
            "model__C": list(np.logspace(-2, 2, 9)),
            "model__class_weight": [None, "balanced"],
        }
    if name == "svm":
        return {
            "estimator__model__C": list(np.logspace(-1, 2, 10)),
            "estimator__model__gamma": ["scale", 0.001, 0.01, 0.05, 0.1],
            "estimator__model__class_weight": [None, "balanced"],
        }
    if name == "mlp":
        return {
            "model__hidden_layer_sizes": [(16,), (32,), (32, 16)],
            "model__alpha": [0.0001, 0.001, 0.01],
            "model__learning_rate_init": [0.001, 0.01],
        }
    return {}
