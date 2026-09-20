import pandas as pd
from sklearn.pipeline import Pipeline
from src.models import build_model, parameter_space


def test_calibration_refits_preprocessing_inside_folds():
    frame = pd.read_csv("examples/applications.csv")
    model = build_model("svm", frame, 2026, False, 400)
    assert isinstance(model.estimator, Pipeline)
    for key, values in parameter_space("svm").items():
        model.set_params(**{key: values[0]})
