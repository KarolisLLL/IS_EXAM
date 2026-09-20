import pandas as pd

from src.fuzzy import FuzzyRiskClassifier


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
