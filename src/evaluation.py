"""Kartotinis vertinimas, kaštų slenkstis, kalibracija ir papildomos analizės."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from joblib import dump
from sklearn.base import clone
from sklearn.calibration import calibration_curve
from sklearn.metrics import (
    average_precision_score,
    balanced_accuracy_score,
    brier_score_loss,
    confusion_matrix,
)
from sklearn.model_selection import (
    RandomizedSearchCV,
    RepeatedStratifiedKFold,
    StratifiedKFold,
    cross_val_predict,
)

from .models import TUNABLE_MODELS, build_model, parameter_space


def bad_probability(estimator, features: pd.DataFrame) -> np.ndarray:
    probabilities = estimator.predict_proba(features)
    classes = list(estimator.classes_)
    return probabilities[:, classes.index(1)]


def expected_cost(y_true, probabilities, threshold: float, false_positive: float, false_negative: float) -> float:
    predicted_bad = np.asarray(probabilities) >= threshold
    y = np.asarray(y_true, dtype=int)
    false_positive_count = int(np.sum((y == 0) & predicted_bad))
    false_negative_count = int(np.sum((y == 1) & ~predicted_bad))
    return float((false_positive * false_positive_count + false_negative * false_negative_count) / len(y))


def choose_cost_threshold(y_true, probabilities, false_positive: float, false_negative: float) -> float:
    candidates = np.linspace(0.01, 0.99, 99)
    costs = [expected_cost(y_true, probabilities, value, false_positive, false_negative) for value in candidates]
    return float(candidates[int(np.argmin(costs))])


def metric_row(
    y_true,
    probabilities,
    threshold: float,
    false_positive: float,
    false_negative: float,
) -> dict[str, float | int]:
    y = np.asarray(y_true, dtype=int)
    p = np.asarray(probabilities, dtype=float)
    prediction = (p >= threshold).astype(int)
    tn, fp, fn, tp = confusion_matrix(y, prediction, labels=[0, 1]).ravel()
    return {
        "balanced_accuracy": float(balanced_accuracy_score(y, prediction)),
        "pr_auc": float(average_precision_score(y, p)),
        "brier_score": float(brier_score_loss(y, p)),
        "expected_cost": expected_cost(y, p, threshold, false_positive, false_negative),
        "threshold": float(threshold),
        "tn": int(tn), "fp": int(fp), "fn": int(fn), "tp": int(tp),
    }


def _inner_cv(seed: int, splits: int) -> StratifiedKFold:
    return StratifiedKFold(n_splits=splits, shuffle=True, random_state=seed)


@dataclass
class FittedModel:
    estimator: Any
    threshold: float
    selected_parameters: dict[str, Any]


def tune_and_fit(
    model_name: str,
    X_train: pd.DataFrame,
    y_train: pd.Series,
    settings: dict[str, Any],
    seed: int,
) -> FittedModel:
    """Parenka parametrus ir slenkstį tik iš pateikto mokymo rinkinio."""
    eval_config = settings["evaluation"]
    estimator = build_model(
        model_name,
        X_train,
        seed,
        settings["preprocessing"]["drop_sensitive_features"],
        settings["models"]["mlp_max_iter"],
    )
    inner = _inner_cv(seed, eval_config["inner_splits"])
    params: dict[str, Any] = {}
    if model_name in TUNABLE_MODELS:
        search = RandomizedSearchCV(
            estimator=estimator,
            param_distributions=parameter_space(model_name),
            n_iter=eval_config["tuning_trials"],
            scoring="average_precision",
            cv=inner,
            n_jobs=eval_config["n_jobs"],
            random_state=seed,
            refit=True,
        )
        search.fit(X_train, y_train)
        estimator = search.best_estimator_
        params = {key: str(value) for key, value in search.best_params_.items()}
    else:
        estimator.fit(X_train, y_train)

    # out-of-fold tikimybės skirtos tik slenksčiui pasirinkti mokymo dalyje
    oof_estimator = clone(estimator)
    oof_probabilities = cross_val_predict(
        oof_estimator,
        X_train,
        y_train,
        cv=inner,
        method="predict_proba",
        n_jobs=eval_config["n_jobs"],
    )
    # Target kodavimas šiame projekte visada yra good=0, bad=1.
    # cross_val_predict paliktos estimatoriaus kopijos neatnaujina, todėl klasės
    # negali būti skaitomos iš oof_estimator po šio kvietimo.
    bad_index = 1
    threshold = choose_cost_threshold(
        y_train,
        oof_probabilities[:, bad_index],
        settings["costs"]["false_positive"],
        settings["costs"]["false_negative"],
    )
    estimator.fit(X_train, y_train)
    return FittedModel(estimator=estimator, threshold=threshold, selected_parameters=params)


def run_outer_evaluation(
    X_development: pd.DataFrame,
    y_development: pd.Series,
    model_names: list[str],
    settings: dict[str, Any],
) -> pd.DataFrame:
    """Palygina metodus tuo pačiu kartotiniu stratifikaciniu išoriniu CV."""
    evaluation = settings["evaluation"]
    outer = RepeatedStratifiedKFold(
        n_splits=evaluation["outer_splits"],
        n_repeats=evaluation["outer_repeats"],
        random_state=settings["seed"],
    )
    rows = []
    for split_number, (train_index, valid_index) in enumerate(outer.split(X_development, y_development), start=1):
        X_train, X_valid = X_development.iloc[train_index], X_development.iloc[valid_index]
        y_train, y_valid = y_development.iloc[train_index], y_development.iloc[valid_index]
        for model_offset, model_name in enumerate(model_names):
            print(f"CV {split_number}: {model_name}", flush=True)
            fitted = tune_and_fit(model_name, X_train, y_train, settings, settings["seed"] + split_number + model_offset)
            probabilities = bad_probability(fitted.estimator, X_valid)
            row = metric_row(
                y_valid,
                probabilities,
                fitted.threshold,
                settings["costs"]["false_positive"],
                settings["costs"]["false_negative"],
            )
            row.update({
                "model": model_name,
                "outer_split": split_number,
                "parameters": json.dumps(fitted.selected_parameters, ensure_ascii=False),
            })
            rows.append(row)
    return pd.DataFrame(rows)


def summarise_outer_results(results: pd.DataFrame) -> pd.DataFrame:
    metrics = ["balanced_accuracy", "pr_auc", "brier_score", "expected_cost"]
    summary = results.groupby("model")[metrics].agg(["mean", "std", "median"])
    summary.columns = ["_".join(column) for column in summary.columns]
    return summary.reset_index().sort_values("expected_cost_mean")


def calibration_rows(y_true, probabilities, bins: int) -> pd.DataFrame:
    observed, predicted = calibration_curve(y_true, probabilities, n_bins=bins, strategy="uniform")
    return pd.DataFrame({"mean_predicted_probability": predicted, "observed_bad_rate": observed})


def fairness_audit(
    X: pd.DataFrame,
    y: pd.Series,
    probabilities: np.ndarray,
    threshold: float,
) -> pd.DataFrame:
    """Nedidelis diagnostinis, o ne teisingumo įrodymo, grupių auditas."""
    audit = X.copy()
    audit["target"] = np.asarray(y)
    audit["prediction"] = (probabilities >= threshold).astype(int)
    groups: dict[str, pd.Series] = {}
    if "age" in audit:
        groups["age_group"] = np.where(pd.to_numeric(audit["age"], errors="coerce") < 25, "under_25", "25_or_over")
    if "personal_status" in audit:
        status = audit["personal_status"].astype(str).str.lower()
        groups["personal_status_group"] = np.where(status.str.contains("female"), "female", "other")
    records = []
    for audit_name, labels in groups.items():
        local = audit.copy()
        local["group"] = labels
        for label, group in local.groupby("group"):
            if len(group) < 5:
                continue
            tn, fp, fn, tp = confusion_matrix(group["target"], group["prediction"], labels=[0, 1]).ravel()
            records.append({
                "audit": audit_name,
                "group": label,
                "n": len(group),
                "bad_recall": tp / (tp + fn) if tp + fn else np.nan,
                "good_rejection_rate": fp / (fp + tn) if fp + tn else np.nan,
            })
    return pd.DataFrame(records)


def mask_values(frame: pd.DataFrame, fraction: float, seed: int) -> pd.DataFrame:
    """Sukuria testavimo kopiją su dirbtinai trūkstamomis reikšmėmis."""
    masked = frame.copy()
    random = np.random.default_rng(seed)
    positions = random.random(masked.shape) < fraction
    masked = masked.mask(positions)
    return masked


def error_examples(
    features: pd.DataFrame,
    y_true: pd.Series,
    probabilities: np.ndarray,
    threshold: float,
    per_error_type: int = 5,
) -> pd.DataFrame:
    """Parenka kelis aiškinamus, didžiausios rizikos klasifikavimo pavyzdžius.

    False negative atvejai rikiuojami nuo mažiausios priskirtos blogos rizikos
    tikimybės, o false positive - nuo didžiausios. Taip ataskaitoje matomos ne
    ribinės, o modelio labiausiai užtikrintos klaidos.
    """
    ledger = features.copy()
    ledger.insert(0, "test_row", ledger.index)
    ledger["actual_class"] = np.where(np.asarray(y_true, dtype=int) == 1, "bad", "good")
    ledger["predicted_class"] = np.where(np.asarray(probabilities) >= threshold, "bad", "good")
    ledger["bad_probability"] = np.asarray(probabilities, dtype=float)
    ledger["decision_threshold"] = threshold
    ledger["error_type"] = np.select(
        [
            (ledger["actual_class"] == "bad") & (ledger["predicted_class"] == "good"),
            (ledger["actual_class"] == "good") & (ledger["predicted_class"] == "bad"),
        ],
        ["false_negative", "false_positive"],
        default="correct",
    )
    selected_columns = [
        name for name in (
            "test_row", "error_type", "actual_class", "predicted_class", "bad_probability",
            "decision_threshold", "duration", "credit_amount", "checking_status", "purpose", "age",
        )
        if name in ledger.columns
    ]
    false_negatives = ledger.loc[ledger["error_type"] == "false_negative"].nsmallest(
        per_error_type, "bad_probability"
    )
    false_positives = ledger.loc[ledger["error_type"] == "false_positive"].nlargest(
        per_error_type, "bad_probability"
    )
    return pd.concat([false_negatives, false_positives], ignore_index=True)[selected_columns]


def save_fitted_model(fitted: FittedModel, output_path: str | Path) -> None:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    dump({"estimator": fitted.estimator, "threshold": fitted.threshold, "parameters": fitted.selected_parameters}, path)
