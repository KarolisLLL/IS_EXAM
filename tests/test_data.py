import numpy as np
import pandas as pd

from src.data import REQUIRED_COLUMNS, split_development_and_test, validate_credit_g
from src.evaluation import error_examples


def test_credit_g_schema_validation_accepts_expected_columns():
    frame = pd.DataFrame({column: [1, 2, 3, 4] for column in REQUIRED_COLUMNS})
    target = pd.Series(["good", "bad", "good", "bad"])
    validate_credit_g(frame, target)


def test_final_test_is_disjoint_from_development_set():
    frame = pd.DataFrame({"value": range(20)})
    target = pd.Series([0, 1] * 10)
    development, final_test, _, _ = split_development_and_test(frame, target, 0.2, 2026)
    assert set(development.index).isdisjoint(set(final_test.index))


def test_error_examples_include_both_error_types():
    features = pd.DataFrame({
        "duration": [12, 24, 36, 48],
        "credit_amount": [1000, 2000, 3000, 4000],
        "checking_status": ["<0", "<0", ">=200", ">=200"],
    }, index=[10, 11, 12, 13])
    errors = error_examples(
        features,
        pd.Series([1, 0, 1, 0], index=features.index),
        np.array([0.01, 0.99, 0.95, 0.02]),
        threshold=0.5,
    )
    assert set(errors["error_type"]) == {"false_negative", "false_positive"}
    assert set(errors["test_row"]) == {10, 11}
