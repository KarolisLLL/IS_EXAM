import pandas as pd
from sklearn.pipeline import Pipeline
from src.models import build_model, parameter_space
import numpy as np
from src.evaluation import choose_cost_threshold, expected_cost, metric_row
from src.data import REQUIRED_COLUMNS, split_development_and_test, validate_credit_g
from src.evaluation import error_examples
from src.fuzzy import FuzzyRiskClassifier
import pytest
from sklearn.dummy import DummyClassifier
from src.predict import predict_frame


def test_calibration_refits_preprocessing_inside_folds():
    frame = pd.read_csv("examples/applications.csv")
    model = build_model("svm", frame, 2026, False, 400)
    assert isinstance(model.estimator, Pipeline)
    for key, values in parameter_space("svm").items():
        model.set_params(**{key: values[0]})


def test_expected_cost_counts_false_positive_and_false_negative():
    y = np.array([0, 1, 1, 0])
    probabilities = np.array([0.8, 0.2, 0.9, 0.1])
    # FP: pirmas įrašas (1); FN: antras įrašas (5); N = 4.
    assert expected_cost(y, probabilities, 0.5, false_positive=1, false_negative=5) == 1.5


def test_cost_threshold_is_a_probability_in_range():
    y = np.array([0, 0, 1, 1])
    probabilities = np.array([0.05, 0.35, 0.65, 0.95])
    threshold = choose_cost_threshold(y, probabilities, 1, 5)
    assert 0.01 <= threshold <= 0.99


def test_metric_row_contains_required_metrics():
    result = metric_row(np.array([0, 1]), np.array([0.1, 0.9]), 0.5, 1, 5)
    assert {"balanced_accuracy", "pr_auc", "brier_score", "expected_cost", "fp", "fn"}.issubset(result)


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


def test_fuzzy_classifier_returns_two_probabilities_per_row():
    features = pd.DataFrame({
        "duration": [12, 48],
        "credit_amount": [1000, 9000],
        "checking_status": [">=200", "<0"],
        "savings_status": [">=1000", "<100"],
    })
    model = FuzzyRiskClassifier().fit(features, pd.Series([0, 1]))
    probabilities = model.predict_proba(features)
    assert probabilities.shape == (2, 2)
    assert (probabilities >= 0).all() and (probabilities <= 1).all()
    assert probabilities[1, 1] > probabilities[0, 1]


def test_saved_threshold_controls_decision():
    frame = pd.read_csv("examples/applications.csv")
    estimator = DummyClassifier(strategy="prior").fit(frame, [0, 1])
    bundle = {"estimator": estimator, "threshold": 0.4}
    result = predict_frame(bundle, frame)
    assert result.predicted_class.tolist() == ["bad", "bad"]
    bundle["threshold"] = 0.6
    assert predict_frame(bundle, frame).predicted_class.tolist() == ["good", "good"]


def test_rejects_incomplete_schema():
    with pytest.raises(ValueError, match="Trūksta"):
        predict_frame({}, pd.DataFrame({"age": [20]}))


def test_rejects_infinite_numeric_value():
    frame = pd.read_csv("examples/applications.csv")
    frame["age"] = np.inf
    with pytest.raises(ValueError, match="Begalinė"):
        predict_frame({}, frame)
