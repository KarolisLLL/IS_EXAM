"""Paprasti, atkuriami rezultatų grafikai galutinei ataskaitai."""

from __future__ import annotations

import os
from pathlib import Path

# Atskiras katalogas išvengia vartotojo profilio Matplotlib talpyklos problemų
# ir užtikrina, kad grafikai būtų generuojami be ekrano serverio.
os.environ.setdefault("MPLCONFIGDIR", str(Path(__file__).resolve().parents[1] / ".mplconfig"))

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd


def save_model_comparison(summary: pd.DataFrame, output_path: str | Path) -> None:
    """Išsaugo dviejų svarbiausių modelių palyginimo rodiklių grafiką."""
    ordered = summary.sort_values("expected_cost_mean")
    fig, axes = plt.subplots(1, 2, figsize=(10, 4.5))
    axes[0].bar(ordered["model"], ordered["expected_cost_mean"], color="#4C78A8")
    axes[0].set_title("Vidutinė klaidų kaina")
    axes[0].set_ylabel("Expected cost")
    axes[0].set_xlabel("Modelis")

    axes[1].bar(ordered["model"], ordered["pr_auc_mean"], color="#59A14F")
    axes[1].set_title("PR AUC")
    axes[1].set_ylabel("PR AUC")
    axes[1].set_xlabel("Modelis")

    for axis in axes:
        axis.tick_params(axis="x", rotation=35)
        axis.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    fig.savefig(output_path, dpi=180, bbox_inches="tight")
    plt.close(fig)


def save_calibration_plot(calibration: pd.DataFrame, output_path: str | Path) -> None:
    """Išsaugo pasirinkto modelio kalibracijos diagramą galutiniam testui."""
    fig, axis = plt.subplots(figsize=(5.5, 4.5))
    axis.plot([0, 1], [0, 1], "--", color="#666666", label="Tobula kalibracija")
    axis.plot(
        calibration["mean_predicted_probability"],
        calibration["observed_bad_rate"],
        marker="o",
        color="#E15759",
        label="Pasirinktas modelis",
    )
    axis.set_title("Kalibracija galutiniame teste")
    axis.set_xlabel("Vidutinė prognozuota bad tikimybė")
    axis.set_ylabel("Stebėta bad dalis")
    axis.set_xlim(0, 1)
    axis.set_ylim(0, 1)
    axis.legend()
    axis.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    fig.savefig(output_path, dpi=180, bbox_inches="tight")
    plt.close(fig)
