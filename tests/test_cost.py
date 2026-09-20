import numpy as np

from src.evaluation import choose_cost_threshold, expected_cost, metric_row


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
