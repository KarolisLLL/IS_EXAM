"""OpenML credit-g gavimas, tikrinimas ir skaidymas."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from pathlib import Path
from typing import Any

import pandas as pd
from sklearn.datasets import fetch_openml
from sklearn.model_selection import train_test_split


REQUIRED_COLUMNS = {
    "checking_status", "duration", "credit_history", "purpose", "credit_amount",
    "savings_status", "employment", "installment_commitment", "personal_status",
    "other_parties", "residence_since", "property_magnitude", "age",
    "other_payment_plans", "housing", "existing_credits", "job",
    "num_dependents", "own_telephone", "foreign_worker",
}


@dataclass(frozen=True)
class CreditData:
    features: pd.DataFrame
    target: pd.Series
    manifest: dict[str, Any]


def _canonical_checksum(features: pd.DataFrame, target: pd.Series) -> str:
    """Sukuria stabilų turinio kontrolinės sumos atitikmenį ataskaitai."""
    frame = features.copy()
    frame["__target__"] = target.astype(str).to_numpy()
    csv = frame.sort_index(axis=1).to_csv(index=False).encode("utf-8")
    return sha256(csv).hexdigest()


def validate_credit_g(features: pd.DataFrame, raw_target: pd.Series) -> None:
    """Sustabdo darbą, jei OpenML schema neatitinka numatytos credit-g struktūros."""
    missing = REQUIRED_COLUMNS.difference(features.columns)
    if missing:
        raise ValueError(f"Trūksta credit-g stulpelių: {sorted(missing)}")
    labels = {str(value).strip().lower() for value in raw_target.dropna().unique()}
    if labels != {"good", "bad"}:
        raise ValueError(f"Netikėtos tikslinės klasės: {sorted(labels)}")
    if features.empty:
        raise ValueError("Duomenų rinkinys tuščias.")
    if raw_target.isna().any():
        raise ValueError("Tikslinėje klasėje yra trūkstamų reikšmių.")


def fetch_credit_g(data_id: int, cache_dir: str | Path) -> CreditData:
    """Atsisiunčia credit-g iš OpenML ir įrašo tik metaduomenis, ne duomenų kopiją."""
    cache_path = Path(cache_dir)
    cache_path.mkdir(parents=True, exist_ok=True)
    bunch = fetch_openml(data_id=data_id, as_frame=True, data_home=str(cache_path))
    features = bunch.data.copy()
    raw_target = pd.Series(bunch.target, name="target").copy()
    validate_credit_g(features, raw_target)

    target = raw_target.astype(str).str.strip().str.lower().eq("bad").astype(int)
    details = getattr(bunch, "details", {}) or {}
    manifest = {
        "openml_data_id": data_id,
        "dataset_name": details.get("name", "credit-g") if isinstance(details, dict) else "credit-g",
        "source_url": f"https://www.openml.org/d/{data_id}",
        "rows": int(features.shape[0]),
        "columns": list(features.columns),
        "target_mapping": {"good": 0, "bad": 1},
        "bad_class_count": int(target.sum()),
        "good_class_count": int((1 - target).sum()),
        "content_sha256": _canonical_checksum(features, raw_target),
        "openml_version": details.get("version") if isinstance(details, dict) else None,
    }
    return CreditData(features=features, target=target, manifest=manifest)


def save_manifest(manifest: dict[str, Any], output_path: str | Path) -> None:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")


def split_development_and_test(
    features: pd.DataFrame,
    target: pd.Series,
    holdout_size: float,
    seed: int,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series]:
    """Sukuria vieną užrakintą stratifikacinį galutinį testą."""
    return train_test_split(
        features,
        target,
        test_size=holdout_size,
        random_state=seed,
        stratify=target,
    )
