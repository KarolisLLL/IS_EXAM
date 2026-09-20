"""Duomenų transformavimas be nutekėjimo į validavimo ar testo duomenis."""

from __future__ import annotations

import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler


SENSITIVE_COLUMNS = ("age", "personal_status")


def choose_columns(frame: pd.DataFrame, drop_sensitive_features: bool) -> tuple[list[str], list[str]]:
    excluded = set(SENSITIVE_COLUMNS) if drop_sensitive_features else set()
    usable = [name for name in frame.columns if name not in excluded]
    numeric = [name for name in usable if pd.api.types.is_numeric_dtype(frame[name])]
    categorical = [name for name in usable if name not in numeric]
    if not numeric and not categorical:
        raise ValueError("Požymių sąrašas tuščias.")
    return numeric, categorical


def make_preprocessor(frame: pd.DataFrame, drop_sensitive_features: bool) -> ColumnTransformer:
    numeric, categorical = choose_columns(frame, drop_sensitive_features)
    transformers = []
    if numeric:
        transformers.append(("numeric", Pipeline([
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
        ]), numeric))
    if categorical:
        transformers.append(("categorical", Pipeline([
            ("imputer", SimpleImputer(strategy="most_frequent")),
            ("onehot", OneHotEncoder(handle_unknown="ignore")),
        ]), categorical))
    return ColumnTransformer(transformers=transformers, remainder="drop")
