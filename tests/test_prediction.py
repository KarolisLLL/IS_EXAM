import numpy as np
import pandas as pd
import pytest
from sklearn.dummy import DummyClassifier

from src.predict import predict_frame


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
