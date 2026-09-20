"""Pagrindinė paleidimo komanda kreditų rizikos eksperimentui."""

from __future__ import annotations

import argparse
import json
import platform
from datetime import datetime, timezone
from importlib.metadata import version
from pathlib import Path

import pandas as pd
import yaml

from .data import fetch_credit_g, save_manifest, split_development_and_test
from .evaluation import (
    bad_probability,
    calibration_rows,
    error_examples,
    fairness_audit,
    mask_values,
    metric_row,
    run_outer_evaluation,
    save_fitted_model,
    summarise_outer_results,
    tune_and_fit,
)
from .plots import save_calibration_plot, save_model_comparison
from .results_view import create_results_view


def load_settings(config_path: str | Path) -> dict:
    with Path(config_path).open("r", encoding="utf-8") as stream:
        return yaml.safe_load(stream)


def quick_settings(settings: dict) -> dict:
    """Mažas paleidimas, skirtas patikrinti, ar visa grandinė veikia."""
    settings = json.loads(json.dumps(settings))
    settings["evaluation"].update({"outer_splits": 3, "outer_repeats": 1, "inner_splits": 2, "tuning_trials": 2})
    return settings


def main() -> None:
    parser = argparse.ArgumentParser(description="Credit-g kredito rizikos eksperimentas")
    parser.add_argument("--config", default="config/experiment.yaml")
    parser.add_argument("--quick", action="store_true", help="Trumpas grandinės patikrinimas")
    parser.add_argument("--models", help="Kableliais atskirtas modelių sąrašas")
    parser.add_argument("--output", help="Atskiras rezultatų katalogas")
    args = parser.parse_args()

    settings = load_settings(args.config)
    if args.quick:
        settings = quick_settings(settings)
    model_names = args.models.split(",") if args.models else settings["models"]["active"]

    output_dir = Path(args.output or ("results/quick" if args.quick else settings["output"]["directory"]))
    output_dir.mkdir(parents=True, exist_ok=True)
    settings["output"]["directory"] = str(output_dir)
    (output_dir / "run_manifest.json").write_text(json.dumps({
        "started_utc": datetime.now(timezone.utc).isoformat(),
        "python": platform.python_version(),
        "packages": {p: version(p) for p in ["numpy", "pandas", "scikit-learn", "PyYAML", "joblib", "matplotlib"]},
        "quick": args.quick, "models": model_names, "settings": settings,
    }, indent=2), encoding="utf-8")
    dataset = fetch_credit_g(settings["data"]["openml_data_id"], settings["data"]["cache_dir"])
    save_manifest(dataset.manifest, output_dir / "data_manifest.json")

    X_dev, X_test, y_dev, y_test = split_development_and_test(
        dataset.features,
        dataset.target,
        settings["data"]["holdout_size"],
        settings["seed"],
    )
    outer_results = run_outer_evaluation(X_dev, y_dev, model_names, settings)
    outer_results.to_csv(output_dir / "outer_fold_results.csv", index=False)
    summary = summarise_outer_results(outer_results)
    summary.to_csv(output_dir / "model_summary.csv", index=False)
    save_model_comparison(summary, output_dir / "model_comparison.png")

    # Modelis pasirenkamas pagal mažiausią CV klaidų kainą, ne pagal galutinio testo rezultatą.
    selected_name = str(summary.iloc[0]["model"])
    fitted = tune_and_fit(selected_name, X_dev, y_dev, settings, settings["seed"])
    test_probabilities = bad_probability(fitted.estimator, X_test)
    final_metrics = metric_row(
        y_test,
        test_probabilities,
        fitted.threshold,
        settings["costs"]["false_positive"],
        settings["costs"]["false_negative"],
    )
    final_metrics.update({"selected_model": selected_name, "parameters": fitted.selected_parameters})
    (output_dir / "final_test_metrics.json").write_text(json.dumps(final_metrics, ensure_ascii=False, indent=2), encoding="utf-8")
    calibration = calibration_rows(y_test, test_probabilities, settings["evaluation"]["calibration_bins"])
    calibration.to_csv(output_dir / "calibration_final_test.csv", index=False)
    save_calibration_plot(calibration, output_dir / "calibration_final_test.png")
    error_examples(X_test, y_test, test_probabilities, fitted.threshold).to_csv(
        output_dir / "error_examples.csv", index=False
    )
    fairness_audit(X_test, y_test, test_probabilities, fitted.threshold).to_csv(
        output_dir / "fairness_audit.csv", index=False
    )

    # Iš anksto apibrėžta požymių jautrumo abliacija. Variantui be age ir
    # personal_status parametrai bei slenkstis vėl parenkami tik development dalyje.
    ablation_settings = json.loads(json.dumps(settings))
    ablation_settings["preprocessing"]["drop_sensitive_features"] = True
    ablated = tune_and_fit(selected_name, X_dev, y_dev, ablation_settings, settings["seed"] + 101)
    ablated_probabilities = bad_probability(ablated.estimator, X_test)
    ablation_rows = []
    for label, probabilities, threshold in (
        ("all_features", test_probabilities, fitted.threshold),
        ("without_age_and_personal_status", ablated_probabilities, ablated.threshold),
    ):
        row = metric_row(
            y_test,
            probabilities,
            threshold,
            settings["costs"]["false_positive"],
            settings["costs"]["false_negative"],
        )
        row["feature_set"] = label
        ablation_rows.append(row)
    pd.DataFrame(ablation_rows).to_csv(output_dir / "sensitive_feature_ablation.csv", index=False)

    robustness_rows = []
    for fraction in (0.05, 0.10):
        masked = mask_values(X_test, fraction, settings["seed"] + int(fraction * 100))
        probabilities = bad_probability(fitted.estimator, masked)
        row = metric_row(y_test, probabilities, fitted.threshold, settings["costs"]["false_positive"], settings["costs"]["false_negative"])
        row["missing_fraction"] = fraction
        robustness_rows.append(row)
    pd.DataFrame(robustness_rows).to_csv(output_dir / "missing_value_robustness.csv", index=False)
    save_fitted_model(fitted, output_dir / "selected_model.joblib")
    create_results_view(output_dir, y_test, test_probabilities, fitted.threshold,
                        settings["costs"]["false_positive"], settings["costs"]["false_negative"])

    print(f"Pasirinktas modelis: {selected_name}")
    print(f"Galutinio testo expected_cost: {final_metrics['expected_cost']:.4f}")
    print(f"Rezultatai: {output_dir.resolve()}")


if __name__ == "__main__":
    main()
