"""Prognozuoja naujas paraiškas iš CSV naudodamas išsaugotą modelį."""
from __future__ import annotations

import argparse
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

from .data import REQUIRED_COLUMNS
from .evaluation import bad_probability

NUMERIC_COLUMNS = {
    "duration", "credit_amount", "installment_commitment", "residence_since",
    "age", "existing_credits", "num_dependents",
}


def predict_frame(bundle: dict, frame: pd.DataFrame) -> pd.DataFrame:
    missing = REQUIRED_COLUMNS.difference(frame.columns)
    if missing:
        raise ValueError(f"Trūksta požymių stulpelių: {sorted(missing)}")
    if frame.empty:
        raise ValueError("Paraiškų failas tuščias.")
    features = frame.loc[:, sorted(REQUIRED_COLUMNS)].copy()
    for name in NUMERIC_COLUMNS:
        features[name] = pd.to_numeric(features[name], errors="raise")
        if np.isinf(features[name].to_numpy(dtype=float)).any():
            raise ValueError(f"Begalinė reikšmė stulpelyje {name}")
    probabilities = bad_probability(bundle["estimator"], features)
    threshold = float(bundle["threshold"])
    return pd.DataFrame({
        "row": np.arange(1, len(features) + 1),
        "bad_probability": probabilities,
        "threshold": threshold,
        "predicted_class": np.where(probabilities >= threshold, "bad", "good"),
    })


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", default="results/final/selected_model.joblib")
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", default="results/predictions.csv")
    args = parser.parse_args()
    # joblib failai turi būti tik iš patikimo šaltinio, nes gali vykdyti kodą.
    bundle = joblib.load(args.model)
    result = predict_frame(bundle, pd.read_csv(args.input))
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    result.to_csv(output, index=False)
    print(result.to_string(index=False))
    print(f"Išsaugota: {output.resolve()}")


if __name__ == "__main__":
    main()
